"""Quick manual test for the retrieval pipeline."""
from app.db.session import SessionLocal
from app.models.user import User
from app.services.retrieval import hybrid_search, semantic_search, keyword_search
from app.services.reranker import rerank


def main():
    db = SessionLocal()
    try:
        user = db.query(User).first()
        if not user:
            print("No users found in DB. Register a user first.")
            return

        query = input("Enter a search query: ").strip()
        if not query:
            print("Empty query.")
            return

        print(f"\n=== SEMANTIC results for: '{query}' ===")
        for i, r in enumerate(semantic_search(query, db, user.id, top_k=5), 1):
            print(f"{i}. [score={r.score:.3f}] {r.document_filename} p.{r.page_number}")
            print(f"   {r.content[:120]}...\n")

        print(f"\n=== KEYWORD results for: '{query}' ===")
        for i, r in enumerate(keyword_search(query, db, user.id, top_k=5), 1):
            print(f"{i}. [score={r.score:.3f}] {r.document_filename} p.{r.page_number}")
            print(f"   {r.content[:120]}...\n")

        print(f"\n=== HYBRID results for: '{query}' ===")
        hybrid = hybrid_search(query, db, user.id, top_k=20)
        for i, r in enumerate(hybrid[:5], 1):
            print(f"{i}. [score={r.score:.4f}] {r.document_filename} p.{r.page_number}")
            print(f"   {r.content[:120]}...\n")

        print(f"\n=== RERANKED results for: '{query}' ===")
        reranked = rerank(query, hybrid, top_k=5)
        for i, r in enumerate(reranked, 1):
            print(f"{i}. [score={r.score:.4f}] {r.document_filename} p.{r.page_number}")
            print(f"   {r.content[:120]}...\n")
    finally:
        db.close()


if __name__ == "__main__":
    main() 