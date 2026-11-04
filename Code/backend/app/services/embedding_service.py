from fastapi import HTTPException

from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def generate_embedding(chunks:list[dict]):


    # Load model only once
    embedding_model = SentenceTransformer(MODEL_NAME)
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