from typing import List, Tuple  # Это устаревшая типизация. Используйте `list[...]` / `tuple[...]`


class MissingWordDetector:
    def detect(self, lemmas: List[str]) -> List[Tuple[str, str, str]]:  # Method 'detect' may be 'static'
        results = []

        for i in range(len(lemmas) - 1):
            if lemmas[i] == "я" and lemmas[i + 1] == "попить":
                results.append(("хотеть", "", "пропуск слова"))

        return results