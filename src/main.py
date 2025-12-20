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


# примеры текстов для анализа
# Написанный: я хчу попить ммолоко и птом пойти в шоклу потому  сегодня хоршая погода и дврево зелёное и хоросо живёца и блохие учиделя и мьягкие конфеты и ещьо там троики
# Задуманный: я хочу попить молоко и потом пойти в школу потому что сегодня хоршая погода и дерево зелёное и хорошо живётся и плохие учителя и мягкие конфеты и ещё там тройки