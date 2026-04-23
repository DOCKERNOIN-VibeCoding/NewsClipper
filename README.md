
# 📰 NewsClipper — AI 기반 뉴스 클리핑 & 미디어 모니터링

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 프로그램 소개

NewsClipper는 기업 홍보/마케팅 담당자를 위한 뉴스 클리핑 자동화 도구입니다.
Naver News API를 통해 관련 뉴스를 자동 수집하고, 매체 등급별 필터링,
유사 기사 병합, 키워드 기반 분류를 수행하여 정리된 결과를 제공합니다.

## 주요 기능

### 뉴스 수집 & 필터링
- Naver News API 기반 실시간 뉴스 수집
- 매체 티어 분류 (Tier 1: 주요 일간지, Tier 2: 경제/방송, Tier 3: 전문/온라인)
- 날짜 범위 필터링 (1일 ~ 30일)

### 스마트 분류
- 제품/브랜드 키워드 우선 매칭
- 기업 기사 / 경쟁사 기사 자동 분류
- 키워드 가중치 기반 관련도 점수 산출

### 유사 기사 병합
- TF-IDF 코사인 유사도 + 명사 겹침률 기반 중복 탐지
- 5단계 감도 조절 가능 (사용자 설정)
- 최고 티어 매체 기사를 대표 기사로 선정
- 병합된 유사 기사 목록 펼침/접힘 확인 가능

### 결과 출력
- 섹션별 기사 카드 (🎯 제품/브랜드, 🏢 기업, ⚔️ 경쟁사)
- HTML 리포트 내보내기 (파일명/저장 위치 지정)
- 매체 티어 뱃지, 매칭 키워드 태그 표시

## 설치 및 실행

### 방법 1: exe 실행 (일반 사용자)
1. [Releases](https://github.com/DOCKERNOIN-VibeCoding/NewsClipper/releases) 에서 최신 버전 zip 다운로드
2. 압축 해제
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

3. 프로그램 설정
- 프로그램 실행 → 🔑 API 설정 → API 키 입력
- 🔍 검색 조건 → 산업군, 제품/브랜드, 회사명, 경쟁사 입력
- 취합 주기 및 유사기사 병합 감도 설정
- 🚀 뉴스 클리핑 시작 클릭

## 기술 스택
- UI: CustomTkinter (Python 네이티브 GUI)
- 뉴스 수집: Naver Search API (REST)
- 유사도 분석: scikit-learn TF-IDF + 코사인 유사도
- 리포트 생성: Jinja2 HTML 템플릿
- 배포: PyInstaller (Windows exe)

## v2 개발 예정 기능
- 🔄 중복 기사 병합 고도화
- 🤖 Gemini AI 기반 기사 요약 (2~3문장)
- 🏷️ AI 관련도 검증 (핵심/관련/간접언급/무관 분류)
- 🔥 HOT KEYWORDS Top 10 시각화
- ⏰ Windows 작업 스케줄러 연동 자동 실행

## 라이선스
MIT License

## 크래딧
Developed by DOCKERNOIN with Claude AI

