# -*- coding: utf-8 -*-
from src.globalConfig import PARSER
from src.text_exerciser.mutate.type_extract import TYPE_TAGS
import nltk
from src.text_exerciser.mutate.nlp import regulations
import re

# Major subjects in a sentence
SUBJECT = ['credential'] + [i for item in TYPE_TAGS.values() for i in item]

# Major contents for constraint
CONTENT = ['letter', 'number', 'digit', 'character', 'alphanumeric', 'lowercase', 'uppercase', 'symbol', 'lowerletter',
           'upperletter', 'word', 'latin', 'special character', 'latin letter', 'latin character', 'latin symbol',
           'alphabet',
           'space', 'numbering', 'special letter', 'special symbol', 'consecutive character', 'blank', 'year', 'point']


class GrammarTree:

    def __init__(self, sentence):
        self.origin = sentence
        count = 1
        while sentence.find('taggedascd') != -1:
            sentence = sentence.replace('taggedascd', str(count), 1)
            count += 1
        self.sentence = sentence
        self.tree = PARSER.raw_parse(self.sentence)
        self.root = list(self.tree)[0]
        self.Nodes = self.__bfs(self.root)

    def Follow(self, tags: list) -> bool:
        if len(tags) <= 1:
            return False
        each_parents = []
        for tag, seq in tags:
            current_parents = []
            if seq == 0:
                while True:
                    seq += 1
                    target = self.get_node_by_type(tag, seq)
                    if target is None:
                        break
                    if target not in current_parents:
                        current_parents.append(self.__parent(target))
            else:
                target = self.get_node_by_type(tag, seq)
                if target is None:
                    return False
                current_parents.append(self.__parent(target))
            if len(current_parents) == 0:
                return False
            each_parents.append(current_parents)
        for target in each_parents[0]:
            for j in range(1, len(each_parents)):
                if target in each_parents[j]:
                    if j == len(each_parents) - 1:
                        return True
                    continue
                break
        return False

    def Contain(self, subtag, tags: list) -> bool:
        if len(tags) == 0 or subtag is None:
            return False
        start_tag, start_seq = subtag
        roots = []
        if start_seq == 0:
            for node in self.Nodes:
                if type(node) != nltk.tree.Tree or node.label() != start_tag:
                    continue
                roots.append(node)
        else:
            root = self.get_node_by_type(start_tag, start_seq)
            if root:
                roots.append(root)
        if len(roots) == 0:
            return False
        for root in roots:
            if root is None:
                return False
            subnodes = self.__bfs(root)
            sublabels = []
            for node in subnodes:
                if type(node) == nltk.tree.Tree:
                    sublabels.append(node.label())
            for tag, seq in tags:
                if seq == 0:
                    if tag not in sublabels:
                        return False
                else:
                    current_node = self.get_node_by_type(tag, seq)
                    if current_node is None:
                        return False
                    if not self.__isSubTree(root, current_node):
                        return False
        return True

    def First(self, tag: str, seq: int) -> bool:
        subject = self.Subject(tag, seq)
        if subject != '':
            for item in SUBJECT:
                if subject.find(item) != -1:
                    return True
        return False

    def Subject(self, tag, seq) -> str:
        if seq == 0:
            seq = 1
        target = self.get_node_by_type(tag, seq)
        if target is None:
            return ''
        sub_nodes = self.__bfs(target)
        result = []
        for item in sub_nodes:
            if type(item) == str:
                result.append(item)
        return ' '.join(result)

    @staticmethod
    def get_mutate_label_from_word(word):
        if word == '':
            return 'Null', word
        for item in regulations.NUMBER:
            if re.findall(item, word):
                return "Number", word
        for item in regulations.SPECIAL:
            if re.findall(item, word):
                return "Special", word
        for item in regulations.SPACE:
            if re.findall(item, word):
                return "Space", word
        for item in regulations.UPPER_CASE:
            if re.findall(item, word):
                return "UpperCase", word
        for item in regulations.LOWER_CASE:
            if re.findall(item, word):
                return "LowerCase", word
        for item in regulations.LETTER:
            if re.findall(item, word):
                return "Letter", word
        return 'Null', word

    def get_mutate_label(self, tag: str, seq: int) -> (str, str):
        body = self.Subject(tag, seq)
        return self.get_mutate_label_from_word(body)

    def Range(self, tag, seq=0) -> int:
        digit = self.Subject(tag, seq)
        if digit.isdigit():
            return int(digit)
        else:
            for i in range(2, len(regulations.DIGIT)):
                if re.findall(regulations.DIGIT[i], digit):
                    return i - 1
            return -1

    def __bfs(self, root):
        if type(root) != nltk.tree.Tree:
            print("Error : root is not correct")
            return None
        queue = [root]
        nodes = []
        while len(queue) != 0:
            current_node = queue.pop(0)
            nodes.append(current_node)
            if type(current_node) != nltk.tree.Tree:
                continue
            for i in range(len(current_node)):
                queue.append(current_node[i])
        return nodes

    def __isSubTree(self, node1, node2):
        subTree1 = self.__bfs(node1)
        if node2 in subTree1:
            return True
        else:
            return False

    def get_node_by_type(self, tag, seq, all_flag=False):
        if seq == 0:
            seq = 1
        count = 0
        nodes = []
        for node in self.Nodes:
            if type(node) != nltk.tree.Tree:
                continue
            if node.label() == tag:
                count += 1
                nodes.append(node)
                if count == seq and not all_flag:
                    return node
        return nodes if all_flag else None

    def __parent(self, node):
        if node not in self.Nodes:
            return None
        end = self.Nodes.index(node)
        for i in range(0, end):
            if type(self.Nodes[i]) != nltk.tree.Tree:
                continue
            for j in range(len(self.Nodes[i])):
                if self.Nodes[i][j] == node:
                    return self.Nodes[i]
        return None
