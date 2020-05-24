# -*- coding: utf-8 -*-
import json, re, os, random
from src import globalConfig
from src.text_exerciser.mutate import constraint_extract as ce
from src.text_exerciser.mutate import type_extract as te
from src.text_exerciser.mutate import mutation
from src.base import node_info
from src.globalConfig import RestrLogName, SherlockRawTextLogName, Str01LogName, StrMultiLogName
from src.text_exerciser.mutate.nlp.hint_identifier import HintIdentifier
import traceback


class IG:
    # Public
    def __init__(self, register_info):
        self.TotalEdit = []
        self.REGISTERS = {
            'UI_TYPE': 'Other',  # Login, Signup, Other
            'CountDown': globalConfig.MaxMutateTime,
            'CandidateHintNodes': [],
            'CandidateDynamicHint': []
        }
        self.LatestNodes = []
        self.operation = 0  # Return: (0-default),(1-verify),(-1,end)
        self.LogPath = ""
        self.ResLogPath = ''
        self.Identifier_01 = HintIdentifier(globalConfig.MODEL_01_PATH)
        self.Identifier_multi = HintIdentifier(globalConfig.MODEL_MULTI_PATH)
        self.register_info = register_info
        global logger
        logger = globalConfig.te_logger

    def identify(self, text_node: list, edit_node: list, texts: list) -> ([str], [str]):
        """
        Determine whether text can be successfully matched with edit_node
        """
        if not edit_node:
            return texts, []
        texts = [t.strip() for t in texts]
        failed_distribute = self.identify_hints(te.find_cover_restrictions(text_node, edit_node), edit_node, [], texts, None)
        failed_distribute = [t.strip() for t in failed_distribute]
        return failed_distribute, list(set(texts) - set(failed_distribute))

    def feed(self, edit_node_list, text_node_list, alert_text_node_list, button, toast_strings=None,
             additional_toasts=None, flag='walk') -> (dict, int, list):
        """
        Generate text inputs for the input boxes on current page
        :return: generated text input(ig_input) and the hint information which cannot find corresponding text box (distribute_failed_texts)
        """
        if toast_strings is None:
            toast_strings = []
        if additional_toasts is None:
            additional_toasts = []
        edit_node = []
        text_node = []
        edit_node += edit_node_list
        text_node += text_node_list
        all_text = []
        if flag == 'walk':
            logger.info("First time for this page")
            isnew = True
        else:
            logger.info("Prepare to mutate")
            isnew = False
        # Update node mutate information
        for node in self.LatestNodes:
            node.clear_mutate()
            if isnew:
                node.reset_mutate_his()
        if toast_strings:
            logger.info('Receive toasts: %s' % (' '.join(toast_strings)))
            self.REGISTERS['CandidateDynamicHint'].extend(toast_strings)
        for node in alert_text_node_list:
            text = ';'.join(node.get_desc())
            if text:
                logger.info('Receive alert text: %s' % (text))
                self.REGISTERS['CandidateDynamicHint'].append(text)
        if len(edit_node) == 0:
            logger.warning('Current page does not have input box')
            return {}, -1, []
        # Record all texts on current page
        all_text.extend(self.REGISTERS['CandidateDynamicHint'])
        all_text.extend(additional_toasts)
        all_text.extend([n.attribute['text'] for n in text_node if n.attribute['text'] != ''])
        all_text.extend([n.attribute['text'] for n in edit_node if n.attribute['text'] != ''])
        # The first input box is not counted in mutate statistics.
        if isnew:
            self.LatestNodes = []
        else:
            self.LatestNodes = list(edit_node)
        self.REGISTERS['CandidateHintNodes'] = te.find_cover_restrictions(text_node, edit_node)

        if isnew:
            identify_failed_texts = self.identify_hints(self.REGISTERS['CandidateHintNodes'], edit_node,
                                                        self.REGISTERS['CandidateDynamicHint'], additional_toasts, None)
        else:
            identify_failed_texts = self.identify_hints(self.REGISTERS['CandidateHintNodes'], edit_node,
                                                        self.REGISTERS['CandidateDynamicHint'], additional_toasts, self.TotalEdit)

        # Determine whether the current page is login or registration
        self.set_app_type(text_node, edit_node, button)
        # generate text inputs
        output = self.generate_input(edit_node, isnew)
        if not isnew:
            if self.REGISTERS['UI_TYPE'] == 'Login':
                if self.REGISTERS['CountDown'] > 5:
                    self.REGISTERS['CountDown'] = 5
            self.REGISTERS['CountDown'] -= 1
        logger.info('Remain CountDown: %d' % self.REGISTERS['CountDown'])
        if self.REGISTERS['CountDown'] <= 0:
            logger.info('Muate count down <=0 ')
            self.operation = -1
        self.__update_edit(edit_node, flag)
        self.REGISTERS['CandidateDynamicHint'].clear()
        after_content = {"Action": "afterfeed"}
        nodes_info = []
        for edit in edit_node:
            nodes_info.append(edit.get_mutate_info())
        after_content["NodesInfo"] = nodes_info
        self.write_log("Median", os.path.join(self.LogPath, RestrLogName), after_content)
        self.write_log("Output", os.path.join(self.LogPath, RestrLogName), output)
        return output, self.operation, identify_failed_texts

    def generate_input(self, edit_nodes, is_new) -> dict:
        """
        Parse Hint and Generate text inputs
        """
        result_input = {}
        for node in edit_nodes:
            if is_new:
                if globalConfig.UseInputDB:
                    initial_input = get_input(node)
                else:
                    initial_input = mutation.random_generate(random.randint(4, 7))
            else:
                # Get initial input
                if node.lastInput != '':
                    initial_input = node.lastInput
                    logger.info(
                        'Choose last input [%s] for node [%s]' % (initial_input, node.attribute['resourceID']))
                else:
                    initial_input = get_input(node)
                    if initial_input == '':
                        initial_input = mutation.random_generate(random.randint(4, 7))
                    logger.info('Choose seed input [%s] for node [%s]' % (initial_input, node.attribute['resourceID']))
            # Classify hints into different categories
            constraints = []
            for sentence in node.hints:
                if len(sentence) == 0:
                    continue
                tagged, cd_matrix = ce.extract_cd(sentence)
                try:
                    pre_res = self.Identifier_multi.predict_hints([tagged])
                except Exception as e:
                    traceback.print_exc()
                    pre_res = [0]
                if pre_res is not None and len(pre_res) > 0:
                    constraints.append((sentence, pre_res[0]))
            logger.info('Node [%s] MultiIdentifier: %s' % (node.attribute['resourceID'], str(constraints)))
            if len(constraints) != 0:
                self.write_log("MultiIdentifier", os.path.join(self.LogPath, StrMultiLogName), constraints)
            # generate text inputs based on hints
            if not is_new:
                if node.lastInput != '' and node.type not in ['Email', 'Phone', 'CountryCode', 'Date']:
                    node.composition.exclude_history([node.lastInput])
                mutate_result = mutation.mutate_input(initial_input, hash(node), constraints, node.composition,
                                                      node.type, self.TotalEdit)
            else:
                logger.info('First mutate without constraints.')
                mutate_result = initial_input

            # Fetch account information for Login
            if self.REGISTERS['UI_TYPE'] == 'Login':
                is_meet_pwd = False
                for info in reversed(self.register_info):
                    if info['type'] == 'Password':
                        is_meet_pwd = True
                    if is_meet_pwd and node.type == info['type']:
                        mutate_result = info['input']
                        break
            if self.REGISTERS['UI_TYPE'] == 'Signup':
                self.register_info.append({'type': node.type, 'input': mutate_result})
            result_input[hash(node)] = mutate_result
            node.lastInput = mutate_result
            if node.type.lower() == 'verifycode':
                result_input[hash(node)] = te.get_input_by_type('VerifyCode')
                self.operation = 1
            logger.info(
                'Node (%s,%d) --> Input: %s' % (node.attribute['resourceID'], hash(node), result_input[hash(node)]))
        return result_input

    def process_re_str(self, text: str) -> str:
        """
        Handle some escape characters
        """
        labels = ['$', '(', ')', '*', '+', '?', '.', '^', '|', '[', ']', '{', '}', r'\\']
        for label in labels:
            text = text.replace(label, r'\\%s' % label)
        return text

    def pre_process_hints(self, hint_node_texts, edit_nodes):
        origin_texts = []
        tagged_texts = []
        last_inputs = {}

        for edit_node in edit_nodes:
            if edit_node.lastInput:
                last_inputs[edit_node.lastInput] = edit_node.type if edit_node.type != 'Null' else ''
        self.write_log('Raw', os.path.join(self.LogPath, SherlockRawTextLogName), hint_node_texts)
        logger.debug('Before preprocess: %s' % (str(hint_node_texts)))
        for text in hint_node_texts:
            # Preprocessing, including sentence breaks, etc .;
            text = text.lower()
            for last_input, type in last_inputs.items():
                last_input = self.process_re_str(last_input)
                # type = '' if re.search('\b%s\b' % type, text, flags=re.IGNORECASE) else type
                # text = re.sub('\b%s\b' % last_input, type, text)
            tmp_texts = ce.pre_process(ce.to_lower(text))
            if tmp_texts:
                origin_texts.extend(tmp_texts)
        for tmp_text in origin_texts:
            # Extract numbers to CD
            tagged_text, cd_matrix = ce.extract_cd(tmp_text)
            tagged_texts.append(tagged_text)
        logger.debug('After preprocess: %s' % str(origin_texts))
        return origin_texts, tagged_texts

    def identify_hints(self, text_nodes, edit_nodes, candidate_dynamic_hints, addition_toast, total_edit) -> [str]:
        """
        Process text and find the corresponding EditNode
        :return: Returns the text that failed to bind EditNode
        """
        result_01 = {}
        total_sentence = []
        total_tagged_text = []
        total_origin = []
        identify_failed_text = []
        for node in text_nodes:
            hint_texts = node.get_desc()
            origin_texts, tagged_texts = self.pre_process_hints(hint_texts, edit_nodes)
            total_tagged_text.extend(tagged_texts)
            total_origin.extend(origin_texts)
            total_sentence.append([str(hash(node)), hint_texts, tagged_texts, origin_texts])
        # dynamic_hints
        origin_dynamic_hints = []
        tagged_dynamic_hints = []
        addtional_origin_toasts = []
        additional_tagged_toasts = []
        if len(addition_toast) != 0:
            addtional_origin_toasts, additional_tagged_toasts = self.pre_process_hints(addition_toast, edit_nodes)
        if len(candidate_dynamic_hints) != 0:
            origin_dynamic_hints, tagged_dynamic_hints = self.pre_process_hints(candidate_dynamic_hints, edit_nodes)
        origin_dynamic_hints.extend(addtional_origin_toasts)
        tagged_dynamic_hints.extend(additional_tagged_toasts)
        total_tagged_text.extend(tagged_dynamic_hints)
        total_origin.extend(origin_dynamic_hints)
        total_sentence.append(['CandidateDynamicHint', candidate_dynamic_hints, tagged_dynamic_hints, origin_dynamic_hints])
        if not total_tagged_text:
            return []
        # use machine learning to identify hints
        try:
            logger.debug('Process ZeroOne for : %s' % (str(total_tagged_text)))
            total_predict_res = self.Identifier_01.predict_hints(total_tagged_text)
            logger.debug('ZeroOne result: %s' % (str(total_predict_res)))
        except Exception:
            logger.error('nlp error when dealing [%s]' ' | '.join(total_tagged_text), exc_info=True)
            traceback.print_exc()
            total_predict_res = [0] * len(total_tagged_text)
            logger.debug('ZeroOne result: %s' % (str(total_predict_res)))
        for text_index, predict_result in enumerate(total_predict_res):
            result_01[total_origin[text_index]] = predict_result
        # Bind the identified hints to corresponding input boxes via keywords mapping and shortest-distance
        for node in text_nodes:
            each_origin_texts = next(filter(lambda x: x[0] == str(hash(node)), total_sentence))[3]
            hints = [text for text in each_origin_texts if result_01[text] == 1]
            if node in edit_nodes:
                target = node
                isself = True
            else:
                target = node.get_closest_node(node_info.EDIT_CLASS)
                isself = False
            for hint in hints:
                logger.info('Distribute: %s' % hint)
                if isself:
                    target_node = edit_nodes[edit_nodes.index(target)]
                    target_node.add_hint([hint])
                    logger.info(
                        'Add hint [%s] to self node [%s].' % (hint, target.attribute['resourceID']))
                    continue
                if not ce.add_hint2type(edit_nodes, hint, None):
                    if target:
                        try:
                            target_node = edit_nodes[edit_nodes.index(target)]
                            target_node.add_hint([hint])
                            logger.info(
                                'Add hint [%s] to cloest node [%s].' % (
                                    hint, target.attribute['resourceID']))
                        except Exception as e:
                            traceback.print_exc()
                            logger.error("Can't add hint to target: %s" % (target.attribute['resourceID']))
                    else:
                        logger.info('No target find for string: %s' % hint)
        # dynamic_hints
        if origin_dynamic_hints:
            res_toasts = [toast for toast in origin_dynamic_hints if result_01[toast] == 1]
            for res_toast in res_toasts:
                logger.info('Distribute: %s' % res_toast)
                if not ce.add_hint2type(edit_nodes, res_toast, total_edit, False):
                    # No binding,
                    # Return to driver and determine whether needs to trace back UI for finding corresponding input box.
                    logger.info('No target find for toast: %s' % res_toast)
                    identify_failed_text.append(res_toast)
        self.write_log("ZeroOne", os.path.join(self.LogPath, Str01LogName), result_01)
        return identify_failed_text

    def write_log(self, tag, filepath, content):
        file = open(filepath, 'a+', encoding='utf-8', errors='ignore')
        output = {"Tag": tag, "Content": content}
        string = json.dumps(output)
        file.write(string + '\n')
        print(string)
        file.close()

    def __update_edit(self, EditNode, flag='walk'):
        """
        Update hints in input box structure. Add current page's nodes to TotalEdit.
        """
        for node in EditNode:
            node.update_constraint(flag)
            # if flag=='walk':
            #     continue
            if node not in self.TotalEdit:
                logger.info('Add Node [%s] to TotalEdit' % (node.attribute['resourceID']))
                self.TotalEdit.append(node)

    def update_input(self, feedback: dict):
        logger.info('Update input from guider. %s' % (str(feedback)))
        for node_hash, input in feedback.items():
            editnode = self.find_node_by_hash(node_hash)
            if editnode:
                editnode.lastInput = input
                logger.info('Node [%s] lastinput= %s' % (editnode.attribute['resourceID'], input))
            else:
                logger.warning('No such hash node --> %s' % (str(node_hash)))
                print(" No such hash node --> " + str(node_hash))
        return True

    def find_node_by_hash(self, node_hash):
        for node in self.TotalEdit:
            if hash(node) == node_hash:
                return node
        return None

    def set_signal(self, signal: str) -> bool:
        if not isinstance(signal, str):
            return False
        logger.info('Receive Signal --> %s' % (signal))
        self.write_log("Signal", os.path.join(self.LogPath, RestrLogName), signal)
        if signal == 'SUCCESS':
            for node in self.LatestNodes:
                node.set_state('Success')
                # if node.hasMutate:
                #     node.setState('Success')
        elif signal == 'FAILED':
            isshowed = False
            for node in self.LatestNodes:
                if node.isinMutate:
                    if not isshowed:
                        isshowed = True
                        node.set_state('Faile')
                else:
                    if isshowed:
                        pass
                    else:
                        if node.hasMutate:
                            node.set_state('Success')
        else:
            pass
        return True

    def clear(self):
        self.REGISTERS = {
            "UI_TYPE": "Other",
            "CountDown": 30,
            "HintNodes": [],
            "Toast": []
        }
        self.operation = 0
        logger.info('InputGenerator finished. Clear Register')

    def set_app_type(self, text_nodes, edit_nodes, button):
        if self.REGISTERS['UI_TYPE'] != "Other":
            logger.info('Current page type: %s' % (self.REGISTERS['UI_TYPE']))
            return
        LogIn = ["login", "signin", "log in", "sign in"]
        SignUp = ["signup", "sign up", "register", "createaccount", "create account"]
        strings = te.node2strings(text_nodes)
        if button:
            strings += te.node2strings(button + button)
        string = ' '.join(strings).lower()
        typelist = []
        for node in edit_nodes:
            typelist.append(node.type)
        login_rate = 0
        signup_rate = 0
        for item in LogIn:
            login_rate += len(re.findall(item, string))
        for item in SignUp:
            signup_rate += len(re.findall(item, string))
        if login_rate > signup_rate and ("Password" in typelist):
            self.REGISTERS['UI_TYPE'] = "Login"
        elif signup_rate > login_rate:
            self.REGISTERS['UI_TYPE'] = "Signup"
        else:
            if typelist.count('Password') >= 2:
                self.REGISTERS['UI_TYPE'] = 'Signup'
            elif ("Username" or "Email" in typelist):
                if len(edit_nodes) <= 3 and ("Password" in typelist):
                    self.REGISTERS['UI_TYPE'] = "Login"
                elif len(edit_nodes) > 3:
                    self.REGISTERS['UI_TYPE'] = "Signup"
        logger.info('Current page type: %s. login_rate=%d,signup_rate=%d' % (
            self.REGISTERS['UI_TYPE'], login_rate, signup_rate))


def get_input(node):
    return te.get_input_by_type(node.type)
