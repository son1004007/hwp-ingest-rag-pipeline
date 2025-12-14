import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda

# LLM: GPT4All (LangChain community)
from langchain_community.llms import GPT4All

from rag_retriever_pgvector import retrieve_blocks_pgvector

def format_context(blocks, max_chars: int = 3500) -> str:
    parts, total = [], 0
    for b in blocks:
        chunk = f"[doc_id={b['doc_id']}|block_id={b['block_id']}|type={b['block_type']}]\n{b['content']}\n"
        if total + len(chunk) > max_chars:
            break
        parts.append(chunk)
        total += len(chunk)
    return "\n---\n".join(parts)

def build_chain(model_path: str):
    # 모델 경로는 반드시 "실제 gguf 파일의 절대경로"가 안정적입니다.
    llm = GPT4All(
        model=model_path,
        max_tokens=512,
        temp=0.2,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "당신은 문서 기반 질의응답 도우미입니다.\n"
         "- 반드시 [문서] 내용에 근거해서만 답하세요.\n"
         "- 문서에 없으면: '문서에 언급되지 않았습니다.'라고 답하세요.\n"
         "- 답변은 한국어로 3~6문장으로 간결하게.\n"
         "- 근거로 사용한 doc_id, block_id를 1~3개만 같이 적으세요.\n"),
        ("human",
         "[문서]\n{context}\n\n[질문]\n{question}\n")
    ])

    def retrieve_and_pack(inputs: dict):
        q = inputs["question"]
        blocks = retrieve_blocks_pgvector(q, top_k=inputs.get("top_k", 8))
        ctx = format_context(blocks, max_chars=inputs.get("max_chars", 3500))
        return {"question": q, "context": ctx, "blocks": blocks}

    chain = (
        RunnableLambda(retrieve_and_pack)
        | RunnableLambda(lambda x: {"question": x["question"], "context": x["context"]})
        | prompt
        | llm
    )
    return chain
