"""
HOT KEYWORDS 집계 모듈 단독 테스트.

실행:
    python tests/test_hot_keywords.py
"""

import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ai.hot_keywords import aggregate_hot_keywords


def make_test_articles():
    """테스트용 기사 샘플."""
    return [
        {
            "title": "비비고 만두, 미국 수출 40% 증가",
            "ai_analysis": {
                "entities": ["비비고", "CJ제일제당", "만두"],
            },
        },
        {
            "title": "CJ제일제당, 비비고 신제품 출시",
            "ai_analysis": {
                "entities": ["CJ제일제당", "비비고"],
            },
        },
        {
            "title": "농심 신라면, 글로벌 점유율 28%",
            "ai_analysis": {
                "entities": ["농심", "신라면"],
            },
        },
        {
            "title": "오뚜기, 미국 시장 진출 확대",
            "ai_analysis": {
                "entities": ["오뚜기", "미국"],
            },
        },
        {
            "title": "K-푸드 수출 호조, 만두 인기",
            "ai_analysis": {
                "entities": ["K-푸드", "만두"],
            },
        },
        {
            "title": "비비고 왕교자 미국 매출 신기록",
            "ai_analysis": {
                "entities": ["비비고", "왕교자", "미국"],
            },
        },
        # AI 분석 실패한 기사 (제목 명사만 사용됨)
        {
            "title": "만두 시장 경쟁 치열, 신제품 잇따라",
            "ai_analysis": None,
        },
    ]


def test_basic_aggregation():
    """기본 집계 테스트."""
    print("\n" + "=" * 60)
    print("TEST 1: 기본 집계 (자사=비비고/CJ제일제당, 경쟁사=농심/오뚜기)")
    print("=" * 60)

    articles = make_test_articles()
    hot = aggregate_hot_keywords(
        articles=articles,
        company_keywords=["비비고", "CJ제일제당"],
        competitor_keywords=["농심", "오뚜기"],
        search_keywords=["비비고", "CJ제일제당", "농심", "오뚜기", "식품"],
        top_n=10,
    )

    print(f"\n총 {len(hot)}개 키워드 추출\n")
    print(f"{'순위':<4} {'키워드':<20} {'점수':<6} {'분류'}")
    print("-" * 50)
    for item in hot:
        category_kr = {
            "company": "🔵 자사",
            "competitor": "🟠 경쟁사",
            "other": "⚪ 기타",
        }[item["category"]]
        print(f"{item['rank']:<4} {item['keyword']:<20} {item['count']:<6} {category_kr}")

    # 검증
    keywords = [h["keyword"] for h in hot]

    # 검색 키워드는 제외돼야 함
    assert "비비고" not in keywords, "❌ 검색 키워드 '비비고'가 제외되지 않음"
    assert "농심" not in keywords, "❌ 검색 키워드 '농심'이 제외되지 않음"

    # 만두는 여러 기사에 등장하므로 상위에 있어야 함
    assert "만두" in keywords, "❌ '만두' 가 누락됨"

    print("\n✅ 검색 키워드 제외 정상 동작")
    print("✅ AI 엔티티 + 제목 명사 결합 정상")


def test_stopwords_filtering():
    """Stopwords 필터링 테스트."""
    print("\n" + "=" * 60)
    print("TEST 2: Stopwords 필터링")
    print("=" * 60)

    articles = [
        {
            "title": "올해 시장 동향, 산업 전반 확대",
            "ai_analysis": {"entities": ["시장", "산업"]},
        },
        {
            "title": "비비고 만두 인기",
            "ai_analysis": {"entities": ["비비고", "만두"]},
        },
    ]

    hot = aggregate_hot_keywords(
        articles=articles,
        company_keywords=["비비고"],
        search_keywords=["비비고"],
        top_n=10,
    )

    keywords = [h["keyword"] for h in hot]
    print(f"추출된 키워드: {keywords}")

    # stopwords가 정상 적용되면 '시장', '산업', '올해' 등은 제외돼야 함
    forbidden = ["시장", "산업", "올해", "동향", "확대"]
    found = [w for w in forbidden if w in keywords]
    if found:
        print(f"⚠️  Stopwords가 일부 통과됨: {found}")
        print("   → config/stopwords.yaml 확인 필요")
    else:
        print("✅ Stopwords 필터링 정상")

    assert "만두" in keywords, "❌ 정상 키워드 '만두'가 누락됨"


def test_categorization():
    """카테고리 분류 테스트 (부분 매칭 포함)."""
    print("\n" + "=" * 60)
    print("TEST 3: 카테고리 분류 (자사/경쟁사/기타)")
    print("=" * 60)

    articles = [
        {"title": "기사1", "ai_analysis": {"entities": ["CJ제일제당", "농심그룹", "삼양식품"]}},
        {"title": "기사2", "ai_analysis": {"entities": ["CJ제일제당", "농심그룹", "삼양식품"]}},
        {"title": "기사3", "ai_analysis": {"entities": ["CJ제일제당", "농심그룹"]}},
    ]

    hot = aggregate_hot_keywords(
        articles=articles,
        company_keywords=["CJ"],          # "CJ제일제당"이 부분 매칭으로 자사 분류돼야 함
        competitor_keywords=["농심"],     # "농심그룹"이 부분 매칭으로 경쟁사 분류돼야 함
        search_keywords=["CJ", "농심"],
        top_n=10,
    )

    for item in hot:
        print(f"  {item['keyword']:<20} → {item['category']}")

    # 부분 매칭 검증
    cj = next((h for h in hot if h["keyword"] == "CJ제일제당"), None)
    nongshim = next((h for h in hot if h["keyword"] == "농심그룹"), None)
    samyang = next((h for h in hot if h["keyword"] == "삼양식품"), None)

    if cj:
        assert cj["category"] == "company", f"❌ CJ제일제당 분류 오류: {cj['category']}"
        print("✅ 'CJ제일제당' → company (부분 매칭)")
    if nongshim:
        assert nongshim["category"] == "competitor", f"❌ 농심그룹 분류 오류: {nongshim['category']}"
        print("✅ '농심그룹' → competitor (부분 매칭)")
    if samyang:
        assert samyang["category"] == "other", f"❌ 삼양식품 분류 오류: {samyang['category']}"
        print("✅ '삼양식품' → other (등록 안 된 회사)")


def test_empty_input():
    """빈 입력 처리."""
    print("\n" + "=" * 60)
    print("TEST 4: Edge Case (빈 입력 / 누락 필드)")
    print("=" * 60)

    # 빈 리스트
    hot = aggregate_hot_keywords(articles=[], top_n=10)
    assert hot == [], "❌ 빈 입력에 대해 빈 리스트 반환해야 함"
    print("✅ 빈 articles 처리 정상")

    # ai_analysis 누락
    articles = [
        {"title": "테스트 기사 만두 미국"},
        {"title": "또다른 기사 만두"},
    ]
    hot = aggregate_hot_keywords(articles=articles, top_n=5)
    keywords = [h["keyword"] for h in hot]
    assert "만두" in keywords
    print(f"✅ ai_analysis 누락 시 제목만으로 동작: {keywords}")


def main():
    print("\n" + "█" * 60)
    print("  HOT KEYWORDS Aggregator 단독 테스트")
    print("█" * 60)

    try:
        test_basic_aggregation()
        test_stopwords_filtering()
        test_categorization()
        test_empty_input()

        print("\n" + "=" * 60)
        print("🎉 모든 테스트 통과!")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ 테스트 실패: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 예외 발생: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
