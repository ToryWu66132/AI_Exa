from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-small-en-v1.5")

def get_embeddings(texts):
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()