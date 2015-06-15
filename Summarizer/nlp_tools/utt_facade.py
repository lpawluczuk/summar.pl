# -*- coding: utf-8 *-*
import subprocess
import re
import paths


class UTT():
    def __init__(self):
        self.tokens_list = None
        self.lemmas = None
        self.pos_tags = None

    def lematize(self, tokens_list):
        if self.tokens_list != tokens_list:
            self.tokens_list = tokens_list
            self.process_results(tokens_list)

        return self.lemmas

    def get_pos_tags(self, tokens_list):
        if self.tokens_list != tokens_list:
            self.tokens_list = tokens_list
            self.process_results(tokens_list)

        return self.pos_tags

    def process_results(self, tokens_list):
        marked_tokens, input_string = self.prepare_input(tokens_list)

        self.process = subprocess.Popen([paths.LEM_PATH, '--one-field'],stdout=subprocess.PIPE,stdin=subprocess.PIPE)
        self.process.stdin.write(input_string.encode('utf-8'))
        self.set_results(self.process.communicate()[0].split("\n"), marked_tokens)

    def set_results(self, result_list, marked_tokens):
            result_list = result_list[1:]
            lemmas = []
            pos_tags = []

            for i, token in enumerate(marked_tokens):
                if token[1] == "W" and "lem:" in result_list[i]:
                    if not "," in result_list[i]:
                        lemmas.append(result_list[i][result_list[i].index("lem:")+len("lem:"):])
                        pos_tags.append([])
                    else:
                        lemmas.append(result_list[i][result_list[i].index("lem:")+len("lem:"):result_list[i].index(",")])
                        if "/" in result_list[i]:
                            pos_tags.append(result_list[i][result_list[i].index(",")+1:result_list[i].index("/")].split(","))
                        else:
                            pos_tags.append(result_list[i][result_list[i].index(",")+1:].split(","))
                else:
                    lemmas.append(token[0])
                    pos_tags.append([])

            pos_tags = [[p[:p.index(";")] if ";" in p else p for p in pos_tag] for pos_tag in pos_tags]

            self.lemmas = lemmas
            self.pos_tags = pos_tags

    def prepare_input(self, tokens_list):
        marked_tokens_list = []
        input_string = u"0000 BOS *\n"

        for token in tokens_list:
            token_class = self.recognize_token_class(token) 
            input_string += token_class + " " + token + "\n"
            marked_tokens_list.append((token, token_class))
        input_string += u"EOS *" 
        return marked_tokens_list, input_string

    def recognize_token_class(self, token):
        """ 
        According to UTT documentation, there are five types of tokens distinguished:

        W (word) - continuous sequence of letters
        N (number) - continuous sequence of digits
        S (space) - continuous sequence of space characters
        P (punctuation mark) - single printable characters not belonging to any of the other classes
        B (unprintable character) - single unprintable character 
        """

        if re.match("\w+", token):
            return "W"
        elif re.match("\d+", token):
            return "N"
        elif re.match("\s+", token):
            return "S"
        elif re.match("[\.\,?!:\"\'\[\]\(\)]+", token):
            return "P"
        else:
            return "B"


