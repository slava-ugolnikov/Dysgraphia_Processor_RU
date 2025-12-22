from src.errors.softness import SoftnessErrorAnalyzer  # from .softness import SoftnessErrorAnalyzer
from src.errors.phonetic import PhoneticConfusionAnalyzer  # from .phonetic import PhoneticConfusionAnalyzer


class ErrorClassifier:
    @staticmethod
    def is_letter_perseveration(correct: str, written: str) -> bool:
        if len(written) != len(correct) + 1:
            return False

        for i in range(len(written) - 1):
            if written[i] == written[i + 1]:
                candidate = written[:i] + written[i + 1:]
                if candidate == correct:
                    return True
        return False

    @staticmethod
    def is_letter_insertion(correct: str, written: str) -> bool:
        if ErrorClassifier.is_letter_perseveration(correct, written):
            return False

        if len(written) != len(correct) + 1:
            return False

        for i in range(len(written)):
            if written[:i] + written[i + 1:] == correct:
                return True
        return False

    @staticmethod
    def is_anticipation(correct: str, written: str) -> bool:
        if len(correct) != len(written):  # Duplicated code fragment (8 lines long)
            return False

        diffs = [(i, c, w) for i, (c, w) in enumerate(zip(correct, written)) if c != w]
        if len(diffs) != 2:
            return False

        (i, c1, w1), (j, c2, w2) = diffs

        return (
                w1 == c2 and
                w2 == c2 and
                i < j  # Expected type 'tuple[int, ...]' (matched generic type 'tuple[_T_co, ...]'), got 'tuple[int, str, str]' instead
        )

    @staticmethod
    def is_transposition(correct: str, written: str) -> bool:
        if len(correct) != len(written):  # Duplicated code fragment (9 lines long)
            return False

        diffs = [(i, c, w) for i, (c, w) in enumerate(zip(correct, written)) if c != w]

        if len(diffs) != 2:
            return False

        (_, c1, w1), (_, c2, w2) = diffs

        return c1 == w2 and c2 == w1

    @staticmethod
    def is_letter_omission(correct: str, written: str) -> bool:
        if len(correct) - len(written) == 1:
            return True
        return False

    @staticmethod
    def is_syllable_omission(correct: str, written: str) -> bool:
        if len(correct) - len(written) >= 2:
            return True
        return False


    @staticmethod
    def classify(correct: str, written: str) -> str:
        if correct == written:
            return "без ошибки"

        softness = SoftnessErrorAnalyzer.analyze(correct, written)
        if softness:
            return softness

        phonetic = PhoneticConfusionAnalyzer.analyze(correct, written)
        if phonetic:
            return phonetic

        if ErrorClassifier.is_letter_perseveration(correct, written):
            return "персеверация (буква)"

        if ErrorClassifier.is_letter_insertion(correct, written):
            return "вставка буквы"

        if ErrorClassifier.is_letter_omission(correct, written):
            return "пропуск буквы"

        if ErrorClassifier.is_anticipation(correct, written):
            return "антиципация"

        if ErrorClassifier.is_transposition(correct, written):
            return "перестановка букв"

        if ErrorClassifier.is_syllable_omission(correct, written):
            return "пропуск слога"

        return "другое"