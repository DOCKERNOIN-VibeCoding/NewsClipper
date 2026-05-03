
\# NewsClipper v2.0 개발 정의서



\## 1. 개요



v1.0에서는 Naver News API + TF-IDF 기반 로컬 처리로 뉴스를 수집·분류했습니다.

v2.0에서는 \*\*Gemini AI를 파이프라인에 통합\*\*하여, 기사의 실제 관련도를 검증하고,

요약을 생성하고, 핵심 엔티티를 추출하여 최종 리포트의 품질을 대폭 향상시킵니다.



\---



\## 2. 사용 모델 및 API 비용



\*\*권장 모델: Gemini 2.5 Flash\*\* (비용 대비 성능 최적)



| 항목 | 내용 |

|------|------|

| 모델 | `gemini-2.5-flash` |

| Free Tier 입력 | 무료 |

| Free Tier 출력 | 무료 |

| Free Tier 일일 한도 | 약 500 RPD (추정, Google 정책에 따라 변동) |

| Paid Tier 입력 | $0.30 / 1M 토큰 |

| Paid Tier 출력 | $2.50 / 1M 토큰 |

| 1회 클리핑 예상 호출 | 30\~80회 (기사 수에 따라) |

| 월간 예상 비용 (Free) | $0 |

| 월간 예상 비용 (Paid, 매일 실행) | $0.5\~2.0 이하 |



\---



\## 3. 개발 기능 목록



\### Phase 2-1: 키워드 구조 개편 + 중복 병합 고도화



\*\*이미 v1에서 완료된 항목:\*\*

\- 제품/브랜드와 회사명 키워드 분리 입력 ✅

\- TF-IDF + 명사 겹침률 기반 유사 기사 병합 ✅

\- 5단계 감도 조절 ✅

\- 유사 기사 펼침/접힘 UI ✅



\*\*v2에서 추가 개선:\*\*

\- 병합 시 기사 본문 앞 200자도 비교 대상에 포함 (현재 제목만 비교)

\- 병합 클러스터 내 기사 수가 많을 경우 대표 기사 선정 로직 보강



\*\*파일:\*\* `dedup/deduplicator.py`, `collectors/body\_crawler.py` (신규)



\---



\### Phase 2-2: AI 통합 분석 (핵심 기능)



하나의 Gemini API 호출로 세 가지 분석을 동시에 수행합니다.



\*\*기능 A — AI 관련도 검증:\*\*



각 대표 기사가 설정된 키워드(제품/회사)에 실제로 관련된 기사인지 판별합니다.



| 관련도 등급 | 설명 | 처리 |

|------------|------|------|

| core (핵심) | 제품/기업이 기사의 주제 | 메인 표시 |

| relevant (관련) | 의미 있게 다뤄짐 | 메인 표시 |

| passing (간접언급) | 예시/비교로 잠깐 언급 | 접힌 섹션 |

| irrelevant (무관) | 키워드만 우연히 포함 | 제외 |



\*\*기능 B — 기사 요약:\*\*



대표 기사마다 2\~3문장 한국어 요약 생성. 핵심 수치, 인물명, 날짜를 포함하도록 프롬프트 설계.



\*\*기능 C — 엔티티 추출 + 키워드 태깅:\*\*



기사에서 언급된 기업명, 브랜드, 인물, 제품을 추출하고, 자사/경쟁사/업계 카테고리로 태깅.



\*\*통합 프롬프트 설계:\*\*



```

당신은 한국 뉴스 분석 전문가입니다.



\[사용자 설정]

\- 자사 제품/브랜드: {products}

\- 자사 회사명: {company}

\- 경쟁사: {competitors}

\- 산업군: {industries}



\[기사 정보]

\- 제목: {title}

\- 매체: {media\_name}

\- 본문: {description}



다음 JSON 형식으로 분석 결과를 반환하세요:

{

&#x20; "relevance\_type": "core|relevant|passing|irrelevant",

&#x20; "relevance\_reason": "판단 근거 1문장",

&#x20; "summary": "기사 핵심 내용 2\~3문장 요약",

&#x20; "category": "product|company|competitor|industry",

&#x20; "entities": \["기업명", "브랜드명", "인물명"],

&#x20; "sentiment": "positive|neutral|negative"

}

```



\*\*API 호출 최적화:\*\*

\- 대표 기사만 분석 (병합 후 30\~80건)

\- 배치 처리: 5건씩 묶어 호출 (프롬프트에 기사 5개 포함)

\- 실패 시 3회 재시도 (exponential backoff)

\- 일일 한도 초과 시 로컬 키워드 매칭으로 fallback



\*\*파일:\*\* `ai/article\_analyzer.py` (신규), `pipeline.py` (Step 6 추가)



\---



\### Phase 2-3: HOT KEYWORDS Top 10



전체 기사에서 가장 많이 언급된 브랜드/제품/기업명을 집계하여 Top 10으로 시각화합니다.



\*\*데이터 소스:\*\*

\- Phase 2-2에서 추출한 entities (우선)

\- 전체 기사 제목의 명사 빈도 (보조)



\*\*제외 대상:\*\* 검색 키워드 자체, 일반 명사 (경제, 시장, 정부, 사회 등)



\*\*시각화:\*\*

\- 자사 관련: 파란색 바

\- 경쟁사 관련: 주황색 바

\- 기타: 회색 바



\*\*파일:\*\* `output/hot\_keywords.py` (신규), `ui/main\_window.py` (하단 차트 추가)



\---



\### Phase 2-4: HTML 리포트 고도화



v1의 기본 HTML 리포트에 AI 분석 결과를 통합합니다.



\*\*리포트 구성:\*\*



| 순서 | 섹션 | 내용 |

|------|------|------|

| 1 | 헤더 | 리포트 날짜, 설정 요약 |

| 2 | 통계 카드 | 수집→필터→병합→AI검증 각 단계 수치 |

| 3 | HOT KEYWORDS | Top 10 가로 바 차트 |

| 4 | 🎯 핵심 기사 | AI 관련도 core, 요약 포함 |

| 5 | 📋 관련 기사 | AI 관련도 relevant, 요약 포함 |

| 6 | ⚔️ 경쟁사 기사 | 경쟁사 동향, 요약 포함 |

| 7 | 💬 간접 언급 | AI 관련도 passing, 접힌 상태 |

| 8 | 푸터 | 생성 시각, 크래딧 |



\*\*각 기사 카드에 추가되는 정보:\*\*

\- AI 요약 (2\~3문장)

\- 관련도 뱃지 (core/relevant/passing)

\- 감성 태그 (긍정/중립/부정)

\- 추출된 엔티티 태그



\*\*파일:\*\* `output/report\_builder.py` (전면 개편), `output/templates/report\_template.html` (신규)



\---



\### Phase 2-5: UI 업데이트



메인 윈도우에 AI 분석 결과를 반영합니다.



\*\*변경 사항:\*\*

\- 기사 카드에 AI 요약 표시 영역 추가

\- 관련도 뱃지 (🟢 핵심 / 🔵 관련 / 🟡 간접 / 🔴 무관)

\- 감성 태그 표시 (긍정 ↑ / 중립 — / 부정 ↓)

\- 결과 하단에 HOT KEYWORDS Top 10 섹션 추가

\- 진행 로그에 AI 분석 단계 표시 ("🤖 AI 분석 중... 15/47건")

\- "간접 언급" 섹션 접힌 상태로 추가



\*\*파일:\*\* `ui/main\_window.py` (기사 카드 + 결과 화면 수정)



\---



\### Phase 2-6: 스케줄링 (자동 실행)



\*\*CLI 모드:\*\*

\- `NewsClipper.exe --auto` 실행 시 UI 없이 백그라운드 클리핑

\- 결과를 HTML로 자동 저장 (`reports/` 폴더)

\- 완료 후 자동 종료



\*\*Windows 작업 스케줄러 연동:\*\*

\- 설정 다이얼로그에 "스케줄 등록" 버튼 추가

\- 매일/매주/매월 선택 + 실행 시각 지정

\- `schtasks` 명령으로 Windows 작업 스케줄러에 등록



\*\*파일:\*\* `main.py` (CLI 인수 처리), `ui/settings\_search\_dialog.py` (스케줄 등록 UI)



\---



\## 4. 파이프라인 흐름 (v2.0)



```

Step 1: 키워드 조합 생성

Step 2: Naver API 뉴스 수집

Step 3: 매체 티어 필터링

Step 4: 날짜 범위 필터링

Step 5: TF-IDF 유사 기사 병합 (대표 기사 선정)

Step 6: ★ Gemini AI 통합 분석 (관련도 + 요약 + 엔티티)  ← 신규

Step 7: ★ AI 관련도 기반 최종 필터링 (irrelevant 제외) ← 신규

Step 8: ★ HOT KEYWORDS 집계                            ← 신규

Step 9: 섹션 분류 + 정렬

Step 10: 결과 반환

```



\---



\## 5. 개발 순서 및 예상 일정



| 순서 | 기능 | 난이도 | 의존성 |

|:---:|------|:---:|------|

| 1 | Phase 2-2: AI 통합 분석 | ★★★ | 없음 (핵심 기능) |

| 2 | Phase 2-5: UI 업데이트 | ★★☆ | Phase 2-2 완료 후 |

| 3 | Phase 2-3: HOT KEYWORDS | ★★☆ | Phase 2-2의 entities 필요 |

| 4 | Phase 2-4: HTML 리포트 고도화 | ★★☆ | Phase 2-2, 2-3 완료 후 |

| 5 | Phase 2-1: 중복 병합 고도화 | ★☆☆ | 독립 가능 |

| 6 | Phase 2-6: 스케줄링 | ★★☆ | 모든 기능 완료 후 |



\---



\## 6. 신규/수정 파일 목록



| 파일 | 상태 | 용도 |

|------|:---:|------|

| `ai/article\_analyzer.py` | 신규 | Gemini API 호출, 프롬프트 관리, 응답 파싱 |

| `collectors/body\_crawler.py` | 신규 | 기사 본문 앞 200자 크롤링 |

| `output/hot\_keywords.py` | 신규 | HOT KEYWORDS 집계 |

| `output/templates/report\_template.html` | 신규 | Jinja2 HTML 리포트 템플릿 |

| `pipeline.py` | 수정 | Step 6\~8 추가 |

| `ui/main\_window.py` | 수정 | AI 요약, 관련도, HOT KEYWORDS UI |

| `output/report\_builder.py` | 수정 | AI 분석 결과 포함 리포트 생성 |

| `dedup/deduplicator.py` | 수정 | 본문 비교 추가 |

| `main.py` | 수정 | `--auto` CLI 옵션 |

| `ui/settings\_search\_dialog.py` | 수정 | 스케줄 등록 버튼 |

| `config/settings\_template.yaml` | 수정 | AI 관련 설정 항목 추가 |

| `requirements.txt` | 수정 | google-genai 추가 확인 |



\---



\## 7. 리스크 및 대응



| 리스크 | 대응 방안 |

|--------|----------|

| Gemini Free Tier 한도 초과 | 로컬 키워드 매칭으로 fallback, 배치 처리로 호출 수 최소화 |

| Gemini 응답 형식 불일치 | JSON 파싱 실패 시 재시도, 3회 실패 시 해당 기사 skip |

| API 응답 지연 | 타임아웃 30초 설정, 진행률 UI에 현재 상태 표시 |

| Free Tier 정책 변경 | Gemini 2.5 Flash-Lite (더 저렴) 로 대체 가능 |



\---



\## 8. 버전 이력



| 버전 | 날짜 | 내용 |

|------|------|------|

| v1.0 | 2026-05 | 최초 릴리스 (Naver API + TF-IDF + CustomTkinter) |

| v2.0 | 예정 | Gemini AI 통합, HOT KEYWORDS, 리포트 고도화, 스케줄링 |

```
