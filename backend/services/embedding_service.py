from sentence_transformers import SentenceTransformer
import numpy as np

class EmbeddingService:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
    
    def embed(self, text):
        if isinstance(text, list):
            return self.model.encode(text, show_progress_bar=False)
        return self.model.encode(text, show_progress_bar=False)
    
    def embed_query(self, query):
        return self.model.encode(query, show_progress_bar=False)
