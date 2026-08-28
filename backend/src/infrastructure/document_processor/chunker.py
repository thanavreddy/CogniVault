"""Recursive text splitter for document chunking."""
import logging
from uuid import UUID, uuid4
import tiktoken

from src.domain.entities.document import DocumentChunk

logger = logging.getLogger(__name__)


class DocumentChunker:
    """Splits documents into overlapping chunks using recursive character splitting."""

    # Separators in order of preference (try paragraph, then sentence, then word)
    SEPARATORS = ["\n\n", "\n", ". ", "! ", "? ", ", ", " ", ""]

    def __init__(self, encoding_name: str = "cl100k_base") -> None:
        """Initialize with tiktoken encoder for accurate token counting."""
        try:
            self._encoder = tiktoken.get_encoding(encoding_name)
        except Exception:
            self._encoder = None
            logger.warning("tiktoken unavailable, using character-based estimation")

    def _count_tokens(self, text: str) -> int:
        """Count tokens accurately with tiktoken, or estimate."""
        if self._encoder:
            return len(self._encoder.encode(text))
        return len(text) // 4  # ~4 chars per token on average

    def chunk(
        self,
        text: str,
        document_id: UUID,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> list[DocumentChunk]:
        """Split text into overlapping chunks."""
        if not text.strip():
            logger.warning("Empty text passed to chunker for document %s", document_id)
            return []

        raw_chunks = self._recursive_split(text, chunk_size, chunk_overlap)

        chunks = []
        for idx, chunk_text in enumerate(raw_chunks):
            if not chunk_text.strip():
                continue

            token_count = self._count_tokens(chunk_text)
            page_number = self._estimate_page(idx, len(raw_chunks), text)

            chunks.append(
                DocumentChunk(
                    id=uuid4(),
                    document_id=document_id,
                    content=chunk_text.strip(),
                    chunk_index=idx,
                    page_number=page_number,
                    token_count=token_count,
                    metadata={
                        "char_count": len(chunk_text),
                        "chunk_size_setting": chunk_size,
                        "chunk_overlap_setting": chunk_overlap,
                    },
                )
            )

        logger.info(
            "Chunked document %s → %d chunks (size=%d, overlap=%d)",
            document_id, len(chunks), chunk_size, chunk_overlap,
        )
        return chunks

    def _recursive_split(
        self,
        text: str,
        chunk_size: int,
        chunk_overlap: int,
        separators: list[str] | None = None,
    ) -> list[str]:
        """Recursively split text using a list of separators."""
        if separators is None:
            separators = self.SEPARATORS

        final_chunks: list[str] = []

        # Find which separator works best for this text
        separator = separators[-1]
        new_separators = []
        for i, sep in enumerate(separators):
            if sep == "":
                separator = sep
                break
            if sep in text:
                separator = sep
                new_separators = separators[i + 1 :]
                break

        # Split on separator
        splits = text.split(separator) if separator else list(text)
        splits = [s for s in splits if s]  # Remove empties

        # Merge splits into chunks of ~chunk_size tokens
        current_chunk: list[str] = []
        current_length = 0

        for split in splits:
            split_length = self._count_tokens(split)

            # If this split alone exceeds chunk_size, recurse on it
            if split_length > chunk_size:
                if current_chunk:
                    final_chunks.append(separator.join(current_chunk))
                    current_chunk = []
                    current_length = 0
                sub_chunks = self._recursive_split(
                    split, chunk_size, chunk_overlap,
                    new_separators if new_separators else separators,
                )
                final_chunks.extend(sub_chunks)
                continue

            if current_length + split_length > chunk_size and current_chunk:
                final_chunks.append(separator.join(current_chunk))

                # Overlap: keep last N characters of overlap
                overlap_chunks: list[str] = []
                overlap_length = 0
                for s in reversed(current_chunk):
                    s_len = self._count_tokens(s)
                    if overlap_length + s_len > chunk_overlap:
                        break
                    overlap_chunks.insert(0, s)
                    overlap_length += s_len

                current_chunk = overlap_chunks
                current_length = overlap_length

            current_chunk.append(split)
            current_length += split_length

        if current_chunk:
            final_chunks.append(separator.join(current_chunk))

        return final_chunks

    @staticmethod
    def _estimate_page(chunk_index: int, total_chunks: int, full_text: str) -> int:
        """Estimate page number from position in document."""
        # Count [Page N] markers if present (from PDF extraction)
        import re
        page_markers = re.findall(r"\[Page (\d+)\]", full_text)
        if page_markers:
            total_pages = int(page_markers[-1])
            position_ratio = chunk_index / max(total_chunks - 1, 1)
            return max(1, round(position_ratio * total_pages))
        # Default: estimate ~250 tokens per page
        return (chunk_index // 3) + 1
