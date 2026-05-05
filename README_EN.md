
## 📄 2. README_EN.md (영문) — 전체 교체

`README_EN.md` 파일도 동일하게 통째로 덮어쓰세요.

```markdown
> 🇰🇷 [한국어 버전](README.md)

# 📰 NewsClipper — AI-Powered News Clipping & Media Monitoring

![Version](https://img.shields.io/badge/version-v2.3-blue)
![Python](https://img.shields.io/badge/python-3.10+-3776AB?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/platform-Windows-0078D6?logo=windows&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)

## About

**NewsClipper** is an **AI-powered news clipping automation tool** designed for corporate PR and marketing professionals in South Korea. It collects **Korean-language news articles** via the Naver News API, then leverages **Google Gemini AI** to verify relevance, summarize content, and extract entities. The result is a polished HTML report that can be pasted directly into Gmail, Outlook, or Word.

> **Note:** This program currently supports Korean news sources only, as it relies on the Naver News API which indexes Korean media outlets.

> 🆕 **v2.3 (May 2026)** — Email-compatible HTML reports (Gmail/Outlook/Word), HOT KEYWORDS color charts, automatic 503 retry, settings deep merge

## ✨ Key Features

### 🔍 News Collection & Filtering
- Real-time news collection via Naver News API
- Media tier classification (Tier 1: Major dailies · Tier 2: Business/Broadcasting · Tier 3: Specialized/Online)
- Date range filtering (1 to 30 days)
- Industry-based automatic keyword expansion

### 🤖 AI Integrated Analysis (Gemini 2.5 Flash-Lite)
- **4-level relevance classification**: core · relevant · passing · irrelevant
- **Korean 2-3 sentence summarization** with key figures preserved (market share, growth rates, etc.)
- **Entity & sentiment extraction**: companies, brands, people + positive/neutral/negative tagging
- **Batch processing** (default 10 articles/call) + **3-attempt auto-retry** (handles 503 errors)
- **Automatic fallback**: switches to local keyword matching when daily quota is exceeded

### 🔥 HOT KEYWORDS Top 10
- Aggregates most-mentioned brands, companies, and products across all articles
- Combines AI entities (weight 2) + title nouns (weight 1)
- AI classification removes generic terms and merges synonyms (e.g., "CJ제일제당" / "CJ" / "제일제당")
- Color-coded horizontal bar chart: company (blue) · competitor (orange) · other (gray)

### 🔄 Similar Article Merging
- Duplicate detection based on TF-IDF cosine similarity + noun overlap ratio
- 5-level sensitivity adjustment
- Highest-tier media article selected as representative
- Expandable/collapsible list of merged similar articles

### 📧 HTML Report (Email-Compatible)
- Section-based article cards (🎯 Product/Brand · 🏢 Company core/related · ⚔️ Competitor · 🏭 Industry)
- AI summary boxes, relevance badges, sentiment tags (↑/—/↓), entity chips
- **Dual copy buttons**:
  - 📋 **Copy as displayed** — for Gmail/Naver Mail (full design)
  - 📧 **Copy for email clients** — for Outlook/Word (table + inline CSS)
- HOT KEYWORDS color bars render correctly across all major email clients

## 🚀 Installation & Usage

### Option 1: Run EXE (Recommended for General Users)
1. Download the latest zip from [Releases](https://github.com/DOCKERNOIN-VibeCoding/NewsClipper/releases/latest)
2. Extract the archive (e.g., `D:\NewsClipper\`)
3. Run `NewsClipper.exe`

### Option 2: Run from Source (Developers)
```bash
git clone https://github.com/DOCKERNOIN-VibeCoding/NewsClipper.git
cd NewsClipper
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python main.py


## Initial Setup
1. Get API Keys
- Naver Search API	https://developers.naver.com	(News article collection(required))
- Google Gemini API	https://aistudio.google.com	(AI analysis (required, Free Tier OK))
- 💡 Recommended for Gemini Free Tier: model gemini-2.5-flash-lite + batch_size: 10 (default). Sufficient for 1-2 clipping runs per day within the free quota.

2. Configure the Program
 1. Launch → 🔑 API Settings → Enter Naver / Gemini keys → Test connection
 2. 🔍 Search Settings → Select industries (max 3) → Enter product/brand, company, competitor, and industry keywords
 3. Set collection frequency (daily/weekly/monthly), media tiers, and dedup sensitivity
 4. Click 🚀 Start News Clipping
 5. Review results → 📥 Export to HTML → Open in browser → Copy & paste into your email


## Tech Stack
- UI: CustomTkinter (native Python GUI)
- News Collection: Naver Search API
- AI Analysis: Google Gemini 2.5 Flash-Lite
- Similarity Analysis: scikit-learn TF-IDF + Cosine Similarity
- Report Generation: Jinja2 HTML Templates (dual mode)
- Distribution: PyInstaller (Windows exe)

## 개발 로드맵
- 2-1 : Advanced duplicate merging중복 병합 고도화 ✅Done
- 2-1 : AI integrated analysisAI 통합 분석 ✅Done
- 2-1 : HOT KEYWORDS Top 10 ✅Done
- 2-1 : HTML report enhancement (email-compatible)HTML 리포트 고도화 (메일 호환) ✅Done
- 2-1 : UI updatesUI 업데이트 ✅Done
- 2-1 : CLI / Windows Task SchedulerCLI  ⏸ Planned

## Changelog
v2.3 (2026-05-05) — Dual HTML report templates, Outlook/Word email compatibility
v2.2.1 (2026-05-04) — settings.yaml preservation (deep merge), 503 retry, dialog stability
v2.2 (2026-05-04) — HOT KEYWORDS Top 10 + color bar chart
v2.0 (2026-05-03) — Gemini AI integration: relevance, summary, entities, sentiment
v1.0 (2026-05) — Initial release with Naver API + TF-IDF

## License
MIT License

## Credits
Developed by DOCKERNOIN with Claude AI
Powered by Naver News API + Google Gemini

