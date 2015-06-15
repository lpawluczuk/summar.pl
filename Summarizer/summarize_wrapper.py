from models import Document
from summarization.summarizer import Summarizer
from summarization.features import Feature
from helpers import read_file, mkdir, load_from_file, read_file_lines
from polish_summaries_corpus_reader import read_psc_file
import codecs
import os
from enum import Enum



class SummarizationWrapper():
    def __init__(self, model, features, config):
        self.summarizer = Summarizer.Instance()
        self.summarizer.set_model(model, features, config)
        self.length = config.get_length()

    def summarize_from_file(self, file_path, length):
        """ Method performs single-document summarization using model given as parameter. """
        self.summarize(read_file(file_path), length)

    def summarize(self, text, length):
        """ Method performs single-document summarization using model given as parameter. """
        document = Document(text)

        summary = self.summarizer.create_summary(document, length)
        # print len(summary.document.paragraphs)
        # if "\n" in summary.document.sentences[0].sentence:
        # print summary.document.sentences[0].sentence[:summary.document.sentences[0].sentence.index("\n")]
        # summary = PostSummarizer().process(summary)
        # print unicode(summary)
        return summary

    # def summarize_directory(self, dir_path):
    #     directory_result_path = "summarization_result"
    #     reference_path = os.path.join(directory_result_path, "reference")
    #     system_path = os.path.join(directory_result_path, "system")
    #     mkdir(directory_result_path)
    #     mkdir(reference_path)
    #     mkdir(system_path)
    #
    #     for root, dirs, files in os.walk(dir_path, topdown=False):
    #         previous_document = None
    #         sum_lengths = []
    #         for i, name in enumerate(files):
    #             print "[Trainer] -> file: %s" % name
    #             doc_psc = read_psc_file(os.path.join(root, name), previous_document)
    #             summary = [(s[1], s[2]) for s in doc_psc.get_summary(self.length)]
    #             self.save_summary_to_file(summary,
    #                                       os.path.join(reference_path, name[2:-4] + "_reference" + str(i + 1) + ".txt"))
    #             previous_document = doc_psc
    #             sum_lengths.append(len(summary))
    #
    #         if previous_document:
    #             summary = self.summarizer.create_summary(previous_document, sum(sum_lengths) / len(sum_lengths))
    #             self.save_summary_to_file(summary.get_scored_sentences(),
    #                                       os.path.join(system_path, name[2:-4] + "_system1.txt"))

    def summarize_directory(self, dir_path):
        directory_result_path = "/home/lukasz/Projects/PracaMagisterska/experiments/tmpROUGE/Wide/rouge_summarization"
        system_path = os.path.join(directory_result_path, "system")
        mkdir(system_path)

        for root, dirs, files in os.walk(dir_path, topdown=False):
            previous_document = None
            sum_lengths = []
            for i, name in enumerate(files):
                # print "[Trainer] -> file: %s" % name
                path = os.path.join('/home/lukasz/Projects/PracaMagisterska/SummarizerApp/Summarizer/dataset_dump', os.path.join(root[root.rfind("/")+1:], name))
                path = path[:path.rfind(".")] + ".xml"
                doc_psc = load_from_file(path)
                previous_document = doc_psc
                sum_lengths.append(len([(s[1], s[2]) for s in doc_psc.get_summary(self.length)]))

            if previous_document:
                summary = self.summarizer.create_summary(previous_document, sum(sum_lengths) / len(sum_lengths))
                self.save_summary_to_file(summary.get_scored_sentences(),
                                          os.path.join(system_path, name[2:-4] + "_system1.txt"))



    def save_summary_to_file(self, summary, file_path):
        file = codecs.open(file_path, "w")
        file.write("\n".join(s[0].sentence for s in summary))
        file.close()


    def summarize_directory_using_score_dump(self, dir_path):
        directory_result_path = "/home/lukasz/Projects/PracaMagisterska/experiments/tmpROUGE/Wide/rouge_summarization"
        system_path = os.path.join(directory_result_path, "system")
        mkdir(system_path)

        for root, dirs, files in os.walk(dir_path, topdown=False):
            sum_lengths = []
            sentences = []
            for i, name in enumerate(files):
                path = os.path.join(root, name)
                if "sentences" in path:
                    # print "[Trainer] -> file: %s" % name
                    sentences = {int(s.split("\t")[0]): s.split("\t")[1] for s in read_file_lines(path)}
                    continue

                summary = read_file_lines(path)
                sum_lengths.append(sum(1.0 for s in summary if s.startswith("2.0")))

            scores = []
            results = []
            res_sum = []
            if summary:
                feats = [str(f)[24:].split(" ")[0][:-7] for f in self.summarizer.get_features()]
                for line in [s.split("|")[1] for s in summary]:
                    scores.append([float(x.split(":")[1]) for x in line[:line.rfind("%")].strip().split(" ") if x.split(":")[0].strip() in feats])
                results = {self.summarizer.model.activate(s)[0]: i for i, s in enumerate(scores)}

                for key in sorted(results, reverse=True)[:int(round((sum(sum_lengths)/len(sum_lengths))))]:
                    res_sum.append(sentences[results[key]])

                file = codecs.open(os.path.join(system_path, name[name.index("_")+1:name.index(".")] + "_system1.txt"), "w", "utf-8")
                file.write("".join(res_sum))
                file.close()
            summary = None