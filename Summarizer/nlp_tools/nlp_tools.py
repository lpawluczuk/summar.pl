# -*- coding: utf-8 *-*

# import nltk_facade as NLTK
# from utt_facade import UTT
from nerf_facade import NERF
from psitoolkit_facade import PSI
import my_tools as MY


class Singleton:
    """
    A non-thread-safe helper class to ease implementing singletons.
    This should be used as a decorator -- not a metaclass -- to the
    class that should be a singleton.

    The decorated class can define one `__init__` function that
    takes only the `self` argument. Other than that, there are
    no restrictions that apply to the decorated class.

    To get the singleton instance, use the `Instance` method. Trying
    to use `__call__` will result in a `TypeError` being raised.

    Limitations: The decorated class cannot be inherited from.

    """

    def __init__(self, decorated):
        self._decorated = decorated

    def Instance(self):
        """
        Returns the singleton instance. Upon its first call, it creates a
        new instance of the decorated class and calls its `__init__` method.
        On all subsequent calls, the already created instance is returned.

        """
        try:
            return self._instance
        except AttributeError:
            self._instance = self._decorated()
            return self._instance

    def __call__(self):
        raise TypeError('Singletons must be accessed through `Instance()`.')

    def __instancecheck__(self, inst):
        return isinstance(inst, self._decorated)


@Singleton
class NLP():
    def __init__(self):
        #self.NERF = NERF()
        self.PSI = PSI()

    def paragraphs(self, input):
        return MY.paragraphs(input)

    def segment(self, input):
        return self.PSI.segment(input)

    def tokenize_lematize_pos_tags(self, input):
        result = self.PSI.lematize(input)
        tokens = []
        lemmas = []
        pos_tags = []
        for r in result:
            x = r.split("|")
            if len(x) < 2:
                tokens.append(x[0])
                lemmas.append(x[0])
                pos_tags.append("")
            else:
                y = x[1].split("+")
                tokens.append(x[0])
                lemmas.append(y[0])
                pos_tags.append(y[1])
        return tokens, lemmas, pos_tags

    def is_header(self, sentence):
        return MY.is_header(sentence)

    def ner(self, sentence):
        return []#self.NERF.recognize_ne(sentence)
