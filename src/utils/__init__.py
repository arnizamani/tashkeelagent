import logging
import unicodedata
from typing import List, Tuple

import regex

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1024 * 4


def make_chunks(arabic_words: List[Tuple[int, int, str]],
                max_chunk_size: int = CHUNK_SIZE
) -> List[str]:
    """Split a list of Arabic words into chunks of max_chunk_size."""
    chunks = []
    current_chunk = []
    current_chunk_size = 0

    for line_i, word_i, word in arabic_words:
        word_size = len(word) + 1
        if current_chunk_size + word_size <= max_chunk_size:
            current_chunk.append((line_i, word_i, word))
            current_chunk_size += word_size
        else:
            chunks.append(current_chunk)
            current_chunk = [(line_i, word_i, word)]
            current_chunk_size = word_size

    if current_chunk:
        chunks.append(current_chunk)

    logging.info(f"Transforming arabic words into {len(chunks)} chunks of max size {max_chunk_size}")
    return chunks


def extract_arabic_words(lines: List[str]):
    """Prase lines to extract all words and arabic words, each word annotated with line number and word number."""

    # Pattern to match Arabic sequences or any non-Arabic sequences
    arabic_chars = '0-9' + '٠-٩' + '\u0621-\u065F\u0670-\u06D3\u06DF\u06E0-\u06E8\u08F0-\u08F3'
    full_pattern = fr'(?:[{arabic_chars}])+' + fr'|[^{arabic_chars}]+'
    arabic_word_pattern = fr'(?:[{arabic_chars}])+'
    non_arabic_text_pattern = fr'[^{arabic_chars}]+'
    full_pattern = arabic_word_pattern + '|' + non_arabic_text_pattern

    all_words = []
    arabic_words = []

    for i, line in enumerate(lines):
        all_parts = regex.findall(full_pattern, line)
        all_words.append(all_parts)
        arabic_parts = [(i, j, part) for j, part in enumerate(all_parts) if regex.match(arabic_word_pattern, part)]
        if not all(bool(regex.match('[0-9]+', p[2])) for p in arabic_parts):
            arabic_words.extend(arabic_parts)

    return all_words, arabic_words


def normalize_arabic_text(text):
    """Return a list of characters with Arabic combining marks removed."""
    def is_arabic_letter(char):
        if not ('\u0600' <= char <= '\u06FF' or '\u0750' <= char <= '\u077F' or
                '\u08A0' <= char <= '\u08FF' or '\uFB50' <= char <= '\uFDFF' or
                '\uFE70' <= char <= '\uFEFF'):
            return False
        return not unicodedata.combining(char)

    normalized = []
    for char in unicodedata.normalize("NFD", text):
        if is_arabic_letter(char) or not unicodedata.combining(char):
            normalized.append(char)
    return ''.join(normalized)


def get_ratio_of_undiacritized_words(text: str) -> float:
    """Calculate the ratio of undiacritized Arabic words to the total number of Arabic words."""

    arabic_diacritics_pattern = regex.compile(r'[\u064B-\u0653\u0670\u06E1]')

    _, arabic_words = extract_arabic_words(text.splitlines())
    total_count = len(arabic_words)

    undiacritized_words = [word for (_, _, word) in arabic_words if arabic_diacritics_pattern.search(word) is None]
    undiacritized_count = len(undiacritized_words)
    return undiacritized_count / total_count if total_count > 0 else 0
