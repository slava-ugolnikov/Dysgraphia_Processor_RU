from typing import List  # Это устаревшая типизация. Используйте `list[...]`
import re


# Не создавайте классы ради классов. Это вполне могло быть функцией
class Tokenizer:
    def tokenize(self, text: str) -> List[str]:  # Method 'tokenize' may be 'static'
        return re.findall(r"[а-яё]+", text.lower())