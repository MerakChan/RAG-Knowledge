import os

class VectorService:
    def __init__(self, collection_name='knowledge_base', persist_directory=None):
        try:
            import chromadb
            self.use_chroma = True
            if persist_directory is None:
                persist_directory = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'data', 'chroma_db')
            
            os.makedirs(persist_directory, exist_ok=True)
            
            self.client = chromadb.PersistentClient(path=persist_directory)
            
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"description": "Knowledge base collection"}
            )
        except ImportError:
            self.use_chroma = False
            self.documents = []
            print("ChromaDB not available, using in-memory storage")
    
    def add_documents(self, documents, ids=None, metadatas=None):
        if self.use_chroma:
            if ids is None:
                ids = [f"doc_{i}" for i in range(len(documents))]
            
            if metadatas is None:
                metadatas = [{"source": "uploaded"} for _ in range(len(documents))]
            
            self.collection.add(
                documents=documents,
                ids=ids,
                metadatas=metadatas
            )
        else:
            for doc in documents:
                self.documents.append(doc)
    
    def similarity_search(self, query, n_results=3, where=None):
        if self.use_chroma:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where
            )
            return results
        else:
            return {'documents': [self.documents[:n_results]]}
    
    def get_all_documents(self):
        if self.use_chroma:
            return self.collection.get()
        else:
            return {'documents': self.documents}
    
    def clear_collection(self):
        if self.use_chroma:
            # 只删除文档，不删除集合本身
            all_docs = self.collection.get()
            if all_docs and all_docs['ids']:
                self.collection.delete(ids=all_docs['ids'])
        else:
            self.documents = []
