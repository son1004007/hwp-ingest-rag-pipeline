# rag_answer.py
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os

def answer_with_context(question: str, context: str, model: str = "gpt-5.2-mini") -> str:
    if not context.strip():
        return "[LLM] context is empty. answer skipped."

    # API 키 체크
    if not os.getenv("OPENAI_API_KEY"):
        return "[LLM] OPENAI_API_KEY not set."

    llm = ChatOpenAI(
        model=model,
        temperature=0.2,
        timeout=30,
        max_retries=2,
    )

    messages = [
        SystemMessage(
            content=(
                "너는 내부 문서를 근거로 답변하는 분석 보조 AI다.\n"
                "제공된 문서 내용에 근거해서만 답변하고, "
                "문서에 없는 내용은 '문서에 명시되어 있지 않다'고 답하라."
            )
        ),
        HumanMessage(
            content=(
                f"[문서 내용]\n{context}\n\n"
                f"[질문]\n{question}\n\n"
                "위 문서 내용을 근거로 간결하고 정확하게 답변하라."
            )
        ),
    ]

    try:
        res = llm.invoke(messages)
        return res.content
    except Exception as e:
        return f"[LLM ERROR] {e}"
