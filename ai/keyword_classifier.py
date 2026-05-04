"""
HOT KEYWORDS 후보 단어를 AI로 분류·정제하는 모듈.

수행 작업 (단일 Gemini 호출):
  1. 트렌드 키워드로 부적합한 단어를 표시 (일반명사·추상개념 등)
  2. 동의어 그룹을 식별 (예: "CJ제일제당" ⊃ "CJ", "제일제당")

실패 시 fallback: 입력 그대로 반환 (모두 유효, 동의어 통합 없음).
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────
# 결과 데이터 구조
# ─────────────────────────────────────────────────────

@dataclass
class ClassifiedKeyword:
    """AI가 분류·통합한 키워드."""
    canonical: str            # 대표 표현 (예: "CJ제일제당")
    aliases: List[str] = field(default_factory=list)  # 동의어 (예: ["CJ", "제일제당"])
    is_valid: bool = True     # 트렌드 키워드로 적합한지

    def all_forms(self) -> List[str]:
        """canonical + aliases 모두 반환."""
        return [self.canonical] + list(self.aliases)


# ─────────────────────────────────────────────────────
# 프롬프트
# ─────────────────────────────────────────────────────

_PROMPT_TEMPLATE = """당신은 한국어 트렌드/뉴스 키워드 분석 전문가입니다.

아래는 뉴스 기사들에서 추출된 빈출 단어 후보 목록입니다.
이 목록을 다음 두 작업을 수행해 정제해주세요.

[작업 1] 부적합 단어 표시
- "트렌드 키워드"로 부적합한 단어는 is_valid=false로 표시하세요.
- 부적합: 일반명사, 추상개념, 동작·상태를 나타내는 명사화 단어,
         단독으로는 의미를 알 수 없는 단어, 너무 흔한 비즈니스 용어
- 적합: 고유명사(회사·브랜드·제품·인물·지역명), 신조어, 트렌드 용어,
       특정 개념을 가리키는 단어

[작업 2] 동의어 그룹 통합
- 같은 대상을 가리키는 단어들은 하나의 그룹으로 묶으세요.
- canonical: 가장 정식·완전한 표현 (예: "CJ제일제당")
- aliases: 같은 대상의 다른 표현 (예: ["CJ", "제일제당"])
- 동의어가 없으면 aliases는 빈 배열 []

[적합 예시]
- "비비고", "K-푸드", "MZ세대", "올리브영", "추석", "이재현",
  "헝가리", "갓생", "빌런", "챌린지", "오피스세대", "Z세대"

[부적합 예시]
- "최대", "회장", "확장", "성공", "진행", "추진", "강화",
  "브랜드"(단독), "기업"(단독), "시장"(단독)

[입력 단어 목록]
{candidates}

반드시 아래 JSON 형식으로만 응답하세요. 설명·코드블록·여분 텍스트 금지.

{{
  "filtered": [
    {{
      "canonical": "단어",
      "aliases": [],
      "is_valid": true
    }}
  ]
}}

규칙:
- 입력의 모든 단어가 어딘가의 canonical 또는 aliases에 정확히 1번 등장해야 합니다.
- 단어 변형(공백·대소문자) 금지. 입력 표기 그대로 사용.
- canonical은 입력 목록에 있는 단어 중에서만 선택.
"""


# ─────────────────────────────────────────────────────
# 메인 클래스
# ─────────────────────────────────────────────────────

class KeywordClassifier:
    """Gemini를 사용해 후보 단어를 정제."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.5-flash-lite",
        timeout_sec: int = 30,
    ):
        self.api_key = api_key or ""
        self.model = model
        self.timeout_sec = timeout_sec
        self._client = None

        if self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Gemini 클라이언트 초기화 실패: {e}")
                self._client = None

    # ─────────────────────────────────────────────────
    # public API
    # ─────────────────────────────────────────────────

    def classify(self, candidates: List[str]) -> Tuple[List[ClassifiedKeyword], bool]:
        """
        후보 단어를 분류·통합.

        Parameters
        ----------
        candidates : list[str]
            정제할 단어 목록 (점수 높은 순).

        Returns
        -------
        (results, ai_used) : (list[ClassifiedKeyword], bool)
            - results: 분류된 키워드 (입력 모두 포함, is_valid 표시)
            - ai_used: 실제로 AI가 사용됐는지 (False면 fallback)
        """
        if not candidates:
            return [], False

        # API 키 없거나 클라이언트 초기화 실패 시 즉시 fallback
        if not self._client:
            logger.info("AI classifier 미사용 → fallback (모두 valid, 통합 없음)")
            return self._fallback(candidates), False

        # AI 호출
        try:
            results = self._call_ai(candidates)
            if not results:
                raise ValueError("AI 응답에서 결과를 추출하지 못했습니다.")
            # 입력 단어가 모두 포함됐는지 검증, 누락 시 보강
            results = self._ensure_completeness(candidates, results)
            return results, True
        except Exception as e:
            logger.warning(f"AI classifier 호출 실패 → fallback: {e}")
            return self._fallback(candidates), False

    # ─────────────────────────────────────────────────
    # 내부 헬퍼
    # ─────────────────────────────────────────────────

    def _call_ai(self, candidates: List[str]) -> List[ClassifiedKeyword]:
        """Gemini 호출 + JSON 파싱."""
        # 후보를 번호 매겨 명확하게 전달
        candidate_text = "\n".join(f"- {w}" for w in candidates)
        prompt = _PROMPT_TEMPLATE.format(candidates=candidate_text)

        from google.genai import types

        response = self._client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json",
            ),
        )

        text = (response.text or "").strip()
        if not text:
            raise ValueError("빈 응답")

        # JSON 추출 (코드블록 래핑 등 보정)
        json_text = self._extract_json(text)
        data = json.loads(json_text)

        filtered = data.get("filtered", [])
        if not isinstance(filtered, list):
            raise ValueError("filtered 필드가 배열이 아닙니다.")

        results = []
        for item in filtered:
            if not isinstance(item, dict):
                continue
            canonical = (item.get("canonical") or "").strip()
            if not canonical:
                continue
            aliases = item.get("aliases") or []
            aliases = [a.strip() for a in aliases if isinstance(a, str) and a.strip()]
            is_valid = bool(item.get("is_valid", True))

            results.append(ClassifiedKeyword(
                canonical=canonical,
                aliases=aliases,
                is_valid=is_valid,
            ))

        return results

    @staticmethod
    def _extract_json(text: str) -> str:
        """코드블록 래핑·후행 텍스트 등 보정."""
        text = text.strip()

        # ```json ... ``` 형태 제거
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```\s*$", "", text)

        # 첫 { 부터 마지막 } 까지만 추출
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start:end + 1]

        # 후행 콤마 보정
        text = re.sub(r",\s*([\]}])", r"\1", text)
        return text

    def _ensure_completeness(
        self,
        candidates: List[str],
        results: List[ClassifiedKeyword],
    ) -> List[ClassifiedKeyword]:
        """입력 단어가 모두 결과에 포함됐는지 검증, 누락분은 fallback 추가."""
        seen = set()
        for r in results:
            seen.add(r.canonical)
            for a in r.aliases:
                seen.add(a)

        missing = [c for c in candidates if c not in seen]
        if missing:
            logger.info(f"AI 응답 누락 단어 {len(missing)}개 fallback 추가: {missing[:5]}...")
            for word in missing:
                results.append(ClassifiedKeyword(
                    canonical=word, aliases=[], is_valid=True
                ))
        return results

    @staticmethod
    def _fallback(candidates: List[str]) -> List[ClassifiedKeyword]:
        """AI 실패 시 모든 단어를 valid로, 통합 없이 반환."""
        return [
            ClassifiedKeyword(canonical=w, aliases=[], is_valid=True)
            for w in candidates
        ]
