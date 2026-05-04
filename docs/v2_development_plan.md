# NewsClipper v2.0 개발 정의서

> **문서 버전**: 1.1 (2026-05-03 갱신)
> **현재 진행 단계**: Phase 2-2, 2-5 완료 → Phase 2-3 진행 예정

---

## 1. 개요

v1.0에서는 Naver News API + TF-IDF 기반 로컬 처리로 뉴스를 수집·분류했습니다.
v2.0에서는 **Gemini AI를 파이프라인에 통합**하여, 기사의 실제 관련도를 검증하고,
요약을 생성하고, 핵심 엔티티를 추출하여 최종 리포트의 품질을 대폭 향상시킵니다.

### 진행 상태 요약

| Phase | 내용 | 상태 |
|:---:|------|:---:|
| 2-1 | 중복 병합 고도화 | 🔵 v1에서 대부분 완료, 본문 비교는 보류 |
| 2-2 | AI 통합 분석 | ✅ **완료** (2026-05-03) |
| 2-3 | HOT KEYWORDS Top 10 | ⏳ **다음 작업** |
| 2-4 | HTML 리포트 고도화 | ⏸ 대기 |
| 2-5 | UI 업데이트 | ✅ **완료** (2026-05-03, 2-2와 동시 진행) |
| 2-6 | CLI/스케줄링 | ⏸ 대기 |

---

## 2. 사용 모델 및 API 비용

**초기 권장 모델: Gemini 2.5 Flash** → **실전 권장 모델: Gemini 2.5 Flash-Lite**

실제 운영 결과 Free Tier 일일 한도(약 500 RPD)가 1~2회 클리핑(약 50건 × 배치 5건 = 약 10회 호출/회)으로도 빠르게 소진되는 현상이 확인되어, **batch_size를 10으로 늘리고 Flash-Lite 모델로 전환**하는 것을 표준 설정으로 정합니다.

| 항목 | Gemini 2.5 Flash | Gemini 2.5 Flash-Lite |
|------|:---:|:---:|
| Free Tier 일일 한도 (RPD) | 약 500 | 약 1,000 |
| Paid 입력 단가 ($/1M tok) | 0.30 | 0.10 |
| Paid 출력 단가 ($/1M tok) | 2.50 | 0.40 |
| 응답 품질 | 매우 우수 | 우수 (실전 테스트로 충분) |
| **권장 용도** | 정밀 분석이 필요한 경우 | **일상 클리핑 (기본값)** |

1회 클리핑 예상 호출: 기사 50건 ÷ batch_size 10 = **5회 호출**
월간 예상 비용 (Free Tier, 매일 실행): **$0**
월간 예상 비용 (Paid Tier 전환 시): **$0.5 미만**

---

## 3. 개발 기능 목록

### Phase 2-1: 키워드 구조 개편 + 중복 병합 고도화

**v1에서 완료된 항목:**
- 제품/브랜드와 회사명 키워드 분리 입력 ✅
- TF-IDF + 명사 겹침률 기반 유사 기사 병합 ✅
- 5단계 감도 조절 ✅
- 유사 기사 펼침/접힘 UI ✅

**v2에서 추가 개선 (현재 보류):**
- 병합 시 기사 본문 앞 200자 비교 추가 → Naver API description으로도 충분히 동작 중이며, 본문 크롤링은 차단 위험과 속도 부담이 있어 **Phase 2-4에서 재검토**
- 병합 클러스터 내 대표 기사 선정 로직은 현재 "최상위 티어 우선" 으로 충분히 동작

**파일:** `dedup/deduplicator.py`, `collectors/body_crawler.py` (보류)

---

### Phase 2-2: AI 통합 분석 ✅ 완료

하나의 Gemini API 호출로 관련도 검증·요약·엔티티 추출을 동시에 수행합니다.

**구현 결과:**

기능 A — AI 관련도 검증: 4단계 등급(core / relevant / passing / irrelevant)으로 분류하여, irrelevant는 제외하고 passing은 접힘 섹션에 배치하도록 구현했습니다.

기능 B — 기사 요약: 한국어 2~3문장 요약을 생성하며, 실제 검증 결과 "점유율 28%", "전년 대비 40% 증가" 같은 핵심 수치를 정확히 포함시키는 품질을 확인했습니다.

기능 C — 엔티티 + 감성 추출: 기업명·브랜드·인물을 배열로 반환하고, 감성을 positive / neutral / negative로 태깅합니다. 실전 테스트에서 "농심 · 삼양" 등 경쟁사 엔티티를 정확히 추출하는 것을 확인했습니다.

**API 호출 최적화 (실제 적용값):**
- 대표 기사만 분석 (병합 후 30~80건)
- **배치 처리: 기본 5건, Flash-Lite 사용 시 10건 권장**
- 실패 시 최대 3회 재시도 (exponential backoff)
- 일일 한도 초과·네트워크 오류 시 **로컬 키워드 매칭으로 자동 fallback**
- 응답 파싱: 코드블록 래핑·후행 콤마·index 키 매칭까지 견고하게 처리

**파이프라인 통합 결과:**
원래 계획은 Step 6에 단일 단계로 추가하는 것이었으나, 실제 구현에서는 **AI 분석(Step 6)과 AI 기반 필터링(Step 7)을 분리**하여 책임을 명확히 했습니다. 이로 인해 파이프라인이 8단계로 확장되었습니다(섹션 4 참조).

**추가 구현 사항 (원 계획에 없던 부분):**
- `logs/newsclipper_YYYYMMDD_HHMMSS.log` 자동 생성 (디버깅용)
- Tkinter 종료 시 백그라운드 스레드 안전 종료(`os._exit(0)`)
- 통계 카드에 `ai_succeeded` / `ai_fallback` 분리 표시

**파일:**
- 신규: `ai/article_analyzer.py`, `tests/test_ai_analyzer.py`
- 수정: `pipeline.py`, `main.py`, `config/settings_template.yaml`

---

### Phase 2-3: HOT KEYWORDS Top 10 ⏳ 다음 작업

전체 기사에서 가장 많이 언급된 브랜드/제품/기업명을 집계하여 Top 10으로 시각화합니다.

**데이터 소스 (확정 필요):**
1. Phase 2-2에서 추출된 `entities` 배열 (1차)
2. 기사 제목의 명사 빈도 (보조)
3. 동의어 처리: "CJ제일제당" / "CJ" / "제일제당" → 정규화 사전 필요

**제외 대상:** 검색 키워드 자체, 일반 명사(경제·시장·정부·사회·뉴스 등 stopword 사전)

**시각화 (UI/HTML 공통):**
- 자사 관련: 파란색 바 (`COBALT`)
- 경쟁사 관련: 주황색 바 (`ACCENT_ORANGE`)
- 기타: 회색 바 (`TEXT_SECONDARY`)
- 차트 방식: HTML/CSS 가로 바 (외부 라이브러리 의존성 회피)

**파일:** `ai/hot_keywords.py` (신규, `output/`에서 `ai/`로 위치 변경 — AI 결과 가공이므로), `ui/main_window.py` (결과 화면 상단에 카드 추가)

---

### Phase 2-4: HTML 리포트 고도화 ⏸ 대기

v1의 기본 HTML 리포트에 AI 분석 결과를 통합합니다.

**리포트 구성:**

| 순서 | 섹션 | 내용 |
|:---:|------|------|
| 1 | 헤더 | 리포트 날짜, 설정 요약 |
| 2 | 통계 카드 | 수집→필터→병합→AI검증 각 단계 수치 |
| 3 | HOT KEYWORDS | Top 10 가로 바 차트 |
| 4 | 🎯 핵심 기사 (core) | AI 요약·관련도·감성·엔티티 포함 |
| 5 | 📋 관련 기사 (relevant) | AI 요약 포함 |
| 6 | ⚔️ 경쟁사 기사 | 경쟁사 동향, AI 요약 포함 |
| 7 | 💬 간접 언급 (passing) | 접힌 상태 |
| 8 | 푸터 | 생성 시각, 크레딧 |

**기사 카드 정보:** AI 요약(2~3문장), 관련도 뱃지, 감성 태그(↑/—/↓), 추출 엔티티 칩

**파일:** `output/report_builder.py` (전면 개편), `output/templates/report_template.html` (신규)

---

### Phase 2-5: UI 업데이트 ✅ 완료

**구현된 변경 사항:**
- 기사 카드에 AI 요약 박스 추가 (연한 파란색 배경)
- 관련도 뱃지: 🟢 핵심 / 🔵 관련 / 🟡 간접 / ⚫ Fallback
- 감성 태그: 긍정 ↑ / 중립 — / 부정 ↓
- 추출 엔티티 칩 표시
- 진행 로그에 "🤖 AI 분석 중... N/M건" 단계 표시
- 💬 간접 언급 기사 접힘/펼침 섹션
- AI 요약 영역 wraplength 확대(820), 좌측 정렬, 통계 카드 컴팩트화
- 스플래시 로고 흰색 테두리 제거 (이미지 자체를 잘라낸 방식으로 해결)

**HOT KEYWORDS 섹션 (Phase 2-3에서 추가 예정):**
- 결과 화면 상단에 가로 바 차트 카드

**파일:** `ui/main_window.py`, `ui/theme.py`, `config/splash_logo.png`

---

### Phase 2-6: 스케줄링 ⏸ 대기

**CLI 모드:**
- `NewsClipper.exe --auto` 실행 시 UI 없이 백그라운드 클리핑
- 결과를 HTML로 자동 저장 (`reports/` 폴더)
- 완료 후 자동 종료

**Windows 작업 스케줄러 연동:**
- 설정 다이얼로그에 "스케줄 등록" 버튼 추가
- 매일/매주/매월 선택 + 실행 시각 지정
- `schtasks` 명령으로 Windows 작업 스케줄러에 등록

**파일:** `main.py` (CLI 인수 처리), `ui/settings_search_dialog.py` (스케줄 등록 UI)

---

## 4. 파이프라인 흐름 (v2.0 — 실제 구현)

```
Step 1: 키워드 조합 생성
Step 2: Naver API 뉴스 수집
Step 3: 매체 티어 필터링
Step 4: 날짜 범위 필터링
Step 5: TF-IDF 유사 기사 병합 (대표 기사 선정)
Step 6: ★ Gemini AI 통합 분석 (관련도 + 요약 + 엔티티 + 감성)  ← v2 신규
Step 7: ★ AI 관련도 기반 최종 필터링 (irrelevant 제외)         ← v2 신규
Step 8: ★ 섹션 분류 + 정렬 (AI category 우선, fallback 시 v1 키워드 매칭)
Step 9: 결과 반환 (HOT KEYWORDS는 Phase 2-3에서 통합 예정)
```

원 계획의 10단계에서 8단계로 정리되었습니다. HOT KEYWORDS 집계는 Phase 2-3 진행 시 Step 8과 Step 9 사이에 삽입될 예정입니다.

---

## 5. 개발 순서 및 진행 현황

| 순서 | 기능 | 난이도 | 의존성 | 상태 |
|:---:|------|:---:|------|:---:|
| 1 | Phase 2-2: AI 통합 분석 | ★★★ | 없음 | ✅ |
| 2 | Phase 2-5: UI 업데이트 | ★★☆ | 2-2 | ✅ |
| 3 | **Phase 2-3: HOT KEYWORDS** | ★★☆ | 2-2 entities | ⏳ **현재** |
| 4 | Phase 2-4: HTML 리포트 고도화 | ★★☆ | 2-2, 2-3 | ⏸ |
| 5 | Phase 2-1: 본문 비교 추가 | ★☆☆ | 독립 | 🔵 보류 |
| 6 | Phase 2-6: 스케줄링 | ★★☆ | 모든 기능 완료 후 | ⏸ |

---

## 6. 신규/수정 파일 목록 (현재 기준)

### Phase 2-2 / 2-5에서 실제로 변경된 파일

| 파일 | 상태 | 용도 |
|------|:---:|------|
| `ai/article_analyzer.py` | ✅ 신규 | Gemini API 호출, 프롬프트, 배치 처리, fallback |
| `tests/test_ai_analyzer.py` | ✅ 신규 | fallback / JSON 파싱 / 실제 API 호출 검증 |
| `pipeline.py` | ✅ 수정 | Step 6~8 추가, AI 통계 추적 |
| `main.py` | ✅ 수정 | logs/ 디렉토리 자동 생성, 상세 로깅 |
| `ui/main_window.py` | ✅ 수정 | AI 요약·관련도·감성·접힘 섹션 |
| `ui/theme.py` | ✅ 수정 | AI UI 색상 상수 추가 |
| `config/settings_template.yaml` | ✅ 수정 | `ai` 블록, `schedule` 기본값 weekly/7일 |
| `config/splash_logo.png` | ✅ 수정 | 흰색 테두리 제거 |
| `requirements.txt` | ✅ 확인 | google-genai, jinja2 포함 확인 |
| `.gitignore` | ✅ 수정 | logs/, *.default, *.bak 제외 |

### 향후 Phase에서 작업할 파일

| 파일 | 상태 | Phase |
|------|:---:|:---:|
| `ai/hot_keywords.py` | 예정 | 2-3 |
| `output/report_builder.py` | 예정 (전면 개편) | 2-4 |
| `output/templates/report_template.html` | 예정 (신규) | 2-4 |
| `collectors/body_crawler.py` | 보류 | 2-1 (재검토) |
| `dedup/deduplicator.py` | 보류 | 2-1 (재검토) |
| `ui/settings_search_dialog.py` | 예정 | 2-6 |

---

## 7. 리스크 및 대응 (실전 경험 반영)

| 리스크 | 대응 방안 | 현재 상태 |
|--------|----------|:---:|
| **Gemini Free Tier 한도 초과** | Flash-Lite 모델 + batch_size 10 + fallback | ✅ 완화책 적용 |
| Gemini 응답 형식 불일치 | JSON 코드블록 래핑·후행 콤마 보정·index 매칭 | ✅ 견고하게 처리 |
| API 응답 지연 | 타임아웃 30초, 진행률 UI 표시 | ✅ 적용 |
| Tkinter 종료 시 백그라운드 잔존 | `os._exit(0)`로 강제 종료 | ✅ 적용 |
| 배치 응답 길이 불일치 | None 처리 후 해당 인덱스만 fallback | ✅ 적용 |
| 무료 정책 변경 | Paid Tier 전환 (월 $0.5 미만 예상) | 모니터링 |

---

## 8. 변경 이력

| 버전 | 날짜 | 내용 |
|:---:|------|------|
| 1.0 | 2026-05-XX | 초안 작성 (전체 6 Phase 정의) |
| **1.1** | **2026-05-03** | **Phase 2-2, 2-5 완료 반영. Free Tier 한도 이슈 발견 후 Flash-Lite + batch 10 권장으로 변경. 파이프라인 8단계로 정리. HOT KEYWORDS를 `ai/` 패키지로 위치 변경.** |

| 코드 버전 | 날짜 | 내용 |
|:---:|------|------|
| v1.0 | 2026-05 | 최초 릴리스 (Naver API + TF-IDF + CustomTkinter) |
| v2.0-alpha | 2026-05-03 | Phase 2-2, 2-5 완료 (develop/v2.0 브랜치) |
| v2.0 | 예정 | 전체 Phase 완료 후 main 머지 |
