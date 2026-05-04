"""
HOT KEYWORDS 집계 모듈

전체 기사에서 자주 언급되는 브랜드/제품/기업명을 집계해 Top N으로 반환합니다.

데이터 소스 (가중치):
  - AI 엔티티 (Phase 2-2의 entities 배열): 가중치 2
  - 기사 제목의 명사: 가중치 1

제외 대상:
  - 사용자 검색 키워드 (제품/회사/경쟁사/산업)
  - config/stopwords.yaml에 정의된 일반 단어
  - 1글자 단어 (단, 영문/숫자 조합은 제외 안 함)

카테고리 분류:
  - 'company': 사용자 자사 키워드 (제품/회사명) 와 매칭
  - 'competitor': 사용자 경쟁사 키워드와 매칭
  - 'other': 그 외 (산업 키워드 매칭 포함)
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
    ):
        """
        Parameters
        ----------
        company_keywords : list[str]
            자사 키워드 (제품 + 회사명). 카테고리 분류에 사용.
        competitor_keywords : list[str]
            경쟁사 키워드. 카테고리 분류에 사용.
        search_keywords : list[str]
            전체 검색 키워드. HOT 집계에서 제외.
        stopwords_path : str
            stopwords.yaml 경로.
        """
        self.company_keywords = self._normalize_keywords(company_keywords or [])
        self.competitor_keywords = self._normalize_keywords(competitor_keywords or [])

        # 검색 키워드는 HOT에서 제외
        search_set = set(self._normalize_keywords(search_keywords or []))
        # 자사/경쟁사도 검색 키워드에 포함되어 있을 가능성이 높지만,
        # 카테고리 분류에는 필요하므로 self에는 보관, 제외만 search_set에 합산
        self.excluded_keywords = (
            search_set
            | set(self.company_keywords)
            | set(self.competitor_keywords)
        )

        self.stopwords = self._load_stopwords(stopwords_path)

    # ─────────────────────────────────────────────────────
    # public API
    # ─────────────────────────────────────────────────────

    def aggregate(self, articles: List[Dict], top_n: int = 10) -> List[Dict]:
        """
        기사 목록에서 HOT KEYWORDS Top N을 집계.

        Parameters
        ----------
        articles : list[dict]
            기사 dict 리스트. 각 기사에 다음 필드 사용:
              - title: 제목 (필수)
              - ai_analysis.entities: AI 추출 엔티티 (선택)
        top_n : int
            반환할 키워드 개수.

        Returns
        -------
        list[dict]
            [
              {
                "rank": 1,
                "keyword": "비비고",
                "count": 24,
                "category": "company",  # company | competitor | other
              },
              ...
            ]
        """
        counter: Counter = Counter()

        for article in articles:
            # 1) AI 엔티티 (가중치 2)
            ai_data = article.get("ai_analysis") or {}
            entities = ai_data.get("entities") or []
            for entity in entities:
                normalized = self._normalize(entity)
                if self._is_valid_keyword(normalized):
                    counter[normalized] += WEIGHT_ENTITY

            # 2) 제목 명사 (가중치 1)
            title = article.get("title", "") or ""
            for noun in self._extract_nouns(title):
                if self._is_valid_keyword(noun):
                    counter[noun] += WEIGHT_TITLE_NOUN

        # Top N 추출
        top = counter.most_common(top_n)

        # 결과 포맷팅 + 카테고리 분류
        result = []
        for rank, (keyword, count) in enumerate(top, start=1):
            result.append({
                "rank": rank,
                "keyword": keyword,
                "count": count,
                "category": self._categorize(keyword),
            })

        return result

    # ─────────────────────────────────────────────────────
    # 내부 헬퍼
    # ─────────────────────────────────────────────────────

    def _extract_nouns(self, text: str) -> List[str]:
        """제목 텍스트에서 명사 후보를 추출 (정규식 기반)."""
        if not text:
            return []
        matches = _NOUN_PATTERN.findall(text)
        return [self._normalize(m) for m in matches]

    def _is_valid_keyword(self, word: str) -> bool:
        """집계 대상으로 유효한지 검증."""
        if not word:
            return False
        if len(word) < 2:
            return False
        if word in self.stopwords:
            return False
        if word in self.excluded_keywords:
            return False
        # 숫자만 있는 단어 제외
        if word.isdigit():
            return False
        return True

    def _categorize(self, keyword: str) -> str:
        """키워드를 자사/경쟁사/기타로 분류."""
        # 정확 매칭 우선
        if keyword in self.company_keywords:
            return "company"
        if keyword in self.competitor_keywords:
            return "competitor"

        # 부분 매칭 (단방향: 키워드가 자사/경쟁사명을 포함하거나, 자사/경쟁사명이 키워드를 포함)
        # 예: "CJ제일제당" 키워드가 자사 "CJ"를 포함하면 company
        for company_kw in self.company_keywords:
            if company_kw and (company_kw in keyword or keyword in company_kw):
                return "company"
        for comp_kw in self.competitor_keywords:
            if comp_kw and (comp_kw in keyword or keyword in comp_kw):
                return "competitor"

        return "other"

    @staticmethod
    def _normalize(text: str) -> str:
        """앞뒤 공백 제거 및 통일."""
        return (text or "").strip()

    @staticmethod
    def _normalize_keywords(keywords: Iterable[str]) -> List[str]:
        """키워드 리스트 정규화 (공백 제거, 빈 문자열 제거)."""
        return [k.strip() for k in keywords if k and k.strip()]

    def _load_stopwords(self, path: str) -> set:
        """stopwords.yaml 로드 (실패 시 빈 set)."""
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
            # 사전 로드 실패 시 fallback (조용히 진행)
            return set()


# ─────────────────────────────────────────────────────
# 편의 함수 (외부에서 간단히 호출용)
# ─────────────────────────────────────────────────────

def aggregate_hot_keywords(
    articles: List[Dict],
    company_keywords: Optional[List[str]] = None,
    competitor_keywords: Optional[List[str]] = None,
    search_keywords: Optional[List[str]] = None,
    top_n: int = 10,
    stopwords_path: str = "config/stopwords.yaml",
) -> List[Dict]:
    """
    함수형 편의 인터페이스.

    Example
    -------
    >>> hot = aggregate_hot_keywords(
    ...     articles=articles,
    ...     company_keywords=["비비고", "CJ제일제당"],
    ...     competitor_keywords=["농심", "오뚜기"],
    ...     search_keywords=["비비고", "CJ제일제당", "농심", "오뚜기"],
    ...     top_n=10,
    ... )
    >>> hot[0]
    {'rank': 1, 'keyword': '만두', 'count': 18, 'category': 'other'}
    """
    aggregator = HotKeywordsAggregator(
        company_keywords=company_keywords,
        competitor_keywords=competitor_keywords,
        search_keywords=search_keywords,
        stopwords_path=stopwords_path,
    )
    return aggregator.aggregate(articles, top_n=top_n)
