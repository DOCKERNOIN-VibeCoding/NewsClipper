"""HTML 리포트 생성 모듈"""
import os
from datetime import datetime
from jinja2 import Environment, BaseLoader

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

  /* 복사 버튼 툴바 (복사 영역 밖에 위치) */
  .toolbar { background: #fff; padding: 14px 20px; border-bottom: 1px solid #e2e8f0;
             text-align: right; }
  .toolbar .info { float: left; font-size: 12px; color: #64748b; padding-top: 8px; }
  .copy-btn { background: #1a3a6b; color: #fff; border: none;
              padding: 9px 16px; border-radius: 6px; font-size: 12px;
              font-weight: bold; cursor: pointer; font-family: inherit;
              margin-left: 8px; transition: all 0.2s; }
  .copy-btn:hover { background: #2563b0; transform: translateY(-1px); }
  .copy-btn.copied { background: #16a34a; }
  .copy-btn.simple { background: #e07b30; }
  .copy-btn.simple:hover { background: #c2410c; }
  .copy-btn.simple.copied { background: #16a34a; }
  .copy-btn small { font-size: 10px; opacity: 0.85; font-weight: normal; }

  .header { background: linear-gradient(135deg, #0a1628 0%, #1a3a6b 100%); color: #fff; padding: 32px 40px; }
  .header h1 { font-size: 24px; margin-bottom: 6px; }
  .header .sub { font-size: 13px; color: #a0b4d0; }

  .container { max-width: 1100px; margin: 0 auto; padding: 24px 20px; }

  /* 통계 */
  .stats { display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }
  .stat-card { background: #fff; border-radius: 10px; padding: 18px 22px; flex: 1; min-width: 140px;
               box-shadow: 0 1px 4px rgba(0,0,0,0.08); text-align: center; }
  .stat-card .num { font-size: 28px; font-weight: bold; color: #1a3a6b; }
  .stat-card .label { font-size: 12px; color: #666; margin-top: 4px; }

  /* 🔥 HOT KEYWORDS */
  .hot-card { background: #fff; border-radius: 10px; padding: 20px 24px;
              margin-bottom: 28px; box-shadow: 0 1px 4px rgba(0,0,0,0.08);
              border: 1px solid #fde4d3; }
  .hot-header { display: flex; justify-content: space-between; align-items: center;
                margin-bottom: 14px; flex-wrap: wrap; gap: 8px; }
  .hot-title { font-size: 15px; font-weight: bold; color: #c2410c; }
  .hot-legend { font-size: 11px; color: #666; }
  .hot-legend .chip { display: inline-block; width: 9px; height: 9px;
                      border-radius: 2px; margin: 0 4px 0 12px; vertical-align: middle; }
  .hot-row { display: flex; align-items: center; gap: 8px; padding: 4px 0; font-size: 13px; }
  .hot-rank { width: 28px; text-align: right; color: #888; font-size: 11px; }
  .hot-keyword { width: 140px; font-weight: bold; color: #222;
                 white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .hot-bar-bg { flex: 1; height: 14px; background: #f1f5f9; border-radius: 4px;
                position: relative; overflow: hidden; }
  .hot-bar { height: 100%; border-radius: 4px; }
  .hot-count { width: 40px; font-size: 11px; color: #666; text-align: left; }

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

  /* 인쇄 시 툴바 숨김 */
  @media print { .toolbar { display: none; } }
</style>
</head>
<body>

<!-- 툴바 (복사 영역 바깥) -->
<div class="toolbar">
  <span class="info">📌 복사 버튼은 복사 결과에 포함되지 않습니다</span>
  <button class="copy-btn" id="copyRichBtn" onclick="copyRich()">
    📋 화면 그대로 복사 <small>(Gmail/네이버메일)</small>
  </button>
  <button class="copy-btn simple" id="copySimpleBtn" onclick="copySimple()">
    📧 메일용 단순 복사 <small>(Outlook/Word)</small>
  </button>
</div>

<!-- 복사 대상: 화면 그대로 버전 -->
<div id="report-content">

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

  <!-- 🔥 HOT KEYWORDS -->
  {% if hot_keywords and hot_keywords|length > 0 %}
  <div class="hot-card">
    <div class="hot-header">
      <div class="hot-title">🔥 HOT KEYWORDS Top {{ hot_keywords|length }}</div>
      <div class="hot-legend">
        <span><span class="chip" style="background:#2563b0;"></span>자사</span>
        <span><span class="chip" style="background:#e07b30;"></span>경쟁사</span>
        <span><span class="chip" style="background:#94a3b8;"></span>기타</span>
      </div>
    </div>
    {% for hk in hot_keywords %}
    <div class="hot-row">
      <div class="hot-rank">{{ hk.rank }}.</div>
      <div class="hot-keyword">{{ hk.keyword }}</div>
      <div class="hot-bar-bg">
        <div class="hot-bar" style="width: {{ hk.bar_pct }}%; background: {{ hk.bar_color }};"></div>
      </div>
      <div class="hot-count">{{ hk.count }}</div>
    </div>
    {% endfor %}
  </div>
  {% endif %}

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
<div class="footer">NewsClipper v2.3 · Generated {{ now }}</div>

</div>
<!-- 복사 대상 끝 -->


<!-- 메일용 단순 버전 (숨김, 복사 시에만 사용) -->
<div id="report-simple" style="display:none;">
{{ simple_html | safe }}
</div>


<script>
  function flashButton(btn, originalHtml) {
    btn.innerHTML = '✅ 복사 완료!';
    btn.classList.add('copied');
    setTimeout(function() {
      btn.innerHTML = originalHtml;
      btn.classList.remove('copied');
    }, 2000);
  }

  // ── 화면 그대로 복사 (디자인 유지) ──
  function copyRich() {
    const btn = document.getElementById('copyRichBtn');
    const target = document.getElementById('report-content');
    const originalHtml = btn.innerHTML;
    copyElementHtml(target, btn, originalHtml);
  }

  // ── 메일용 단순 복사 (Outlook 호환) ──
  function copySimple() {
    const btn = document.getElementById('copySimpleBtn');
    const target = document.getElementById('report-simple');
    const originalHtml = btn.innerHTML;
    // 잠시 보이게 했다가 복사
    target.style.display = 'block';
    copyElementHtml(target, btn, originalHtml, function() {
      target.style.display = 'none';
    });
  }

  function copyElementHtml(target, btn, originalHtml, afterCallback) {
    try {
      const range = document.createRange();
      range.selectNode(target);
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);

      const ok = document.execCommand('copy');
      selection.removeAllRanges();

      if (afterCallback) afterCallback();

      if (ok) {
        flashButton(btn, originalHtml);
      } else {
        throw new Error('execCommand failed');
      }
    } catch (e) {
      // Clipboard API fallback
      try {
        const html = target.innerHTML;
        const blob = new Blob([html], { type: 'text/html' });
        const data = [new ClipboardItem({ 'text/html': blob })];
        navigator.clipboard.write(data).then(function() {
          if (afterCallback) afterCallback();
          flashButton(btn, originalHtml);
        });
      } catch (e2) {
        if (afterCallback) afterCallback();
        alert('복사 실패: 본문을 직접 드래그해서 복사해주세요.');
      }
    }
  }
</script>

</body>
</html>"""


# ── 메일용 단순 버전 템플릿 (table + 인라인 스타일) ──
SIMPLE_TEMPLATE = r"""<table cellpadding="0" cellspacing="0" border="0" width="100%" style="font-family:'Malgun Gothic','맑은 고딕',sans-serif;color:#222;background:#ffffff;max-width:800px;">
  <!-- 헤더 -->
  <tr>
    <td style="background:#1a3a6b;color:#ffffff;padding:24px 28px;">
      <div style="font-size:22px;font-weight:bold;margin-bottom:4px;">뉴스 클리핑 리포트</div>
      <div style="font-size:12px;color:#a0b4d0;">{{ report_date }}{% if settings_summary %} · {{ settings_summary }}{% endif %}</div>
    </td>
  </tr>

  <!-- 통계 -->
  <tr>
    <td style="padding:18px 28px;background:#f4f6f9;font-size:13px;color:#444;">
      {% for stat in stats %}<b>{{ stat.label }}</b> {{ stat.value }}{% if not loop.last %} &nbsp;·&nbsp; {% endif %}{% endfor %}
    </td>
  </tr>

  {% if hot_keywords and hot_keywords|length > 0 %}
  <!-- HOT KEYWORDS -->
  <tr>
    <td style="padding:20px 28px 8px 28px;background:#ffffff;">
      <div style="font-size:15px;font-weight:bold;color:#c2410c;margin-bottom:10px;">🔥 HOT KEYWORDS Top {{ hot_keywords|length }}</div>
      <table cellpadding="0" cellspacing="0" border="0" width="100%" style="font-size:13px;">
        {% for hk in hot_keywords %}
        <tr>
          <td width="30" style="padding:3px 0;color:#888;font-size:11px;">{{ hk.rank }}.</td>
          <td width="160" style="padding:3px 0;font-weight:bold;color:#222;">{{ hk.keyword }}</td>
          <td style="padding:3px 0;">
            <table cellpadding="0" cellspacing="0" border="0" width="100%"><tr>
              <td width="{{ hk.bar_pct }}%" bgcolor="{{ hk.bar_color }}" height="12" style="background-color:{{ hk.bar_color }};height:12px;line-height:1px;font-size:1px;mso-line-height-rule:exactly;">&nbsp;</td>
              <td bgcolor="#f1f5f9" height="12" style="background-color:#f1f5f9;height:12px;line-height:1px;font-size:1px;mso-line-height-rule:exactly;">&nbsp;</td>
            </tr></table>
          </td>
          <td width="40" style="padding:3px 0 3px 8px;color:#666;font-size:11px;">{{ hk.count }}</td>
        </tr>
        {% endfor %}
      </table>
      <table cellpadding="0" cellspacing="0" border="0" style="margin-top:10px;">
        <tr>
          <td width="12" height="12" bgcolor="#2563b0" style="background-color:#2563b0;width:12px;height:12px;font-size:1px;line-height:1px;mso-line-height-rule:exactly;">&nbsp;</td>
          <td style="padding:0 14px 0 5px;font-size:11px;color:#666;">자사</td>
          <td width="12" height="12" bgcolor="#e07b30" style="background-color:#e07b30;width:12px;height:12px;font-size:1px;line-height:1px;mso-line-height-rule:exactly;">&nbsp;</td>
          <td style="padding:0 14px 0 5px;font-size:11px;color:#666;">경쟁사</td>
          <td width="12" height="12" bgcolor="#94a3b8" style="background-color:#94a3b8;width:12px;height:12px;font-size:1px;line-height:1px;mso-line-height-rule:exactly;">&nbsp;</td>
          <td style="padding:0 0 0 5px;font-size:11px;color:#666;">기타</td>
        </tr>
      </table>
    </td>
  </tr>
  {% endif %}

  <!-- 섹션별 기사 -->
  {% for section in sections %}{% if section.articles|length > 0 %}
  <tr>
    <td style="padding:18px 28px 6px 28px;">
      <div style="background:{{ section.bg_color }};color:#ffffff;font-size:15px;font-weight:bold;padding:9px 14px;">{{ section.icon }} {{ section.title }} ({{ section.articles|length }}건)</div>
    </td>
  </tr>
  {% for art in section.articles %}
  <tr>
    <td style="padding:0 28px 10px 28px;">
      <table cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#ffffff;border-left:3px solid {{ section.bg_color }};">
        <tr><td style="padding:12px 14px;">
          <div style="font-size:11px;color:#888;margin-bottom:4px;">
            <span style="background:{{ section.bg_color }};color:#ffffff;padding:1px 6px;font-size:10px;">Tier {{ art.tier|default(3) }}</span>
            &nbsp;{{ art.media_name|default('') }} · {{ art.pubDate|default('') }}
          </div>
          <div style="font-size:14px;font-weight:bold;margin-bottom:4px;">
            {% if art.link %}<a href="{{ art.link }}" style="color:#1a3a6b;text-decoration:none;">{{ art.title }}</a>{% else %}{{ art.title }}{% endif %}
          </div>
          {% if art.description %}<div style="font-size:12px;color:#444;line-height:1.5;">{{ art.description }}</div>{% endif %}
          {% if art.matched_keywords %}<div style="font-size:11px;color:#1a3a6b;margin-top:4px;">🔑 {{ art.matched_keywords|join(', ') }}</div>{% endif %}
          {% if art.similar_articles and art.similar_articles|length > 0 %}
          <div style="font-size:11px;color:#888;margin-top:6px;padding-top:6px;border-top:1px dashed #ddd;">
            📎 유사 기사 {{ art.similar_count|default(art.similar_articles|length) }}건:
            {% for sim in art.similar_articles %}
            <br>&nbsp;&nbsp;· {{ sim.media_name|default('') }} – {% if sim.link %}<a href="{{ sim.link }}" style="color:#5577aa;">{{ sim.title }}</a>{% else %}{{ sim.title }}{% endif %}
            {% endfor %}
          </div>
          {% endif %}
        </td></tr>
      </table>
    </td>
  </tr>
  {% endfor %}
  {% endif %}{% endfor %}

  <tr><td style="padding:16px 28px;font-size:11px;color:#999;text-align:center;">NewsClipper v2.3 · Generated {{ now }}</td></tr>
</table>"""


SECTION_CONFIG = {
    "product":          {"title": "제품/브랜드 기사",  "icon": "🎯", "css_class": "product",     "bg_color": "#1a3a6b"},
    "company_core":     {"title": "기업 기사 (핵심)",  "icon": "🏢", "css_class": "company",     "bg_color": "#2563b0"},
    "company_related":  {"title": "기업 기사 (관련)",  "icon": "🏢", "css_class": "company",     "bg_color": "#2563b0"},
    "company":          {"title": "기업 기사",         "icon": "🏢", "css_class": "company",     "bg_color": "#2563b0"},
    "competitor":       {"title": "경쟁사 기사",       "icon": "⚔️", "css_class": "competitor",  "bg_color": "#e07b30"},
    "industry":         {"title": "업계 기사",         "icon": "🏭", "css_class": "industry",    "bg_color": "#5a6f8a"},
}

# HOT KEYWORDS 카테고리별 색상 (메인 창 UI와 동일)
HOT_BAR_COLORS = {
    "company":    "#2563b0",   # 자사 - 코발트
    "competitor": "#e07b30",   # 경쟁사 - 오렌지
    "other":      "#94a3b8",   # 기타 - 회색
}


def build_html_report(
    articles: list,
    stats: dict,
    settings: dict,
    hot_keywords: list = None,
) -> str:
    """
    기사 리스트 + 통계 + 설정 + HOT KEYWORDS → 완성된 HTML 문자열 반환.

    화면용(디자인 유지)과 메일용(table + 인라인 스타일) 두 버전을 함께 포함.
    """
    env = Environment(loader=BaseLoader(), autoescape=True)

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

    # ── HOT KEYWORDS 가공 (바 너비 % + 색상 미리 계산) ──
    hot_keywords_processed = []
    if hot_keywords:
        max_count = max((hk.get("count", 0) for hk in hot_keywords), default=1)
        max_count = max(max_count, 1)

        for hk in hot_keywords:
            count = hk.get("count", 0)
            ratio = count / max_count
            bar_pct = int(ratio * 100)
            bar_pct = max(bar_pct, 3) if count > 0 else 0

            category = hk.get("category", "other")
            bar_color = HOT_BAR_COLORS.get(category, HOT_BAR_COLORS["other"])

            hot_keywords_processed.append({
                "rank": hk.get("rank", 0),
                "keyword": hk.get("keyword", ""),
                "count": count,
                "category": category,
                "bar_pct": bar_pct,
                "bar_color": bar_color,
            })

    # ── 섹션 구성 ──
    section_order = ["product", "company_core", "company_related", "company", "competitor", "industry"]
    sections = []
    for sec_key in section_order:
        sec_articles = [a for a in articles if a.get("section") == sec_key]
        if not sec_articles:
            continue
        cfg = SECTION_CONFIG.get(sec_key, {"title": sec_key, "icon": "📄", "css_class": "industry", "bg_color": "#5a6f8a"})
        sections.append({
            "title": cfg["title"],
            "icon": cfg["icon"],
            "css_class": cfg["css_class"],
            "bg_color": cfg["bg_color"],
            "articles": sec_articles,
        })

    # ── 설정 요약 ──
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
    common_ctx = dict(
        report_date=now.strftime("%Y년 %m월 %d일"),
        settings_summary=settings_summary,
        stats=stat_cards,
        hot_keywords=hot_keywords_processed,
        sections=sections,
        now=now.strftime("%Y-%m-%d %H:%M"),
    )

    # 1) 메일용 단순 버전 먼저 렌더 (위 화면용 안에 삽입할 것)
    simple_template = env.from_string(SIMPLE_TEMPLATE)
    simple_html = simple_template.render(**common_ctx)

    # 2) 화면용 풀 버전 렌더 (메일용 버전을 숨김 영역에 끼워 넣음)
    main_template = env.from_string(REPORT_TEMPLATE)
    html = main_template.render(simple_html=simple_html, **common_ctx)
    return html


def save_report(html: str, output_dir: str = "reports") -> str:
    """HTML을 파일로 저장하고 경로 반환."""
    os.makedirs(output_dir, exist_ok=True)
    filename = f"news_clip_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    return filepath
