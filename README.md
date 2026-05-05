> 🇺🇸 [English Version](README_EN.md)

# 📰 NewsClipper — AI 기반 뉴스 클리핑 & 미디어 모니터링

![Version](https://img.shields.io/badge/version-v2.3-blue)
![Python](https://img.shields.io/badge/python-3.10+-3776AB?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/platform-Windows-0078D6?logo=windows&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)

## 프로그램 소개

**NewsClipper**는 기업 홍보/마케팅 담당자를 위한 **AI 기반 뉴스 클리핑 자동화 도구**입니다.
Naver News API로 관련 뉴스를 자동 수집하고, **Google Gemini AI**가 기사의 관련도를 검증·요약·엔티티를 추출하여 정리된 결과를 제공합니다. 메일에 그대로 붙여넣을 수 있는 HTML 리포트까지 한 번에 만들어 줍니다.

> 🆕 **v2.3 (2026-05)** — HTML 리포트 메일 호환(Gmail/Outlook/Word), HOT KEYWORDS 색상 그래프, 503 자동 재시도, 설정 보존 deep merge

## ✨ 주요 기능

### 🔍 뉴스 수집 & 필터링
- Naver News API 기반 실시간 뉴스 수집
- 매체 티어 분류 (Tier 1: 주요 일간지 · Tier 2: 경제/방송 · Tier 3: 전문/온라인)
- 날짜 범위 필터링 (1일 ~ 30일)
- 산업군 기반 키워드 자동 보강

### 🤖 AI 통합 분석 (Gemini 2.5 Flash-Lite)
- **관련도 4단계 분류**: 핵심(core) · 관련(relevant) · 간접언급(passing) · 무관(irrelevant)
- **한국어 2~3문장 요약**: 핵심 수치(점유율, 증감율 등) 자동 포함
- **엔티티 + 감성 추출**: 기업명·브랜드·인물 + 긍정/중립/부정 태깅
- **배치 처리** (기본 10건/회) + **3회 자동 재시도** (503 오류 대응)
- **자동 fallback**: 일일 한도 초과 시 로컬 키워드 매칭으로 전환

### 🔥 HOT KEYWORDS Top 10
- 전체 기사에서 가장 많이 언급된 브랜드/기업/제품 집계
- AI 엔티티(가중치 2) + 제목 명사(가중치 1) 결합
- AI 분류로 일반어 제거 + 동의어 자동 통합 (예: "CJ제일제당" / "CJ" / "제일제당")
- 자사(파랑) · 경쟁사(주황) · 기타(회색) 색상 구분 가로 바 차트

### 🔄 유사 기사 병합
- TF-IDF 코사인 유사도 + 명사 겹침률 기반 중복 탐지
- 5단계 감도 조절 (사용자 설정)
- 최고 티어 매체를 대표 기사로 자동 선정
- 병합된 유사 기사 펼침/접힘 UI

### 📧 HTML 리포트 (메일 호환)
- 섹션별 기사 카드 (🎯 제품/브랜드 · 🏢 자사 핵심·관련 · ⚔️ 경쟁사 · 🏭 업계)
- AI 요약 박스, 관련도 뱃지, 감성 태그(↑/—/↓), 엔티티 칩
- **듀얼 복사 버튼**:
  - 📋 **화면 그대로 복사** — Gmail/네이버 메일용 (풀 디자인)
  - 📧 **메일용 단순 복사** — Outlook/Word용 (table + inline CSS)
- HOT KEYWORDS 색상 막대가 모든 메일 클라이언트에서 정상 표시

## 🚀 설치 및 실행

### 방법 1: EXE 실행 (일반 사용자 권장)
1. [Releases](https://github.com/DOCKERNOIN-VibeCoding/NewsClipper/releases/latest)에서 최신 zip 다운로드
2. 압축 해제 (예: `D:\NewsClipper\`)
3. `NewsClipper.exe` 실행

### 방법 2: 소스코드 실행 (개발자)
```bash
git clone https://github.com/DOCKERNOIN-VibeCoding/NewsClipper.git
cd NewsClipper
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## 초기 설정
1. API 키 발급이 필요합니다.
- Naver 검색 API	https://developers.naver.com	뉴스 기사 수집
- Google Gemini API	https://aistudio.google.com	AI 분석 (v2 예정)

1-1.💡 Gemini Free Tier 권장 설정: 모델 gemini-2.5-flash-lite + batch_size: 10 (기본값) 일 평균 1~2회 클리핑 시 무료 한도 내에서 충분히 운영 가능합니다.

2. 프로그램 설정
- 프로그램 실행 → 🔑 API 설정 → API 키 입력
- 🔍 검색 조건 → 산업군, 제품/브랜드, 회사명, 경쟁사 입력
- 취합 주기 및 유사기사 병합 감도 설정
- 🚀 뉴스 클리핑 시작 클릭

## 기술 스택
- UI: CustomTkinter (Python 네이티브 GUI)
- 뉴스 수집: Naver Search API (REST)
- 유사도 분석: scikit-learn TF-IDF + 코사인 유사도
- 리포트 생성: Jinja2 HTML 템플릿 (듀얼 모드)
- 배포: PyInstaller (Windows exe)

## 개발 로드맵
- 2-1 : 중복 병합 고도화 ✅완료
- 2-1 : AI 통합 분석 ✅완료
- 2-1 : HOT KEYWORDS Top 10 ✅완료
- 2-1 : HTML 리포트 고도화 (메일 호환) ✅완료
- 2-1 : UI 업데이트 ✅완료
- 2-1 : CLI / Windows 작업 스케줄러  ⏸ 진행 예정

- 🏷️ 자세한 내용은 docs/v2_development_plan.md 참고

## 변경 이력
  v2.3 (2026-05-05) — HTML 리포트 듀얼 템플릿, Outlook/Word 메일 호환
  v2.2.1 (2026-05-04) — settings.yaml 보존(deep merge), 503 재시도, 다이얼로그 안정화
  v2.2 (2026-05-04) — HOT KEYWORDS Top 10 + 색상 바 차트
  v2.0 (2026-05-03) — Gemini AI 통합 분석, 관련도/요약/엔티티/감성
  v1.0 (2026-05) — Naver API + TF-IDF 기반 최초 릴리스


## 라이선스
MIT License

## 크래딧
Developed by DOCKERNOIN with Claude AI
Powered by Naver News API + Google Gemini

