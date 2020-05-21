# -*- coding: utf-8 -*-
import re
from src.text_exerciser.mutate import type_extract as te
from nltk import word_tokenize
from nltk.tag import StanfordPOSTagger
from nltk.stem import WordNetLemmatizer
from nltk import Tree
from src.text_exerciser.mutate.nlp.regulations import NAME_DICT
from src.text_exerciser.mutate.nlp import regulations
from nltk.corpus import stopwords
from src.globalConfig import PARSER
from src import globalConfig


MODEL = globalConfig.STANFORD_TAGGER
MY_TAGGER = StanfordPOSTagger(MODEL, globalConfig.STANFORD_TAGGER_JAR)

STOP_WORDS = {':', '.', 'the', 'a', 'e', "'", ',', '!', '?', '~', 'the', 'you', 'this', 'like', 'there', 'look', '...',
              '(', ')', '’', 'please', 'pleasae', 'inlcude', 'contain', 'contains', 'include', 'must', 'let', 'using',
              'seems', 'seem', 'pleae', 'retry', 'specified', 'hmmmm', 'oops', '0ops', 'uh', 'oh', 'whoops', 'woah',
              'sorry', 'allowed', 'following', 'required', 'requires', 'continuing', 'also', 'youve',
              'microsoft'}.union(set(stopwords.words('english')))

REMOVE_WORDS = {"couldn't", "mightn't", "shouldn't", "wfind typeouldn't", "didn't", "dosen't", "hadn't", "hasn't",
                'not',
                'no', "haven't", "isn't", "aren't", "don't", "doesn't", "can't", "doesnt", 'cannot', 'other', 'at',
                'most', 'between', 'too', 'same', 'only', 'than', 'both', 'once', 'again', 'and', 'to', 'each', 'in',
                'or', 'more', 'over', 'up', 'already', 'above'}

MY_STOP_WORDS = STOP_WORDS.difference(REMOVE_WORDS)


def tags2abs(Tags):
    new_dict = {v: k for k, v in NAME_DICT.items()}
    abstractSent = ""
    for item in Tags:
        abstractSent += new_dict[item[1]]
    return abstractSent


def lex_analysis(string):
    string = re.sub(r'[\'‘’“”]', '', string)
    for sp in re.findall(r'(?:[^\w\s\'\’]|_)', string):
        string = re.sub(r'\s*' + re.escape(sp) + r'\s*', r' ' + sp + r' ', string)
    result = []
    tmp = word_tokenize(string)
    for word in tmp:
        result.append(word2lex(word))
    return result


def word2lex(origin_word):
    word = origin_word.lower()
    lextag = ()
    ismatch = False
    if not ismatch:
        for item in regulations.OBJECT:
            if re.findall(item, origin_word):
                lextag = (word, "Object")
                ismatch = True
                break
    if not ismatch:
        for item in regulations.VALID:
            if re.findall(item, word):
                lextag = (word, "Valid")
                ismatch = True
                break
    if not ismatch:
        for item in regulations.BIGGER:
            if re.findall(item, word):
                lextag = (word, "Bigger")
                ismatch = True
                break
    if not ismatch:
        for item in regulations.SMALLER:
            if re.findall(item, word):
                lextag = (word, "Smaller")
                ismatch = True
                break
    if not ismatch:
        for item in regulations.NUMBER:
            if re.findall(item, word):
                lextag = (word, "Number")
                ismatch = True
                break
    if not ismatch:
        for item in regulations.DECORATION:
            if re.findall(item, word):
                lextag = (word, "Decoration")
                ismatch = True
                break
    if not ismatch:
        for item in regulations.SPECIAL:
            if re.findall(item, word):
                lextag = (word, "Special")
                ismatch = True
                break
    if not ismatch:
        for item in regulations.SPACE:
            if re.findall(item, word):
                lextag = (word, "Space")
                ismatch = True
                break
    if not ismatch:
        for item in regulations.LETTER:
            if re.findall(item, word):
                lextag = (word, "Letter")
                ismatch = True
                break
    if not ismatch:
        for item in regulations.EQUAL:
            if re.findall(item, word):
                lextag = (word, "Equal")
                ismatch = True
                break
    if not ismatch:
        for item in regulations.OR:
            if re.findall(item, word):
                lextag = (word, "Or")
                ismatch = True
                break
    if not ismatch:
        for item in regulations.AND:
            if re.findall(item, word):
                lextag = (word, "And")
                ismatch = True
                break
    if not ismatch:
        for item in regulations.NOT:
            if re.findall(item, word):
                lextag = (word, "Not")
                ismatch = True
                break
    if not ismatch:
        for item in regulations.TRANSITION:
            if re.findall(item, word):
                lextag = (word, "Transition")
                ismatch = True
                break
    if not ismatch:
        for item in regulations.UPPER_BOUND:
            if re.findall(item, word):
                lextag = (word, "Upperbound")
                ismatch = True
                break
    if not ismatch:
        for item in regulations.DIGIT:
            if re.findall(item, word):
                lextag = (word, "Digit")
                ismatch = True
                break
    if not ismatch:
        for item in regulations.END:
            if re.findall(item, word):
                lextag = (word, "End")
                ismatch = True
                break
    if not ismatch:
        for item in regulations.ALERT:
            if re.findall(item, word):
                lextag = (word, "Alert")
                ismatch = True
                break
    if ismatch:
        for item in regulations.LOWER_BOUND:
            if re.findall(item, lextag[1]):
                lextag = (word, "Lowerbound")
                break
        for item in regulations.BODY:
            if re.findall(item, lextag[1]):
                lextag = (word, "Body")
                break
    else:
        lextag = (word, "Null")
    return lextag


def add_toast2type(target_edit, toast):
    for x in target_edit:
        x.add_hint([toast])
    return True


def add_hint2type(edit_nodes, string, total_edit, is_textnode=True):
    """
    distribute hints to edit node via keywords mapping
    """
    candidate = te.sentence2type(string)
    globalConfig.te_logger.info('Find candidate %s in "%s"' % (str(candidate), string))
    hasTarget = False
    if candidate is not None:
        type = {}
        for item in candidate:
            if item[0] in type.keys():
                if len(type[item[0]]) < len(item[1]):
                    type[item[0]] = item[1]
                else:
                    pass
            else:
                type[item[0]] = item[1]
        for item in type.items():
            string = re.sub(r'(?i)' + str(item[1]), item[0], string)
        print("Text : " + string, file=globalConfig.OUTPUT_MODE)
        if len(type) == 1:
            typename = list(type)[0]
            target_edit = []
            for x in edit_nodes:
                if x.type.lower() == typename.lower():
                    target_edit.append(x)
            if len(target_edit) == 0:
                # may be cross view restriction
                globalConfig.te_logger.info('May be cross view')
                if total_edit:
                    for x in total_edit:
                        if bool(re.search(x.type.lower(), typename.lower())):
                            x.add_hint([string])
                            hasTarget = True
                else:
                    globalConfig.te_logger.warning('No match type [%s] in Total EditNode' % (typename))
                    print("Error : Can't find type %s in Total EditNode" % typename, file=globalConfig.OUTPUT_MODE)
            elif len(target_edit) == 1:
                # the only one
                globalConfig.te_logger.info('Find only one edit node with type [%s]' % (typename))
                x = target_edit[0]
                x.add_hint([string])
                hasTarget = True
            else:
                globalConfig.te_logger.info('Current page has more than one Edit with type [%s]' % (typename))
                if not is_textnode or typename.lower() == 'password':
                    add_toast2type(target_edit, string)
                    hasTarget = True
        else:
            tags = lex_analysis(string)
            print("Tags : ", tags, file=globalConfig.OUTPUT_MODE)
            lexical = tags2abs(tags)
            pattern = r'(?:j?[gca]*[lkj]?[gca]+)+'
            abs = re.split(r'q', lexical)
            typelist = {}
            start = 0
            for i in abs:
                if i == '':
                    continue
                if i.find(pattern) != -1:
                    end = lexical.find(i)
                    if end > 0:
                        position = 0
                        for t in re.findall(r'a', lexical[start:end]):
                            position = start + lexical[start:end].find('a', position)
                            currentType = tags[position][0]
                            if currentType in typelist.keys():
                                typelist[currentType].append(" ".join([tags[x][0] for x in range(start, end)]))
                            else:
                                typelist[currentType] = [" ".join([tags[x][0] for x in range(start, end)])]
                            position += 1
                    start = end
                else:
                    continue
            if start < len(lexical) - 1:
                end = len(lexical)
                for t in re.findall(r'a', lexical[start:end]):
                    position = start + lexical[start:end].find('a')
                    currentType = tags[position][0]
                    if currentType in typelist.keys():
                        typelist[currentType].append(" ".join([tags[x][0] for x in range(start, end)]))
                    else:
                        typelist[currentType] = [" ".join([tags[x][0] for x in range(start, end)])]
            if len(typelist) == 0:
                globalConfig.te_logger.warning('Empty typelist')
                return False
            for typename in typelist.keys():
                target_edit = []
                for x in edit_nodes:
                    if x.type.lower() == typename.lower():
                        target_edit.append(x)
                if len(target_edit) == 0:
                    globalConfig.te_logger.info("Type [%s] may cross views" % (typename))
                    if total_edit:
                        for x in total_edit:
                            if bool(re.search(x.type.lower(), typename.lower())):
                                x.add_hint(typelist[typename])
                                hasTarget = True
                    else:
                        globalConfig.te_logger.warning('No match type [%s] in Total EditNode' % (typename))
                        print("Error : Can't find type %s in Total EditNode" % typename, file=globalConfig.OUTPUT_MODE)
                elif len(target_edit) == 1:
                    globalConfig.te_logger.info('Find only one edit node with type [%s]' % (typename))
                    x = target_edit[0]
                    x.add_hint(typelist[typename])
                    hasTarget = True
                else:
                    globalConfig.te_logger.info('Current page has more than one Edit with type [%s]' % (typename))
                    if not is_textnode or typename.lower() == 'password':
                        add_toast2type(target_edit, typelist[typename])
                        hasTarget = True
    if hasTarget:
        return True
    else:
        return False


def extract_cd(sentence):
    sentence = sentence.lower()
    places = [s.start() for s in re.finditer('taggedascd_', sentence)]
    if len(places) == 0:
        return sentence, []
    cd = re.findall(r'taggedascd_(\w+)', sentence)
    filted = re.sub(r'taggedascd_([^\s\n\t]+)', 'taggedascd', sentence)
    return filted, cd


def insert_cd(sentences, cd):
    if len(cd) == 0:
        return sentences
    result = []
    i = 0
    for s in sentences:
        tmp = s.split('taggedascd')
        string = ''
        for j in range(0, len(tmp) - 1):
            if i < len(cd):
                string += tmp[j] + 'taggedascd_' + cd[i]
                i += 1
            else:
                string += tmp[j] + 'taggedascd'
        string += tmp[-1]
        result.append(string)
    return result


def pre_process(sentence):
    result = []
    sentence = sentence.strip().split()
    if len(sentence) < 2 or len(sentence) > 25:
        return ''
    sentence = ' '.join(sentence)
    tmp = remove_special(sentence)
    tmp = split_sentence(tmp)
    # paste cdTag
    for line in tmp:
        if len(line) < 2:
            continue
        result.append(line)
    while '' in result:
        result.remove('')
    return result


def remove_special(sentence):
    tmp = sentence.strip(b'\x00'.decode()).lower()
    tmp = re.sub(r"e–mail", "email", tmp)
    tmp = re.sub(r"e-mail", "email", tmp)
    tmp = re.sub(r"’", "'", tmp)
    tmp = re.sub(r"‘", "'", tmp)
    # for substring in re.findall(r'[a-zA-Z]\s?-\s?[a-zA-Z0-9]|[a-zA-Z0-9]\s?-\s?[a-zA-Z]',tmp):
    # remove -  in 4-digital, digital-4
    for substring in re.findall(r'[a-zA-Z]\s?-\s?[0-9]|[0-9]\s?-\s?[a-zA-Z]', tmp):
        targetstring1 = re.sub(r'-', ' ', substring)
        tmp = re.sub(substring, targetstring1, tmp)
        targetstring2 = re.sub(r'–', ' ', substring)
        tmp = re.sub(substring, targetstring2, tmp)
        #  enter a valid e-mail address include an '@' in the email address. 10-20
    for sp in re.findall(r'(?:[^\w\s]|_)', tmp):
        if sp == '-' or sp == '–':
            tmpstr = tmp[tmp.find(sp) - 1: tmp.find(sp)] + tmp[tmp.find(sp) + 1: tmp.find(sp) + 2]
            if tmpstr.isalpha():  # can not split e-mail, re-try
                pass
            else:
                tmp = re.sub(r'\s*' + re.escape(sp) + r'\s*', r' ' + sp + r' ', tmp)  # split 10-20 , 10 - 20
        else:
            tmp = re.sub(r'\s*' + re.escape(sp) + r'\s*', r' ' + sp + r' ', tmp)  # split '@', ' @ '
    tmp = re.sub(r'\–', '-', tmp)
    tmp = re.sub(r'\~', '-', tmp)
    tmp = re.sub(r'\_', ' ', tmp)
    tmp = re.sub('/', " ", tmp)
    tmp = re.sub(r"'", " ", tmp)
    tmp = re.sub(r"‘", " ", tmp)
    tmp = re.sub(r"’", " ", tmp)
    tmp = re.sub(r"。", " ", tmp)
    tmp = re.sub(r"“", " ", tmp)
    tmp = re.sub(r"”", " ", tmp)
    tmp = re.sub(r'"', ' ', tmp)
    tmp = re.sub(r"©", " ", tmp)
    tmp = re.sub(r"®", " ", tmp)
    tmp = re.sub(r"%", " ", tmp)
    tmp = re.sub(r"\*", " ", tmp)
    tmp = re.sub(r'✓', ' ', tmp)
    tmp = re.sub(r"\(", ' ', tmp)
    tmp = re.sub(r"\)", ' ', tmp)
    tmp = re.sub(r"\[", ' ', tmp)
    tmp = re.sub(r"\]", ' ', tmp)
    tmp.replace('\\', ' ')
    tmp.replace('...', ' ')
    return tmp.strip()


def to_lower(sentence):
    #  divide sentence like PasswordAtLeast
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
    result = tmp.lower()
    return result


def split_sentence(sentence):
    filted, cd = extract_cd(sentence)
    st = PARSER.raw_parse(filted)
    lemmatizer = WordNetLemmatizer()
    parse_tree = ''
    for line in st:
        parse_tree += str(line).strip()
        parse_tree = parse_tree.replace('\t', '')
        parse_tree = re.sub('\s+', ' ', parse_tree)
        parse_tree = parse_tree.replace('\n', '')
    # paste CD
    parse_tree = re.sub(r'(?<=\(CD)(\s)(?=\d+\))', ' TaggedAsCD_', parse_tree)
    # get root
    leaves = list(set(re.findall(r'\([A-Z]+ [^\s\)]+\)', parse_tree)))
    for leaf in leaves:
        tag = leaf.split(' ')[0][1:]
        content = leaf.split(' ')[1][:-1]
        if tag.startswith('NNS'):
            content = lemmatizer.lemmatize(content, pos='n')
            parse_tree = re.sub(leaf, '(' + tag + ' ' + content + ')', parse_tree)
    t = Tree.fromstring(parse_tree)
    subtexts = []
    for subtree in t.subtrees():
        if subtree.label() == 'S' or subtree.label() == 'SBAR' or subtree.label() == '.':
            subtexts.append(' '.join(subtree.leaves()).strip())
    string = ' '.join([w for w in t.leaves()])
    for i in range(len(subtexts)):
        if string == '':
            break
        end = string.index(subtexts[i])
        subtexts[i] = string[0:end]
        string = string[end:]
    if string != '':
        subtexts.append(string)
    for i in range(len(subtexts)):
        subtexts[i] = re.sub('\.', '', subtexts[i])
        if len(subtexts[i].strip().split()) == 1:
            if i < len(subtexts) - 1:
                subtexts[i + 1] = ''.join(subtexts[i:i + 2])
                subtexts[i] = ''
    while '' in subtexts:
        subtexts.remove('')
    return subtexts


def res_pre_process(tagged_sentence, kind: int):
    """
    modify sentence based on SubMinorCategory of hint
    """
    filter_words_for_all_kind = [r'your', r'our', r'his', r'her', r'my', r'its', r'their', r'still', r'also',
                                 r'yet', r'this', r'the', 'these', 'those', 'that', r'please']
    tagged_sentence = delete_words(tagged_sentence, filter_words_for_all_kind)
    if kind == 1:
        delete_targets = [
            'please', 'can', 'could', 'may', 'might', 'need to', 'must', 'need', 'ought to', 'dared', 'dare', 'shall',
            'should', 'will', 'would',
            'your', 'our', 'his', 'her', 'my', 'its', 'their',
            'still', 'also', 'yet',
            'be', 'are', 'is', 'am', 'were', 'was', 'being'  # be
        ]
        tagged_sentence = delete_words(tagged_sentence, delete_targets)
        abbrs = ['can t', 'haven t', 'couldn t', 'shouldn t', 'don t', 'doesn t', 'didn t', 'wouldn t', 'needn t',
                 'need not', 'can not', 'could not', 'have not', 'should not', 'do not', 'does not', 'did not']
        tagged_sentence = synonym_format(tagged_sentence, abbrs, 'not')
        synonyms = [
            'minimum of', 'minimum', 'or more', 'or above', 'or longer', 'or long', 'or over', 'greater than',
            'longer than',
            'not less than', 'no less than', 'not under', 'more than', 'not up to', 'no up to', 'over', '+'
        ]
        tagged_sentence = synonym_format(tagged_sentence, synonyms, 'at least')
        forword = ['lower', 'upper']
        backword = ['character', 'letter']
        tagged_sentence = concate(tagged_sentence, forword, backword)
        delete_targets = ['this', 'the', 'these', 'those', 'that', 'for', 'to']
        tagged_sentence = delete_words(tagged_sentence, delete_targets)
    elif kind == 2:
        delete_targets = [
            'please', 'can', 'could', 'may', 'might', 'need to', 'must', 'need', 'ought to', 'dared', 'dare', 'shall',
            'should', 'will', 'would',
            'your', 'our', 'his', 'her', 'my', 'its', 'their',
            'still', 'also', 'yet',  # adv
            'be', 'are', 'is', 'am', 'were', 'was', 'being'  # be
        ]
        tagged_sentence = delete_words(tagged_sentence, delete_targets)
        abbrs = ['can t', 'haven t', 'couldn t', 'shouldn t', 'don t', 'doesn t', 'didn t', 'wouldn t', 'needn t',
                 'need not', 'can not', 'could not', 'have not', 'should not', 'do not', 'does not', 'did not']
        tagged_sentence = synonym_format(tagged_sentence, abbrs, 'not')
        synonyms = [
            'limited', 'limit', 'under', 'maximum of', 'maximum', 'or less', 'or shorter', 'less than', 'shorter than',
            'within', 'short than', 'no greater than', 'not greater than', 'no more than', 'not longer than',
            'no longer than', 'not over', 'up to', '-'
        ]
        tagged_sentence = synonym_format(tagged_sentence, synonyms, 'at most')
        forword = ['lower', 'upper']
        backword = ['character', 'letter']
        tagged_sentence = concate(tagged_sentence, forword, backword)
        delete_targets = ['this', 'the', 'these', 'those', 'that', 'for', 'to']
        tagged_sentence = delete_words(tagged_sentence, delete_targets)
    elif kind == 3:
        delete_targets = [
            'please', 'can', 'could', 'may', 'might', 'need to', 'must', 'need', 'ought to', 'dared', 'dare', 'shall',
            'should', 'will', 'would',
            'your', 'our', 'his', 'her', 'my', 'its', 'their',
            'still', 'also', 'yet',
            'this', 'the', 'these', 'those', 'that'
        ]
        tagged_sentence = delete_words(tagged_sentence, delete_targets)
        tagged_sentence = synonym_format(tagged_sentence, ['-', '~'], 'to')
        tagged_sentence = synonym_format(tagged_sentence, ['contain'], 'have')
        tagged_sentence = synonym_format(tagged_sentence, ['input'], 'enter')
        tagged_sentence = concate(tagged_sentence, ['alphanumeric'], ['letter'])
    elif kind == 4:
        delete_targets = [
            'please', 'can', 'could', 'may', 'might', 'need to', 'must', 'need', 'ought to', 'dared', 'dare', 'shall',
            'should', 'will', 'would',
            'your', 'our', 'his', 'her', 'my', 'its', 'their',
            'still', 'also', 'yet',
            'this', 'the', 'these', 'those', 'that',
            '-', 'a'
        ]
        tagged_sentence = delete_words(tagged_sentence, delete_targets)
        tagged_sentence = synonym_format(tagged_sentence, ['pin'], 'pinnumber')
        tagged_sentence = synonym_format(tagged_sentence, ['verificationcode'], 'verificationnumber')
        tagged_sentence = concate(tagged_sentence, ['verification', 'zip'], ['code'])
        tagged_sentence = concate(tagged_sentence, ['lower', 'upper'], ['case'])
    elif kind == 5:
        delete_targets = [
            'please', 'can', 'could', 'may', 'might', 'need to', 'must', 'need', 'ought to', 'dared', 'dare', 'shall',
            'should', 'will', 'would',
            'your', 'our', 'his', 'her', 'my', 'its', 'their',
            'still', 'also', 'yet',
            'this', 'the', 'these', 'those', 'that',
            'an', 'a',
        ]
        tagged_sentence = delete_words(tagged_sentence, delete_targets)
        abbrs = ['can t', 'haven t', 'couldn t', 'shouldn t', 'don t', 'doesn t', 'didn t', 'wouldn t', 'needn t',
                 'need not', 'can not', 'could not', 'have not', 'should not', 'do not', 'does not', 'did not']
        tagged_sentence = synonym_format(tagged_sentence, abbrs, 'not')
        tagged_sentence = synonym_format(tagged_sentence, ["' @ '", "'@'"], " @ ")
    elif kind == 6:
        tagged_sentence = synonym_format(tagged_sentence, ['can t', 'cannot'], 'can not')
        tagged_sentence = synonym_format(tagged_sentence, ['haven t', 'have not'], 'have not')
        tagged_sentence = synonym_format(tagged_sentence, ['couldn t', 'couldnot'], 'could not')
        tagged_sentence = synonym_format(tagged_sentence, ['shouldn t', 'should not'], 'should not')
        tagged_sentence = synonym_format(tagged_sentence, ['don t', 'donot'], 'do not')
        tagged_sentence = synonym_format(tagged_sentence, ['doesn t', 'doesnot'], 'does not')
        tagged_sentence = synonym_format(tagged_sentence, ['didn t', 'didnot'], 'did not')
        tagged_sentence = synonym_format(tagged_sentence, ['wouldn t'], 'should not')
        tagged_sentence = synonym_format(tagged_sentence, ['needn t', 'neednote'], 'need not')
        tagged_sentence = synonym_format(tagged_sentence, ['blank'], 'space')
        tagged_sentence = concate(tagged_sentence, ['country'], ['code'])
        tagged_sentence = delete_words(tagged_sentence,
                                       ['a', 'please', 'your', 'our', 'his', 'her', 'my', 'its', 'their'])
    elif kind == 7:
        delete_targets = [
            'please', 'can', 'could', 'may', 'might', 'need to', 'must', 'need', 'ought to', 'dared', 'dare', 'shall',
            'should', 'will', 'would'  # modal verb
        ]
        tagged_sentence = delete_words(tagged_sentence, delete_targets)
        synonyms = [
            'minimum of', 'minimum', 'or more', 'or above', 'or longer', 'or long', 'or over', 'greater than',
            'longer than',
            'not less than', 'no less than', 'not under', 'more than', 'up to', 'over', '+'
        ]
        tagged_sentence = synonym_format(tagged_sentence, synonyms, 'at least')
        tagged_sentence = concate(tagged_sentence, ['expiration'], ['date'])
    elif kind == 8:
        delete_targets = [
            'please', 'can', 'could', 'may', 'might', 'need to', 'must', 'need', 'ought to', 'dared', 'dare', 'shall',
            'should', 'will', 'would'  # modal verb
        ]
        tagged_sentence = delete_words(tagged_sentence, delete_targets)
        synonyms = [
            'limited', 'limit', 'under', 'maximum of', 'maximum', 'or less', 'or shorter', 'less than', 'shorter than',
            'within', 'short than', 'no greater than', 'not greater than', 'no more than', 'not longer than',
            'no longer than', 'not over', 'not up to', 'no up to', '-'
        ]
        tagged_sentence = synonym_format(tagged_sentence, synonyms, 'at most')
    elif kind == 9:
        delete_targets = [
            'please', 'can', 'could', 'may', 'might', 'need to', 'must', 'need', 'ought to', 'dared', 'dare', 'shall',
            'should', 'will', 'would',  # modal verb
            'your', 'our', 'his', 'her', 'my', 'its', 'their',  # adjective possessive pronoun
            'still', 'also', 'yet',  # adverb
            'this', 'the', 'these', 'those', 'that'  # universal pronoun
        ]
        tagged_sentence = delete_words(tagged_sentence, delete_targets)
        tagged_sentence = synonym_format(tagged_sentence, ['-', '~'], 'to')
        tagged_sentence = synonym_format(tagged_sentence, ['contain'], 'have')
        tagged_sentence = synonym_format(tagged_sentence, ['input'], 'enter')
    elif kind == 10:
        pass
    elif kind == 11:
        pass
    elif kind == 12:
        pass
    elif kind == 13:
        pass
    elif kind == 14:
        tagged_sentence = delete_words(tagged_sentence, ['an', 'a'])
    elif kind == 15 or kind == 16:
        tagged_sentence = synonym_format(tagged_sentence, ['can t', 'cannot'], 'can not')
        tagged_sentence = synonym_format(tagged_sentence, ['haven t', 'have not'], 'have not')
        tagged_sentence = synonym_format(tagged_sentence, ['couldn t', 'couldnot'], 'could not')
        tagged_sentence = synonym_format(tagged_sentence, ['shouldn t', 'should not'], 'should not')
        tagged_sentence = synonym_format(tagged_sentence, ['don t', 'donot'], 'do not')
        tagged_sentence = synonym_format(tagged_sentence, ['doesn t', 'doesnot'], 'does not')
        tagged_sentence = synonym_format(tagged_sentence, ['didn t', 'didnot'], 'did not')
        tagged_sentence = synonym_format(tagged_sentence, ['wouldn t'], 'should not')
        tagged_sentence = synonym_format(tagged_sentence, ['needn t', 'neednote'], 'need not')
    elif kind == 17:
        pass
    elif kind == 18:
        tagged_sentence = delete_words(tagged_sentence, ['make sure to', 'a', 'an'])
    else:  # default
        print("Error : unrecognized multi_classification type !")
    return tagged_sentence


def synonym_format(sentence: str, synonyms: list, synword):
    """
    replace synonym
    """
    for item in synonyms:
        # special meaning of '+'
        if item == '+':
            if synword == 'at least':
                sentence = re.sub('taggedascd \+', 'at least taggedascd', sentence.lower())
            else:
                print("Unkown rule : ", synword)
        # special meaning of '-'
        elif item == '-' and synword == 'at most':
            sentence = re.sub('taggedascd -', 'at most taggedascd', sentence.lower())
        # special meaning of ~、-
        elif (item == '-' or item == '~') and synword == 'to':
            sentence = re.sub('\s+[~\-]\s+', ' to ', sentence.lower())
        elif item == 'blank':
            sentence = re.sub(r'blank\W?$', 'space', sentence)
        else:
            sentence = re.sub(item, synword, sentence.lower())
    return sentence


def concate(sentence: str, forword: list, backword: list):
    if len(sentence) < 2:
        return
    tmp = sentence.lower().strip().split()
    for f_word in forword:
        if f_word not in tmp:
            continue
        f_place = tmp.index(f_word)
        for b_word in backword:
            if b_word not in tmp:
                continue
            b_place = tmp.index(b_word)
            if f_place + 1 == b_place:
                tmp[f_place] = tmp[f_place] + tmp[b_place]
                tmp.pop(b_place)
    return ' '.join(tmp)


def delete_words(target_sentence: str, words: list):
    for word in words:
        target_sentence = re.sub(r'\b%s\b' % word, '', target_sentence, flags=re.IGNORECASE)
    return target_sentence
