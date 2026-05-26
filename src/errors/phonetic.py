from src.config import (VOICED, VOICELESS, SIBILANTS, HUSHING, AFFRICATES,
                        AFFRICATE_COMPONENTS, LABIAL_VOWELS, GRAPHIC_SIMILAR_PAIRS)

_HUSHING_VOICING_PAIRS = frozenset({("ж", "ш"), ("ш", "ж")})


class PhoneticConfusionAnalyzer:
    """
    Классификатор фонетических смешений (дисграфия, класс A).
    Требует ровно 1 различие при одинаковой длине слов.
    Возвращает None для нераспознанных пар — чтобы антиципация могла сработать.
    """

    @staticmethod
    def analyze(correct: str, written: str) -> str | None:
        if len(correct) != len(written):
            return None

        diffs = [(c, w) for c, w in zip(correct, written) if c != w]
        if len(diffs) != 1:
            return None

        c, w = diffs[0]

        # ж-ш: оба шипящих — смешение внутри группы (до проверки зв/гл)
        if (c, w) in _HUSHING_VOICING_PAIRS:
            return "Смешения свистящих-шипящих"

        # Звонкий - глухой
        if (c in VOICED and w in VOICELESS) or (c in VOICELESS and w in VOICED):
            return "Смешения звонких-глухих согласных"

        # Свистящий - шипящий
        if (c in SIBILANTS and w in HUSHING) or (c in HUSHING and w in SIBILANTS):
            return "Смешения свистящих-шипящих"

        # Аффриката - компонент
        if c in AFFRICATES and w in AFFRICATE_COMPONENTS.get(c, set()):
            return "Смешения аффрикат и их компонентов"
        if w in AFFRICATES and c in AFFRICATE_COMPONENTS.get(w, set()):
            return "Смешения аффрикат и их компонентов"

        # Лабиализованные гласные
        if LABIAL_VOWELS.get(c) == w:
            return "Смешения лабиализованных гласных О-У"

        # Графически сходные пары вынесены в финальный фолбэк classifier.py,
        # ПОСЛЕ проверок антиципации/персеверации, иначе пара ё-е (или ы-и)
        # ошибочно перехватывает антиципационные подмены.

        return None
