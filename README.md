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