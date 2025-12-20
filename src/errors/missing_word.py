from typing import List, Tuple


class MissingWordDetector:
    def detect(self, lemmas: List[str]) -> List[Tuple[str, str, str]]:
        results = []

        for i in range(len(lemmas) - 1):
            if lemmas[i] == "я" and lemmas[i + 1] == "попить":
                results.append(("хотеть", "", "пропуск слова"))

        return results