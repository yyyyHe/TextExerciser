# -*- coding: utf-8 -*-
import re
import numpy as np
from nltk.tag import StanfordPOSTagger
from code.src.text_exerciser.mutate.db.db_helper import get_tags_by_type, get_type_order, get_hints_by_type, get_all_types
import difflib
from code.src import globalConfig


MODEL = globalConfig.STANFORD_TAGGER
MY_TAGGER = StanfordPOSTagger(MODEL, globalConfig.STANFORD_TAGGER_JAR)

# nlp stopwords
STOP_WORDS = {"i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", "yourself",
              "yourselves", "he", "him", "his", "himself", "she", "her", "hers", "herself", "it", "its", "itself",
              "they", "them", "their", "theirs", "themselves", "what", "which", "who", "whom", "this", "that", "these",
              "those", "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "having", "do",
              "does", "did", "doing", "a", "an", "the", "but", "if", "because", "as", "until", "while", "of", "by",
              "for", "with", "about", "against", "through", "during", "from", "out", "off", "over", "further", "then",
              "once", "here", "there", "when", "where", "why", "how", "all", "any", "each", "few", "more", "most",
              "other", "some", "such", "only", "own", "so", "than", "too", "very", "s", "t", "can", "will", "just",
              "don", "should", "now"}
STOP_WORDS.update({"edit", "button", "Edit", "edt", "verb", "signup", "enter"})

# words to keep(using nlp )
TAGS = ["NN", "CD", "NNS", "NNP"]

# keywords to keep
KEYWORDS = [
    "repeat", "Repeat", "or", "and", "Or", "And", "cc", "CC", "Email",
    "and", "at", "between", "into", "before", "after", "above", "below", "to", "up", "down", "in", "on", "under",
    "again", "both", "no", "not", "nor", "same"
]

NUM_SEED = "1234567890"
LETTER_SEED = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
SPECIAL_SEED = "!@#$%^&*()_+=-"

ALL_TYPES = get_all_types()
TYPE_TAGS = {type: get_tags_by_type(type) for type in ALL_TYPES}
TYPE_ORDER = {type: get_type_order(type) for type in ALL_TYPES}


def get_input_by_type(type: str) -> str:
    if type == 'Email':
        return globalConfig.EmailAddress
    if type == 'Phone':
        return globalConfig.PhoneNumber
    return get_hints_by_type(type)[0]


def node2strings(TextNode):
    Strings = []
    for node in TextNode:
        Strings += node.get_desc()
    return Strings


def type_regulation(edit_node, around_nodes, in_node):
    """
    Determine the type of input box
    """
    globalConfig.te_logger.info("Set type for EditNode [%s]" % (edit_node.attribute['resourceID']))
    # First determine whether it is a password
    if edit_node.attribute['password'] == 'true':
        edit_node.set_type('Password')
        return
    edit_type = 'Null'
    # Information in the input box itself
    resource_id_info_type = []
    # The information of the textInputLayout node outside the input box
    input_layout_info_type = []
    # Text information around the input box
    around_text_info_type = []
    print("---------------------------------------------------------------------", file=globalConfig.OUTPUT_MODE)
    self_desc = ' '.join(edit_node.get_desc())
    des_candi = sentence2type(self_desc)
    if des_candi is not None:
        resource_id_info_type = list(np.array(des_candi)[:, 0])
    in_text = node2strings(in_node)
    if len(in_text) != 0:
        in_text_condi = sentence2type(' . '.join(in_text))
        if in_text_condi is not None:
            input_layout_info_type = list(np.array(in_text_condi)[:, 0])
    strings = node2strings(around_nodes)
    nearby_str = ''
    if len(strings) != 0:
        nearby_str = ' . '.join(strings)
        text_candi = sentence2type(nearby_str)
        if text_candi is not None:
            around_text_info_type = list(np.array(text_candi)[:, 0])
    globalConfig.te_logger.info('Extract type %s from id_info stence %s' % (','.join(resource_id_info_type), self_desc))
    globalConfig.te_logger.info('Extract type %s from layout_info stence %s' % (','.join(input_layout_info_type), in_text))
    globalConfig.te_logger.info('Extract type %s from around_info stence %s' % (','.join(around_text_info_type), nearby_str))
    # vote
    all_detected_type = resource_id_info_type + input_layout_info_type + around_text_info_type
    if all_detected_type:
        tmp_count = {may_type: all_detected_type.count(may_type) for may_type in all_detected_type}
        max_count = max(tmp_count.values())
        may_types = [tmp for tmp in tmp_count.keys() if tmp_count[tmp] == max_count]
        if len(may_types) == 1:
            edit_type = may_types[0]
        else:
            tmp_count = {may_type: all_detected_type.index(may_type) for may_type in may_types}
            min_index = min(tmp_count.values())
            may_types = [tmp for tmp in tmp_count.keys() if tmp_count[tmp] == min_index]
            if len(may_types) == 1:
                edit_type = may_types[0]
            else:
                tmp_count = {may_type: TYPE_ORDER[may_type] for may_type in may_types}
                edit_type = min(zip(tmp_count.values(), tmp_count.keys()))
    else:
        edit_type = 'Text'
    # countrycode
    if edit_type == 'Phone' and edit_node.attribute['text'].find('+') != -1:
        edit_type = 'CountryCode'
        globalConfig.te_logger.info('Find "+" may indicate the country code for a phone')
    globalConfig.te_logger.info('Choose type [%s]' % (edit_type))
    edit_node.set_type(edit_type)


def similar(a, b):
    seq = difflib.SequenceMatcher(None, a, b)
    ratio = seq.ratio()
    return ratio


def sentence2type(sentence):
    sentence = re.sub(r'([a-z]|\d)([A-Z])', r'\1_\2', sentence)
    words = re.split(r'[^a-zA-Z0-9]\s*', sentence.lower())
    while '' in words:
        words.remove("")
    Candidate = []
    i = 0
    while i < len(words):
        currentType = []
        for type, inst in TYPE_TAGS.items():
            maxType = ""
            for keywords in inst:
                tmpType = ""
                for j in range(0, 2):
                    if i + j >= len(words):
                        break
                    if similar(keywords, ' '.join(words[i:i + j + 1])) > 0.9:
                        tmpType = ' '.join(words[i:i + j + 1])
                if len(tmpType) > len(maxType):
                    maxType = tmpType
            if maxType != "":
                currentType.append((type, maxType))
        tmp = []
        maxlen = 0
        for t in currentType:
            if len(t[1]) > maxlen:
                tmp.clear()
                maxlen = len(t[1])
                tmp.append(t)
                continue
            if len(t[1]) == maxlen:
                tmp.append(t)

        if len(tmp) != 0:
            Candidate.append(tmp[0])
            i = i + len(tmp[0][1].split(r' '))
        else:
            i += 1
    if len(Candidate) != 0:
        return Candidate
    return None


def sent2words(sentence):
    tmp = ''
    flag = 0
    for alpha in sentence:
        if alpha.isupper() and flag == 0:
            tmp += '_' + alpha
            flag = 1
        else:
            tmp += alpha
            if alpha.isalpha() and alpha.islower():
                flag = 0
    sentence = tmp
    # sentence split
    words = re.split(r'[_\-;\s]\s*', sentence)
    words = tag_filter(words)
    words = list(filter(lambda x: x.lower() not in STOP_WORDS, words))
    return words


def is_valid_word(word):
    if not word.isalpha():
        return True
    if word in KEYWORDS:
        return True
    return False


def tag_filter(words):
    while "" in words:
        words.remove("")
    temp = MY_TAGGER.tag(words)
    for item in temp:
        if is_valid_word(item[0]):
            continue
        if item[1] not in TAGS:
            words.remove(item[0])
            print("remove ", item, file=globalConfig.OUTPUT_MODE)
    return words


def find_cover_restrictions(text_nodes, edit_nodes):
    globalConfig.te_logger.info('Draw start')
    nodes = text_nodes + edit_nodes
    candidate_hint_nodes = set()
    for edit_node in edit_nodes:
        right = left = up = down = inside = 99999
        leftnode = []
        upnode = []
        downnoad = []
        innode = []
        rightnode = []
        confilict_nodes = []
        globalConfig.te_logger.debug('Focuse on EditNode : [%s,%s] ' % (edit_node.attribute['resourceID'], edit_node.type))
        for textnode in nodes:
            if textnode == edit_node:
                continue
            if len(textnode.get_desc()) == 0:
                continue
            dist = edit_node.visual_distance(textnode)
            direct = edit_node.visual_direction(textnode)
            if textnode.attribute['classType'] == 'TextInputLayout' and direct != 'inside':
                continue
            globalConfig.te_logger.debug('TextNode:[%s]  Dist:[%s]   Direct:[%s]' % (
                textnode.attribute['resourceID'] + ':' + str(textnode.get_desc()), dist, direct))
            if textnode.attribute['classType'] == 'android.widget.EditText' and dist != 0:
                if direct == 'down':
                    if dist < down:
                        downnoad.clear()
                elif direct == 'up':
                    if dist < up:
                        upnode.clear()
                continue
            if direct == "down":
                if dist == down:
                    downnoad.append(textnode)
                if dist < down:
                    downnoad.clear()
                    downnoad.append(textnode)
                    down = dist
                continue
            if direct == "left":
                if dist == left:
                    leftnode.append(textnode)
                if dist < left:
                    leftnode.clear()
                    leftnode.append(textnode)
                    left = dist
                continue
            if direct == "up":
                if dist == up:
                    upnode.append(textnode)
                if dist < up:
                    upnode.clear()
                    upnode.append(textnode)
                    up = dist
                continue
            if direct == "inside":
                if dist == inside:
                    innode.append(textnode)
                if dist < inside:
                    innode.clear()
                    innode.append(textnode)
                    inside = dist
                continue
            if direct == 'right':
                if dist == right:
                    rightnode.append(textnode)
                if dist < right:
                    rightnode.clear()
                    rightnode.append(textnode)
                    right = dist
                continue
            if direct == 'invalid-position':
                confilict_nodes.append(textnode)
                continue
        around_nodes = set(upnode + downnoad + leftnode + rightnode)
        if edit_node.type == 'Null' or edit_node.type == '':
            type_regulation(edit_node, around_nodes, innode)
        candidate_hint_nodes.update(around_nodes.union(innode).union(confilict_nodes))
        candidate_hint_nodes.add(edit_node)
    globalConfig.te_logger.info('Draw complete')
    return list(candidate_hint_nodes)
