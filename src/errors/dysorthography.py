"""
dysorthography.py — модуль классификации дизорфографических ошибок.

Реализованные правила:
D1  Безударная гласная в корне
D2  Парные глухие-звонкие согласные в корне
       ассимиляция внутри слова (гладкой-глаткой)
       ИЛИ оглушение на конце слова (снег-снек)
       ИЛИ озвончение-гиперкоррекция (полоска-полозка)
D3   Смешение приставок при-/пре-
D11  Жи-ши, ча-ща, чу-щу
D13  Непроизносимые согласные в корне
D14  Правописание приставок с з-/с- (без-/бес-, раз-/рас- и др.)
D15  Правописание неизменяемых приставок (по-, под-, от- и др.)
D16  Безударные падежные окончания существительных
D17  Безударные падежные окончания прилагательных
D18  Безударные окончания глаголов
D19  Правописание суффиксов
D20  Ь — грамматический показатель (женский род, императив;
       включает ь после шипящих как грамматический маркер)
D22  Непроверяемые написания (словарные слова)

Удалены (не в актуальной спецификации):
  Ъ разделительный (D4)
  Не-/ни- (D5)
  Удвоенные согласные (D6)
  -тся/-ться (D8)
"""

import re
import pymorphy3

_morph = pymorphy3.MorphAnalyzer()

# Константы 

VOWELS = frozenset("аеёиоуыэюя")

VOICED_CONSONANTS    = frozenset("бвгджзлмнрй")
VOICELESS_CONSONANTS = frozenset("пфктшсхцчщ")
VOICED_TO_VOICELESS  = {"б":"п","в":"ф","г":"к","д":"т","ж":"ш","з":"с"}
VOICELESS_TO_VOICED  = {v: k for k, v in VOICED_TO_VOICELESS.items()}

SHIBILANTS = frozenset("жшщч")

# Правила жи-ши, ча-ща, чу-щу, чк-чн
ZHI_SHI_RULES: list[tuple[frozenset, str, str]] = [
    (frozenset("жш"), "и", "ы"),   # жи-ши: ы-и
    (frozenset("чщ"), "а", "я"),   # ча-ща: я-а
    (frozenset("чщ"), "у", "ю"),   # чу-щу: ю-у
    (frozenset("ч"),  "н", "ьн"),  # чн без ь: формальный маркер
]

# Кластеры непроизносимых согласных
SILENT_CLUSTERS: list[tuple[str, str, str]] = [
    ("стн",  "т",  "сн"),
    ("здн",  "д",  "зн"),
    ("лнц",  "л",  "нц"),
    ("рдц",  "д",  "рц"),
    ("вств", "в",  "ств"),
    ("нтск", "т",  "нск"),
    ("ндск", "д",  "нск"),
    ("стл",  "т",  "сл"),
    ("знь",  "з",  "нь"),
    ("стск", "т",  "сск"),
]

# Изменяемые приставки (з/с на конце)
ALTERNATING_PREFIXES: list[tuple[str, str]] = [
    ("без",   "бес"),
    ("из",    "ис"),
    ("раз",   "рас"),
    ("воз",   "вос"),
    ("вз",    "вс"),
    ("через", "черес"),
]

# Неизменяемые приставки
FIXED_PREFIXES: list[str] = [
    "по", "под", "над", "на", "за", "вы", "у", "о", "об",
    "от", "до", "с", "со", "в", "пере", "про",
]

# Суффиксы существительных и прилагательных
NOUN_SUFFIXES_RULES: list[tuple[str, str]] = [
    ("чик",  "щик"),
    ("щик",  "чик"),
    ("ёнок", "онок"),
    ("онок", "ёнок"),
    ("ек",   "ик"),
    ("ик",   "ек"),
]

# Словарные слова
VOCABULARY_WORDS: frozenset[str] = frozenset({
    "корова", "ворона", "собака", "лисица", "медведь", "заяц",
    "берёза", "рябина", "малина", "капуста", "морковь", "огурец",
    "ребята", "учитель", "тетрадь", "карандаш", "пенал", "портфель",
    "деревня", "улица", "москва", "россия", "народ",
    "работа", "суббота", "завтра", "сегодня", "потому", "поэтому",
    "однажды", "вдруг", "скоро", "опять", "снова",
    "хорошо", "плохо", "сильно", "быстро", "далеко", "близко",
    "пальто", "платок", "сапоги", "посуда",
    "воробей", "петух", "корзина", "яблоко", "помидор",
    "трактор", "автобус", "дорога", "машина",
    "погода", "мороз", "ветер", "облако",
    "здравствуй", "спасибо", "пожалуйста", "товарищ",
    "тарелка", "кораблик", "словно", "рядом", "диктант",
})

VOCABULARY_MISSPELLINGS: dict[str, str] = {
    "карова":  "корова",
    "варона":  "ворона",
    "сабака":  "собака",
    "субота":  "суббота",
    "сиводня": "сегодня",
    "севодня": "сегодня",
    "патому":  "потому",
    "воробий": "воробей",
    "яблака":  "яблоко",
    "машена":  "машина",
    "тиреть":  "тетрадь",
    "дектанд": "диктант",
}


# Вспомогательные функции 

def _parse(word: str):
    return _morph.parse(word.lower())[0]

def _get_diffs(correct: str, written: str) -> list[tuple[int, str, str]]:
    if len(correct) != len(written):
        return []
    return [(i, c, w) for i, (c, w) in enumerate(zip(correct, written)) if c != w]


#  D1: Безударная гласная в корне 

def _is_unstressed_vowel_error(correct: str, written: str) -> bool:
    """
    D1. Безударная гласная в корне.
    Все различия — гласные из пар {о-а, е-и, я-е/и}.
    Пары мягкости (я-а, ё-о, е-э, ю-у) исключены.
    """
    UNSTRESSED_SUBS = {
        "о": frozenset({"а"}),
        "а": frozenset({"о"}),
        "е": frozenset({"и", "я"}),
        "и": frozenset({"е"}),
        "я": frozenset({"е", "и"}),
    }
    diffs = _get_diffs(correct, written)
    if not diffs:
        return False
    for _, c, w in diffs:
        if c not in VOWELS or w not in VOWELS:
            return False
        if w not in UNSTRESSED_SUBS.get(c, frozenset()):
            return False
    SOFTNESS_PAIRS = {"я": "а", "ё": "о", "е": "э", "ю": "у"}
    if all(SOFTNESS_PAIRS.get(c) == w for _, c, w in diffs):
        return False
    return True


#  D2: Парные глухие-звонкие согласные в корне

def _is_paired_consonant_error(correct: str, written: str) -> bool:
    """
    D2. Парные глухие-звонкие согласные в корне.

    Объединяет три случая:
    A) Оглушение на конце слова: снег-снек (last pos, звонкий-глухой).
    B) Оглушение/озвончение внутри слова: гладкой-глаткой, полоска-полозка.
       Позиция строго внутри (не первая, не последняя).
       Требует соседнего согласного (контекст ассимиляции).
    C) Оглушение конечного согласного НЕ у последней позиции, но перед
       тихим окончанием (красиф вместо красив — в исходе, но не абсолютный конец).
    """
    if len(correct) != len(written):
        return False
    diffs = _get_diffs(correct, written)
    if len(diffs) != 1:
        return False
    i, c_char, w_char = diffs[0]

    is_devoicing = VOICED_TO_VOICELESS.get(c_char) == w_char
    is_voicing   = VOICED_TO_VOICELESS.get(w_char) == c_char
    if not (is_devoicing or is_voicing):
        return False

    # A) Конец слова
    if i == len(correct) - 1:
        return True

    # B) Внутри слова, не первая позиция + контекст согласного
    if i > 0:
        neighbors = [correct[i - 1]]
        if i < len(correct) - 1:
            neighbors.append(correct[i + 1])
        if any(n in VOICED_CONSONANTS or n in VOICELESS_CONSONANTS for n in neighbors):
            return True

    return False


#  D3: Смешение при-/пре- 

def _is_prefix_pri_pre_confusion(correct: str, written: str) -> bool:
    """D3. Смешение приставок при- и пре-."""
    c_lo, w_lo = correct.lower(), written.lower()
    if c_lo.startswith("при") and w_lo.startswith("пре") and c_lo[3:] == w_lo[3:]:
        return True
    if c_lo.startswith("пре") and w_lo.startswith("при") and c_lo[3:] == w_lo[3:]:
        return True
    return False


#  D11: Жи-ши, ча-ща, чу-щу 

def _is_zhi_shi_error(correct: str, written: str) -> bool:
    """D11. Ошибки в сочетаниях жи-ши, ча-ща, чу-щу."""
    diffs = _get_diffs(correct, written)
    if len(diffs) != 1:
        return False
    i, c_char, w_char = diffs[0]
    if i == 0:
        return False
    prev = correct[i - 1]
    for consonants, right_vowel, wrong_vowel in ZHI_SHI_RULES:
        if prev in consonants and c_char == right_vowel and w_char == wrong_vowel:
            return True
    return False


#  D13: Непроизносимые согласные

def _is_silent_consonant_error(correct: str, written: str) -> bool:
    """
    D13. Пропуск или вставка непроизносимого согласного.
    постный-посный (пропуск т), чудесный-чудестный (вставка т).
    """
    c_lo = correct.lower()
    w_lo = written.lower()

    if len(correct) - len(written) == 1:
        for full_cluster, silent, reduced in SILENT_CLUSTERS:
            if full_cluster in c_lo:
                idx = c_lo.index(full_cluster)
                if c_lo[:idx] + reduced + c_lo[idx + len(full_cluster):] == w_lo:
                    return True

    if len(written) - len(correct) == 1:
        for full_cluster, silent, reduced in SILENT_CLUSTERS:
            if reduced in c_lo:
                idx = c_lo.index(reduced)
                if c_lo[:idx] + full_cluster + c_lo[idx + len(reduced):] == w_lo:
                    return True

    return False


#  D14: Приставки с з-/с-

def _is_alternating_prefix_error(correct: str, written: str) -> bool:
    """D14. Смешение вариантов без-/бес-, раз-/рас-, из-/ис- и др."""
    c_lo, w_lo = correct.lower(), written.lower()
    for pref_z, pref_s in ALTERNATING_PREFIXES:
        if c_lo.startswith(pref_z) and w_lo.startswith(pref_s) and c_lo[len(pref_z):] == w_lo[len(pref_s):]:
            return True
        if c_lo.startswith(pref_s) and w_lo.startswith(pref_z) and c_lo[len(pref_s):] == w_lo[len(pref_z):]:
            return True
    return False


#  D15: Неизменяемые приставки 

def _is_fixed_prefix_error(correct: str, written: str) -> bool:
    """D15. Ошибка в написании неизменяемой приставки (по-, под-, от- и др.).

    Жёсткие требования: остаток должен парситься как полнозначное слово
    (NOUN/VERB/INFN/ADJF/PRTF/ADVB) с высоким score; иначе любая ошибка
    в первой букве слова ошибочно классифицируется как «приставка».
    """
    OPEN_POS = {"NOUN", "VERB", "INFN", "ADJF", "ADJS", "PRTF", "PRTS", "ADVB"}
    c_lo, w_lo = correct.lower(), written.lower()
    for pref in sorted(FIXED_PREFIXES, key=len, reverse=True):
        if c_lo.startswith(pref):
            stem = c_lo[len(pref):]
            if len(stem) < 4:
                continue
            for plen in range(max(1, len(pref) - 1), len(pref) + 2):
                w_pref = w_lo[:plen]
                w_stem = w_lo[plen:]
                if w_stem == stem and w_pref != pref:
                    diff_count = sum(1 for a, b in zip(pref, w_pref) if a != b)
                    diff_count += abs(len(pref) - len(w_pref))
                    if diff_count != 1:
                        continue
                    # Остаток должен быть знаменатльной частью речи c высоким score
                    try:
                        p = _morph.parse(stem)[0]
                        if str(p.tag.POS) in OPEN_POS and p.score > 0.5:
                            # И «неправильная» приставка тоже должна быть в списке
                            if w_pref in FIXED_PREFIXES:
                                return True
                    except Exception:
                        pass
    return False


#  D16: Падежные окончания существительных 

def _is_noun_case_ending_error(correct: str, written: str) -> bool:
    """D16. Ошибочное написание безударного падежного окончания существительного.
    Срабатывает только при равной длине — пропуск буквы это не ошибка окончания.
    """
    if len(correct) != len(written):
        return False
    try:
        p = _parse(correct)
        if p.tag.POS != "NOUN":
            return False
        if p.tag.case in (None, "nomn"):
            return False
        min_len = min(len(correct), len(written))
        if correct[:min_len - 3] != written[:min_len - 3] and correct[:min_len - 2] != written[:min_len - 2]:
            return False
        w_p = _parse(written)
        if w_p.tag.POS != "NOUN":
            return True
        if w_p.normal_form == p.normal_form and w_p.tag.case != p.tag.case and correct != written:
            return True
    except Exception:
        pass
    return False


#  D17: Падежные окончания прилагательных

def _is_adjective_case_ending_error(correct: str, written: str) -> bool:
    """D17. Ошибочное написание падежного окончания прилагательного."""
    c_lo, w_lo = correct.lower(), written.lower()

    ADJ_ENDING_PAIRS: list[tuple[str, str]] = [
        ("ого",  "ово"),  ("его",  "ево"),
        ("ово",  "ого"),  ("ево",  "его"),
        ("ому",  "аму"),  ("ому",  "ему"),
        ("ему",  "аму"),  ("ему",  "ому"),
        ("ой",   "ый"),   ("ой",   "ий"),
        ("ый",   "ой"),   ("ий",   "ой"),
        ("ыми",  "ими"),  ("ими",  "ыми"),
        ("ыми",  "ами"),  ("ыми",  "оми"),  # зелёнами/зелёноми
        ("ими",  "ами"),  ("ими",  "оми"),
        ("ых",   "их"),   ("их",   "ых"),
        ("ую",   "юю"),   ("ую",   "аю"),
        ("ами",  "оми"),  ("оми",  "ами"),
        # Им. падеж мн. число и сред. род
        ("ые",   "ыи"),   ("ые",   "ое"),   ("ие",   "ии"),
        ("ие",   "ее"),   ("ое",   "ые"),   ("ее",   "ие"),
        # Предложный/творит. ед.ч.
        ("ом",   "ам"),   ("ом",   "ем"),   ("ам",   "ом"),
    ]

    for c_end, w_end in ADJ_ENDING_PAIRS:
        if (c_lo.endswith(c_end) and w_lo.endswith(w_end) and
                c_lo[:-len(c_end)] == w_lo[:-len(w_end)]):
            return True

    try:
        p = _parse(correct)
        if "Adjf" not in str(p.tag) and "Adjs" not in str(p.tag):
            return False
        if p.tag.case in (None, "nomn"):
            return False
        min_len = min(len(c_lo), len(w_lo))
        if c_lo[:min_len - 3] != w_lo[:min_len - 3]:
            return False
        w_p = _parse(written)
        if "Adjf" not in str(w_p.tag) and "Adjs" not in str(w_p.tag):
            return True
    except Exception:
        pass
    return False


#  D18: Безударные окончания глаголов

def _is_verb_ending_error(correct: str, written: str) -> bool:
    """
    D18. Безударное окончание глагола.
    Включает: -ет/-ит, -ешь/-ишь, -ют/-ят, -ем/-им, -ете/-ите,
    -ут/-ат, -овать/-евать, -или/-ели.
    """
    c_lo, w_lo = correct.lower(), written.lower()
    VERB_PAIRS: list[tuple[str, str]] = [
        ("ет",    "ит"),  ("ит",    "ет"),
        ("ешь",   "ишь"), ("ишь",   "ешь"),
        ("ют",    "ят"),  ("ят",    "ют"),
        ("ем",    "им"),  ("им",    "ем"),
        ("ете",   "ите"), ("ите",   "ете"),
        ("ут",    "ат"),  ("ат",    "ут"),
        ("овать", "евать"), ("евать", "овать"),
        ("или",   "ели"), ("ели",   "или"),
        # Краткие причастия и формы глагольной парадигмы
        ("ят",    "ет"),  ("ет",    "ят"),
        ("ит",    "ет"),  # ходит-ходет
        ("ают",   "ают"),  # no-op safety
    ]
    for c_end, w_end in VERB_PAIRS:
        if (c_lo.endswith(c_end) and w_lo.endswith(w_end) and
                c_lo[:-len(c_end)] == w_lo[:-len(w_end)]):
            return True
    return False


#  D19: Суффиксы

def _is_suffix_error(correct: str, written: str) -> bool:
    """D19. Ошибки в написании суффиксов (-чик/-щик, -ёнок/-онок, -ек/-ик и др.)."""
    c_lo, w_lo = correct.lower(), written.lower()
    for c_suf, w_suf in NOUN_SUFFIXES_RULES:
        if c_suf in c_lo and w_suf in w_lo:
            try:
                c_stem = c_lo[:c_lo.rindex(c_suf)]
                w_stem = w_lo[:w_lo.rindex(w_suf)]
                c_tail = c_lo[c_lo.rindex(c_suf) + len(c_suf):]
                w_tail = w_lo[w_lo.rindex(w_suf) + len(w_suf):]
                if c_stem == w_stem and c_tail == w_tail and len(c_stem) >= 2:
                    return True
            except ValueError:
                pass

    if len(correct) == len(written):
        diffs = _get_diffs(c_lo, w_lo)
        if len(diffs) == 1:
            i, c_ch, w_ch = diffs[0]
            # Суффиксная гласная: ов-ев (как раньше) и ов-ав
            # (типичная ошибка в глагольном суффиксе -ова-/-ева-)
            pair = {c_lo[i:i + 2], w_lo[i:i + 2]}
            if pair in ({"ов", "ев"}, {"ов", "ав"}):
                return True
    return False


#  D20: Ь — грамматический показатель

def _is_grammatical_soft_sign_error(correct: str, written: str) -> bool:
    """
    D20. Ь как грамматический показатель.

    Случай A: ь после шипящих (ночь-ноч, идёшь-идёш) —
              существительные ж.р. или глаголы 2 л. ед.ч. / инфинитив.
    Случай B: ь у существительных 3-го склонения, не после шипящего
              (тетрадь-тетрад, лошадь-лошад).
    Случай C: лишний ь у существительных муж./ср. рода.
    """
    c_lo, w_lo = correct.lower(), written.lower()

    # A и B: пропуск ь в конце
    if c_lo.endswith("ь") and w_lo == c_lo[:-1]:
        try:
            p = _parse(correct)
            if p.tag.POS == "NOUN" and p.tag.gender == "femn":
                return True
            if p.tag.POS in ("VERB", "INFN"):
                return True
        except Exception:
            return True  # консервативно

    # C: лишний ь
    if w_lo.endswith("ь") and c_lo == w_lo[:-1]:
        try:
            p = _parse(correct)
            if p.tag.POS == "NOUN" and p.tag.gender in ("masc", "neut"):
                return True
        except Exception:
            pass

    return False


#  D22: Словарные слова

def _is_vocabulary_word_error(correct: str, written: str) -> bool:
    """D22. Непроверяемые написания (словарные слова).

    Проверяем как точное вхождение, так и по лемме correct — потому что
    словарь хранит начальные формы (тарелка), а в тексте встречается
    «тарелками».
    """
    c_lo = correct.lower()
    w_lo = written.lower()

    if w_lo in VOCABULARY_MISSPELLINGS and VOCABULARY_MISSPELLINGS[w_lo] == c_lo:
        return True

    if len(c_lo) != len(w_lo) or c_lo == w_lo:
        return False

    # Различия — все гласные (типичный признак неударной гласной в словарном слове)
    diffs = [(cc, ww) for cc, ww in zip(c_lo, w_lo) if cc != ww]
    if not diffs or not all(cc in VOWELS and ww in VOWELS for cc, ww in diffs):
        return False

    # Прямое попадание в словарь
    if c_lo in VOCABULARY_WORDS:
        return True
    # По лемме
    try:
        lemma = _morph.parse(c_lo)[0].normal_form
        if lemma in VOCABULARY_WORDS:
            return True
    except Exception:
        pass
    return False



class DysorthographyAnalyzer:
    """
    Классификатор дизорфографических ошибок.
    Правила применяются в строгом порядке приоритета.
    Возвращает строку-метку или None.
    """

    _RULES: list[tuple[str, object]] = [
        # 1. Фундаментальные фонетико-орфографические — ДО морфологии.
        #    Это правила графического типа: вне зависимости от позиции
        #    в слове, ы после ж/ш или я/ю после ч/щ — всегда жи-ши.
        ("Жи-ши, ча-ща, чу-щу, чк-чн",                    _is_zhi_shi_error),
        ("Непроизносимые согласные в корне",              _is_silent_consonant_error),

        # 2. Приставочные правила — структурно «привязаны» к началу слова.
        ("Правописание приставок",                        _is_prefix_pri_pre_confusion),
        ("Правописание приставок",                        _is_alternating_prefix_error),
        ("Правописание приставок",                        _is_fixed_prefix_error),

        # 3. Суффиксы
        ("Правописание суффиксов",                        _is_suffix_error),

        # 4. Ь — грамматический показатель (включает ь после шипящих).
        #    В экспертной разметке отдельной метки нет — всё лежит под
        #    «Нарушения обозначения мягкости согласных при помощи Ь».
        ("Нарушения обозначения мягкости согласных при помощи Ь",
                                                          _is_grammatical_soft_sign_error),

        # 5. Безударные окончания (после жи-ши и суффиксов)
        ("Безударные окончания глаголов",                 _is_verb_ending_error),
        ("Безударные падежные окончания прилагательных",  _is_adjective_case_ending_error),
        ("Безударные падежные окончания сущ.",            _is_noun_case_ending_error),

        # 6. Парные согл. в корне (оглушение/озвончение)
        ("Парные глухие-звонкие согласные в корне",       _is_paired_consonant_error),

        # 7. Словарные слова — до безударной гласной
        ("Непроверяемые написания",                       _is_vocabulary_word_error),

        # 8. Безударная гласная — самый последний
        ("Безударные гласные в корне",                    _is_unstressed_vowel_error),
    ]

    @classmethod
    def analyze(cls, correct: str, written: str) -> str | None:
        if correct == written:
            return None
        c = correct.lower().strip()
        w = written.lower().strip()
        for label, rule_fn in cls._RULES:
            try:
                if rule_fn(c, w):
                    return label
            except Exception:
                continue
        return None
