# rag_answer_gpt4all.py
import os
from gpt4all import GPT4All
from pathlib import Path

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

_system_prompt = """당신은 '문서 기반 질의응답' 도우미입니다.

규칙:
- 반드시 아래 [문서]에 포함된 내용만 근거로 답변하세요.
- 문서에 없는 정보는 '문서에 명시되어 있지 않습니다.' 라고 답하세요.
- 답변은 반드시 한국어로만 작성하세요. (영어 사용 금지)
- 3~6문장 이내로 간결하게 작성하세요.
- 가능하면 근거가 된 문서 조각의 doc_id, block_id를 1~3개 같이 적어주세요.
"""
from gpt4all import GPT4All
from pathlib import Path
import os

def _resolve_model_path(model_name: str) -> tuple[str, str]:
    # 1) 사용자가 절대경로를 줬으면 그대로 사용
    p = Path(model_name)
    if p.exists() and p.is_file():
        return p.name, str(p.parent)

    # 2) 환경변수로 모델 디렉토리 지정 가능
    env_dir = os.getenv("GPT4ALL_MODEL_DIR", "").strip()
    if env_dir:
        cand = Path(env_dir) / model_name
        if cand.exists():
            return model_name, env_dir

    # 3) Windows에서 흔한 기본 경로들 탐색
    candidates = [
        Path.home() / ".cache" / "gpt4all",
        Path(os.getenv("LOCALAPPDATA", "")) / "nomic.ai" / "GPT4All",
    ]
    for d in candidates:
        cand = d / model_name
        if cand.exists():
            return model_name, str(d)

    raise FileNotFoundError(f"Model file does not exist in known dirs: {model_name}")

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

    model_name = (model or os.getenv("GPT4ALL_MODEL", "")).strip()
    
    if not model_name:
        return (
            "[LLM] GPT4All model not specified.\n"
            "Set GPT4ALL_MODEL env var or pass --model <model.gguf>\n"
            "Example: set GPT4ALL_MODEL=Meta-Llama-3-8B-Instruct.Q4_0.gguf"
        )

    prompt = _build_prompt(question, context)

    try:
        name, model_dir = _resolve_model_path(model_name)
        llm = GPT4All(name, model_path=model_dir, allow_download=False)
        with llm.chat_session():
            out = llm.generate(
                prompt,
                max_tokens=DEFAULT_MAX_TOKENS,
                temp=DEFAULT_TEMP,
            )
        return out.strip()
    except Exception as e:
        return f"[LLM ERROR] {e}"
