from src.config import (VOICED, VOICELESS, SIBILANTS, HUSHING, AFFRICATES,
                        AFFRICATE_COMPONENTS, LABIAL_VOWELS)


class PhoneticConfusionAnalyzer:

    @staticmethod
    def analyze(correct: str, written: str) -> str | None:
        if len(correct) != len(written):
            return None

        diffs = [
            (c, w)
            for c, w in zip(correct, written)
            if c != w
        ]

        if len(diffs) != 1:
            return None

        c, w = diffs[0]

        # Звонкие - глухие
        if (
            (c in VOICED and w in VOICELESS) or
            (c in VOICELESS and w in VOICED)
        ):
            return "смешение звонких и глухих согласных"

        # Свистящие - шипящие
        if (
            (c in SIBILANTS and w in HUSHING) or
            (c in HUSHING and w in SIBILANTS)
        ):
            return "смешение свистящих и шипящих"

        # Аффрикаты - их компоненты
        if c in AFFRICATES and w in AFFRICATE_COMPONENTS.get(c, set()):
            return "смешение аффрикаты и компонента"

        if w in AFFRICATES and c in AFFRICATE_COMPONENTS.get(w, set()):
            return "смешение компонента и аффрикаты"

        # Лабиализованные гласные
        if LABIAL_VOWELS.get(c) == w:
            return "смешение лабиализованных гласных"

        # Нетипичное фонетическое смешение
        if c.isalpha() and w.isalpha():
            return "нетипичное фонетическое смешение"

        return None