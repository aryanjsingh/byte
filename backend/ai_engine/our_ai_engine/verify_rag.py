from kb_engine import retrieve_best_practices, load_and_index_docs
import os

def test_rag():
    print("Testing RAG Workflow...")
    
    # Check if keys are set
    if not os.getenv("PINECONE_API_KEY") or not os.getenv("GOOGLE_API_KEY"):
        print("Skipping actual RAG test due to missing API keys.")
        return

    # Index first (optional check?)
    # In a real scenario, we might assume index exists, but here we run it to be sure.
    try:
        load_and_index_docs()
    except Exception as e:
        print(f"Indexing failed: {e}")
        return

    # Query
    print("\n--- Query: 'What is the password policy?' ---")
    response = retrieve_best_practices("What is the password policy?")
    print(response)

    print("\n--- Query: 'Tell me about protect function' ---")
    response = retrieve_best_practices("Tell me about protect function")
    print(response)

if __name__ == "__main__":
    test_rag()
