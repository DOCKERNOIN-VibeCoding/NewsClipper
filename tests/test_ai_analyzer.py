"""ArticleAnalyzer 단독 동작 검증 스크립트

실행:
    python -m tests.test_ai_analyzer
또는:
    python tests/test_ai_analyzer.py

사전 준비:
    1. config/settings.yaml 파일이 있고 api.gemini.api_key가 설정되어 있어야 함
    2. (선택) GEMINI_API_KEY 환경변수로 대체 가능
"""

import os
import sys
import yaml
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가 (단독 실행 대비)
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ai.article_analyzer import ArticleAnalyzer, analyze_with_ai


# ═══════════════════════════════════════════════════════
#  더미 데이터
# ═══════════════════════════════════════════════════════
SAMPLE_ARTICLES = [
    {
        "title": "CJ제일제당 비비고, 미국 만두 시장 점유율 1위 굳혔다",
        "media_name": "한국경제",
        "description": (
            "CJ제일제당의 비비고 만두가 지난 분기 미국 냉동만두 시장에서 "
            "점유율 28%를 기록하며 1위 자리를 굳혔다. 회사 측은 현지 생산공장 "
            "증설로 공급 능력을 끌어올린 것이 주효했다고 밝혔다."
        ),
    },
    {
        "title": "오뚜기, 신제품 라면 출시…간편식 경쟁 격화",
        "media_name": "매일경제",
        "description": (
            "오뚜기가 새로운 프리미엄 라면 신제품을 출시한다. "
            "농심·삼양과의 라면 시장 경쟁이 한층 치열해질 전망이다."
        ),
    },
    {
        "title": "정부, 식품업계 수출 지원책 발표",
        "media_name": "연합뉴스",
        "description": (
            "정부가 식품업계 수출 활성화를 위한 지원책을 발표했다. "
            "CJ제일제당, 농심 등 주요 업체들이 혜택을 볼 것으로 예상된다."
        ),
    },
    {
        "title": "오늘의 날씨: 전국 대체로 맑음",
        "media_name": "기상청",
        "description": "전국이 대체로 맑은 날씨를 보이겠다. 미세먼지 농도는 보통.",
    },
    {
        "title": "비비고 김치, 일본 수출량 전년 대비 40% 증가",
        "media_name": "조선일보",
        "description": (
            "CJ제일제당의 비비고 김치가 일본 시장에서 전년 대비 40% 증가한 "
            "수출 실적을 기록했다. K-푸드 인기에 힘입은 결과다."
        ),
    },
]

KEYWORD_GROUPS = {
    "products": ["비비고", "비비고 만두", "비비고 김치"],
    "company": ["CJ제일제당", "CJ"],
    "competitors": ["오뚜기", "농심", "풀무원"],
    "industry": ["식품 수출", "냉동식품"],
}


# ═══════════════════════════════════════════════════════
#  유틸
# ═══════════════════════════════════════════════════════
def load_api_key() -> str:
    # 1) 환경변수 우선
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if key:
        return key
    # 2) settings.yaml
    settings_path = ROOT / "config" / "settings.yaml"
    if settings_path.exists():
        with open(settings_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return (data.get("api", {}).get("gemini", {}).get("api_key", "") or "").strip()
    return ""


def print_separator(title: str = ""):
    print("\n" + "═" * 60)
    if title:
        print(f"  {title}")
        print("═" * 60)


# ═══════════════════════════════════════════════════════
#  테스트 케이스
# ═══════════════════════════════════════════════════════
def test_fallback_mode():
    """API 키 없이 동작하는지 (fallback)"""
    print_separator("TEST 1: Fallback 모드 (API 키 없이)")

    analyzer = ArticleAnalyzer(api_key="")
    assert not analyzer.is_available, "API 키 없이는 is_available=False여야 함"

    articles = [dict(a) for a in SAMPLE_ARTICLES]  # 깊은 복사
    analyzer.analyze_articles(
        articles,
        KEYWORD_GROUPS,
        log_callback=lambda m: print(m),
    )

    for i, a in enumerate(articles, 1):
        assert a.get("ai_fallback") is True, f"기사 {i}에 fallback 표시가 없음"
        assert "ai_relevance" in a
        print(f"  [{i}] {a['title'][:30]}... → {a['ai_relevance']} / {a['ai_category']}")

    print("✅ Fallback 모드 통과")


def test_real_api(api_key: str):
    """실제 Gemini API 호출"""
    print_separator("TEST 2: 실제 Gemini API 호출")

    articles = [dict(a) for a in SAMPLE_ARTICLES]
    _, stats = analyze_with_ai(
        articles,
        KEYWORD_GROUPS,
        api_key=api_key,
        model="gemini-2.5-flash",
        batch_size=5,
        log_callback=lambda m: print(m),
    )

    print("\n── 분석 결과 ──")
    for i, a in enumerate(articles, 1):
        print(f"\n[{i}] {a['title']}")
        print(f"    관련도: {a.get('ai_relevance')} ({a.get('ai_relevance_reason', '')})")
        print(f"    카테고리: {a.get('ai_category')}")
        print(f"    감성: {a.get('ai_sentiment')}")
        print(f"    엔티티: {a.get('ai_entities')}")
        print(f"    요약: {a.get('ai_summary')}")
        print(f"    AI사용: {a.get('ai_analyzed')} / fallback: {a.get('ai_fallback')}")

    print("\n── 통계 ──")
    print(f"  총 {stats['total']}건 / 성공 {stats['ai_succeeded']} / fallback {stats['fallback']}")
    print(f"  관련도 분포: {stats['by_relevance']}")

    # 기본 검증
    assert stats["total"] == len(SAMPLE_ARTICLES)
    irrelevant_titles = [
        a["title"] for a in articles
        if a.get("ai_relevance") == "irrelevant"
    ]
    print(f"\n  irrelevant 판정: {irrelevant_titles}")
    # "오늘의 날씨" 기사는 irrelevant 또는 passing이어야 자연스러움
    weather = articles[3]
    assert weather["ai_relevance"] in ("irrelevant", "passing"), \
        f"날씨 기사가 core/relevant로 잘못 판정됨: {weather['ai_relevance']}"

    print("✅ 실제 API 호출 통과")


def test_json_parsing():
    """다양한 응답 형태 파싱 견고성 (단위 테스트)"""
    print_separator("TEST 3: JSON 파싱 견고성")

    analyzer = ArticleAnalyzer(api_key="")

    cases = [
        # (입력, 라벨)
        ('[{"index":1,"relevance_type":"core","summary":"a","category":"product","entities":[],"sentiment":"positive"}]', "최소 정상"),
        ('```json\n[{"index":1,"relevance_type":"core","summary":"a","category":"product","entities":["X"],"sentiment":"neutral"}]\n```', "코드블록 래핑"),
        ('어쩌고저쩌고\n[{"index":1,"relevance_type":"INVALID","summary":"a","category":"???","entities":"X","sentiment":""}]\n끝', "잘못된 값 + 주변 텍스트"),
        ('[{"index":1,"relevance_type":"core","summary":"a","category":"product","entities":[],"sentiment":"positive"},]', "후행 콤마"),
    ]
    for raw, label in cases:
        try:
            parsed = analyzer._parse_response(raw, expected_count=1)
            assert len(parsed) == 1
            assert parsed[0] is not None, f"{label}: None 반환"
            print(f"  ✓ {label}: {parsed[0]['relevance_type']} / {parsed[0]['category']} / {parsed[0]['sentiment']}")
        except Exception as e:
            print(f"  ✗ {label}: 실패 ({e})")
            raise

    print("✅ JSON 파싱 통과")


# ═══════════════════════════════════════════════════════
#  메인
# ═══════════════════════════════════════════════════════
def main():
    print("NewsClipper v2.0 - ArticleAnalyzer 테스트")

    test_fallback_mode()
    test_json_parsing()

    api_key = load_api_key()
    if api_key:
        print(f"\nAPI 키 발견 (길이 {len(api_key)}). 실제 호출 테스트를 진행합니다.")
        test_real_api(api_key)
    else:
        print("\n⚠️ Gemini API 키가 없어 실제 호출 테스트를 건너뜁니다.")
        print("   - GEMINI_API_KEY 환경변수 설정 또는")
        print("   - config/settings.yaml에 api.gemini.api_key 입력 후 다시 실행")

    print_separator("전체 테스트 완료 ✨")


if __name__ == "__main__":
    main()
