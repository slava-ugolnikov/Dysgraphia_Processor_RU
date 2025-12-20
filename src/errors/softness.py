from src.config import HARD_CONSONANTS, VOWEL_PAIRS, SOFTENING_VOWELS, IOTATED


class SoftnessErrorAnalyzer:
    @staticmethod
    def _missed_soft_sign_after_consonant(correct, written):
        if "ь" not in correct or "ь" in written:
            return False

        for i in range(len(correct)):
            if correct[i] == "ь":
                if i > 0 and correct[i - 1] in HARD_CONSONANTS:
                    candidate = correct[:i] + correct[i + 1:]
                    if candidate == written:
                        return True
        return False

    @staticmethod
    def _iotated_replaced(correct, written):
        if len(correct) != len(written):
            return False

        for c, w in zip(correct, written):
            if c in VOWEL_PAIRS and VOWEL_PAIRS[c] == w:
                return True
        return False

    @staticmethod
    def _mixed_softness_methods(correct, written):
        patterns = ["ьа", "ьу", "ьо", "ьэ", "ья", "ью", "ьё", "ье", "ь"]

        for p in patterns:
            if p in written and any(v in correct for v in SOFTENING_VOWELS):
                return True
        return False

    @staticmethod
    def _confusion_j_and_iotated(correct, written):
        pairs = {
            "й": IOTATED,
            **{v: {"й"} for v in IOTATED}
        }

        if len(correct) != len(written):
            return False

        for c, w in zip(correct, written):
            if c in pairs and w in pairs[c]:
                return True
        return False

    @staticmethod
    def _missing_separating_soft_sign(correct, written):
        if "ь" not in correct:
            return False

        for i in range(len(correct)):
            if correct[i] == "ь":
                if (
                        i > 0 and
                        i < len(correct) - 1 and
                        correct[i + 1] in IOTATED
                ):
                    candidate = correct[:i] + correct[i + 1:]
                    if candidate == written:
                        return True
        return False

    @staticmethod
    def analyze(correct: str, written: str) -> str | None:
        # работаем только с близкими по длине словами
        if abs(len(correct) - len(written)) > 2:
            return None

        # Пропуск Ь после твёрдого согласного (дожд -> дождь)
        if SoftnessErrorAnalyzer._missed_soft_sign_after_consonant(correct, written):
            return "нарушение обозначения мягкости (пропуск Ь)"

        # Йотированная -> нейотированная (мягкий -> магкий)
        if SoftnessErrorAnalyzer._iotated_replaced(correct, written):
            return "нарушение обозначения мягкости йотированной гласной"

        # Смешение способов обозначения мягкости
        if SoftnessErrorAnalyzer._mixed_softness_methods(correct, written):
            return "смешение способов обозначения мягкости"

        # Смешение Й и йотированных гласных
        if SoftnessErrorAnalyzer._confusion_j_and_iotated(correct, written):
            return "смешение Й и йотированных гласных"

        # Пропуск разделительного Ь (друзя -> друзья)
        if SoftnessErrorAnalyzer._missing_separating_soft_sign(correct, written):
            return "пропуск разделительного Ь"

        return None