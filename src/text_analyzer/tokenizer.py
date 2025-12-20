from typing import List
import re


class Tokenizer:
    def tokenize(self, text: str) -> List[str]:
        return re.findall(r"[а-яё]+", text.lower())