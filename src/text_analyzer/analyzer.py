from difflib import SequenceMatcher

from src.language.vocabulary import Vocabulary  # from language import Vocabulary, WordReconstructor
from src.text_analyzer.tokenizer import Tokenizer  # from .tokenizer import Tokenizer
from src.language.reconstructor import WordReconstructor
from src.errors.missing_word import MissingWordDetector  # from errors import MissingWordDetector, ErrorClassifier
from src.export import ExcelExporter  # from export import ExcelExporter
from src.errors.classifier import ErrorClassifier


class TextAnalyzer:
    def __init__(self, vocabulary: Vocabulary | None = None):
        self.tokenizer = Tokenizer()
        self.vocab = vocabulary
        self.reconstructor = (
            WordReconstructor(vocabulary) if vocabulary else None
        )
        self.missing_word_detector = MissingWordDetector()
        self.exporter = ExcelExporter()

    def analyze(
        self,
        written_text: str,
        output_path: str,
        reference_text: str | None = None
    ):
        written_tokens = self.tokenizer.tokenize(written_text)
        rows = []


        # РЕЖИМ С ЭТАЛОНОМ
        if reference_text:
            ref_tokens = self.tokenizer.tokenize(reference_text)

            matcher = SequenceMatcher(None, ref_tokens, written_tokens)

            for tag, i1, i2, j1, j2 in matcher.get_opcodes():

                # Совпадение
                if tag == "equal":
                    for c, w in zip(ref_tokens[i1:i2], written_tokens[j1:j2]):
                        rows.append((c, w, "без ошибки"))

                # Замена (ошибки в словах)
                elif tag == "replace":
                    for c, w in zip(ref_tokens[i1:i2], written_tokens[j1:j2]):
                        error = ErrorClassifier.classify(c, w)
                        rows.append((c, w, error))

                # Пропуск слова
                elif tag == "delete":
                    for c in ref_tokens[i1:i2]:
                        rows.append((c, "", "пропуск слова"))

                # Лишнее слово
                elif tag == "insert":
                    for w in written_tokens[j1:j2]:
                        rows.append(("", w, "лишнее слово"))

        # РЕЖИМ БЕЗ ЭТАЛОНА
        else:
            # Ошибки внутри слов
            for w in written_tokens:
                c, error = self.reconstructor.reconstruct(w)
                rows.append((c, w, error))

            # Пропуски слов (rule-based)
            lemmas = [
                self.vocab.morph.parse(w)[0].normal_form
                for w in written_tokens
            ]

            missing_word_errors = self.missing_word_detector.detect(lemmas)
            rows.extend(missing_word_errors)

        # ЭКСПОРТ
        self.exporter.export(rows, output_path)