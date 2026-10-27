"""
=============================================================================
PROJECT 10: GenAI RAG PLATFORM (CAPSTONE)
=============================================================================
FILE: services/chunking_service.py
PURPOSE: Splits documents into searchable chunks

CHUNKING is the FIRST STEP in a RAG pipeline:
1. 📄 Document comes in (could be 100 pages)
2. ✂️ Chunking splits it into smaller pieces
3. 🧮 Each piece gets embedded separately
4. 🗄️ Each piece is independently searchable

CHUNKING STRATEGIES (Strategy Pattern from P9):
- Fixed size: Every N characters
- Sentence-based: Split on sentence boundaries
- Paragraph-based: Split on paragraph boundaries
- Semantic: Split where topic changes (advanced)

WHY CHUNK SIZE MATTERS:
- Too large: Retrieval finds relevant chunk but includes noise
- Too small: Context is fragmented, loses coherence
- Sweet spot: 200-500 tokens (varies by use case)
=============================================================================
"""

from models.document import Document, DocumentChunk


class ChunkingService:
    """
    Service responsible for splitting documents into chunks.

    STRATEGY PATTERN APPLICATION:
    Different chunking strategies for different document types:
    - Code: Split on function boundaries
    - Prose: Split on paragraphs
    - Data: Split on record boundaries

    For simplicity, this implementation uses paragraph-based chunking
    with overlap (sliding window).
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        """
        Args:
            chunk_size: Target characters per chunk
            overlap: Characters of overlap between consecutive chunks

        WHY OVERLAP?
        Without overlap, a sentence split across two chunks is lost.
        With overlap, the end of chunk N appears at the start of chunk N+1.
        This ensures no information falls through the cracks.

        EXAMPLE (overlap=10):
            Chunk 1: "...the cat sat on the mat. The"
            Chunk 2: "on the mat. The dog ran fast..."
            ↑ "on the mat. The" appears in BOTH chunks
        """
        self._chunk_size = chunk_size
        self._overlap = overlap

    def chunk_document(self, document: Document) -> list[DocumentChunk]:
        """
        Split a document into chunks using paragraph-aware splitting.

        ALGORITHM:
        1. Split content by paragraphs (double newlines)
        2. Accumulate paragraphs until chunk_size is reached
        3. Create a chunk
        4. Start next chunk with overlap from previous
        5. Repeat until all content is chunked
        """
        if not document.content:
            return []

        # Split into paragraphs
        paragraphs = [p.strip() for p in document.content.split("\n\n") if p.strip()]

        chunks: list[DocumentChunk] = []
        current_text = ""
        chunk_index = 0

        for paragraph in paragraphs:
            # Would adding this paragraph exceed chunk_size?
            if current_text and len(current_text) + len(paragraph) > self._chunk_size:
                # Create a chunk from accumulated text
                chunk = DocumentChunk(
                    document_id=document.document_id,
                    content=current_text.strip(),
                    chunk_index=chunk_index,
                    metadata={
                        "source": document.source,
                        "doc_title": document.title,
                        "doc_type": document.doc_type,
                    },
                )
                chunks.append(chunk)
                chunk_index += 1

                # Start new chunk with overlap
                if self._overlap > 0 and len(current_text) > self._overlap:
                    current_text = current_text[-self._overlap :] + "\n\n" + paragraph
                else:
                    current_text = paragraph
            else:
                # Accumulate paragraph
                if current_text:
                    current_text += "\n\n" + paragraph
                else:
                    current_text = paragraph

        # Don't forget the last chunk!
        if current_text.strip():
            chunk = DocumentChunk(
                document_id=document.document_id,
                content=current_text.strip(),
                chunk_index=chunk_index,
                metadata={
                    "source": document.source,
                    "doc_title": document.title,
                    "doc_type": document.doc_type,
                },
            )
            chunks.append(chunk)

        return chunks

    def get_stats(self, chunks: list[DocumentChunk]) -> dict:
        """Return statistics about the chunking result."""
        if not chunks:
            return {"count": 0, "avg_size": 0, "min_size": 0, "max_size": 0}

        sizes = [len(c.content) for c in chunks]
        return {
            "count": len(chunks),
            "avg_size": sum(sizes) // len(sizes),
            "min_size": min(sizes),
            "max_size": max(sizes),
            "total_chars": sum(sizes),
        }
