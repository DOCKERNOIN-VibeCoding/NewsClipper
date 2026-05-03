"""Gemini AI 통합 기사 분석기

하나의 API 호출로 다음 3가지를 동시에 수행:
  A) 관련도 검증 (core / relevant / passing / irrelevant)
  B) 2~3문장 한국어 요약
  C) 엔티티 추출 + 카테고리 태깅 (자사/경쟁사/업계)

특징:
  - 배치 처리(기본 5건/호출)로 API 호출 수 최소화
  - 3회 지수 백오프 재시도
  - 일일 한도 초과/연속 실패 시 로컬 키워드 매칭으로 fallback
  - JSON 파싱 실패 시 기사별 skip (전체 파이프라인은 계속)
"""

from __future__ import annotations

import json
import re
import time
import logging
from typing import Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════
#  상수
# ═══════════════════════════════════════════════════════════
DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_BATCH_SIZE = 5
DEFAULT_MAX_RETRIES = 3
DEFAULT_TIMEOUT_SEC = 30
DEFAULT_BACKOFF_BASE = 2.0  # 1차 2s, 2차 4s, 3차 8s

VALID_RELEVANCE = {"core", "relevant", "passing", "irrelevant"}
VALID_CATEGORY = {"product", "company", "competitor", "industry", "unknown"}
VALID_SENTIMENT = {"positive", "neutral", "negative"}


# ═══════════════════════════════════════════════════════════
#  메인 클래스
# ═══════════════════════════════════════════════════════════
class ArticleAnalyzer:
    """Gemini 기반 통합 기사 분석기"""

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        batch_size: int = DEFAULT_BATCH_SIZE,
        max_retries: int = DEFAULT_MAX_RETRIES,
        timeout_sec: int = DEFAULT_TIMEOUT_SEC,
    ):
        self.api_key = (api_key or "").strip()
        self.model_name = model
        self.batch_size = max(1, batch_size)
        self.max_retries = max(1, max_retries)
        self.timeout_sec = timeout_sec

        self._client = None
        self._fallback_mode = False  # True가 되면 이후 호출은 모두 로컬 fallback
        self._init_client()

    # ────────────────────────────────────────────────
    #  초기화
    # ────────────────────────────────────────────────
    def _init_client(self):
        """google-genai 클라이언트 초기화. 실패 시 fallback 모드."""
        if not self.api_key:
            logger.warning("Gemini API key가 비어 있습니다. 로컬 fallback 모드로 동작합니다.")
            self._fallback_mode = True
            return

        try:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        except ImportError:
            logger.error(
                "google-genai 패키지를 찾을 수 없습니다. "
                "`pip install google-genai`를 실행해 주세요."
            )
            self._fallback_mode = True
        except Exception as e:
            logger.error(f"Gemini 클라이언트 초기화 실패: {e}")
            self._fallback_mode = True

    @property
    def is_available(self) -> bool:
        """AI가 정상적으로 사용 가능한지 여부"""
        return (not self._fallback_mode) and (self._client is not None)

    # ────────────────────────────────────────────────
    #  공개 API
    # ────────────────────────────────────────────────
    def analyze_articles(
        self,
        articles: List[Dict],
        keyword_groups: Dict[str, List[str]],
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        log_callback: Optional[Callable[[str], None]] = None,
    ) -> List[Dict]:
        """
        기사 리스트에 AI 분석 결과를 추가해 반환.

        각 기사 dict에 추가되는 키:
          - ai_relevance: "core" | "relevant" | "passing" | "irrelevant"
          - ai_relevance_reason: str
          - ai_summary: str
          - ai_category: "product" | "company" | "competitor" | "industry" | "unknown"
          - ai_entities: List[str]
          - ai_sentiment: "positive" | "neutral" | "negative"
          - ai_analyzed: bool   (성공적으로 분석됐는지)
          - ai_fallback: bool   (로컬 fallback으로 채워졌는지)
        """
        if not articles:
            return articles

        total = len(articles)

        def _log(msg: str):
            if log_callback:
                log_callback(msg)

        def _progress(done: int, msg: str):
            if progress_callback:
                progress_callback(done, total, msg)

        # 사용 불가 → 전부 fallback
        if not self.is_available:
            _log(f"  ⚠️ Gemini 사용 불가. 로컬 fallback으로 {total}건 처리합니다.")
            for idx, article in enumerate(articles):
                self._apply_fallback(article, keyword_groups)
                _progress(idx + 1, f"  🔁 로컬 분석 {idx + 1}/{total}")
            return articles

        # 배치 처리
        analyzed_count = 0
        failed_count = 0
        batches = [
            articles[i : i + self.batch_size]
            for i in range(0, total, self.batch_size)
        ]

        _log(f"  🤖 Gemini AI 분석 시작 ({total}건, {len(batches)}배치, 배치당 {self.batch_size}건)")

        for batch_idx, batch in enumerate(batches):
            # fallback 모드로 전환된 경우 남은 기사 모두 로컬 처리
            if self._fallback_mode:
                for article in batch:
                    self._apply_fallback(article, keyword_groups)
                analyzed_count += len(batch)
                _progress(analyzed_count, f"  🔁 fallback {analyzed_count}/{total}")
                continue

            try:
                results = self._analyze_batch(batch, keyword_groups)
                # results는 batch와 같은 길이의 dict 리스트
                for article, result in zip(batch, results):
                    if result is None:
                        # 단건 파싱 실패 → 해당 기사만 fallback
                        self._apply_fallback(article, keyword_groups)
                        failed_count += 1
                    else:
                        self._apply_result(article, result)

            except FallbackTriggered as e:
                # 일일 한도 초과 등 — 이후 모두 로컬 처리
                _log(f"  ⚠️ AI 분석 중단, fallback 전환: {e}")
                self._fallback_mode = True
                for article in batch:
                    self._apply_fallback(article, keyword_groups)

            except Exception as e:
                # 배치 전체 실패 → 해당 배치만 fallback (다음 배치는 시도)
                logger.exception("배치 분석 실패")
                _log(f"  ⚠️ 배치 {batch_idx + 1} 실패, 로컬 처리: {str(e)[:80]}")
                for article in batch:
                    self._apply_fallback(article, keyword_groups)
                failed_count += len(batch)

            analyzed_count += len(batch)
            _progress(
                analyzed_count,
                f"  🤖 AI 분석 중... {analyzed_count}/{total}건"
            )

        # 실제 결과를 정확히 집계 (fallback 모드 전환 후에도 정확)
        actual_succeeded = sum(
            1 for a in articles
            if a.get("ai_analyzed") and not a.get("ai_fallback")
        )
        actual_fallback = sum(1 for a in articles if a.get("ai_fallback"))

        _log(
            f"  ✅ AI 분석 완료 (성공 {actual_succeeded}건, "
            f"fallback {actual_fallback}건)"
        )
        return articles


    # ────────────────────────────────────────────────
    #  배치 1회 분석
    # ────────────────────────────────────────────────
    def _analyze_batch(
        self,
        batch: List[Dict],
        keyword_groups: Dict[str, List[str]],
    ) -> List[Optional[Dict]]:
        prompt = self._build_batch_prompt(batch, keyword_groups)

        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response_text = self._call_gemini(prompt)
                parsed = self._parse_response(response_text, expected_count=len(batch))

                # ── 디버그: 파싱 결과 진단 ──
                none_count = sum(1 for p in parsed if p is None)
                if none_count > 0:
                    logger.warning(
                        f"배치 파싱 부분 실패: 총 {len(batch)}건 중 {none_count}건이 None. "
                        f"응답 앞 300자: {response_text[:300]!r}"
                    )
                else:
                    logger.debug(f"배치 파싱 성공: {len(batch)}건 모두 정상")

                return parsed


            except FallbackTriggered:
                # 즉시 상위로 전파 (재시도 안함)
                raise

            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    sleep_sec = DEFAULT_BACKOFF_BASE ** attempt
                    logger.warning(
                        f"Gemini 호출 실패 (시도 {attempt}/{self.max_retries}): "
                        f"{e} — {sleep_sec:.1f}초 후 재시도"
                    )
                    time.sleep(sleep_sec)
                else:
                    logger.error(f"Gemini 호출 최종 실패: {e}")

        # 모든 재시도 실패
        raise last_error if last_error else RuntimeError("Unknown Gemini error")

    # ────────────────────────────────────────────────
    #  Gemini 호출
    # ────────────────────────────────────────────────
    def _call_gemini(self, prompt: str) -> str:
        """Gemini API 호출. 응답 텍스트 반환."""
        try:
            response = self._client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
        except Exception as e:
            msg = str(e).lower()
            # 일일 한도 / 쿼터 초과 패턴 감지 → fallback 트리거
            if any(k in msg for k in ("quota", "rate limit", "resource_exhausted", "429")):
                raise FallbackTriggered(f"API 한도 초과: {str(e)[:100]}")
            raise

        text = getattr(response, "text", None)
        if not text:
            # 일부 SDK 버전에서는 candidates에 들어 있음
            try:
                text = response.candidates[0].content.parts[0].text
            except Exception:
                text = ""

        if not text:
            raise RuntimeError("Gemini 응답이 비어 있습니다.")

        return text

    # ────────────────────────────────────────────────
    #  프롬프트 생성
    # ────────────────────────────────────────────────
    def _build_batch_prompt(
        self,
        batch: List[Dict],
        keyword_groups: Dict[str, List[str]],
    ) -> str:
        products = ", ".join(keyword_groups.get("products", [])) or "(없음)"
        company = ", ".join(keyword_groups.get("company", [])) or "(없음)"
        competitors = ", ".join(keyword_groups.get("competitors", [])) or "(없음)"
        # industry는 기사용 키워드(조합형)일 수 있어 일반 산업명만 추리는 게 좋지만,
        # 단순히 첫 단어 기반으로 추출해도 의미 있음
        industries = ", ".join(self._extract_industry_terms(keyword_groups.get("industry", []))) or "(없음)"

        articles_block = []
        for idx, art in enumerate(batch, start=1):
            title = (art.get("title") or "").strip()
            media = (art.get("media_name") or art.get("source") or "").strip()
            desc = (art.get("description") or "").strip()
            # description이 너무 길면 자르기 (입력 토큰 절약)
            if len(desc) > 400:
                desc = desc[:400] + "..."
            articles_block.append(
                f"[기사 {idx}]\n"
                f"- 제목: {title}\n"
                f"- 매체: {media}\n"
                f"- 본문: {desc}"
            )

        articles_text = "\n\n".join(articles_block)

        return f"""당신은 한국 뉴스 분석 전문가입니다.

[사용자 설정]
- 자사 제품/브랜드: {products}
- 자사 회사명: {company}
- 경쟁사: {competitors}
- 산업군: {industries}

[기사 목록]
{articles_text}

각 기사를 분석하여 아래 JSON 배열로만 응답하세요. 설명, 주석, 코드블록 없이 JSON만 출력하세요.
배열의 길이는 정확히 {len(batch)}개여야 하며, 입력된 기사 순서를 그대로 따릅니다.

[관련도 판단 기준]
- core: 자사 제품/브랜드/회사가 기사의 주요 주제
- relevant: 의미 있게 다뤄지지만 주제는 아님
- passing: 예시·비교·나열로 잠깐 언급만 됨
- irrelevant: 검색 키워드와 우연히 같은 단어가 들어갔을 뿐 실제로는 무관

[카테고리 기준]
- product: 자사 제품/브랜드 관련
- company: 자사 회사 관련 (제품과 무관)
- competitor: 경쟁사 관련
- industry: 일반 산업 동향
- unknown: 위 어디에도 속하지 않음

응답 형식 (정확히 이 JSON 스키마):
[
  {{
    "index": 1,
    "relevance_type": "core|relevant|passing|irrelevant",
    "relevance_reason": "한 문장으로 판단 근거",
    "summary": "핵심 내용 2~3문장 한국어 요약. 핵심 수치·인물·날짜 포함",
    "category": "product|company|competitor|industry|unknown",
    "entities": ["기업명1", "브랜드명2", "인물명3"],
    "sentiment": "positive|neutral|negative"
  }}
]
"""

    @staticmethod
    def _extract_industry_terms(industry_keywords: List[str]) -> List[str]:
        """파이프라인이 만든 '제품명 + 산업명' 조합에서 산업명만 추출"""
        terms = set()
        for kw in industry_keywords:
            parts = kw.strip().split()
            if len(parts) >= 2:
                terms.add(parts[-1])
            elif parts:
                terms.add(parts[0])
        return sorted(terms)

    # ────────────────────────────────────────────────
    #  응답 파싱
    # ────────────────────────────────────────────────
    def _parse_response(
        self,
        response_text: str,
        expected_count: int,
    ) -> List[Optional[Dict]]:
        """Gemini 응답에서 JSON 배열 추출 → 길이 검증 → 정규화"""
        json_str = self._extract_json_array(response_text)
        if not json_str:
            logger.error(f"JSON 배열 추출 실패. 응답: {response_text[:500]!r}")
            raise ValueError("응답에서 JSON 배열을 찾을 수 없습니다.")

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            # 후행 콤마 등 약식 보정 1회 시도
            fixed = re.sub(r",\s*([\]}])", r"\1", json_str)
            try:
                data = json.loads(fixed)
            except json.JSONDecodeError:
                logger.error(
                    f"JSON 파싱 최종 실패: {e}. "
                    f"파싱 시도한 문자열 앞 300자: {json_str[:300]!r}"
                )
                raise

        if not isinstance(data, list):
            raise ValueError("응답 JSON이 배열이 아닙니다.")

        # ── 배열 길이 검증 ──
        if len(data) != expected_count:
            logger.warning(
                f"배열 길이 불일치: 기대 {expected_count}건, 실제 {len(data)}건. "
                f"누락분은 fallback으로 처리됨."
            )

        # index 키가 있으면 그것 기준으로 정렬, 없으면 입력 순서로 가정
        results: List[Optional[Dict]] = [None] * expected_count
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                logger.warning(f"배열 항목 {i}가 dict가 아님: {type(item).__name__}")
                continue
            idx = item.get("index", i + 1)
            try:
                pos = int(idx) - 1
            except (TypeError, ValueError):
                pos = i
            if 0 <= pos < expected_count:
                results[pos] = self._normalize_result(item)
            else:
                logger.warning(f"인덱스 범위 초과: {idx} (expected_count={expected_count})")

        return results


    @staticmethod
    def _extract_json_array(text: str) -> str:
        """텍스트에서 첫 번째 JSON 배열 블록을 추출"""
        # 코드블록 제거
        text = re.sub(r"```(?:json)?\s*", "", text)
        text = text.replace("```", "")

        # 첫 [ 부터 매칭되는 ] 까지 brace counting
        start = text.find("[")
        if start == -1:
            return ""
        depth = 0
        in_string = False
        escape = False
        for i in range(start, len(text)):
            ch = text[i]
            if escape:
                escape = False
                continue
            if ch == "\\":
                escape = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
        return ""

    @staticmethod
    def _normalize_result(raw: Dict) -> Dict:
        """LLM이 약간 다른 값/형식을 줘도 표준화"""
        rel = str(raw.get("relevance_type", "")).strip().lower()
        if rel not in VALID_RELEVANCE:
            rel = "passing"  # 모호한 경우 안전한 중간값

        cat = str(raw.get("category", "")).strip().lower()
        if cat not in VALID_CATEGORY:
            cat = "unknown"

        sent = str(raw.get("sentiment", "")).strip().lower()
        if sent not in VALID_SENTIMENT:
            sent = "neutral"

        entities = raw.get("entities", [])
        if not isinstance(entities, list):
            entities = []
        # 문자열만, 공백/중복 제거, 길이 제한
        clean_entities: List[str] = []
        seen = set()
        for e in entities:
            if not isinstance(e, str):
                continue
            e = e.strip()
            if e and 1 < len(e) <= 30 and e not in seen:
                seen.add(e)
                clean_entities.append(e)

        summary = str(raw.get("summary", "")).strip()
        if len(summary) > 500:
            summary = summary[:500] + "..."

        reason = str(raw.get("relevance_reason", "")).strip()
        if len(reason) > 200:
            reason = reason[:200] + "..."

        return {
            "relevance_type": rel,
            "relevance_reason": reason,
            "summary": summary,
            "category": cat,
            "entities": clean_entities,
            "sentiment": sent,
        }

    # ────────────────────────────────────────────────
    #  결과 적용
    # ────────────────────────────────────────────────
    @staticmethod
    def _apply_result(article: Dict, result: Dict) -> None:
        article["ai_relevance"] = result["relevance_type"]
        article["ai_relevance_reason"] = result["relevance_reason"]
        article["ai_summary"] = result["summary"]
        article["ai_category"] = result["category"]
        article["ai_entities"] = result["entities"]
        article["ai_sentiment"] = result["sentiment"]
        article["ai_analyzed"] = True
        article["ai_fallback"] = False

    @staticmethod
    def _apply_fallback(article: Dict, keyword_groups: Dict[str, List[str]]) -> None:
        """
        AI 호출 실패 시 로컬 키워드 매칭으로 최소한의 값을 채움.
        v1 파이프라인의 분류 로직과 호환되도록 보수적으로 채움.
        """
        title = (article.get("title") or "").lower()
        desc = (article.get("description") or "").lower()
        text = f"{title} {desc}"

        products = [k.lower() for k in keyword_groups.get("products", [])]
        company = [k.lower() for k in keyword_groups.get("company", [])]
        competitors = [k.lower() for k in keyword_groups.get("competitors", [])]

        product_hit = any(k in text for k in products if k)
        company_hit = any(k in text for k in company if k)
        competitor_hit = any(k in text for k in competitors if k)

        if product_hit:
            relevance, category = "relevant", "product"
        elif company_hit:
            relevance, category = "relevant", "company"
        elif competitor_hit:
            relevance, category = "relevant", "competitor"
        else:
            # 키워드가 본문에 없는데 검색에 걸렸다면 간접언급 가능성
            relevance, category = "passing", "industry"

        article["ai_relevance"] = relevance
        article["ai_relevance_reason"] = "로컬 키워드 매칭 기반 (AI 사용 불가)"
        article["ai_summary"] = (article.get("description") or "")[:200]
        article["ai_category"] = category
        article["ai_entities"] = []
        article["ai_sentiment"] = "neutral"
        article["ai_analyzed"] = False
        article["ai_fallback"] = True


# ═══════════════════════════════════════════════════════════
#  내부 예외
# ═══════════════════════════════════════════════════════════
class FallbackTriggered(Exception):
    """일일 한도 초과 등으로 AI 사용을 즉시 중단해야 할 때"""
    pass


# ═══════════════════════════════════════════════════════════
#  편의 함수: pipeline.py에서 1줄로 호출 가능
# ═══════════════════════════════════════════════════════════
def analyze_with_ai(
    articles: List[Dict],
    keyword_groups: Dict[str, List[str]],
    api_key: str,
    *,
    model: str = DEFAULT_MODEL,
    batch_size: int = DEFAULT_BATCH_SIZE,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    log_callback: Optional[Callable[[str], None]] = None,
) -> Tuple[List[Dict], Dict]:
    """
    파이프라인에서 호출하기 위한 thin wrapper.
    
    Returns:
        (analyzed_articles, ai_stats)
        ai_stats: {
          "total": int,
          "ai_succeeded": int,
          "fallback": int,
          "by_relevance": {"core": n, "relevant": n, "passing": n, "irrelevant": n},
        }
    """
    analyzer = ArticleAnalyzer(
        api_key=api_key,
        model=model,
        batch_size=batch_size,
    )
    analyzer.analyze_articles(
        articles,
        keyword_groups,
        progress_callback=progress_callback,
        log_callback=log_callback,
    )

    by_relevance = {"core": 0, "relevant": 0, "passing": 0, "irrelevant": 0}
    succeeded = 0
    fallback = 0
    for a in articles:
        rel = a.get("ai_relevance", "passing")
        by_relevance[rel] = by_relevance.get(rel, 0) + 1
        if a.get("ai_fallback"):
            fallback += 1
        elif a.get("ai_analyzed"):
            succeeded += 1

    stats = {
        "total": len(articles),
        "ai_succeeded": succeeded,
        "fallback": fallback,
        "by_relevance": by_relevance,
    }
    return articles, stats
