"""
KeywordClassifier 단독 테스트.

실행:
    python tests/test_keyword_classifier.py
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ai.keyword_classifier import KeywordClassifier, ClassifiedKeyword


def _load_api_key():
    """settings.yaml 또는 환경변수에서 API 키 로드."""
    key = os.environ.get("GEMINI_API_KEY", "")
    if key:
        return key
    try:
        import yaml
        path = ROOT / "config" / "settings.yaml"
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            return data.get("api", {}).get("gemini", {}).get("api_key", "") or ""
    except Exception:
        pass
    return ""


def test_fallback_without_key():
    """API 키 없이 fallback 동작 확인."""
    print("\n" + "=" * 60)
    print("TEST 1: API 키 없이 → fallback")
    print("=" * 60)

    classifier = KeywordClassifier(api_key="")
    candidates = ["비비고", "최대", "CJ제일제당"]

    results, ai_used = classifier.classify(candidates)

    assert ai_used is False, "API 키 없을 때 ai_used=False 여야 함"
    assert len(results) == len(candidates), "fallback은 모든 입력 보존"
    for r in results:
        assert r.is_valid is True, "fallback은 모두 valid"
        assert r.aliases == [], "fallback은 동의어 통합 없음"

    print(f"✅ fallback 정상: {len(results)}개, 모두 valid, 통합 없음")


def test_real_api():
    """실제 Gemini API로 분류 + 동의어 통합 확인."""
    print("\n" + "=" * 60)
    print("TEST 2: 실제 Gemini API")
    print("=" * 60)

    api_key = _load_api_key()
    if not api_key:
        print("⏭️ API 키 없음 → 스킵")
        return

    classifier = KeywordClassifier(api_key=api_key)
    candidates = [
        "비비고", "비비고만두", "CJ제일제당", "CJ", "제일제당",
        "농심", "신라면", "최대", "회장", "확장",
        "올리브영", "K-푸드", "추석", "이재현", "헝가리",
        "MZ세대", "갓생",
    ]

    print(f"입력 단어 ({len(candidates)}개): {candidates}")
    results, ai_used = classifier.classify(candidates)

    print(f"\nai_used: {ai_used}")
    print(f"결과 그룹 수: {len(results)}")
    print()
    print(f"{'canonical':<20} {'is_valid':<10} aliases")
    print("-" * 70)
    for r in results:
        valid_mark = "✅" if r.is_valid else "❌"
        aliases_str = ", ".join(r.aliases) if r.aliases else ""
        print(f"{r.canonical:<20} {valid_mark:<10} {aliases_str}")

    # 검증: 일반어가 invalid로 잡혔는지
    invalid_words = {r.canonical for r in results if not r.is_valid}
    expected_invalid = {"최대", "회장", "확장"}
    found = invalid_words & expected_invalid
    if found:
        print(f"\n✅ 일반어 부적합 처리 확인: {found}")
    else:
        print(f"\n⚠️ 일반어가 적합으로 분류됨 (AI가 다르게 판단): {expected_invalid - invalid_words}")

    # 검증: 동의어 통합 확인
    cj_group = next((r for r in results if "CJ" in r.canonical or "CJ" in r.aliases), None)
    if cj_group and cj_group.aliases:
        print(f"✅ CJ 동의어 통합 확인: canonical={cj_group.canonical}, aliases={cj_group.aliases}")


def main():
    print("\n" + "█" * 60)
    print("  KeywordClassifier 단독 테스트")
    print("█" * 60)

    test_fallback_without_key()
    test_real_api()

    print("\n" + "=" * 60)
    print("🎉 테스트 완료")
    print("=" * 60)


if __name__ == "__main__":
    main()
