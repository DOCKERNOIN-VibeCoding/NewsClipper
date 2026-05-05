# NewsClipper v2.0 개발 정의서

> **문서 버전**: 1.4 (2026-05-05 갱신)
> **현재 진행 단계**: Phase 2-1 ~ 2-5 완료 → Phase 2-6 (스케줄링)만 남음
> **최신 릴리즈**: v2.3 (HTML 리포트 고도화 + Outlook/Word 메일 호환)

---

## 1. 개요

v1.0에서는 Naver News API + TF-IDF 기반 로컬 처리로 뉴스를 수집·분류했습니다.
v2.0에서는 **Gemini AI를 파이프라인에 통합**하여, 기사의 실제 관련도를 검증하고,
요약을 생성하고, 핵심 엔티티를 추출하여 최종 리포트의 품질을 대폭 향상시킵니다.
v2.3에서는 **HTML 리포트를 메일 클라이언트(Gmail/Outlook/Word)에 그대로 붙여넣을 수 있는 형태**로 고도화했습니다.

### 진행 상태 요약

| Phase | 내용 | 상태 |
|:---:|------|:---:|
| 2-1 | 중복 병합 고도화 | 🔵 v1에서 대부분 완료, 본문 비교는 보류 |
| 2-2 | AI 통합 분석 | ✅ **완료** (2026-05-03) |
| 2-3 | HOT KEYWORDS Top 10 | ✅ **완료** (2026-05-04) |
| 2-4 | HTML 리포트 고도화 | ✅ **완료** (2026-05-05, v2.3) |
| 2-5 | UI 업데이트 | ✅ **완료** (2026-05-03) |
| 2-6 | CLI/스케줄링 | ⏸ 다음 작업 |

---

## 2. 사용 모델 및 API 비용

**실전 권장 모델: Gemini 2.5 Flash-Lite + batch_size 10**

실제 운영 결과 Free Tier 일일 한도(약 500 RPD)가 1~2회 클리핑으로도 빠르게 소진되어, **batch_size를 10으로 늘리고 Flash-Lite로 전환**하는 것을 표준 설정으로 정했습니다.

| 항목 | Gemini 2.5 Flash | Gemini 2.5 Flash-Lite |
|------|:---:|:---:|
| Free Tier 일일 한도 (RPD) | 약 500 | 약 1,000 |
| Paid 입력 단가 ($/1M tok) | 0.30 | 0.10 |
| Paid 출력 단가 ($/1M tok) | 2.50 | 0.40 |
| 응답 품질 | 매우 우수 | 우수 (실전 충분) |
| **권장 용도** | 정밀 분석 | **일상 클리핑 (기본값)** |

1회 클리핑 예상 호출: 기사 50건 ÷ batch_size 10 = **5회 호출**
월간 예상 비용: Free Tier $0 / Paid Tier $0.5 미만

---

## 3. 개발 기능 목록

### Phase 2-1: 키워드 구조 개편 + 중복 병합 고도화

v1에서 완료된 항목으로 제품/브랜드와 회사명 키워드 분리 입력, TF-IDF + 명사 겹침률 기반 유사 기사 병합, 5단계 감도 조절, 유사 기사 펼침/접힘 UI가 포함됩니다. v2에서 추가하기로 했던 본문 200자 비교는 Naver API description으로도 충분히 동작 중이며 본문 크롤링은 차단 위험과 속도 부담이 있어 보류 상태입니다.

**파일:** `dedup/deduplicator.py`

---

### Phase 2-2: AI 통합 분석 ✅ 완료

하나의 Gemini API 호출로 관련도 검증·요약·엔티티 추출을 동시에 수행합니다. 4단계 등급(core / relevant / passing / irrelevant)으로 분류하고, 한국어 2~3문장 요약을 생성하며, 기업명·브랜드·인물 엔티티와 감성(positive/neutral/negative)을 함께 추출합니다.

**API 호출 최적화 (실제 적용값):** 대표 기사만 분석(병합 후 30~80건), batch_size 기본 10(Flash-Lite), 실패 시 최대 3회 재시도(exponential backoff), 일일 한도 초과·네트워크 오류 시 로컬 키워드 매칭으로 자동 fallback, 응답 파싱 시 코드블록 래핑·후행 콤마·index 키 매칭까지 견고하게 처리합니다.

**파일:** `ai/article_analyzer.py`, `tests/test_ai_analyzer.py`, `pipeline.py`, `main.py`, `config/settings_template.yaml`

---

### Phase 2-3: HOT KEYWORDS Top 10 ✅ 완료

전체 기사에서 가장 많이 언급된 브랜드/제품/기업명을 집계하여 Top 10으로 시각화합니다. AI entities(weight 2)와 제목 명사(weight 1)를 가중 합산한 뒤, AI 분류 단계로 일반어를 제거하고 동의어를 통합합니다.

**v2.2.1에서 추가된 503 재시도 로직:** `ai/keyword_classifier.py`에 `article_analyzer.py`와 동일한 재시도 메커니즘(3회, exponential backoff 2/4/8초)을 추가하여 일시적 503 오류 시 자동 복구하도록 했습니다.

**시각화 색상:** 자사 = 코발트 블루(#2563b0), 경쟁사 = 오렌지(#e07b30), 기타 = 회색(#94a3b8). UI/HTML/메일 버전 모두 동일한 팔레트를 사용합니다.

**파일:** `ai/hot_keywords.py`, `ai/keyword_classifier.py`, `ui/main_window.py`

---

### Phase 2-4: HTML 리포트 고도화 ✅ 완료 (v2.3)

v1의 기본 HTML 리포트에 AI 분석 결과와 HOT KEYWORDS를 통합하고, **메일 클라이언트 호환성**을 추가했습니다.

**리포트 구성:** 헤더(리포트 날짜·설정 요약), 통계 카드(수집→필터→병합→AI검증), HOT KEYWORDS Top N 가로 바 차트, 섹션별 기사 카드(제품/브랜드, 자사 핵심·관련, 경쟁사, 업계), 푸터(생성 시각·크레딧 v2.3).

**기사 카드 정보:** AI 요약(2~3문장), Tier 뱃지, 매체명·발행일, 매칭 키워드 칩, 유사 기사 접힘 영역.

**듀얼 복사 버튼 (v2.3 핵심 기능):**
- 📋 **화면 그대로 복사** — Gmail/네이버 메일용. 풀 디자인(`<style>` 태그 + flexbox)을 그대로 복사합니다.
- 📧 **메일용 단순 복사** — Outlook/Word용. table + 인라인 CSS + HTML4 `bgcolor` 속성 기반의 단순 버전을 복사합니다.

복사 버튼 자체는 `#report-content` 바깥의 `.toolbar`에 배치하여 복사 결과에 포함되지 않도록 했고, 메일용 단순 버전은 `#report-simple` 숨김 영역에 별도 렌더링됩니다.

**Outlook/Word 호환을 위한 핵심 처리:**
1. `<span style="background-color">` 대신 `<td bgcolor="#xxx" style="background-color:#xxx">` 사용
2. 빈 셀에 `&nbsp;` + `font-size:1px; line-height:1px; mso-line-height-rule:exactly;` 적용
3. 막대 그래프와 범례 색상 박스를 모두 table 셀 기반으로 재구성
4. JavaScript는 `execCommand('copy')` 우선, 실패 시 `Clipboard API` fallback

**파일:** `output/report_builder.py` (REPORT_TEMPLATE + SIMPLE_TEMPLATE 듀얼 템플릿), `ui/main_window.py` (`_on_export_click`, `_on_pipeline_complete`에서 hot_keywords 전달)

---

### Phase 2-5: UI 업데이트 ✅ 완료

기사 카드에 AI 요약 박스(연한 파란색 배경), 관련도 뱃지(🟢 핵심 / 🔵 관련 / 🟡 간접 / ⚫ Fallback), 감성 태그(↑/—/↓), 추출 엔티티 칩, 진행 로그의 "🤖 AI 분석 중... N/M건" 표시, 💬 간접 언급 기사 접힘/펼침 섹션, AI 요약 영역 wraplength 확대(820), 스플래시 로고 흰색 테두리 제거를 완료했습니다.

HOT KEYWORDS 섹션은 결과 화면 상단에 가로 바 차트 카드로 추가되어 있습니다.

**파일:** `ui/main_window.py`, `ui/theme.py`, `config/splash_logo.png`

---

### Phase 2-6: CLI/스케줄링 ⏸ 다음 작업

**CLI 모드:** `NewsClipper.exe --auto` 실행 시 UI 없이 백그라운드 클리핑 → HTML 자동 저장(`reports/`) → 자동 종료.

**Windows 작업 스케줄러 연동:** 설정 다이얼로그에 "스케줄 등록" 버튼 추가, 매일/매주/매월 + 실행 시각 지정, `schtasks` 명령으로 작업 등록.

**파일:** `main.py` (CLI 인수 처리), `ui/settings_search_dialog.py` (스케줄 등록 UI)

---

## 4. 파이프라인 흐름 (v2.3 — 실제 구현)

- Step 1: 키워드 조합 생성 
- Step 2: Naver API 뉴스 수집 
- Step 3: 매체 티어 필터링 
- Step 4: 날짜 범위 필터링 
- Step 5: TF-IDF 유사 기사 병합 (대표 기사 선정) 
- Step 6: ★ Gemini AI 통합 분석 (관련도 + 요약 + 엔티티 + 감성) 
- Step 7: ★ AI 관련도 기반 최종 필터링 (irrelevant 제외) 
- Step 8: ★ 섹션 분류 + 정렬 (AI category 우선, fallback 시 v1 키워드 매칭) 
- Step 9: ★ HOT KEYWORDS 집계 + AI 분류 (entities 가중 + 제목 명사 보조) 
- Step 10: 결과 반환 → UI / HTML 리포트

---

## 5. v2.2 → v2.3 버그 수정 및 안정화 (2026-05-04 ~ 05)

### v2.2.1 (2026-05-04)
- `ai/keyword_classifier.py`: 503 재시도 로직 추가 (`article_analyzer.py`와 동일 패턴, 3회 backoff)
- `utils/settings_io.py` 신규: `ensure_settings_file()` + `load_settings()` + `save_settings()` (deep merge)
- `utils/paths.py` 신규: PyInstaller 환경에서 리소스/유저 데이터 경로 분리
- `ui/settings_api_dialog.py`, `ui/settings_search_dialog.py`: 부분 dict + `save_settings()` 호출로 변경 → **다른 섹션(`ai`, `media`) 보존**
- `ui/main_window.py`: `_load_settings`에 `return self.settings` 누락 수정 → `AttributeError: 'NoneType' object has no attribute 'get'` 해결
- `ui/settings_search_dialog.py`: `include_tier3_var` → `tier3_coverage_var` 변수명 통일, 누락된 `_parse_csv` 정적 메서드 추가
- `pipeline.py`, `filters/media_filter.py`, `config/settings_template.yaml`, `ai/hot_keywords.py`: PyInstaller 리소스 경로 통합

**효과:** 이전에는 `settings.yaml`에서 `ai` 섹션이 사라지면서 `batch_size`가 하드코딩 기본값(5)으로 fallback되어 EXE에서 AI 분석이 4분 이상 걸리던 현상이, 정상적으로 `batch_size: 10`이 보존되면서 약 1분으로 단축되었습니다.

### v2.3 (2026-05-05)
- `output/report_builder.py` 전면 개편: REPORT_TEMPLATE(화면용) + SIMPLE_TEMPLATE(메일용) 듀얼 템플릿
- 📋 화면 그대로 복사 / 📧 메일용 단순 복사 두 버튼 추가
- HOT KEYWORDS 막대·범례를 `<table>` + `bgcolor` + `mso-line-height-rule:exactly`로 재구성하여 Outlook/Word 색상 표시 정상화
- `ui/main_window.py`: `_last_hot_keywords` 보관 + `build_html_report`에 전달, `save_report()` 추가

---

## 6. 리스크 및 대응 (실전 경험 반영)

| 리스크 | 대응 방안 | 현재 상태 |
|--------|----------|:---:|
| Gemini Free Tier 한도 초과 | Flash-Lite + batch_size 10 + fallback | ✅ |
| Gemini 응답 형식 불일치 | JSON 코드블록·후행 콤마·index 매칭 보정 | ✅ |
| API 응답 지연 / 503 | 타임아웃 30초, 3회 재시도(2·4·8초 backoff) | ✅ (v2.2.1) |
| 429 (일일 한도 초과) | 로컬 키워드 매칭 fallback + "⚠ 키워드매칭" 뱃지 | ✅ |
| Tkinter 종료 시 잔존 스레드 | `os._exit(0)` 강제 종료 | ✅ |
| 설정 다이얼로그가 다른 섹션 덮어쓰기 | `utils/settings_io.deep_merge` 도입 | ✅ (v2.2.1) |
| Outlook/Word 색상 미표시 | table + `bgcolor` 속성 + `mso-line-height-rule` | ✅ (v2.3) |
| PyInstaller 리소스 경로 오류 | `utils/paths.py`로 환경별 분기 | ✅ (v2.2.1) |
| 무료 정책 변경 | Paid Tier 전환 (월 $0.5 미만 예상) | 모니터링 |

---

## 7. 향후 작업 (v2.4 ~)

### 우선순위 1 — Phase 2-6 CLI/스케줄링
1. `main.py`에 `argparse` 도입, `--auto` 모드 구현
2. CLI 모드에서 자동으로 HTML 리포트를 `reports/`에 저장 후 종료
3. 설정 다이얼로그에 "스케줄 등록" 탭/버튼 추가
4. `schtasks /Create` 명령 래퍼 작성 (매일/매주/매월 + 시각 지정)
5. EXE 환경에서 작업 스케줄러 등록 동작 검증

### 우선순위 2 — 메일 자동 발송 (선택적 v2.5)
1. SMTP 설정 다이얼로그(Gmail / Naver / Outlook)
2. CLI 모드 완료 후 지정 수신자에게 HTML 메일 발송
3. 발송 로그 + 실패 재시도

### 우선순위 3 — 품질·UX 개선
1. HOT KEYWORDS 클릭 시 해당 기사로 점프(앵커 링크)
2. 리포트에 검색 키워드 / 검색 기간 표시 명확화
3. 다국어(EN) 모드 (UI 텍스트 + 프롬프트 분리)
4. 본문 200자 비교를 통한 중복 병합 정확도 향상 (Phase 2-1 잔여)

### 우선순위 4 — 운영·배포
1. GitHub Actions CI 도입 (PyInstaller 빌드 자동화)
2. 자동 업데이트 체크 (GitHub Releases API 조회)
3. 사용자 가이드 문서(`docs/USER_GUIDE.md`) 작성

---

## 8. 변경 이력

| 문서 버전 | 날짜 | 내용 |
|:---:|------|------|
| 1.0 | 2026-05-XX | 초안 작성 (전체 6 Phase 정의) |
| 1.1 | 2026-05-03 | Phase 2-2, 2-5 완료 반영. Flash-Lite + batch 10 표준화 |
| 1.2 | 2026-05-04 | Phase 2-3 (HOT KEYWORDS) 완료 |
| 1.3 | 2026-05-04 | v2.2.1 안정화 패치 (settings 보존, 503 재시도, 다이얼로그 버그 수정) |
| **1.4** | **2026-05-05** | **Phase 2-4 (HTML 리포트 고도화) 완료 — v2.3 릴리즈. 듀얼 템플릿(화면용/메일용) + Outlook/Word 호환** |

| 코드 버전 | 날짜 | 내용 |
|:---:|------|------|
| v1.0 | 2026-05 | 최초 릴리스 (Naver API + TF-IDF + CustomTkinter) |
| v2.0-alpha | 2026-05-03 | Phase 2-2, 2-5 완료 |
| v2.2 | 2026-05-04 | Phase 2-3 완료 + EXE 빌드 |
| v2.2.1 | 2026-05-04 | settings.yaml 보존, 503 재시도, 다이얼로그 버그 수정 |
| **v2.3** | **2026-05-05** | **HTML 리포트 고도화 + Outlook/Word 메일 호환 (현재)** |
| v2.4 | 예정 | Phase 2-6 CLI/스케줄링 |
