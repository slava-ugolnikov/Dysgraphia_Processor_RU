from src.errors.softness import SoftnessErrorAnalyzer
from src.errors.phonetic import PhoneticConfusionAnalyzer
from src.errors.dysorthography import DysorthographyAnalyzer
from difflib import SequenceMatcher


class ErrorClassifier:
    """
    Многоуровневый классификатор ошибок письма.

    Дисграфические категории (классы A, B):
      Персеверации, Вставки, Пропуски букв, Пропуски слогов и слов,
      Антиципации, Перестановки букв,
      ошибки мягкости (SoftnessErrorAnalyzer),
      фонетические смешения (PhoneticConfusionAnalyzer).

    Дизорфографические категории (класс E):
      DysorthographyAnalyzer (правила D1–D22 по актуальной спецификации).

    Приоритет:
    1.  Непроизносимые согл. 
    2.  Персеверации 
    3.  Вставки 
    4.  SoftnessErrorAnalyzer
    5.  Пропуски 
    6.  Пропуски слогов 
    7.  Дизорфография 
    8.  PhoneticConfusionAnalyzer 
    9.  Антиципация 
    10. Перестановка 
    11. Нетипичные смешения
    """

    # Структурные методы
    @staticmethod
    def is_letter_perseveration(correct: str, written: str) -> bool:
        """
        Персеверация: |written| = |correct| + 1,
        удаление одного из двух соседних одинаковых символов - correct.
        Пример: молоко-ммолоко, кошка-кошкка.
        """
        if len(written) != len(correct) + 1:
            return False
        for i in range(len(written) - 1):
            if written[i] == written[i + 1]:
                if written[:i] + written[i + 1:] == correct:
                    return True
        return False

    @staticmethod
    def is_perseveration_substitution(correct: str, written: str) -> bool:
        """
        Персеверация при одинаковой длине: 1 различие, написанная
        буква совпадает с соседней. Пример: далёком-ддлёком (а-д копирует д
        слева), красивыми-красивымм (и-м копирует м слева), лосёнком-лосённом
        (к-н копирует н слева).
        """
        if len(correct) != len(written):
            return False
        diffs = [(i, c, w) for i, (c, w) in enumerate(zip(correct, written)) if c != w]
        if len(diffs) != 1:
            return False
        i, _, w_char = diffs[0]
        if i > 0 and written[i - 1] == w_char:
            return True
        if i < len(written) - 1 and written[i + 1] == w_char:
            return True
        return False

    @staticmethod
    def is_letter_insertion(correct: str, written: str) -> bool:
        """
        Вставка буквы: |written| = |correct| + 1,
        не персеверативная.
        Пример: школа-шекола, котик-кнотик, шапка-шапска.
        """
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
        """
        Антиципация: ровно 1 различие; written[i] совпадает
        с correct[j] для некоторого j > i.
        Пример: тарелками-карелками (т-к, к есть в correct[5]).
        """
        if len(correct) != len(written):
            return False
        diffs = [(i, c, w) for i, (c, w) in enumerate(zip(correct, written)) if c != w]
        if len(diffs) != 1:
            return False
        i, _, w_char = diffs[0]
        return any(correct[j] == w_char for j in range(i + 1, len(correct)))

    @staticmethod
    def classify_context_substitution(correct: str, written: str) -> str | None:
        """
        Контекстная подмена при одинаковой длине, 1 различие.
          • Антиципации — написанная буква встречается ПОЗЖЕ в correct.
          • Персеверации — написанная буква встречается РАНЬШЕ в written
                            (т.е. писатель «застрял» на ранее написанной букве).
        Если применимы обе интерпретации — возвращаем мульти-метку
        «Антиципации; Персеверации».
        """
        if len(correct) != len(written):
            return None
        diffs = [(i, c, w) for i, (c, w) in enumerate(zip(correct, written)) if c != w]
        if len(diffs) != 1:
            return None
        i, _, w_char = diffs[0]
        anticip = any(correct[j] == w_char for j in range(i + 1, len(correct)))
        perseve = w_char in written[:i]
        if anticip and perseve:
            return "Антиципации; Персеверации"
        if anticip:
            return "Антиципации"
        if perseve:
            return "Персеверации"
        return None

    @staticmethod
    def is_transposition(correct: str, written: str) -> bool:
        """
        Перестановка (метатеза): 2 символа поменялись местами.
        Пример: школу-шоклу.
        """
        if len(correct) != len(written):
            return False
        diffs = [(i, c, w) for i, (c, w) in enumerate(zip(correct, written)) if c != w]
        if len(diffs) != 2:
            return False
        (_, c1, w1), (_, c2, w2) = diffs
        return c1 == w2 and c2 == w1

    @staticmethod
    def is_letter_omission(correct: str, written: str) -> bool:
        return len(correct) - len(written) == 1

    @staticmethod
    def _omitted_letter(correct: str, written: str) -> str | None:
        """Возвращает пропущенную букву (если ровно одна), иначе None."""
        if len(correct) - len(written) != 1:
            return None
        for i in range(len(correct)):
            if correct[:i] + correct[i + 1:] == written:
                return correct[i]
        return None

    @staticmethod
    def _label_for_omission(correct: str, written: str) -> str:
        """Гласные/согласные пропуски — раздельно."""
        VOWELS = set("аеёиоуыэюя")
        letter = ErrorClassifier._omitted_letter(correct, written)
        if letter is None:
            return "Пропуски слогов и слов"
        if letter in VOWELS:
            return "Пропуски гласных букв"
        if letter == "ь":
            # пропуск ь обрабатывается softness/D20; сюда попасть не должно
            return "Пропуски согласных букв"
        return "Пропуски согласных букв"

    @staticmethod
    def is_syllable_omission(correct: str, written: str) -> bool:
        return len(correct) - len(written) >= 2

    # Главный метод
    @staticmethod
    def classify(correct: str, written: str) -> str:
        if correct == written:
            return ""

        c = correct.lower().strip()
        w = written.lower().strip()

        # 1. Непроизносимые согласные — до проверки вставок/пропусков
        d_pre = DysorthographyAnalyzer.analyze(c, w)
        if d_pre == "Непроизносимые согласные в корне":
            return d_pre

        # 2. Персеверации (len+1, удвоение)
        if ErrorClassifier.is_letter_perseveration(c, w):
            return "Персеверации"

        # 3. Вставки (len+1, любые не-персеверативные)
        if ErrorClassifier.is_letter_insertion(c, w):
            return "Вставки"

        # 4. Ошибки мягкости
        softness = SoftnessErrorAnalyzer.analyze(c, w)
        if softness:
            return softness

        # 5. Пропуск буквы (len-1) — с дизорфографической проверкой
        if ErrorClassifier.is_letter_omission(c, w):
            dysorth = DysorthographyAnalyzer.analyze(c, w)
            if dysorth:
                return dysorth
            return ErrorClassifier._label_for_omission(c, w)

        # 6. Пропуск слога (len-2+) — аналогично
        if ErrorClassifier.is_syllable_omission(c, w):
            dysorth = DysorthographyAnalyzer.analyze(c, w)
            if dysorth:
                return dysorth
            return "Пропуски слогов и слов"

        # 7. Все дизорфографические правила (одинаковая длина)
        dysorth = DysorthographyAnalyzer.analyze(c, w)
        if dysorth:
            return dysorth

        # 8. Фонетические смешения (1 diff, определённые пары)
        phonetic = PhoneticConfusionAnalyzer.analyze(c, w)
        if phonetic:
            return phonetic

        # 9. Антиципации / Персеверации (контекст)
        ctx = ErrorClassifier.classify_context_substitution(c, w)
        if ctx:
            return ctx

        # 10. Перестановка
        if ErrorClassifier.is_transposition(c, w):
            return "Перестановки букв"

        # 11. Финальный fallback.
        if len(c) == len(w):
            diffs = sum(1 for a, b in zip(c, w) if a != b)
            if diffs == 1:
                return "Смешения графически сходных букв"

        return "Нетипичные смешения"

    # Мульти-классификация (для слов с несколькими ошибками)

    @staticmethod
    def _split_edit_ops(correct: str, written: str) -> list[tuple[str, str]]:
        """
        Разбивает (correct, written) на список «синтетических» пар,
        в каждой из которых применена ТОЛЬКО одна правка.
        Остальные позиции совпадают с correct.

        Пример: большими - балшыми
          [(большими, болшими), # о-а — безударная гласная
           (большими, болшыми), # и-ы — жи-ши после ш
           (большими, бользими)] # ь пропущен — softness
        и т.д. — по одной правке на синтез.

        Большие подряд идущие 'replace'-блоки одинаковой длины
        дополнительно разбиваются на отдельные позиции.
        """
        matcher = SequenceMatcher(a=correct, b=written, autojunk=False)
        opcodes = matcher.get_opcodes()

        # Развернём 'replace' одинаковой длины в позиционные подмены
        expanded: list[tuple[str, int, int, int, int]] = []
        for tag, i1, i2, j1, j2 in opcodes:
            if tag == "replace" and (i2 - i1) == (j2 - j1) and (i2 - i1) > 1:
                for k in range(i2 - i1):
                    expanded.append(("replace", i1 + k, i1 + k + 1, j1 + k, j1 + k + 1))
            else:
                expanded.append((tag, i1, i2, j1, j2))

        synthetic_pairs: list[tuple[str, str]] = []
        for idx, (tag, i1, i2, j1, j2) in enumerate(expanded):
            if tag == "equal":
                continue
            parts: list[str] = []
            for k, (t2, ii1, ii2, jj1, jj2) in enumerate(expanded):
                if k == idx:
                    parts.append(written[jj1:jj2])
                else:
                    parts.append(correct[ii1:ii2])
            synthetic_pairs.append((correct, "".join(parts)))
        return synthetic_pairs

    @staticmethod
    def _count_diffs(correct: str, written: str) -> int:
        """Грубое число «правок» по opcodes (без блока 'equal')."""
        matcher = SequenceMatcher(a=correct, b=written, autojunk=False)
        n = 0
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                continue
            if tag == "replace" and (i2 - i1) == (j2 - j1):
                n += i2 - i1
            else:
                n += max(i2 - i1, j2 - j1)
        return n

    @staticmethod
    def classify_multi(correct: str, written: str) -> str:
        """
        Классификация слова с возможно несколькими ошибками.
        Возвращает метки через '; ' — по одной метке на каждую обнаруженную
        правку, в порядке появления, БЕЗ дедупликации (как у эксперта:
        «Безударные гласные в корне; Безударные гласные в корне»).

        Дополнительно детектирует «Нарушения обозначения границ предложения»
        — несовпадение регистра первой буквы (correct=Заглавная,
        written=строчная или наоборот) — и приписывает эту метку первой.
        """
        if not correct or correct == written:
            return ""

        # Регистр проверяем ДО lowercase — это маркер границы предложения
        boundary = ""
        if (correct[:1].isalpha() and written[:1].isalpha()
                and correct[0].isupper() != written[0].isupper()):
            boundary = "Нарушения обозначения границ предложения"

        c = correct.lower().strip()
        w = written.lower().strip()

        # Если различался только регистр — это чистая ошибка границы
        if c == w:
            return boundary

        diff_count = ErrorClassifier._count_diffs(c, w)

        # Один эффективный edit
        if diff_count <= 1:
            base = ErrorClassifier.classify(c, w)
            if boundary and base:
                return f"{boundary}; {base}"
            return boundary or base

        # Несколько правок — декомпозиция
        labels: list[str] = []
        for c_syn, w_syn in ErrorClassifier._split_edit_ops(c, w):
            lbl = ErrorClassifier.classify(c_syn, w_syn)
            if lbl and lbl != "Нетипичные смешения":
                labels.append(lbl)

        if not labels:
            fallback = ErrorClassifier.classify(c, w)
            base = fallback or "Нетипичные смешения"
        else:
            base = "; ".join(labels)

        if boundary:
            return f"{boundary}; {base}"
        return base
