#-*- coding: utf-8 -*-

import random
import unittest
import models
import summarization.features 

doc_text = u"Człowiek z bieguna \n\n \
        Dopiero w 1909 roku człowiek zdołał dotrzeć po raz pierwszy do bieguna północnego, \
        dopiero w 1911 do południowego, a już w pół wieku później na biegunie południowym zbudowano \
        stację naukową; powstałaby jeszcze wcześniej, gdyby nie dziesięcioletnia przerwa w badaniach \
        spowodowana dwoma wojnami światowymi. Jeszcze nie dobiegło końca \"biegunowe\" stulecie, a już \
        samotne marsze do nich stały się rodzajem sportu, uprawia go wielu ludzi, w tym również kobiety. \n\n \
        Bieguny tak spowszedniały, że jeden człowiek (Marek Kamiński) był w stanie odwiedzić obydwa, pieszo, w \
        ciągu jednego roku kalendarzowego. Jednak biegunowe wyprawy, nim stały się banalne, pochłonęły wiele ofiar \
        i czasu. Zdobycie tych ekstremalnych punktów planety zajęło ludzkości dwa i pół tysiąclecia."

class TestFeatures(unittest.TestCase):

    def setUp(self):
        self.document = models.Document(doc_text)
        summarization.features.FeaturesConfig.Instance().set_stop_list("stop-list.txt")

    def test_document(self):
        self.assertEqual(len(self.document.paragraphs), 3)
        self.assertEqual(len(self.document.paragraphs[0].sentences), 1)
        self.assertEqual(len(self.document.paragraphs[1].sentences), 2)
        self.assertEqual(len(self.document.paragraphs[2].sentences), 3)

    def test_fake_feature(self):
        scores = [1,1,1,1,1,1]

        feature = summarization.features.FakeFeature()
        feature.init(self.document)

        result = []
        for paragraph_number, paragraph in enumerate(self.document.paragraphs):
            for sentence_number, sentence in enumerate(paragraph.sentences):
                result.append(feature.process(sentence, paragraph, paragraph_number, sentence_number))
        self.assertEqual(result, scores)
 
    def test_sent_special_section_feature(self):
        scores = [1,-1,-1,0,0,0]

        feature = summarization.features.SentSpecialSectionFeature()
        feature.init(self.document)

        result = []
        for paragraph_number, paragraph in enumerate(self.document.paragraphs):
            for sentence_number, sentence in enumerate(paragraph.sentences):
                result.append(feature.process(sentence, paragraph, paragraph_number, sentence_number))
        # print result
        self.assertEqual(result, scores)

    def test_para_loc_section_feature(self):
        scores = [-1,0,0,1,1,1]

        feature = summarization.features.ParaLocSectionFeature()
        feature.init(self.document)

        result = []
        for paragraph_number, paragraph in enumerate(self.document.paragraphs):
            for sentence_number, sentence in enumerate(paragraph.sentences):
                result.append(feature.process(sentence, paragraph, paragraph_number, sentence_number))
        # print result
        self.assertEqual(result, scores)

    def test_sent_loc_para_feature(self):
        scores = [0.5,-0.5, 0.0, -1.0, -0.5, 0.0]

        feature = summarization.features.SentLocParaFeature()
        feature.init(self.document)

        result = []
        for paragraph_number, paragraph in enumerate(self.document.paragraphs):
            for sentence_number, sentence in enumerate(paragraph.sentences):
                result.append(feature.process(sentence, paragraph, paragraph_number, sentence_number))
        # print result
        self.assertEqual(result, scores)

    def test_header_feature(self):
        scores = [0.5, -0.5, -0.5, -0.5, -0.5, -0.5]

        feature = summarization.features.HeaderFeature()
        feature.init(self.document)

        result = []
        for paragraph_number, paragraph in enumerate(self.document.paragraphs):
            for sentence_number, sentence in enumerate(paragraph.sentences):
                result.append(feature.process(sentence, paragraph, paragraph_number, sentence_number))
        # print result
        self.assertEqual(result, scores)

    def test_sent_in_highest_pname_feature(self):
        scores = [0.3333333333333333, 0.020833333333333332, 0.03333333333333333, 0.12, 0.06666666666666667, 0.08333333333333333]

        feature = summarization.features.SentInHighestPnameFeature()
        feature.init(self.document)

        result = []
        for paragraph_number, paragraph in enumerate(self.document.paragraphs):
            for sentence_number, sentence in enumerate(paragraph.sentences):
                result.append(feature.process(sentence, paragraph, paragraph_number, sentence_number))
        # print result
        self.assertEqual(result, scores)

    def test_sent_in_highest_title_feature(self):
        scores = [1.0, 0.0625, 0.0, 0.08, 0.0, 0.0]

        feature = summarization.features.SentInHighestTitleFeature()
        feature.init(self.document)

        result = []
        for paragraph_number, paragraph in enumerate(self.document.paragraphs):
            for sentence_number, sentence in enumerate(paragraph.sentences):
                result.append(feature.process(sentence, paragraph, paragraph_number, sentence_number))
        # print result
        self.assertEqual(result, scores)
  
    def test_tf_idf_feature(self):
        scores = [1.0, 0.0625, 0.0, 0.08, 0.0, 0.0]
        
        feature = summarization.features.TfIdfFeature()
        feature.init(self.document)

        result = []
        for paragraph_number, paragraph in enumerate(self.document.paragraphs):
            for sentence_number, sentence in enumerate(paragraph.sentences):
                result.append(feature.process(sentence, paragraph, paragraph_number, sentence_number))
        # print result
        self.assertEqual(result, scores)

if __name__ == '__main__':
    unittest.main()