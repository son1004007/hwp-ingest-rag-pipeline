# rag_answer_ollama.py
import requests

def answer_with_context_ollama(question: str, context: str, model: str = "llama3.2") -> str:
    if not context.strip():
        return "[LLM] context is empty. answer skipped."

    prompt = (
        "당신은 문서 기반 QA 도우미입니다.\n"
        "아래 [문서] 내용만 근거로 답변하세요. 문서에 없으면 '문서에 없음'이라고 답하세요.\n\n"
        f"[문서]\n{context}\n\n"
        f"[질문]\n{question}\n"
    )

    r = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=120,
    )
    r.raise_for_status()
    return r.json().get("response", "").strip()
