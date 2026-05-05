"""News Clipper 색상 테마 정의"""

# ── 메인 컬러 ──
NAVY = "#1E3A5F"
NAVY_LIGHT = "#264A73"
NAVY_DARK = "#152E4D"
COBALT = "#1A56DB"
COBALT_HOVER = "#1648B8"
SKY_BLUE = "#E1EFFE"

# ── 배경 ──
BG_MAIN = "#F3F6FC"
BG_WHITE = "#FFFFFF"
BG_CARD = "#FFFFFF"

# ── 텍스트 ──
TEXT_PRIMARY = "#1F2937"
TEXT_SECONDARY = "#6B7280"
TEXT_ON_NAVY = "#FFFFFF"
TEXT_ON_NAVY_DIM = "#94A3B8"
TEXT_PLACEHOLDER = "#9CA3AF"

# ── 강조 ──
ACCENT_ORANGE = "#F97316"
SUCCESS = "#10B981"
ERROR = "#EF4444"
WARNING = "#F59E0B"

# ── 티어 뱃지 ──
TIER_1_BG = "#1A56DB"
TIER_1_FG = "#FFFFFF"
TIER_2_BG = "#6B7280"
TIER_2_FG = "#FFFFFF"
TIER_3_BG = "#D1D5DB"
TIER_3_FG = "#374151"

# ── 폰트 ──
FONT_FAMILY = "맑은 고딕"
FONT_TITLE = (FONT_FAMILY, 22, "bold")      
FONT_SUBTITLE = (FONT_FAMILY, 18, "bold")   
FONT_BODY = (FONT_FAMILY, 16)               
FONT_BODY_BOLD = (FONT_FAMILY, 16, "bold")  
FONT_SMALL = (FONT_FAMILY, 14)
FONT_SMALL_BOLD = (FONT_FAMILY, 14, "bold")
FONT_CAPTION = (FONT_FAMILY, 13)


# ─────────────────────────────────────
#  v2.0: AI 분석 결과 표시용 색상
# ─────────────────────────────────────
# 관련도 뱃지
RELEVANCE_CORE_BG = "#10B981"      # 초록 (핵심)
RELEVANCE_RELEVANT_BG = "#3B82F6"  # 파랑 (관련)
RELEVANCE_PASSING_BG = "#F59E0B"   # 주황 (간접)
RELEVANCE_IRRELEVANT_BG = "#9CA3AF"  # 회색 (무관, 보통은 표시 안함)

# 감성 태그
SENTIMENT_POSITIVE = "#10B981"
SENTIMENT_NEUTRAL = "#6B7280"
SENTIMENT_NEGATIVE = "#EF4444"

# AI 요약 박스
AI_SUMMARY_BG = "#F0F7FF"       # 아주 연한 하늘색
AI_SUMMARY_BORDER = "#BFDBFE"
AI_SUMMARY_TEXT = "#1E3A5F"

# 엔티티 칩
ENTITY_CHIP_BG = "#EEF2FF"
ENTITY_CHIP_TEXT = "#4338CA"

# Fallback(키워드 매칭) 표시
FALLBACK_BADGE_BG = "#FEF3C7"
FALLBACK_BADGE_TEXT = "#92400E"

# ── HOT KEYWORDS (Phase 2-3) ──
HOT_BAR_COMPANY = COBALT          # 자사 (파란색)
HOT_BAR_COMPETITOR = ACCENT_ORANGE  # 경쟁사 (주황색)
HOT_BAR_OTHER = "#9CA3AF"          # 기타 (회색)
HOT_BAR_BG = "#F3F4F6"             # 바 배경 (연한 회색)
HOT_CARD_BG = "#FFFBEB"            # 카드 배경 (살짝 노란기 — 강조)
HOT_CARD_BORDER = "#FCD34D"        # 카드 테두리 (노랑)
HOT_TITLE_COLOR = "#92400E"        # 제목 텍스트 (진한 갈색)
