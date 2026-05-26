import pymorphy3

# не используется в этой версии проекта
class MorphAnalyzerWrapper:
    def __init__(self):
        self.morph = pymorphy3.MorphAnalyzer()

    def normalize(self, word: str) -> str:
        parse = self.morph.parse(word)
        return parse[0].normal_form if parse else word

    def is_known_word(self, word: str) -> bool:
        return bool(self.morph.parse(word))