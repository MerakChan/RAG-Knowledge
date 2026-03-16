class ChunkService:
    def __init__(self, chunk_size=500, overlap=50):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def split_text(self, text):
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + self.chunk_size
            
            if end >= text_length:
                chunk = text[start:]
            else:
                chunk = text[start:end]
                
                last_space = chunk.rfind(' ')
                if last_space != -1:
                    end = start + last_space + 1
                    chunk = text[start:end]
            
            chunks.append(chunk)
            start = end - self.overlap
        
        return chunks
