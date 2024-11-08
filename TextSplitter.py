import tiktoken
import re
from typing import List, Dict, Tuple
from collections import defaultdict


class TextSplitter:
    def __init__(self, model_name: str = 'gpt-4'):
        self.MODEL_NAME = model_name
        self.tokenizer = None
        self.SPECIAL_TOKENS = {
            "<|im_start|>": 100264,
            "<|im_end|>": 100265,
            "<|im_sep|>": 100266
        }

    async def initialize_tokenizer(self):
        if not self.tokenizer:
            # Inicjalizujemy tokenizator
            self.tokenizer = tiktoken.encoding_for_model(self.MODEL_NAME)

    def count_tokens(self, text: str) -> int:
        """Zliczanie tokenów w tekście"""
        if not self.tokenizer:
            raise RuntimeError("Tokenizer not initialized")
        formatted_content = self.format_for_tokenization(text)
        # Przesyłamy tekst do enkodera
        tokens = self.tokenizer.encode(formatted_content)
        return len(tokens)

    def format_for_tokenization(self, text: str) -> str:
        """Formatujemy tekst do tokenizacji"""
        return f"<|im_start|>user\n{text}<|im_end|>\n<|im_start|>assistant<|im_end|>"

    async def split(self, text: str, limit: int) -> List[Dict]:
        print(f"Starting split process with limit: {limit} tokens")
        await self.initialize_tokenizer()
        chunks = []
        position = 0
        total_length = len(text)
        current_headers = defaultdict(list)

        while position < total_length:
            print(f"Processing chunk starting at position: {position}")
            chunk_text, chunk_end = self.get_chunk(text, position, limit)
            tokens = self.count_tokens(chunk_text)
            print(f"Chunk tokens: {tokens}")

            headers_in_chunk = self.extract_headers(chunk_text)
            self.update_current_headers(current_headers, headers_in_chunk)

            content, urls, images = self.extract_urls_and_images(chunk_text)

            chunks.append({
                "text": content,
                "metadata": {
                    "tokens": tokens,
                    "headers": dict(current_headers),
                    "urls": urls,
                    "images": images,
                }
            })

            print(f"Chunk processed. New position: {chunk_end}")
            position = chunk_end

        print(f"Split process completed. Total chunks: {len(chunks)}")
        return chunks

    def get_chunk(self, text: str, start: int, limit: int) -> Tuple[str, int]:
        print(f"Getting chunk starting at {start} with limit {limit}")

        overhead = self.count_tokens(
            self.format_for_tokenization('')) - self.count_tokens('')

        end = min(start + int((len(text) - start) * limit /
                  self.count_tokens(text[start:])), len(text))
        chunk_text = text[start:end]
        tokens = self.count_tokens(chunk_text)

        while tokens + overhead > limit and end > start:
            print(f"Chunk exceeds limit with {
                  tokens + overhead} tokens. Adjusting end position...")
            end = self.find_new_chunk_end(text, start, end)
            chunk_text = text[start:end]
            tokens = self.count_tokens(chunk_text)

        end = self.adjust_chunk_end(text, start, end, tokens + overhead, limit)
        chunk_text = text[start:end]
        print(f"Final chunk end: {end}")
        return chunk_text, end

    def adjust_chunk_end(self, text: str, start: int, end: int, current_tokens: int, limit: int) -> int:
        min_chunk_tokens = int(limit * 0.8)

        next_newline = text.find('\n', end)
        prev_newline = text.rfind('\n', start, end)

        if next_newline != -1 and next_newline < len(text):
            extended_end = next_newline + 1
            if min_chunk_tokens <= self.count_tokens(text[start:extended_end]) <= limit:
                print(f"Extending chunk to next newline at position {
                      extended_end}")
                return extended_end

        if prev_newline > start:
            reduced_end = prev_newline + 1
            if min_chunk_tokens <= self.count_tokens(text[start:reduced_end]) <= limit:
                print(f"Reducing chunk to previous newline at position {
                      reduced_end}")
                return reduced_end

        return end

    def find_new_chunk_end(self, text: str, start: int, end: int) -> int:
        return max(start + 1, end - (end - start) // 10)

    def extract_headers(self, text: str) -> Dict[str, List[str]]:
        headers = defaultdict(list)
        header_regex = r"(^|\n)(#{1,6})\s+(.*)"

        for match in re.finditer(header_regex, text):
            level = len(match.group(2))
            content = match.group(3).strip()
            headers[f"h{level}"].append(content)

        return headers

    def update_current_headers(self, current: Dict[str, List[str]], extracted: Dict[str, List[str]]):
        for level in range(1, 7):
            key = f"h{level}"
            if key in extracted:
                current[key] = extracted[key]
                self.clear_lower_headers(current, level)

    def clear_lower_headers(self, headers: Dict[str, List[str]], level: int):
        for l in range(level + 1, 7):
            headers.pop(f"h{l}", None)

    def extract_urls_and_images(self, text: str) -> Tuple[str, List[str], List[str]]:
        urls, images = [], []
        url_index, image_index = 0, 0

        def url_replacement(match):
            nonlocal url_index
            urls.append(match.group(2))
            return f"[{match.group(1)}]({{url{url_index}}})"

        def image_replacement(match):
            nonlocal image_index
            images.append(match.group(2))
            return f"![{match.group(1)}]({{img{image_index}}})"

        content = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", image_replacement, text)
        content = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", url_replacement, content)

        return content, urls, images
