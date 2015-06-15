# -*- coding: utf-8 *-*
import PSIToolkit

class PSI():
    def __init__(self):
        self.segmenter = PSIToolkit.PipeRunner('segment --lang pl ! write-simple --tags segment')
        self.lemmatizer = PSIToolkit.PipeRunner('morfologik ! simple-writer --tags token;lexeme')

    def process(self, input, psi):
        return [r.strip() for r in psi.run(input).split("\n") if r.strip()]

    def segment(self, input):
        print self.process(input, self.segmenter)
        return self.process(input, self.segmenter)

    def lematize(self, input):
        return [r.lower() for r in self.process(input, self.lemmatizer)]
