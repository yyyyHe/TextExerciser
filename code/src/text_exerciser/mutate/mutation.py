# -*- coding: utf-8 -*-
from code import src as te, src as tg
import code.src.text_exerciser.mutate.constraint_extract as ce
import re, random, time
import string as hstring
import numpy as np
from code.src import globalConfig
from code.src.text_exerciser.mutate.composition import Composition


def random_generate(length: int = 1, number=False, letter=False):
    result = ''
    if letter:
        result += ''.join(random.sample(te.LETTER_SEED, 1))
    if number:
        result += ''.join(random.sample(te.NUM_SEED, 1))
    if len(result) >= length:
        return result
    else:
        return result + ''.join(random.sample(te.NUM_SEED + te.LETTER_SEED, length - len(result)))


def mutate_input(init_input, self_hash, constraints, composition: Composition, node_type, total_edit):
    """
    Generate input based on syntax_tree
    :param init_input: Value of input box that before mutation.
    :param constraints:  SubMinorCategory id and hints content.
    :param composition: matrix of constraint representation
    :param node_type: type of input box
    :param total_edit: edit boxes
    :return: value after mutation
    """
    globalConfig.te_logger.info('refineInput for string: %s' % str(init_input))
    if composition is None:
        globalConfig.te_logger.warning('Receive empty node')
        return init_input
    if not constraints:
        globalConfig.te_logger.info('No hints for current input box')
        return init_input
    # Adjust the composition for current input box based on its hints.
    composition.type = 'Null'
    for hint, kind in constraints:
        process_syntax_tree(init_input, hint, kind, composition, node_type)
    globalConfig.te_logger.info('Composition: %s' % (str(composition.compose)))
    # array for mutation.
    probArray = {
        'add': [globalConfig.prob_equalitarian, None, 0],
        'sub': [globalConfig.prob_equalitarian, None, 0],
        'replace': [globalConfig.prob_equalitarian, None, None, 0],
        'concat': [globalConfig.prob_domination, '', '']
    }

    if composition.type == 'Null':
        globalConfig.te_logger.info("Mutation type: Default")
        start = time.clock()
        result_str, result_int = composition.solve()
        if result_str:
            init_input = result_str
        else:
            while check_adjust_prob(init_input, composition, probArray):
                init_input = solve_input(init_input, probArray)
                runtime = time.clock() - start
                if runtime > 60:
                    globalConfig.te_logger.error("Mutation out of time")
                    break
    elif composition.type == 'invalid':
        globalConfig.te_logger.info("Mutation type: invalid")
        stringRealm = ''.join(set(init_input))
        if node_type.lower() == 'email':
            globalConfig.te_logger.info('Mutate as Email')
            if init_input.find('@') == -1:
                globalConfig.te_logger.warning('Input not match email type.')
                init_input = te.get_input_by_type('Email')
            domain = re.findall(r'@([a-zA-Z0-9]+\.[a-zA-Z0-9]+)', init_input)
            if domain:
                domain = domain[0]
            # domain = input_str.split('@')[1]
            if domain:
                globalConfig.te_logger.info('domain may be valid: ' + str(domain))
            else:
                from code.src import RootDomain
                domain = random_generate(3) + '.' + random.choice(RootDomain)
            pool = composition.compose['Number'][1] + composition.compose['Letter'][1]
            probArray['add'] = [globalConfig.add_tendency, pool, int(len(stringRealm) * 0.2) + 1]
            probArray['sub'] = [globalConfig.sub_tendency, stringRealm, int(len(stringRealm) * 0.2) + 1]
            probArray['replace'] = [globalConfig.replace_tendency, pool, pool, int(len(stringRealm) * 0.2) + 1]
            username = solve_input(init_input.split('@')[0], probArray)
            init_input = solve_input(username, probArray) + '@' + domain
        else:
            globalConfig.te_logger.info('Mutate as default')
            result_str, result_int = composition.solve()
            if result_str:
                init_input = result_str
            else:
                pool = composition.compose['Number'][1] + composition.compose['Letter'][1] + \
                       composition.compose['Special'][1]
                probArray['add'] = [globalConfig.add_tendency, pool, int(len(stringRealm) * 0.2) + 1]
                probArray['sub'] = [globalConfig.sub_tendency, stringRealm, int(len(stringRealm) * 0.2) + 1]
                probArray['replace'] = [globalConfig.replace_tendency, pool, pool, int(len(stringRealm) * 0.2) + 1]
                init_input = solve_input(init_input, probArray)
    elif composition.type == 'value':
        globalConfig.te_logger.info("Mutation type: value")
        mutate_str = solve_valuable_input(init_input, composition, node_type)
        if len(mutate_str) > 0:
            init_input = mutate_str
        else:
            pool = composition.compose['Number'][1]
            stringRealm = ''.join(set(init_input))
            probArray['add'] = [globalConfig.add_tendency, pool, int(len(stringRealm) * 0.2) + 1]
            probArray['sub'] = [globalConfig.sub_tendency, stringRealm, int(len(stringRealm) * 0.2) + 1]
            probArray['replace'] = [globalConfig.replace_tendency, pool, pool, int(len(stringRealm) * 0.2) + 1]
            init_input = solve_input(init_input, probArray)
    elif composition.type == 'repeat':
        # handle joint filed situation
        globalConfig.te_logger.info("Mutation type: repeat")
        target = None
        for item in total_edit:
            if hash(item) != self_hash and item.type == node_type:
                target = item
                break
        if target:
            globalConfig.te_logger.info('Repeat input as the same with [%s]' % target.attribute['resourceID'])
            if len(init_input) < len(target.lastInput):
                init_input = target.lastInput
            elif len(init_input) == len(target.lastInput) and init_input != target.lastInput:
                init_input = target.lastInput
            else:
                globalConfig.te_logger.info('Self input may be valid')
        else:
            globalConfig.te_logger.warn('No repeat target find...')
    else:
        globalConfig.te_logger.error("Unknown composition type!")
    return init_input


def process_syntax_tree(input_str, hint, kind: int, composition, node_type):
    """
    Pre-processing and extracting key information from the syntax tree
    :param input_str: string value for input box that need to be mutate.
    :param hint: one sentence containing key info of composition.
    :param kind: constraint type(SubMinorCategory of hints)
    :param composition: matrix of constraint representation
    :param node_type: type of current input box
    :return: None
    """
    # Convert numbers in sentences to tags
    tagged_sentence, cd_matrix = ce.extract_cd(hint)
    clean_sentence = ce.res_pre_process(tagged_sentence, kind)
    clean_sentence = ce.insert_cd([clean_sentence], cd_matrix)[0]
    origin_sentence = re.sub('taggedascd_', '', clean_sentence)
    # Generate syntax tree
    tree = tg.GrammarTree(origin_sentence)
    globalConfig.te_logger.info('Adjust compose from: %s; kind=%d' % (origin_sentence, kind))
    if kind == 1:  # lower bound
        minimum = -1
        format = ''
        body = ''
        # Extract cd and format information according to each category
        if tree.Follow([('QP', 0), ('NN', 2)]) and tree.Contain(('QP', 0), [('CD', 0)]) and tree.First('NP', 1):
            format, body = tree.get_mutate_label('NN', 2)
            minimum = tree.Range('CD')
            composition.convert_length_constraint(format, minimum, 9999)
        elif tree.Follow([('QP', 0), ('NN', 1)]) and tree.Contain(('QP', 0), [('CD', 0)]) and tree.First('NN', 2):
            format, body = tree.get_mutate_label('NN', 1)
            minimum = tree.Range('CD')
            composition.convert_length_constraint(format, minimum, 9999)
        elif tree.Follow([('QP', 0), ('JJ', 0), ('NN', 2)]) and tree.Contain(('QP', 0), [('CD', 0)]) and tree.First(
                'NN', 1):
            format, body = tree.get_mutate_label('JJ', 0)
            if format == 'Null':
                format, body = tree.get_mutate_label('NN', 2)
            minimum = tree.Range('CD')
        elif tree.Follow([('QP', 0), ('NN', 0)]) and tree.Contain(('QP', 0), [('CD', 0)]):
            format, body = tree.get_mutate_label('NN', 0)
            minimum = tree.Range('CD')
        elif tree.Follow([('ADVP', 0), ('NP', 1)]) and tree.Contain(('NP', 1),
                                                                    [('CD', 0), ('NN', 1)]) and tree.First(
            'VP', 0):
            format, body = tree.get_mutate_label('NN', 1)
            minimum = tree.Range('CD')
        elif tree.Follow([('NP', 2), ('ADVP', 0)]) and tree.Contain(('NP', 2), [('CD', 0), ('NN', 0)]):
            format, body = tree.get_mutate_label('NN', 0)
            minimum = tree.Range('CD')
        else:
            minimum = tree.Range('CD')
            format, body = tree.get_mutate_label('NN', 0)
            if format == 'Null':
                format = ''
        composition.convert_length_constraint(format, minimum, 9999)
        if format != '':
            if format == 'Null':
                globalConfig.te_logger.warning('Unknown format in: %s' % hint)
                print('[Error]Unknown format:' + hint, file=globalConfig.OUTPUT_MODE)
            else:
                composition.convert_content_constraint(format, body)
    elif kind == 2:
        maximum = -1
        format = ''
        body = ''
        if tree.Follow([('QP', 0), ('NN', 2)]) and tree.Contain(('QP', 0), [('CD', 0)]) and tree.First('NP', 1):
            format, body = tree.get_mutate_label('NN', 2)
            maximum = tree.Range('CD')
        elif tree.Follow([('QP', 0), ('NN', 3)]) and tree.Contain(('QP', 0), [('CD', 0)]) and tree.First('NP', 1):
            format, body = tree.get_mutate_label('NN', 3)
            maximum = tree.Range('CD')
        elif tree.Contain(('ROOT', 0), [('NP', 2)]) and tree.Contain(('NP', 2), [('CD', 0), ('NN', 0)]):
            format, body = tree.get_mutate_label('NN', 0)
            maximum = tree.Range('CD')
        else:
            format, body = tree.get_mutate_label('NN', 0)
            if format == 'Null':
                format = ''
            maximum = tree.Range('CD')
        composition.convert_length_constraint(format, 0, maximum)
        if format != '':
            if format == 'Null':
                print('[Error]Unknown format:' + hint, file=globalConfig.OUTPUT_MODE)
                globalConfig.te_logger.warning('Unknown format in: %s' % (hint))
            else:
                composition.convert_content_constraint(format, body)
    elif kind == 3:
        minimum = -1
        maximum = -1
        format = ''
        body = ''
        if tree.Follow([('QP', 0), ('NN', 2)]) and tree.Contain(('QP', 0), [('CD', 1), ('CD', 2)]) and tree.First(
                'NP',
                1):
            minimum = tree.Range('CD', 1)
            maximum = tree.Range('CD', 2)
            format, body = tree.get_mutate_label('NN', 2)
        elif tree.Follow([('QP', 0), ('NN', 1)]) and tree.Contain(('QP', 0), [('CD', 1), ('CD', 2)]) and tree.First(
                'NN', 2):
            minimum = tree.Range('CD', 1)
            maximum = tree.Range('CD', 2)
            format, body = tree.get_mutate_label('NN', 1)
        elif tree.Contain(('ROOT', 0), [('QP', 0)]) and tree.Contain(('QP', 0),
                                                                     [('CD', 1), ('CD', 2)]) and tree.First(
            'NP', 1):
            minimum = tree.Range('CD', 1)
            maximum = tree.Range('CD', 2)
        elif tree.Follow([('QP', 0), ('NN', 0)]) and tree.Contain(('QP', 0), [('CD', 1), ('CD', 2)]):
            minimum = tree.Range('CD', 1)
            maximum = tree.Range('CD', 2)
            format, body = tree.get_mutate_label('NN', 0)
        else:
            minimum = tree.Range('CD', 1)
            maximum = tree.Range('CD', 2)
            format, body = tree.get_mutate_label('NN', 0)
            if format == 'Null':
                format = ''
        composition.convert_length_constraint(format, minimum, maximum)
        if format != '':
            if format == 'Null':
                print('[Error]Unknown format:' + hint, file=globalConfig.OUTPUT_MODE)
                globalConfig.te_logger.warning('Unknown format in: %s' % (hint))
            else:
                composition.convert_content_constraint(format, body)
    elif kind == 4:
        length = -1
        format = ''
        body = ''
        if tree.Contain(('ROOT', 0), [('NP', 2)]) and tree.Contain(('NP', 2),
                                                                   [('CD', 0), ('NN', 2)]) and tree.First(
            'NP', 1):
            format, body = tree.get_mutate_label('NN', 2)
            length = tree.Range('CD')
        elif tree.Contain(('ROOT', 0), [('NP', 1)]) and tree.Contain(('NP', 1),
                                                                     [('CD', 0), ('NN', 1)]) and tree.First(
            'NP', 2):
            format, body = tree.get_mutate_label('NN', 1)
            length = tree.Range('CD')
        elif tree.Contain(('ROOT', 0), [('NP', 0)]) and tree.Contain(('NP', 0),
                                                                     [('CD', 0), ('NN', 1)]) and tree.First(
            'NP', 1) and tree.First('VBN', 0):
            format, body = tree.get_mutate_label('NN', 1)
            length = tree.Range('CD')
        elif tree.Contain(('ROOT', 0), [('NP', 2)]) and tree.Contain(('NP', 2),
                                                                     [('CD', 0), ('NN', 1)]) and tree.First(
            'NN', 2):
            format, body = tree.get_mutate_label('NN', 1)
            length = tree.Range('CD')
        elif tree.Contain(('ROOT', 0), [('NP', 0)]) and tree.Contain(('NP', 0),
                                                                     [('CD', 0), ('NN', 1)]) and tree.First(
            'NN', 2):
            format, body = tree.get_mutate_label('NN', 1)
            length = tree.Range('CD')
        elif tree.Contain(('ROOT', 0), [('NP', 0)]) and tree.Contain(('NP', 0), [('CD', 0)]) and tree.First('NN',
                                                                                                            0):
            length = tree.Range('CD')
        elif tree.Contain(('ROOT', 0), [('NP', 0)]) and tree.Contain(('NP', 0), [('CD', 0), ('NN', 0)]):
            format, body = tree.get_mutate_label('NN', 0)
            length = tree.Range('CD')
        else:
            # default Can be executed according to the unconditional judgment in c4
            format, body = tree.get_mutate_label('NN', 0)
            if format == 'Null':
                format = ''
            length = tree.Range('CD')
        composition.convert_length_constraint(format, length, length)
        if format != '':
            if format == 'Null':
                print('[Error]Unknown format:' + hint, file=globalConfig.OUTPUT_MODE)
                globalConfig.te_logger.warning('Unknown format in: %s' % (hint))
            else:
                composition.convert_content_constraint(format, body)
    elif kind == 5:
        possible_words = [node[0] for node in tree.get_node_by_type('NN', 0, True) if isinstance(node[0], str)]
        need_labels = set()
        for possible_word in possible_words:
            label, word = tree.get_mutate_label_from_word(possible_word)
            need_labels.add(label)
            composition.convert_content_constraint(label, word)
        j_words = [node[0] for node in tree.get_node_by_type('JJ', 0, True) if isinstance(node[0], str)]
        if 'only' in j_words or 'just' in j_words:
            for label in Composition.get_content_labels() - need_labels:
                composition.convert_content_constraint(label, '', False)
    elif kind == 6:
        possible_words = [node[0] for node in tree.get_node_by_type('NN', 0, True) if isinstance(node[0], str)]
        for possible_word in possible_words:
            label, word = tree.get_mutate_label_from_word(possible_word)
            composition.convert_content_constraint(label, word, False)
    elif kind == 7:
        minval = 0
        if tree.Follow([('QP', 0), ('NN', 2)]) and tree.Contain(('QP', 0), [('CD', 0)]) and tree.First('NN', 1):
            minval = tree.Range('CD')
        elif tree.Follow([('QP', 0), ('NN', 2), ('PP', 0)]) and tree.Contain(('QP', 0),
                                                                             [('CD', 0)]) and tree.Contain(
            ('PP', 0), [('IN', 1), ('NN', 3)]) and tree.First('NP', 1):
            minval = tree.Range('CD')
        elif tree.Contain(('ROOT', 0), [('NP', 0)]) and tree.Contain(('NP', 0), [('CD', 0), ('NN', 0)]):
            minval = tree.Range('CD')
            format, body = tree.get_mutate_label('NN', 0)
        elif tree.Contain(('ROOT', 0), [('QP', 0)]) and tree.Contain(('QP', 0), [('CD', 0)]) and tree.First('NP',
                                                                                                            1):
            minval = tree.Range('CD')
        else:
            minval = tree.Range('CD')
        if minval != -1:
            composition.convert_value_constraint(minval, 9999, 'value')
        else:
            globalConfig.te_logger.warning('No CD found in: %s' % (origin_sentence))
    elif kind == 8:
        maxval = 9999
        if tree.Contain(('ROOT', 0), [('QP', 0)]) and tree.Contain(('QP', 0), [('CD', 0)]) and tree.First('NP', 1):
            maxval = tree.Range('CD')
        elif tree.Contain(('ROOT', 0), [('PP', 0)]) and tree.Contain(('PP', 0), [('CD', 0)]) and tree.First('NN',
                                                                                                            1):
            maxval = tree.Range('CD')
        else:
            maxval = tree.Range('CD')
        if maxval != -1:
            composition.convert_value_constraint(0, maxval, 'value')
        else:
            globalConfig.te_logger.warning('No CD found in: %s' % (origin_sentence))
    elif kind == 9:
        minval = 0
        maxval = 9999
        if tree.Contain(('ROOT', 0), [('QP', 0)]) and tree.Contain(('QP', 0),
                                                                   [('CD', 1), ('CD', 2)]) and tree.First(
            'NP', 1):
            minval = tree.Range('CD', 1)
            maxval = tree.Range('CD', 2)
        elif tree.Contain(('ROOT', 0), [('PP', 0)]) and tree.Contain(('PP', 0),
                                                                     [('CD', 1), ('CD', 2)]) and tree.First(
            'NN', 1):
            minval = tree.Range('CD', 1)
            maxval = tree.Range('CD', 2)
        else:
            minval = tree.Range('CD', 1)
            maxval = tree.Range('CD', 2)
        if minval or maxval != -1:
            composition.convert_value_constraint(minval, maxval, 'value')
        else:
            globalConfig.te_logger.warning('No CD1 CD2 found in: %s' % (origin_sentence))
    elif kind == 10:
        minimum = len(input_str) + 1
        format = ''
        if tree.First('NN', 0):
            pass
        else:
            pass
        composition.convert_length_constraint(format, minimum, 9999)
    elif kind == 11:
        maximum = len(input_str) - 1
        format = ''
        if tree.First('NP', 3):
            pass
        else:  # default
            pass
        composition.convert_length_constraint(format, 0, maximum)
    elif kind == 12:
        if node_type.lower() != 'date':
            digit = re.sub(r'\D', '', input_str)
            if digit == '':
                print("[Error]wrong initial input_str for type 12 :" + input_str, file=globalConfig.OUTPUT_MODE)
                globalConfig.te_logger.error('wrong initial input_str: %s' % (input_str))
                minval = 33
            else:
                minval = int(digit) + 1
        else:
            minval = random.randint(0, 19)
        if tree.First('NP', 1):
            pass
        else:  # default
            pass
        composition.convert_value_constraint(minval, 9999, 'value')
    elif kind == 13:
        if node_type.lower() != 'date':
            digit = re.sub(r'\D', '', input_str)
            if digit == '':
                print("[Error]wrong initial input_str for type 13 :" + input_str, file=globalConfig.OUTPUT_MODE)
                globalConfig.te_logger.error('wrong initial input_str: %s' % (input_str))
                maxval = 33
            else:
                maxval = int(digit) - 1
        else:
            maxval = random.randint(0, 19)
        if tree.First('NP', 1):
            pass
        else:
            pass
        composition.convert_value_constraint(0, maxval, 'value')
    elif kind == 14:
        # default
        if composition.type == 'Null':
            composition.type = 'invalid'
    elif kind == 15:
        if tree.Contain(('ROOT', 0), [('NN', 1)]) and tree.First('NN', 1):
            pass
        elif tree.First('NP', 1) and tree.First('NP', 2):
            pass
        else:  # default
            pass
        composition.type = 'repeat'
    elif kind == 16:
        if tree.First('NP', 0):
            pass
        elif tree.First('NP', 1) and tree.First('NP', 2):  # Not reachable?
            pass
        else:
            pass
        if composition.type == 'Null':
            composition.type = 'invalid'
    elif kind == 17:
        digit = re.sub(r'\D', '', input_str)
        if digit == '':
            print("[Error]wrong initial input_str for type 17 :" + input_str, file=globalConfig.OUTPUT_MODE)
            globalConfig.te_logger.error('wrong initial input_str: %s ' % (input_str))
            maxval = 33
        else:
            maxval = int(digit) - 1
        if tree.First('NP', 1) and tree.First('NP', 2):
            pass
        else:
            pass
        composition.convert_value_constraint(0, maxval, 'value')
    elif kind == 18:
        if tree.First('NP', 1) and tree.First('NP', 2):
            pass
        else:
            pass
    else:  # default
        globalConfig.te_logger.warning('wrong type for hint: %s ' % (hint))


def check_adjust_prob(string, composition, prob):
    """
    Set the probability matrix of the operation
    """
    if composition is None:
        globalConfig.te_logger.warn('Receive invalid composition.')
        return False
    if composition.check_compose(string, 'Number', prob):
        globalConfig.te_logger.info('Content [Number] has not been satisfied.')
        return True
    if composition.check_compose(string, 'Letter', prob):
        globalConfig.te_logger.info('Content [Letter] has not been satisfied.')
        return True
    if composition.check_compose(string, 'Special', prob):
        globalConfig.te_logger.info('Content [Special] has not been satisfied.')
        return True
    if composition.check_compose(string, 'Space', prob):
        globalConfig.te_logger.info('Content [Space] has not been satisfied.')
        return True
    pool = composition.compose['Number'][1] + composition.compose['Letter'][1] + composition.compose['Special'][1]
    if len(string) < composition.compose['minlength']:  # Random add characters to reach min length requirement.
        prob['add'] = [1, pool, composition.compose['minlength'] - len(string)]
        prob['sub'] = [0, None, 0]
        prob['replace'] = [0, None, None, 0]
        return True
    if len(string) > composition.compose['maxlength']:  # Random add characters to reach max length requirement.
        prob['sub'] = [1, string, len(string) - composition.compose['maxlength']]
        prob['add'] = [0, None, 0]
        prob['replace'] = [0, None, None, 0]
        return True
    return False


def solve_input(string: str, probArray: dict):
    """
    Mutate according to probability array.
    :param string: input string value.
    :param probArray: {'add':(p,pool,value),'sub':(p,pool,value),'replace':(p,target,pool,value)}
    :return:
    """
    globalConfig.te_logger.info(str(probArray))
    if probArray is None:
        return string
    if probArray['concat'][0] == 1:
        return probArray['concat'][1] + string + probArray['concat'][2]
    array = []
    for item in probArray.values():
        array.append(item[0])
    p = np.array(array)
    np.random.seed(0)
    index = np.random.choice(list(range(0, len(array))), p=p.ravel())
    if index == 0:
        globalConfig.te_logger.info('[Mutation Method] Add')
        length = probArray['add'][2]
        if length == 0:
            length = random.choice(range(1, 4))
        string += ''.join(random.sample(probArray['add'][1], length))
    elif index == 1:
        globalConfig.te_logger.info('[Mutation Method] Sub')
        if probArray['sub'][1]:
            pool = probArray['sub'][1]
        else:
            pool = set(string)
        tmp = probArray['sub'][2]
        if tmp == 0:
            tmp = len(pool)
        while tmp > 0:
            target = random.sample(pool, 1)[0]
            position = string.find(target)
            if position != -1:
                tmp -= 1
                string = string[0:position] + string[position + 1:]
    elif index == 2:
        globalConfig.te_logger.info('[Mutation Method] Replace')
        if not probArray['replace'][1]:
            globalConfig.te_logger.warn('No thing to replace')
            return string
        length = probArray['replace'][3]
        if length == 0:
            length = len(re.findall(r'[' + ''.join(probArray['replace'][1]) + ']', string))
        for target in probArray['replace'][1]:
            while string.find(target) != -1:
                if length <= 0:
                    break
                else:
                    length -= 1
                if probArray['replace'][2]:
                    atom = random.sample(probArray['replace'][2], 1)[0]
                else:
                    globalConfig.te_logger.error('Invalid probability array for ---- %s.' % (string))
                    atom = random.sample(hstring.digits, 1)[0]
                string = string.replace(target, atom, 1)
        pass
    elif index == 3:  # leave empty.
        pass
    else:
        globalConfig.te_logger.error('None operation')
    return string


def solve_valuable_input(string: str, composition, nodeType):
    digit = re.sub('\D', '', string)
    if composition is None or composition.type != 'value':
        globalConfig.te_logger.warn('Incorrect parameters : input=[%s], nodeType=[%s]' % (string, nodeType))
        return string
    if nodeType.lower() == 'date':
        import datetime
        try:
            date = datetime.datetime.strptime(string, "%Y/%m/%d")
        except ValueError as e:
            globalConfig.te_logger.warn(str(e))
            print(e)
            date = datetime.datetime.now()
        if composition.compose['minval'] > 0:
            delta = datetime.timedelta(days=composition.compose['minval'] * 360)
            string = (date - delta).strftime("%Y/%m/%d")
        elif composition.compose['maxval'] < 9999:
            delta = datetime.timedelta(days=composition.compose['maxval'] * 360)
            string = (date + delta).strftime("%Y/%m/%d")
    else:
        if digit == '':
            globalConfig.te_logger.warn('Incorrect input type')
            return ''
        else:
            digit = int(digit)
        result_str, result_int = composition.solve('value')
        if result_int != -1:
            digit = result_int
        else:
            while digit < composition.compose['minval'] or digit > composition.compose['maxval']:
                if digit < composition.compose['minval']:
                    digit += random.randint(1, int(digit / 2) + 1)
                if digit > composition.compose['maxval']:
                    digit -= random.randint(1, int(digit / 2) + 1)
        string = str(digit)
    return string
