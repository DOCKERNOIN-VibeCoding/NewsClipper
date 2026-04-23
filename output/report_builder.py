"""HTML 리포트 생성 모듈"""
import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, BaseLoader

# ── 인라인 HTML 템플릿 (외부 파일 불필요) ──
REPORT_TEMPLATE = r"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>뉴스 클리핑 리포트 – {{ report_date }}</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: '맑은 고딕', 'Malgun Gothic', sans-serif; background: #f4f6f9; color: #222; }
  .header { background: linear-gradient(135deg, #0a1628 0%, #1a3a6b 100%); color: #fff; padding: 32px 40px; }
  .header h1 { font-size: 24px; margin-bottom: 6px; }
  .header .sub { font-size: 13px; color: #a0b4d0; }
  .container { max-width: 1100px; margin: 0 auto; padding: 24px 20px; }

  /* 통계 */
  .stats { display: flex; gap: 16px; margin-bottom: 28px; flex-wrap: wrap; }
  .stat-card { background: #fff; border-radius: 10px; padding: 18px 22px; flex: 1; min-width: 140px;
               box-shadow: 0 1px 4px rgba(0,0,0,0.08); text-align: center; }
  .stat-card .num { font-size: 28px; font-weight: bold; color: #1a3a6b; }
  .stat-card .label { font-size: 12px; color: #666; margin-top: 4px; }

  /* 섹션 */
  .section { margin-bottom: 32px; }
  .section-title { font-size: 17px; font-weight: bold; padding: 10px 16px; border-radius: 8px;
                   margin-bottom: 14px; color: #fff; }
  .section-title.product { background: #1a3a6b; }
  .section-title.company { background: #2563b0; }
  .section-title.competitor { background: #e07b30; }
  .section-title.industry { background: #5a6f8a; }

  /* 기사 카드 */
  .card { background: #fff; border-radius: 10px; padding: 18px 20px; margin-bottom: 12px;
          box-shadow: 0 1px 3px rgba(0,0,0,0.06); border-left: 4px solid #ddd; }
  .card.tier-1 { border-left-color: #1a3a6b; }
  .card.tier-2 { border-left-color: #2563b0; }
  .card.tier-3 { border-left-color: #8899aa; }
  .card .meta { font-size: 12px; color: #888; margin-bottom: 6px; }
  .card .meta .tier { display: inline-block; padding: 1px 8px; border-radius: 4px; color: #fff; font-size: 11px; margin-right: 6px; }
  .card .meta .tier-1 { background: #1a3a6b; }
  .card .meta .tier-2 { background: #2563b0; }
  .card .meta .tier-3 { background: #8899aa; }
  .card .title { font-size: 15px; font-weight: bold; margin-bottom: 4px; }
  .card .title a { color: #1a3a6b; text-decoration: none; }
  .card .title a:hover { text-decoration: underline; }
  .card .desc { font-size: 13px; color: #444; line-height: 1.6; margin-bottom: 6px; }
  .card .tags { font-size: 11px; color: #1a3a6b; }

  /* 유사 기사 */
  .similar { font-size: 12px; color: #888; margin-top: 8px; padding-top: 8px; border-top: 1px dashed #ddd; }
  .similar a { color: #5577aa; text-decoration: none; }
  .similar a:hover { text-decoration: underline; }

  .footer { text-align: center; padding: 20px; font-size: 11px; color: #999; }
</style>
</head>
<body>
<div class="header">
  <h1>뉴스 클리핑 리포트</h1>
  <div class="sub">{{ report_date }}  ·  {{ settings_summary }}</div>
</div>
<div class="container">

  <!-- 통계 -->
  <div class="stats">
    {% for stat in stats %}
    <div class="stat-card">
      <div class="num">{{ stat.value }}</div>
      <div class="label">{{ stat.label }}</div>
    </div>
    {% endfor %}
  </div>

  <!-- 섹션별 기사 -->
  {% for section in sections %}
  {% if section.articles|length > 0 %}
  <div class="section">
    <div class="section-title {{ section.css_class }}">{{ section.icon }} {{ section.title }} ({{ section.articles|length }}건)</div>
    {% for art in section.articles %}
    <div class="card tier-{{ art.tier|default(3) }}">
      <div class="meta">
        <span class="tier tier-{{ art.tier|default(3) }}">Tier {{ art.tier|default(3) }}</span>
        {{ art.media_name|default('') }}  ·  {{ art.pubDate|default('') }}
      </div>
      <div class="title"><a href="{{ art.link }}" target="_blank">{{ art.title }}</a></div>
      <div class="desc">{{ art.description|default('') }}</div>
      {% if art.matched_keywords %}
      <div class="tags">🔑 {{ art.matched_keywords|join(', ') }}</div>
      {% endif %}
      {% if art.similar_articles and art.similar_articles|length > 0 %}
      <div class="similar">
        📎 유사 기사 {{ art.similar_count|default(art.similar_articles|length) }}건:
        {% for sim in art.similar_articles %}
        <br>&nbsp;&nbsp;· {{ sim.media_name|default('') }} – <a href="{{ sim.link }}" target="_blank">{{ sim.title }}</a>
        {% endfor %}
      </div>
      {% endif %}
    </div>
    {% endfor %}
  </div>
  {% endif %}
  {% endfor %}

</div>
<div class="footer">NewsClipper v1 · Generated {{ now }}</div>
</body>
</html>"""


SECTION_CONFIG = {
    "product":          {"title": "제품/브랜드 기사",  "icon": "🎯", "css_class": "product"},
    "company_core":     {"title": "기업 기사 (핵심)",  "icon": "🏢", "css_class": "company"},
    "company_related":  {"title": "기업 기사 (관련)",  "icon": "🏢", "css_class": "company"},
    "company":          {"title": "기업 기사",         "icon": "🏢", "css_class": "company"},
    "competitor":       {"title": "경쟁사 기사",       "icon": "⚔️", "css_class": "competitor"},
    "industry":         {"title": "업계 기사",         "icon": "🏭", "css_class": "industry"},
}


def build_html_report(articles: list, stats: dict, settings: dict) -> str:
    """
    기사 리스트 + 통계 + 설정 → 완성된 HTML 문자열 반환.
    articles: pipeline 결과 리스트 (각 기사 dict에 'section' 키 포함)
    stats: pipeline이 반환한 stats dict
    settings: config/settings.yaml 로드 결과
    """
    env = Environment(loader=BaseLoader(), autoescape=True)
    template = env.from_string(REPORT_TEMPLATE)

    # ── 통계 카드 ──
    stat_cards = []
    stat_mapping = [
        ("total_collected", "총 수집"),
        ("after_media_filter", "매체 필터 후"),
        ("after_date_filter", "날짜 필터 후"),
        ("after_dedup", "중복 병합 후"),
        ("final", "최종 기사"),
        ("product_count", "제품/브랜드"),
        ("company_count", "기업 기사"),
        ("competitor_count", "경쟁사"),
    ]
    for key, label in stat_mapping:
        val = stats.get(key)
        if val is not None:
            stat_cards.append({"value": val, "label": label})

    # ── 섹션 구성 ──
    section_order = ["product", "company_core", "company_related", "company", "competitor", "industry"]
    sections = []
    for sec_key in section_order:
        sec_articles = [a for a in articles if a.get("section") == sec_key]
        if not sec_articles:
            continue
        cfg = SECTION_CONFIG.get(sec_key, {"title": sec_key, "icon": "📄", "css_class": "industry"})
        sections.append({
            "title": cfg["title"],
            "icon": cfg["icon"],
            "css_class": cfg["css_class"],
            "articles": sec_articles,
        })

    # ── 설정 요약 문자열 ──
    kw = settings.get("keywords", {})
    products = kw.get("product", kw.get("company", []))
    company = kw.get("company_name", [])
    summary_parts = []
    if products:
        summary_parts.append(f"제품: {', '.join(products[:5])}")
    if company:
        summary_parts.append(f"회사: {', '.join(company[:3])}")
    settings_summary = "  ·  ".join(summary_parts) if summary_parts else ""

    now = datetime.now()
    html = template.render(
        report_date=now.strftime("%Y년 %m월 %d일"),
        settings_summary=settings_summary,
        stats=stat_cards,
        sections=sections,
        now=now.strftime("%Y-%m-%d %H:%M"),
    )
    return html


def save_report(html: str, output_dir: str = "reports") -> str:
    """HTML을 파일로 저장하고 경로 반환."""
    os.makedirs(output_dir, exist_ok=True)
    filename = f"news_clip_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    return filepath
