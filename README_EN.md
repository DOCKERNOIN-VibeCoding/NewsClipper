> 🇰🇷 [한국어 버전](README.md)

# 📰 NewsClipper — AI-Powered News Clipping & Media Monitoring

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-green)

## About

NewsClipper is an automated news clipping tool designed for corporate PR and marketing professionals. It collects relevant news articles via the Naver News API, applies media tier filtering, merges similar articles, and classifies results by keyword relevance.

## Key Features

### News Collection & Filtering
- Real-time news collection via Naver News API
- Media tier classification (Tier 1: Major dailies, Tier 2: Business/Broadcasting, Tier 3: Specialized/Online)
- Date range filtering (1 to 30 days)

### Smart Classification
- Product/brand keyword priority matching (weight: 150 points)
- Company name keyword matching (weight: 50 points)
- Automatic classification into company / competitor articles

### Similar Article Merging
- Duplicate detection based on TF-IDF cosine similarity + noun overlap ratio
- 5-level sensitivity adjustment
- Highest-tier media article selected as representative
- Expandable/collapsible list of merged similar articles

### Output
- Section-based article cards (🎯 Product/Brand, 🏢 Company, ⚔️ Competitor)
- HTML report export (custom save location and filename)
- Media tier badges and matched keyword tags

## Installation & Usage

### Option 1: Run exe (General Users)

1. Download the latest zip from [Releases](https://github.com/DOCKERNOIN-VibeCoding/NewsClipper/releases)
2. Extract the archive
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
- Naver Search API	https://developers.naver.com	(News article collection)
- Google Gemini API	https://aistudio.google.com	(AI analysis (planned for v2))

2. Configure the Program
- Launch the program → 🔑 API Settings → Enter Naver API key
- 🔍 Search Settings → Enter industry, product/brand, company name, competitors
- Set collection frequency and similar article merging sensitivity
- Click 🚀 Start News Clipping

## Tech Stack
- UI: CustomTkinter
- News Collection: Naver Search API
- Similarity Analysis: scikit-learn TF-IDF + Cosine Similarity
- Report Generation: Jinja2 HTML Templates
- Distribution: PyInstaller (Windows exe)

## Planned for v2
- 🤖 Gemini AI-powered article summarization (2-3 sentences)
- 🎯 AI relevance verification (core / relevant / passing / irrelevant)
- 🏷️ AI keyword tagging (company / competitor / industry classification)
- 🔥 HOT KEYWORDS Top 10 visualization
- 📊 Enhanced HTML reports
- ⏰ Windows Task Scheduler integration for automated execution

## Credits
Developed by DOCKERNOIN with Claude AI

