import os
import time
import requests
import hashlib
from typing import List
from langchain_core.embeddings import Embeddings
from app.config import settings

class HuggingFaceInferenceEmbeddings(Embeddings):
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", hf_api_token: str = None):
        self.model_name = model_name
        self.hf_api_token = hf_api_token
        self.api_url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{model_name}"
        self.headers = {"Authorization": f"Bearer {hf_api_token}"} if hf_api_token else {}

    def _embed(self, texts: List[str]) -> List[List[float]]:
        max_retries = 5
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json={"inputs": texts, "options": {"wait_for_model": True}},
                    timeout=30
                )
                if response.status_code == 200:
                    embeddings = response.json()
                    if isinstance(embeddings, list):
                        if len(embeddings) > 0 and isinstance(embeddings[0], list):
                            return embeddings
                        elif len(embeddings) > 0 and isinstance(embeddings[0], float):
                            return [embeddings]
                    raise ValueError(f"Unexpected response format from HF Inference API: {embeddings}")
                elif response.status_code == 503 or "loading" in response.text.lower():
                    try:
                        wait_time = response.json().get("estimated_time", 15)
                    except Exception:
                        wait_time = 15
                    print(f"HF Model is loading, waiting {wait_time}s and retrying (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(min(wait_time, 30))
                else:
                    raise ValueError(f"HF Inference API error {response.status_code}: {response.text}")
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                time.sleep(2 ** attempt)
        return []

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        batch_size = 16
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            batch_embeddings = self._embed(batch)
            all_embeddings.extend(batch_embeddings)
        return all_embeddings

    def embed_query(self, text: str) -> List[float]:
        embeddings = self._embed([text])
        return embeddings[0]


class MockOfflineEmbeddings(Embeddings):
    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def _embed_text(self, text: str) -> List[float]:
        h = hashlib.sha256(text.encode("utf-8")).digest()
        vector = []
        for i in range(self.dimension):
            val = hashlib.sha256(h + i.to_bytes(4, "big")).digest()
            float_val = (int.from_bytes(val[:4], "big") / 4294967295.0) * 2.0 - 1.0
            vector.append(float_val)
        return vector

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed_text(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed_text(text)


def get_resilient_embeddings():
    hf_token = settings.HF_API_TOKEN
    if hf_token:
        hf_token = hf_token.strip('"\'')
        
    try:
        # Quick DNS / connection test to check if HuggingFace is reachable
        print("Checking connection to HuggingFace Inference API...")
        response = requests.head("https://api-inference.huggingface.co", timeout=3)
        print("HF Inference API is reachable. Using HuggingFaceInferenceEmbeddings (dimension: 384).")
        return HuggingFaceInferenceEmbeddings(hf_api_token=hf_token)
    except Exception as e:
        print(f"HF Inference API is unreachable ({e}). Falling back to MockOfflineEmbeddings (dimension: 384).")
        return MockOfflineEmbeddings()
