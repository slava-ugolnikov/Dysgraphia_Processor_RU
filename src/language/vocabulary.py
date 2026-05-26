import pymorphy3
from wordfreq import top_n_list


class Vocabulary:
    def __init__(self, size: int = 30000):
        """
        size — сколько самых частотных слов брать
        """
        self.morph = pymorphy3.MorphAnalyzer()
        self.words = self._build_vocab(size)

    def _build_vocab(self, size: int) -> set[str]:
        vocab = set()

        for word in top_n_list("ru", size):
            parsed = self.morph.parse(word)
            if not parsed:
                continue

            lemma = parsed[0].normal_form
            vocab.add(lemma)

        return vocab

    def contains(self, word: str) -> bool:
        lemma = self.morph.parse(word)[0].normal_form
        return lemma in self.words
