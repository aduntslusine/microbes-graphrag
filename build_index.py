"""Build a vector index over data/passages.json.

Build: .venv/bin/python build_index.py
Search: .venv/bin/python build_index.py "lactate butyrate"
"""

import json
import sys
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

DATA_DIR = Path(__file__).resolve().parent / "data"
PASSAGES_FILE = DATA_DIR / "passages.json"
INDEX_FILE = DATA_DIR / "embeddings.npy"
MODEL_NAME = "NeuML/biomedbert-small-embeddings"


def load_model():
    return SentenceTransformer(MODEL_NAME)


def build(model):
    passages = json.loads(PASSAGES_FILE.read_text())
    texts = [passage["text"] for passage in passages]
    vectors = model.encode(texts, normalize_embeddings=True)
    DATA_DIR.mkdir(exist_ok=True)
    np.save(INDEX_FILE, vectors)
    print(f"embedded {len(passages)} passages with {MODEL_NAME}")
    print(f"wrote {INDEX_FILE} with shape {tuple(vectors.shape)}")


def search(model, query):
    passages = json.loads(PASSAGES_FILE.read_text())
    vectors = np.load(INDEX_FILE)
    query_vector = model.encode([query], normalize_embeddings=True)[0]
    scores = vectors @ query_vector
    best = scores.argsort()[::-1][:5]
    for rank, index in enumerate(best, start=1):
        passage = passages[index]
        print(f"{rank}. {passage['pmcid']}  {scores[index]:.3f}")
        print(passage["text"][:300])
        print()


def main():
    model = load_model()
    if len(sys.argv) > 1:
        search(model, " ".join(sys.argv[1:]))
    else:
        build(model)


if __name__ == "__main__":
    main()
