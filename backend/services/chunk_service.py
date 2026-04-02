import re


class ChunkService:
    def __init__(self, chunk_size=500, overlap=50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def split_text(self, text):
        text = str(text or '').strip()
        if not text:
            return []

        paragraphs = [paragraph.strip() for paragraph in re.split(r'\n{2,}', text) if paragraph.strip()]
        chunks = []
        current_chunk = ''

        for paragraph in paragraphs:
            if len(paragraph) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ''
                chunks.extend(self._split_long_paragraph(paragraph))
                continue

            candidate = f"{current_chunk}\n\n{paragraph}".strip() if current_chunk else paragraph
            if len(candidate) <= self.chunk_size:
                current_chunk = candidate
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph

        if current_chunk:
            chunks.append(current_chunk.strip())

        return self._apply_overlap(chunks)

    def _split_long_paragraph(self, paragraph):
        segments = [segment.strip() for segment in re.split(r'(?<=[。！？!?；;])', paragraph) if segment.strip()]
        chunks = []
        current_chunk = ''

        for segment in segments:
            if len(segment) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ''
                chunks.extend(self._split_by_length(segment))
                continue

            candidate = f"{current_chunk}{segment}".strip() if current_chunk else segment
            if len(candidate) <= self.chunk_size:
                current_chunk = candidate
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = segment

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _split_by_length(self, text):
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = min(start + self.chunk_size, text_length)
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= text_length:
                break
            start = max(end - self.overlap, start + 1)

        return chunks

    def _apply_overlap(self, chunks):
        if not chunks:
            return []
        if self.overlap <= 0:
            return chunks

        overlapped_chunks = []
        for index, chunk in enumerate(chunks):
            if index == 0:
                overlapped_chunks.append(chunk)
                continue

            previous_tail = chunks[index - 1][-self.overlap:].strip()
            if previous_tail and not chunk.startswith(previous_tail):
                merged = f"{previous_tail}\n{chunk}".strip()
                overlapped_chunks.append(merged[: self.chunk_size + self.overlap])
            else:
                overlapped_chunks.append(chunk)

        return overlapped_chunks
