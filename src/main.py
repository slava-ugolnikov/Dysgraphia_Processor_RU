from src.text_analyzer.analyzer import TextAnalyzer
from src.language.vocabulary import Vocabulary


if __name__ == "__main__":
    print("Режим работы:")
    print("1 — ввести задуманный текст (с эталоном)")
    print("2 — анализировать только написанный текст (без эталона)")

    mode = input("Выбор (1/2): ").strip()

    written_text = input("\nВведите написанный текст:\n")

    if mode == "1":
        reference_text = input("\nВведите задуманный текст:\n")
        analyzer = TextAnalyzer()
        analyzer.analyze(written_text, "errors.xlsx", reference_text)

    else:
        vocab = Vocabulary(size=30000)
        analyzer = TextAnalyzer(vocab)
        analyzer.analyze(written_text, "errors.xlsx")

    print("\nГотово. Результат сохранён в errors.xlsx")