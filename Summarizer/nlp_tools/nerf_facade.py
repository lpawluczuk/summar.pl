#-*- coding: utf-8 -*-

from nerf.scripts import ner_service
from utt_facade import UTT
import paths


class NERF():
    def __init__(self):
        self.ner = ner_service.init_model(paths.NER_PATH)

    def recognize_ne(self, input):
        ner = ner_service.recognize(self.ner, input)
        return [(n[0], n[1][1]) for n in zip(UTT().lematize([n[0].decode("UTF-8") for n in ner]), ner)]