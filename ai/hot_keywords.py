"""
HOT KEYWORDS 집계 모듈

전체 기사에서 자주 언급되는 브랜드/제품/기업명을 집계해 Top N으로 반환합니다.

데이터 소스 (가중치):
  - AI 엔티티 (Phase 2-2의 entities 배열): 가중치 2
  - 기사 제목의 명사: 가중치 1

처리 흐름:
  1. 모든 기사에서 단어 수집 + 가중치 합산
  2. stopwords 1차 필터링 (config/stopwords.yaml)
  3. 검색 키워드 정확 매칭만 제외
  4. 점수 순 상위 N_CANDIDATES 추출 (기본 30개)
  5. AI 분류 (있으면): 부적합 제거 + 동의어 통합
     실패 시 fallback: 4단계 결과 그대로
  6. 점수 순 Top N 추출 (기본 10개)
  7. 자사/경쟁사/기타 카테고리 분류
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Iterable

import yaml


# AI 엔티티 가중치 (제목 명사 대비)
WEIGHT_ENTITY = 2
WEIGHT_TITLE_NOUN = 1

# AI 분류에 보낼 후보 단어 수
DEFAULT_CANDIDATE_POOL = 30

# 명사 추출용 정규식: 한글 2자 이상, 영문 2자 이상, 영숫자 조합
_NOUN_PATTERN = re.compile(r"[가-힣]{2,}|[A-Za-z][A-Za-z0-9]+|[0-9]+[가-힣A-Za-z]+")


class HotKeywordsAggregator:
    """기사 목록에서 HOT KEYWORDS Top N을 집계."""

    def __init__(
        self,
        company_keywords: Optional[List[str]] = None,
        competitor_keywords: Optional[List[str]] = None,
        search_keywords: Optional[List[str]] = None,
        stopwords_path: str = "config/stopwords.yaml",
        ai_api_key: str = "",
        ai_model: str = "gemini-2.5-flash-lite",
        candidate_pool_size: int = DEFAULT_CANDIDATE_POOL,
    ):
        """
        Parameters
        ----------
        company_keywords : list[str]
            자사 키워드 (제품 + 회사명). 카테고리 분류에 사용.
        competitor_keywords : list[str]
            경쟁사 키워드. 카테고리 분류에 사용.
        search_keywords : list[str]
            전체 검색 키워드. HOT 집계에서 정확 매칭만 제외.
        stopwords_path : str
            stopwords.yaml 경로.
        ai_api_key : str
            Gemini API key. 비어있으면 AI 분류 스킵 (stopwords만 적용).
        ai_model : str
            AI 분류용 모델.
        candidate_pool_size : int
            AI에 보낼 후보 단어 수.
        """
        self.company_keywords = self._normalize_keywords(company_keywords or [])
        self.competitor_keywords = self._normalize_keywords(competitor_keywords or [])

        # 검색 키워드는 HOT에서 정확 매칭만 제외
        # (자사/경쟁사 키워드는 카테고리 분류용으로만 사용, 제외 대상에 넣지 않음)
        self.excluded_keywords = set(self._normalize_keywords(search_keywords or []))

        self.stopwords = self._load_stopwords(stopwords_path)

        # AI 분류기
        self.ai_api_key = ai_api_key
        self.ai_model = ai_model
        self.candidate_pool_size = candidate_pool_size

    # ─────────────────────────────────────────────────────
    # public API
    # ─────────────────────────────────────────────────────

    def aggregate(
        self,
        articles: List[Dict],
        top_n: int = 10,
        log_callback=None,
    ) -> List[Dict]:
        """
        기사 목록에서 HOT KEYWORDS Top N을 집계.

        Returns
        -------
        list[dict]
            [
              {
                "rank": 1,
                "keyword": "비비고",
                "count": 24,
                "category": "company",
                "aliases": ["비비고만두"],   # AI가 통합한 동의어
                "ai_classified": True,        # AI가 검증한 키워드인지
              },
              ...
            ]
        """
        # ── 1단계: 단어 수집 + 가중치 합산 ──
        counter: Counter = Counter()

        for article in articles:
            ai_data = article.get("ai_analysis") or {}
            entities = ai_data.get("entities") or []
            for entity in entities:
                normalized = self._normalize(entity)
                if self._is_valid_keyword(normalized):
                    counter[normalized] += WEIGHT_ENTITY

            title = article.get("title", "") or ""
            for noun in self._extract_nouns(title):
                if self._is_valid_keyword(noun):
                    counter[noun] += WEIGHT_TITLE_NOUN

        if not counter:
            return []

        # ── 2단계: 후보 풀 추출 ──
        candidate_pool = counter.most_common(self.candidate_pool_size)
        candidate_words = [w for w, _ in candidate_pool]

        if log_callback:
            log_callback(f"  [HOT] 후보 단어 {len(candidate_words)}개 추출")

        # ── 3단계: AI 분류 ──
        classified, ai_used = self._classify_with_ai(candidate_words, log_callback)

        # ── 4단계: AI 결과를 기반으로 점수 합산 + 동의어 통합 ──
        merged = self._merge_aliases(classified, counter)

        # ── 5단계: 유효한 것만 + Top N ──
        valid = [item for item in merged if item["is_valid"]]
        valid.sort(key=lambda x: x["count"], reverse=True)
        top = valid[:top_n]

        # ── 6단계: 결과 포맷팅 + 카테고리 분류 ──
        result = []
        for rank, item in enumerate(top, start=1):
            result.append({
                "rank": rank,
                "keyword": item["canonical"],
                "count": item["count"],
                "category": self._categorize(item["canonical"], item["aliases"]),
                "aliases": item["aliases"],
                "ai_classified": ai_used,
            })

        return result

    # ─────────────────────────────────────────────────────
    # AI 분류
    # ─────────────────────────────────────────────────────

    def _classify_with_ai(self, candidates: List[str], log_callback):
        """AI 분류 호출. 실패 시 fallback."""
        if not candidates:
            return [], False

        try:
            from ai.keyword_classifier import KeywordClassifier
            classifier = KeywordClassifier(
                api_key=self.ai_api_key,
                model=self.ai_model,
            )
            results, ai_used = classifier.classify(candidates)

            if log_callback:
                if ai_used:
                    valid_cnt = sum(1 for r in results if r.is_valid)
                    invalid_cnt = len(results) - valid_cnt
                    alias_groups = sum(1 for r in results if r.aliases)
                    log_callback(
                        f"  [HOT] AI 분류 완료: 적합 {valid_cnt} / 부적합 {invalid_cnt}"
                        f" / 동의어그룹 {alias_groups}"
                    )
                else:
                    log_callback("  [HOT] AI 분류 미사용 (fallback): stopwords 결과 그대로 표시")

            return results, ai_used

        except Exception as e:
            if log_callback:
                log_callback(f"  [HOT] ⚠️ AI 분류 실패 → fallback: {e}")
            # fallback: 모두 valid 처리
            from ai.keyword_classifier import ClassifiedKeyword
            return [
                ClassifiedKeyword(canonical=w, aliases=[], is_valid=True)
                for w in candidates
            ], False

    def _merge_aliases(self, classified, counter: Counter) -> List[Dict]:
        """동의어 그룹의 점수를 합산."""
        merged = []
        for item in classified:
            total_count = counter.get(item.canonical, 0)
            for alias in item.aliases:
                total_count += counter.get(alias, 0)

            merged.append({
                "canonical": item.canonical,
                "aliases": item.aliases,
                "is_valid": item.is_valid,
                "count": total_count,
            })
        return merged

    # ─────────────────────────────────────────────────────
    # 내부 헬퍼
    # ─────────────────────────────────────────────────────

    def _extract_nouns(self, text: str) -> List[str]:
        if not text:
            return []
        matches = _NOUN_PATTERN.findall(text)
        return [self._normalize(m) for m in matches]

    def _is_valid_keyword(self, word: str) -> bool:
        if not word:
            return False
        if len(word) < 2:
            return False
        if word in self.stopwords:
            return False
        if word in self.excluded_keywords:
            return False
        if word.isdigit():
            return False
        return True

    def _categorize(self, keyword: str, aliases: Optional[List[str]] = None) -> str:
        """canonical과 aliases 모두 고려해서 분류."""
        all_forms = [keyword] + list(aliases or [])

        # 정확 매칭
        for form in all_forms:
            if form in self.company_keywords:
                return "company"
            if form in self.competitor_keywords:
                return "competitor"

        # 부분 매칭
        for form in all_forms:
            for company_kw in self.company_keywords:
                if company_kw and (company_kw in form or form in company_kw):
                    return "company"
            for comp_kw in self.competitor_keywords:
                if comp_kw and (comp_kw in form or form in comp_kw):
                    return "competitor"

        return "other"

    @staticmethod
    def _normalize(text: str) -> str:
        return (text or "").strip()

    @staticmethod
    def _normalize_keywords(keywords: Iterable[str]) -> List[str]:
        return [k.strip() for k in keywords if k and k.strip()]

    def _load_stopwords(self, path: str) -> set:
        try:
            p = Path(path)
            if not p.exists():
                return set()
            with p.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            stopwords = set()
            for category, words in data.items():
                if isinstance(words, list):
                    stopwords.update(self._normalize(w) for w in words if w)
            return stopwords
        except Exception:
            return set()


# ─────────────────────────────────────────────────────
# 편의 함수
# ─────────────────────────────────────────────────────

def aggregate_hot_keywords(
    articles: List[Dict],
    company_keywords: Optional[List[str]] = None,
    competitor_keywords: Optional[List[str]] = None,
    search_keywords: Optional[List[str]] = None,
    top_n: int = 10,
    stopwords_path: str = "config/stopwords.yaml",
    ai_api_key: str = "",
    ai_model: str = "gemini-2.5-flash-lite",
    log_callback=None,
) -> List[Dict]:
    aggregator = HotKeywordsAggregator(
        company_keywords=company_keywords,
        competitor_keywords=competitor_keywords,
        search_keywords=search_keywords,
        stopwords_path=stopwords_path,
        ai_api_key=ai_api_key,
        ai_model=ai_model,
    )
    return aggregator.aggregate(articles, top_n=top_n, log_callback=log_callback)
