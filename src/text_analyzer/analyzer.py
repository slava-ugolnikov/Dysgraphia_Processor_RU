import pandas as pd
from difflib import SequenceMatcher

from src.language.vocabulary import Vocabulary
from src.text_analyzer.tokenizer import Tokenizer
from src.language.reconstructor import WordReconstructor
from src.errors.missing_word import MissingWordDetector
from src.export import ExcelExporter
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

        if reference_text:
            ref_tokens = self.tokenizer.tokenize(reference_text)
            matcher = SequenceMatcher(None, ref_tokens, written_tokens)
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag == "equal":
                    for c, w in zip(ref_tokens[i1:i2], written_tokens[j1:j2]):
                        rows.append((c, w, "без ошибки"))
                elif tag == "replace":
                    for c, w in zip(ref_tokens[i1:i2], written_tokens[j1:j2]):
                        error = ErrorClassifier.classify(c, w)
                        rows.append((c, w, error))
                elif tag == "delete":
                    for c in ref_tokens[i1:i2]:
                        rows.append((c, "", "пропуск слова"))
                elif tag == "insert":
                    for w in written_tokens[j1:j2]:
                        rows.append(("", w, "лишнее слово"))
        else:
            for w in written_tokens:
                c, error = self.reconstructor.reconstruct(w)
                rows.append((c, w, error))

            lemmas = [self.vocab.morph.parse(w)[0].normal_form for w in written_tokens]
            missing_word_errors = self.missing_word_detector.detect(lemmas)
            rows.extend(missing_word_errors)

        self.exporter.export(rows, output_path)

    # НОВЫЙ МЕТОД
    def analyze_excel(self, input_path: str, output_path: str = "auto_classified.xlsx"):
        """
        Принимает Excel (один или несколько листов) с колонками:
            «Задуманное слово», «Написанное слово»
        Добавляет колонку «Авто_Тип_ошибки» и сохраняет новый файл.
        """
        print(f"Читаем Excel: {input_path}")
        dfs = pd.read_excel(input_path, sheet_name=None)  # все листы

        for sheet_name, df in dfs.items():
            if 'Задуманное слово' not in df.columns or 'Написанное слово' not in df.columns:
                print(f"Лист «{sheet_name}» пропущен (нет нужных колонок)")
                continue

            def get_auto_error(row):
                correct = str(row['Задуманное слово']).strip() if pd.notna(row['Задуманное слово']) else ""
                written = str(row['Написанное слово']).strip() if pd.notna(row['Написанное слово']) else ""

                if not correct or correct == "nan":
                    return ""

                # Специальный случай пропуска целого слова (как в вашей разметке)
                if written in ["-", ""]:
                    return "Пропуски слогов и слов"

                return ErrorClassifier.classify(correct, written)

            df['Авто_Тип_ошибки'] = df.apply(get_auto_error, axis=1)
            print(f"Лист «{sheet_name}» обработан: {len(df)} строк")

        # Сохраняем все листы обратно
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for sheet_name, df in dfs.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)

        print(f"Готово! Результат сохранён в {output_path}")