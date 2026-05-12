import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from google import genai
from google.genai import types as genai_types
from db.models import Transaction
from config.settings import settings
import structlog

logger = structlog.get_logger()

# Initialize new google.genai client
_genai_client = genai.Client(api_key=settings.gemini_api_key)

class CustomGeminiEmbeddingFunction(EmbeddingFunction):
    """Custom wrapper for Gemini Embeddings using the new google.genai SDK."""
    def __call__(self, input: Documents) -> Embeddings:
        result = _genai_client.models.embed_content(
            model="models/gemini-embedding-001",
            contents=input,
            config=genai_types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
        )
        return [e.values for e in result.embeddings]

# Initialize ChromaDB client with local persistence
chroma_client = chromadb.PersistentClient(path=settings.chroma_persist_dir)

# Get or create the collection using our custom function
collection = chroma_client.get_or_create_collection(
    name="transactions_memory",
    embedding_function=CustomGeminiEmbeddingFunction()
)

def embed_transaction(txn: Transaction) -> None:
    """Embed a single transaction and store it in ChromaDB."""
    try:
        # Create a rich natural language document to embed
        doc = (
            f"Transaction ID: {txn.id}. "
            f"Type: {txn.type}. "
            f"Category: {txn.category}. "
            f"Amount: ₹{txn.amount}. "
            f"Date: {txn.txn_date}. "
            f"Description: {txn.description or 'No description'}. "
            f"Raw Input Context: {txn.raw_input or 'None'}."
        )
        
        collection.add(
            documents=[doc],
            metadatas=[{
                "user_id": str(txn.user_id),
                "type": txn.type,
                "category": txn.category or "unknown",
                "txn_date": str(txn.txn_date),
                "amount": float(txn.amount)
            }],
            ids=[f"txn_{txn.id}"]
        )
        logger.info("Transaction embedded in ChromaDB", txn_id=txn.id)
    except Exception as e:
        logger.error("Failed to embed transaction in ChromaDB", error=str(e), txn_id=txn.id)

def search_transactions(user_id: int, query: str, n_results: int = 5) -> list[str]:
    """Search for relevant transactions using semantic query matching."""
    try:
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where={"user_id": str(user_id)}
        )
        
        # results["documents"] is a list of lists of documents
        if results and results.get("documents") and len(results["documents"]) > 0:
            return results["documents"][0]
        return []
    except Exception as e:
        logger.error("Semantic search failed", error=str(e), user_id=user_id)
        return []
