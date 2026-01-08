import os
from dotenv import load_dotenv

load_dotenv()

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Define the persistence directory
current_dir = os.path.dirname(os.path.abspath(__file__))
PERSIST_DIRECTORY = os.path.join(current_dir, "db")

# Initialize embeddings
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

def load_documents():
    """
    Loads text documents from the 'docs' directory, parses metadata, 
    and chunks them into smaller segments for the vector store.
    """
    docs_dir = os.path.join(current_dir, "docs")
    documents = []
    
    if not os.path.exists(docs_dir):
        try:
            os.makedirs(docs_dir)
            print(f"Created docs directory at {docs_dir}. Please add .txt files.")
        except OSError:
            pass # Directory might exist
        return []

    for filename in os.listdir(docs_dir):
        if filename.endswith(".txt"):
            file_path = os.path.join(docs_dir, filename)
            try:
                # Custom parsing for metadata
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                metadata = {"source": filename}
                text_content = content
                
                # Check for METADATA block
                if "METADATA" in content and "CONTENT" in content:
                    parts = content.split("CONTENT")
                    meta_block = parts[0].replace("METADATA", "").strip()
                    text_content = parts[1].strip()
                    
                    for line in meta_block.split("\n"):
                        if ":" in line:
                            key, val = line.split(":", 1)
                            metadata[key.strip().lower()] = val.strip()

                # Chunking
                text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
                chunks = text_splitter.create_documents([text_content], metadatas=[metadata])
                documents.extend(chunks)
                print(f"Loaded and chunked {len(chunks)} segments from {filename}")
                
            except Exception as e:
                print(f"Error loading {filename}: {e}")
    
    return documents

def initialize_vector_store():
    """
    Initializes or updates the Chroma vector store with documents from the 'docs' folder.
    """
    documents = load_documents()
    if documents:
        # Create and persist the vector store
        vectordb = Chroma.from_documents(
            documents=documents, 
            embedding=embeddings, 
            persist_directory=PERSIST_DIRECTORY
        )
        print(f"Vector store initialized at {PERSIST_DIRECTORY}")
        return vectordb
    else:
        print("No documents found to initialize vector store.")
        return None

def query_rag(query_text: str, n_results: int = 5):
    """
    Queries the vector store for relevant context based on the input text.
    """
    # Load the persisted vector store
    vectordb = Chroma(persist_directory=PERSIST_DIRECTORY, embedding_function=embeddings)
    
    # Perform similarity search
    results = vectordb.similarity_search(query_text, k=n_results)
    
    # Create a list of context strings
    context_list = [f"[Source: {doc.metadata.get('source', 'Unknown')}]\n{doc.page_content}" for doc in results]
    
    return context_list

# Generate the DB on import if it doesn't exist
if not os.path.exists(PERSIST_DIRECTORY):
    initialize_vector_store()
