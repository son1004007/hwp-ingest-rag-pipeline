# HWP Ingest RAG Pipeline

한컴오피스 한글(HWP/HWPX) 문서를 자동으로 처리하여  
LLM/RAG에서 활용 가능한 **구조화된 문서 블록**으로 변환하는 파이프라인입니다.

## 핵심 목표
- HWP → HWPX 자동 변환 (Windows + 한글 COM)
- HWPX(XML) 직접 파싱 (네임스페이스 독립)
- 문단 / 표 단위로 구조화
- LangChain `Document` 형태로 변환
- 향후 RAG / DB / LLM 연계를 위한 표준 Ingest 단계 제공

---

## 전체 처리 흐름

HWP
└─(Hancom COM Automation)
→ HWPX
└─(ZIP + XML Parsing)
→ Section / Paragraph / Table
→ JSON-like Structure
→ LangChain Document

## 프로젝트 구조
.
├── hwp_to_hwpx.py # HWP → HWPX 변환 (한글 COM)
├── hwpx_to_json.py # HWPX(XML) 파싱
├── json_to_langchain_docs.py # JSON → LangChain Document
├── hwp_ingest_pipeline.py # End-to-End Ingest 파이프라인
├── preview_docs.py # 파싱 결과 미리보기
├── .gitignore
└── README.md

---

## 현재 구현 상태

- [x] HWP → HWPX 자동 변환
- [x] HWPX XML 직접 파싱
- [x] 문단 / 표 블록 추출
- [x] LangChain Document 생성
- [ ] PostgreSQL 원문 블록 저장
- [ ] 벡터DB 연동
- [ ] RAG 질의응답
- [ ] LangGraph 기반 워크플로우

---

## 기술 스택

- Python 3.10
- Windows + Hancom Office
- XML / ZIP Parsing
- LangChain
- (예정) PostgreSQL, pgvector, LangGraph, LLM

---

## 활용 시나리오

- 공공 문서(HWP) RAG 시스템
- 인터페이스 설계서 / 동의서 자동 분석
- 문서 기반 SQL / 보고서 생성
- 내부 규정 질의응답 챗봇

---

## 주의사항

- 본 저장소에는 실제 HWP/HWPX 문서 파일을 포함하지 않습니다.
- Windows 환경에서 한컴오피스 한글이 설치되어 있어야 합니다.


---
## 한글(HWP) 자동화 보안 팝업(“접근 허용”) 최소화

본 프로젝트는 pyhwpx / COM Automation을 사용해 한글(HWP)을 자동으로 열고 HWPX로 변환합니다.
한글 보안 정책에 따라 외부 프로그램이 파일에 접근할 때 “접근 허용(Y)” 팝업이 표시될 수 있습니다.

### 해결 개요
한글의 파일 경로 검사 모듈(FilePathCheckerModule)을 레지스트리에 등록하여,
자동화 실행 시 보안 팝업이 반복적으로 뜨는 현상을 완화합니다.

### 레지스트리 수동 설정(Windows)
`regedit` 실행 후 아래 경로 중 존재하는 위치에 문자열(REG_SZ) 값을 추가합니다.

- (경로1) `HKEY_CURRENT_USER\Software\HNC\HwpCtrl\Modules`
- (경로2) `HKEY_CURRENT_USER\Software\HNC\HwpAutomation\Modules`

값 추가:
- 이름(Name): `FilePathCheck`  (임의의 이름도 가능하나 예제와 동일하게 사용)
- 데이터(Value): `FilePathCheckerModule.dll`의 전체 경로

예시:
- `C:\Users\son10\venv\Lib\site-packages\pyhwpx\FilePathCheckerModule.dll`

설정 후에는 한글(HWP) 프로세스를 완전히 종료한 뒤 다시 실행해야 적용됩니다.

### 자동 설정 스크립트(권장: 1회 실행)
레지스트리 설정을 자동으로 적용하려면 아래 스크립트를 1회 실행합니다.

```bat
python scripts\setup_hwp_registry.py "C:\Users\son10\venv\Lib\site-packages\pyhwpx\FilePathCheckerModule.dll"
주의: 본 설정은 현재 사용자(HKCU) 계정에만 적용됩니다.
```
	
---

## 3) “자동으로 레지스트리 수정”이 부적절할 수 있는 이유(짧게)

- 회사/공공 환경에서 레지스트리 변경이 정책 위반일 수 있음
- 실행할 때마다 변경하면 “애플리케이션이 시스템 설정을 몰래 바꾼다”로 보일 수 있음
- 그래서 **setup 스크립트로 분리**하는 게 포트폴리오 관점에서도 깔끔합니다

---

## 4) 다음 단계 제안

레지스트리 세팅까지 안정화되면, 다음은 한 번에 가치가 확 올라갑니다.

1) `HWP_PATH` 단일 파일 → **폴더 전체 배치 적재**
2) `doc_blocks`에 `hash(content)` 같은 컬럼 추가해서 변경 감지/중복 제어 강화
3) 이후 `pgvector` 붙여서 RAG 질의까지

원하시면, “폴더 배치 적재 + 파일별 doc_id 규칙 + 실행 로그 남기기”까지 바로 이어서 정리해드리겠습니다.
::contentReference[oaicite:0]{index=0}

---

## Full Text Search(FTS) 적용 (PostgreSQL)

문서 원문 블록이 PostgreSQL에 적재된 이후,  
LLM/RAG 이전 단계로 **키워드 기반 검색(Full Text Search)** 을 먼저 적용합니다.

### 적용 목적
- LLM 없이도 문서 내용 검색 가능
- RAG에서 사용할 후보 문서(top-k) 선별 단계로 활용
- pgvector 도입 전 단계의 경량 검색 인프라 구성

### 적용 SQL

```sql
-- 1. tsvector 컬럼 추가
ALTER TABLE public.doc_blocks
ADD COLUMN IF NOT EXISTS tsv tsvector;

-- 2. 기존 데이터에 대해 tsvector 생성
UPDATE public.doc_blocks
SET tsv = to_tsvector('simple', coalesce(content,''));

-- 3. 검색 성능을 위한 GIN 인덱스 생성
CREATE INDEX IF NOT EXISTS ix_doc_blocks_tsv
ON public.doc_blocks USING GIN (tsv);

-- 검색 예시
SELECT doc_id, block_id, LEFT(content, 200) AS preview
FROM public.doc_blocks
WHERE tsv @@ plainto_tsquery('simple', '운행제한')
ORDER BY id
LIMIT 20;
```

이를 통해 문서 전체를 LLM에 전달하지 않고도
질의와 관련된 문단 블록만 선별할 수 있습니다.

## FTS 기반 RAG (최소 구현, CLI)

PostgreSQL Full Text Search(FTS)로 관련 문서 블록(top-k)을 먼저 선별한 뒤,
선별된 블록을 LLM 컨텍스트로 전달하여 답변을 생성합니다.

### 구성
- `rag_retriever.py`: PostgreSQL FTS(tsv) 기반 블록 검색
- `rag_answer.py`: LangChain(ChatOpenAI)로 컨텍스트 기반 답변 생성
- `rag_cli.py`: CLI 실행 진입점

### 환경변수(.env)
```env
OPENAI_API_KEY=...
PG_HOST=localhost
PG_PORT=5432
PG_DB=postgres
PG_USER=postgres
PG_PASS=postgres
PG_TABLE=doc_blocks
```


## RAG 단계별 구현 전략

본 프로젝트는 RAG를 한 번에 완성하지 않고,
아래와 같은 단계적 접근으로 구현하였다.

1. 문서 파싱 및 블록 구조화 (HWP/HWPX)
2. PostgreSQL 저장 및 정형 검색 기반 구축
3. 한국어 대응 Retriever (FTS + Keyword Fallback)
4. (예정) LLM 연동 기반 질의응답
5. (확장) Table 전용 라우팅 및 Vector Search

이를 통해 LLM 의존도를 최소화하면서도
점진적으로 고도화 가능한 구조를 지향한다.

## 진행 방향

1) rag-llm 브랜치 만들어서 LLM 붙이기 (최소 비용/안전)
2) LangGraph로 질문 유형 분기부터 만들기
3) 검색 품질 튜닝(키워드 추출 고도화)


## LLM 연동 (rag-llm 브랜치)

본 프로젝트는 검색 파이프라인(search-only)과
LLM 연동(RAG)을 명확히 분리하여 구현하였다.

### 설계 원칙
- 검색 결과가 없으면 LLM을 호출하지 않음
- 문서 근거 기반 답변만 허용
- API Key 미설정/Quota 초과 시 안전 종료

### 실행 예시

```bash
# 검색 결과만 확인 (LLM 미사용)
python rag_cli.py "질문 문장" --dry-run

# LLM 기반 답변 생성
python rag_cli.py "질문 문장"
```
이를 통해 LLM 의존도를 최소화하면서도
필요한 시점에만 생성 모델을 활용하는 구조를 지향한다.
---
### LLM 모델 선택 기준

본 프로젝트는 RAG 구조 특성상
- 검색 정확도가 응답 품질의 대부분을 차지하고
- LLM은 요약 및 근거 정리 역할을 수행한다.

이에 따라 기본 모델로 `gpt-5.2-mini`를 사용하며,
CLI 옵션을 통해 모델을 유연하게 교체할 수 있도록 설계하였다.

```bash
python rag_cli.py "질문 문장" --model gpt-5.2-mini
```
---
## 로컬 무료 LLM 실행 (Windows)

본 프로젝트는 OpenAI 대신 무료 로컬 LLM을 사용할 수 있도록 지원합니다.

### Ollama 설치 (Windows)
1. https://ollama.com/download 에서 다운로드 후 설치
2. CMD에서 모델 다운로드: ollama pull llama2-7b
3. 질의 실행: ollama chat llama2-7b

### Python에서 이용
```python
from ollama import Ollama
client = Ollama()
res = client.chat(model="llama2-7b", prompt="질문 문장")
print(res)
```

## LLM 선택 전략

### 1) Local / 무료 / PoC
- GPT4All (권장)
- 장점: 설치 간단, GUI 제공, 서버 불필요

### 2) Local / 서버형
- Ollama
- 장점: API 서버, 확장성
- 단점: GPU/러너 이슈 발생 가능

### 3) 상용 / 품질 최우선
- OpenAI GPT-4.x / GPT-5.x



