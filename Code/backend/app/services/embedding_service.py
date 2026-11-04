from fastapi import HTTPException

from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Load model only once
embedding_model = SentenceTransformer(MODEL_NAME)
def generate_embedding(chunks:list[dict]):



    try:
        texts=[]
        for chunk in chunks:
            text=chunk["text"]
            if text:
                texts.append(text)
        if not texts:
            raise ValueError("No valid text chunks provided for embedding generation") 
        embeddings=embedding_model.encode(texts, batch_size=32 , show_progress_bar=False , normalize_embeddings=True)
        result=[]
        for chunk, embedding in zip(chunks, embeddings):
            result.append({
                **chunk,
                "embedding":embedding.tolist()
            })
        return result
    except Exception as e:
        print(f"Embedding generation error: {e}")
        raise HTTPException(status_code=500, detail="Error generating embeddings")

def generate_query_embedding(query:str):
    try:
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        embedding=embedding_model.encode(
            query.strip(),
            normalize_embeddings=True
        )    
        return embedding.tolist()
    except Exception as e:
        print(f"Query embedding generation error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error generating query embedding"
        )        