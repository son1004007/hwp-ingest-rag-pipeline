# rag_answer_gpt4all.py
import os
from gpt4all import GPT4All

# 모델 파일(.gguf)은 GPT4All 앱에서 다운로드한 것을 사용해도 되고,
# GPT4All이 관리하는 기본 모델 디렉토리에 있는 것을 그대로 써도 됩니다.
#
# 기본 검색 경로:
# - Windows: C:\Users\<USER>\AppData\Local\nomic.ai\GPT4All\
#
# 아래 환경변수로 모델명을 지정하면 편합니다.
#   GPT4ALL_MODEL=Meta-Llama-3-8B-Instruct.Q4_0.gguf  (예시)
DEFAULT_MODEL = os.getenv("GPT4ALL_MODEL", "").strip()

# 성능/메모리 튜닝(필요 시 조정)
DEFAULT_MAX_TOKENS = int(os.getenv("GPT4ALL_MAX_TOKENS", "512"))
DEFAULT_TEMP = float(os.getenv("GPT4ALL_TEMP", "0.2"))

_system_prompt = """너는 문서 기반 QA 도우미다.
- 반드시 제공된 [문서] 내용에 근거해서만 답변하라.
- 문서에 없는 내용은 '문서에 명시되어 있지 않습니다.' 라고 답하라.
- 답변은 한국어로, 핵심만 간결하게 작성하라.
"""

def _build_prompt(question: str, context: str) -> str:
    return f"""{_system_prompt}

[문서]
{context}

[질문]
{question}

[답변]
"""

def answer_with_context(question: str, context: str, model: str = "") -> str:
    """
    GPT4All 로컬 모델로 답변 생성.
    - model 인자가 비어있으면 환경변수 GPT4ALL_MODEL 사용
    - rag_cli.py에서 --model 옵션으로 모델명을 넘기면 그것이 우선
    """
    if not context or not context.strip():
        return "[LLM] context is empty. answer skipped."

    model_name = (model or DEFAULT_MODEL).strip()
    if not model_name:
        return (
            "[LLM] GPT4All model not specified.\n"
            "Set GPT4ALL_MODEL env var or pass --model <model.gguf>\n"
            "Example: set GPT4ALL_MODEL=Meta-Llama-3-8B-Instruct.Q4_0.gguf"
        )

    prompt = _build_prompt(question, context)

    try:
        # allow_download=False: 자동 다운로드가 원치 않는 경우를 방지
        llm = GPT4All(model_name, allow_download=False)
        with llm.chat_session():
            out = llm.generate(
                prompt,
                max_tokens=DEFAULT_MAX_TOKENS,
                temp=DEFAULT_TEMP,
            )
        return out.strip()
    except Exception as e:
        return f"[LLM ERROR] {e}"
