# rag_cli.py
import os
import argparse
from dotenv import load_dotenv

from rag_retriever import retrieve_blocks_fts, retrieve_blocks_fallback, format_context
# from rag_answer import answer_with_context
# from rag_answer_ollama import answer_with_context_ollama as answer_with_context
from rag_answer_gpt4all import answer_with_context


def main():
    load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument("question", type=str, help="질문 문장")
    parser.add_argument("--top-k", type=int, default=12, help="가져올 블록 개수")
    parser.add_argument("--model", type=str, default="gpt-4o-mini", help="사용할 모델명")
    parser.add_argument("--dry-run", action="store_true", help="LLM 호출 없이 검색 결과만 출력")
    args = parser.parse_args()

    table = os.getenv("PG_TABLE", "doc_blocks")

    # 1) FTS
    blocks = retrieve_blocks_fts(args.question, top_k=args.top_k, table_name=table)

    # 2) fallback
    if not blocks:
        print("[retriever] FTS hit=0, fallback to ILIKE(OR keywords)")
        blocks = retrieve_blocks_fallback(args.question, top_k=args.top_k, table_name=table)

        # # 3) no blocks → stop
        # if not blocks:
        #     print("[retriever] hit=0 (FTS+fallback). stop.")
        #     return


    # 4) dry-run이면 여기서 결과 미리보기만
    if args.dry_run:
        for i, b in enumerate(blocks[:5], start=1):
            preview = (b["content"] or "")[:120].replace("\n", " ")
            print(f"  - {i}. ({b['doc_id']}, {b['block_id']}, {b['block_type']}) {preview}")
        return

    # 5) LLM
    context = format_context(blocks)
    print(f"[retriever] blocks={len(blocks)} top_k={args.top_k}")
    print("[answer] generating...\n")
    answer = answer_with_context(args.question, context, model=args.model)
    print(answer)

if __name__ == "__main__":
    main()
