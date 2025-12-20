from src.language.vocabulary import Vocabulary


class WordReconstructor:

    def __init__(self, vocabulary: Vocabulary):
        self.vocab = vocabulary

    def reconstruct(self, written_word: str) -> tuple[str, str]:
        lemma_written = self.vocab.morph.parse(written_word)[0].normal_form

        # 1. Если слово уже корректно
        if lemma_written in self.vocab.words:
            return lemma_written, "без ошибки"

        # 2. Кандидаты по длине
        candidates = [
            w for w in self.vocab.words
            if abs(len(w) - len(lemma_written)) <= 1
        ]

        # 3. Пробуем классифицировать
        for correct in candidates:
            error = ErrorClassifier.classify(correct, written_word)
            if error != "другое":
                return correct, error

        return lemma_written, "не удалось восстановить"