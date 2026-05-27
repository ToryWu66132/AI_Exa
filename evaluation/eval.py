from sentence_transformers import SentenceTransformer
import numpy as np
from evaluation.test_data import test_cases

# 加载多个模型
models = {
    "bge-small": SentenceTransformer("BAAI/bge-small-en-v1.5"),
    "bge-base": SentenceTransformer("BAAI/bge-base-en-v1.5"),
    "miniLM": SentenceTransformer("all-MiniLM-L6-v2")
}


def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def evaluate_model(model, name):
    print(f"\n===== Evaluating {name} =====")

    total_score = 0
    count = 0

    for case in test_cases:
        query = case["query"]
        docs = case["relevant_docs"]

        query_emb = model.encode(query)

        for doc in docs:
            doc_emb = model.encode(doc)
            sim = cosine_similarity(query_emb, doc_emb)

            total_score += sim
            count += 1

            print(f"\nQuery: {query}")
            print(f"Doc: {doc}")
            print(f"Similarity: {sim:.4f}")

    avg_score = total_score / count
    print(f"\n>>> Avg Similarity for {name}: {avg_score:.4f}")

    return avg_score


def run_evaluation():
    results = {}

    for name, model in models.items():
        score = evaluate_model(model, name)
        results[name] = score

    print("\n===== Final Ranking =====")
    sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)

    for name, score in sorted_results:
        print(f"{name}: {score:.4f}")


if __name__ == "__main__":
    run_evaluation()
