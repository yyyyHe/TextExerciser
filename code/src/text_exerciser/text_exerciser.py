# -*- coding: utf-8 -*-
import os
import time
import random
import copy
import traceback
from src.base.node_info import is_same_bound
from src.base import shell_cmd
from func_timeout import func_set_timeout
from selenium.common.exceptions import WebDriverException
from src.base.server.server_interactor import ServerInteractor
from src.text_exerciser.mutate.type_extract import sentence2type
from src.base.xml_builder import XmlTree
from src.base.node_info import has_filter_key, split_resource_id
from src import globalConfig
from src.text_exerciser.mutate.input_generator import IG
from src.triggers.te_trigger.node import Node
from src.triggers.te_trigger.edge import Edge
from src.triggers.te_trigger.device import Device
from src.text_exerciser.mutate.type_extract import get_input_by_type


class AbstractClickableNode:
    def __init__(self, type, node=None):
        self.type = type
        self.node = node

    def get_node(self):
        return self.node

    def is_enter(self):
        if self.type == 'Enter':
            return True
        return False


class TextExerciser:
    def __init__(self, device: Device, udid, test_pkg, sdk_int, record_path, exerciser_log,
                 lukas_raw_text_log, appear_text_log, time_worker=None,
                 graph=None, ui_waiting_duration=3, register_info=None):
        self.device = device
        self.udid = udid
        self.pkg_name = test_pkg
        self.recordPath = record_path
        self.register_info = register_info
        self.ig = IG(self.register_info)
        self.ig.LogPath = self.recordPath
        self.sdkInt = sdk_int
        self.ui_waiting_duration = ui_waiting_duration
        self.timeWorker = time_worker
        self.InitialScene = ""
        self.graph = graph
        # Log
        self.exerciserLog = exerciser_log
        self.lukasRawTextLog = lukas_raw_text_log
        self.appearTextLog = appear_text_log
        self.logTextNodes = []
        # double get to initial toast
        self.toastRecord = []
        self.toastRecord, self.newtoast = get_toast(udid, self.toastRecord)
        self.toastRecord, self.newtoast = get_toast(udid, self.toastRecord)
        self.SI = ServerInteractor(self.pkg_name)
        self.eventNum = 0
        self.store_screen_shoot('init-page')
        global logger
        logger = globalConfig.te_logger

    def store_screen_shoot(self, pre_name, time=str(time.time())):
        """
        Store screen-shoot, require Android>=4.2
        """
        if self.sdkInt >= 17:
            png_path = os.path.join(self.recordPath, pre_name + time + ".png")
            self.device.get_screen_shoot(png_path)

    def wait_and_get_valuable_new_page(self, stop_seconds=4) -> XmlTree:
        tmp_son_nodes = []
        start_time = time.time()
        new_toast = None
        while True:
            if time.time() - start_time > stop_seconds:
                break
            tmp_son_nodes.append(XmlTree('', self.device.dump_raw_xml()))
        final_node = XmlTree('', self.device.dump_raw_xml())
        for tmp_node in tmp_son_nodes:
            tmp_node_texts = set(
                filter(lambda x: x != '', [text_node.attribute['text'] for text_node in tmp_node.TextNodes]))
            final_node_texts = set(
                filter(lambda x: x != '', [text_node.attribute['text'] for text_node in final_node.TextNodes]))
            if tmp_node_texts.issuperset(final_node_texts) and len(tmp_node_texts) != len(final_node_texts):
                new_toast = list(tmp_node_texts - final_node_texts)[0]
                final_node = tmp_node
                break
        self.toastRecord, self.newtoast = get_toast(self.udid, self.toastRecord)
        if new_toast is not None:
            self.newtoast.append(new_toast)
        return final_node

    def is_need_enter(self, node):
        may_next_word = ['register', 'next', 'done', 'ok', 'log in', 'sign up', 'next', 'login', 'sign', 'continue',
                         'submit']
        clickable_text = ';'.join(filter(lambda x: x != '', [c_node.attribute['text'].lower() for c_node in
                                                             node.ClickableNodes + node.NoEnabledClickNodes + node.ButtonNodes]))
        for pre_word in may_next_word:
            if pre_word in clickable_text:
                return False
        return True

    def get_clickable_buttons(self, source_node: Node) -> [AbstractClickableNode]:
        """
        Get all the clickable buttons in source_node
        """
        # source_node.process_clickable_nodes_by_ig(self.ig.REGISTERS["UI_TYPE"])
        try_clickable_nodes = [e for e in source_node.clickable_elements_for_te if not e.is_explored_in_mutation]
        try_clickable_nodes_conbine_enter = [AbstractClickableNode(type='Button', node=node) for node in
                                             try_clickable_nodes]
        if self.is_need_enter(source_node.page):
            try_clickable_nodes_conbine_enter.insert(0, AbstractClickableNode(type='Enter'))
        return try_clickable_nodes_conbine_enter

    def click_abs_button(self, button: AbstractClickableNode):
        if button is None:
            return
        if button.is_enter():
            self.device.press_enter()
        else:
            button.node.is_explored_in_mutation = True
            mbn = self.get_click_element_by_node(button.get_node())
            if mbn is not None:
                self.device.click_ui2_element(mbn)

    @func_set_timeout(globalConfig.PageHandlerTimeout)
    def page_handle(self, start_node: Node) -> (bool, Node):
        """
        Handling pages with input boxes
        :return: a flag whether it is successful , and return node that needs to be traced back
        """
        # The button that make hint appeared when text input don't satisfy the restriction
        consume_button = None
        # Whether initial text inputs exist in current page
        is_initial_input = False
        source_page = start_node.page
        clickable_buttons = self.get_clickable_buttons(start_node)
        mutate_count = 0
        max_mutate_time = globalConfig.MaxMutateTime
        alert_text_node_list = []
        while mutate_count < max_mutate_time + len(clickable_buttons):
            mutate_count += 1
            if not is_initial_input or consume_button is not None:
                if not is_initial_input:
                    flag = 'walk'
                else:
                    flag = 'probe'
                # step1：Send the information of the current page to IG for getting text input
                cp_edit_node_list = copy.deepcopy(source_page.EditNodes)
                cp_text_node_list = copy.deepcopy(source_page.TextNodes)
                cp_button_node_list = copy.deepcopy(source_page.ButtonNodes)
                ig_input, operation, distribute_failed_texts = self.ig.feed(cp_edit_node_list, cp_text_node_list,
                                                                            alert_text_node_list, cp_button_node_list,
                                                                            self.newtoast, start_node.addition_res,
                                                                            flag)
                if operation == -1:
                    self.ig.set_signal('FAILED')
                    self.ig.clear()
                    return False, None
                elif operation == 1:
                    # Process input verification code
                    if self.deal_verify_page(source_page, ig_input):
                        self.log_input('Deal verify code success.')
                    else:
                        self.log_input('Deal verify code fail.')

                # If no text box match the hint in current page,
                # trace the graph for finding the page which contains the corresponding text box that can match the hint
                if distribute_failed_texts:
                    logger.info('Find target edit-box')
                    target_back_node = None
                    max_back_count = 5
                    for ui_node in list(reversed(self.graph.get_path_between(start_node)))[1:max_back_count]:
                        distribute_failed_texts, success_texts = self.ig.identify(
                            copy.deepcopy(ui_node.page.TextNodes), copy.deepcopy(ui_node.page.EditNodes),
                            distribute_failed_texts)
                        if success_texts:
                            ui_node.log_addition_res(success_texts)
                            target_back_node = ui_node
                        if not distribute_failed_texts:
                            break
                    if target_back_node is not None:
                        self.ig.set_signal('FAILED')
                        self.ig.clear()
                        return False, target_back_node
                self.logTextNodes = copy.deepcopy(source_page.TextNodes)
                log_text_to_file(self.lukasRawTextLog, self.logTextNodes)
                alert_text_node_list = []
                # step2：Inject the generated text inputs and update page information
                send_re = self.send_input(ig_input, source_page)
                if send_re == -1:
                    self.log_input("SendInput case fail of mutate")
                    return False, None
                start_node.log_last_input(ig_input)

                cp_text_node_list = XmlTree("", self.device.dump_raw_xml()).TextNodes
                log_appear_text_to_file(self.appearTextLog, self.logTextNodes, cp_text_node_list)
                self.logTextNodes = cp_text_node_list
                # update
                self.update_node(source_page, ig_input)
                self.ig.update_input(copy.deepcopy(ig_input))
                self.InitialScene = self.ig.REGISTERS["UI_TYPE"]
                logger.info("Scene:" + str(self.InitialScene))
                is_initial_input = True
            # step3：Find and click the consume_button
            if consume_button is None:
                if not clickable_buttons:
                    self.ig.set_signal('FAILED')
                    self.ig.clear()
                    return False, None
                else:
                    current_button = clickable_buttons.pop(0)
                    self.log_input('Try a new button!')
                    if not current_button.is_enter() and current_button.node.attribute['enable'] == 'false':
                        logger.warn('Try to deal no enable clickable buttons')
                        time.sleep(self.ui_waiting_duration)
                        if self.get_click_element_by_node(current_button.node) is not None:
                            if not self.get_click_element_by_node(current_button.node).info['enabled']:
                                clickable_buttons.append(current_button)
                                current_button = None
            else:
                current_button = consume_button
            # Skip the buttons that case page return
            if current_button is not None and not current_button.is_enter() and (current_button.get_node().attribute[
                                                                                     "packageName"] != self.pkg_name or current_button.get_node().is_at_left_top()):
                continue
            self.click_abs_button(current_button)

            after_click_page = self.wait_and_get_valuable_new_page()

            # step4: Handle the page that after clicked consume_button
            if current_button is not None and not current_button.is_enter() and current_button.get_node().is_third_party():
                self.log_input("Third Party Button")
                backPage = XmlTree("", self.device.dump_raw_xml())
                backCount = 0
                while backPage.cal_similarity(source_page) != 1:
                    self.log_input("Press Back")
                    self.device.press_back()
                    time.sleep(self.ui_waiting_duration)
                    self.add_event_count()
                    backPage = XmlTree("", self.device.dump_raw_xml())
                    backCount += 1
                    if backCount > 3:
                        break
                time.sleep(self.ui_waiting_duration)
                continue
            if self.device.get_current_package() != self.pkg_name:
                self.log_input("Handle Permission")
                self.handle_out_of_app()
                continue
            # step5：Compare the change between source_page and after_click_page
            change_state = check_mutate_state(source_page, after_click_page, self.newtoast)
            # No change after clicking
            if change_state == 0:
                # Try clicking the input box to get the change
                for edit_box in self.device.get_elements_by_class_type('android.widget.EditText'):
                    self.device.click_ui2_element(edit_box)
                    tmp_page = XmlTree("", self.device.dump_raw_xml())
                    tmp_state = check_mutate_state(source_page, tmp_page, '')
                    # update
                    if tmp_state != 0:
                        change_state = tmp_state
                        after_click_page = tmp_page
            # New ui appears after clicked consume_button
            if change_state == 1:
                is_success = False
                if after_click_page.is_alert(self.pkg_name):
                    logger.info("After click is a Alert Page")
                    # Insight: clicking any button in alert page has same effect
                    for confirm_button in after_click_page.ClickableNodes[::-1]:
                        tbn = self.get_click_element_by_node(confirm_button)
                        if tbn is not None:
                            self.log_input('Alert Page Click: ' + confirm_button.attribute['resourceID'] + '--' +
                                           confirm_button.attribute['text'])
                            self.device.click_ui2_element(tbn)
                            break
                    else:
                        self.log_input("Press Back Because Alert Page Find No Clickable buttons")
                        self.device.press_back()
                    time.sleep(self.ui_waiting_duration)
                    back_page = XmlTree("", self.device.dump_raw_xml())
                    if self.device.get_current_package() != self.pkg_name:
                        self.log_input("Handle Permission")
                        self.handle_out_of_app()
                    else:
                        # If the source-page is the same as the original page, then the consume-button is determined.
                        if back_page.cal_similarity(source_page) == 1:
                            consume_button = current_button
                            alert_text_node_list = copy.deepcopy(after_click_page.TextNodes)
                            source_page = back_page
                        else:
                            is_success = True
                else:
                    is_success = True
                # handle the situation that the text constraint is successfully passed
                if is_success:
                    success_node = self.graph.get_node(self.device.get_current_view_node())
                    if current_button.is_enter():
                        trans_edge = Edge(type=Edge.TYPE_TE, action=Edge.ACTION_ENTER)
                    else:
                        trans_edge = Edge(type=Edge.TYPE_TE, element=current_button.get_node(),
                                          action=Edge.ACTION_CLICK)
                    self.graph.add_nodes_with_edge(start_node, success_node, trans_edge)
                    self.ig.set_signal('SUCCESS')
                    self.ig.clear()
                    return True, None
            if change_state == 2:
                consume_button = current_button
                source_page = after_click_page
        self.ig.set_signal('FAILED')
        self.ig.clear()
        return False, None

    def get_click_element_by_node(self, btn):
        if btn.attribute["resourceID"]:
            elements = self.device.get_elements_by_resource_id(btn.attribute['resourceID'])
            elen = len(elements)
            if elen > 0:
                if elen == 1:
                    return elements[0]
                else:
                    for e in elements:
                        cinfo = self.device.get_element_info(e)
                        if cinfo["className"] == btn.attribute["classType"] and is_same_bound(
                                btn.attribute["bound"], self.get_format_bound(cinfo)):
                            return e
                    return elements[0]
            else:
                self.log_input("Have id but find None:" + str(btn.attribute["resourceID"]))
                return None
        else:
            elements = self.device.get_elements_by_class_type(btn.attribute["classType"])
            if len(elements) > 0:
                for e in elements:
                    ei = self.device.get_element_info(e)
                    if is_same_bound(btn.attribute["bound"], self.get_format_bound(ei)):
                        return e
                self.log_input("Same classType but no match")
                return None
            else:
                self.log_input("No same classType widgets")
                return None

    def find_send_code_and_click(self, current_node):
        name_key_words = ['send']
        if not current_node.VerifyCodeNodes:
            self.log_input("Error:No Send button")
            return
        if len(current_node.VerifyCodeNodes) > 1:
            self.log_input("Error:Send button matching multiple verification codes")
            for e in current_node.VerifyCodeNodes:
                print("Captcha send button：", e.attribute['resourceID'], e.attribute['name'])
                if e.attribute['name'] and has_filter_key(e.attribute['name'], name_key_words):
                    tb = self.get_click_element_by_node(e)
                    self.log_input("Click Send VerifyCode: " + e.attribute['resourceID'] + "--" + e.attribute['name'])
                    self.device.click_ui2_element(tb)
        else:
            e = current_node.VerifyCodeNodes[0]
            tb = self.get_click_element_by_node(e)
            self.log_input("Click Send VerifyCode: " + e.attribute['resourceID'] + "--" + e.attribute['name'])
            self.device.click_ui2_element(tb)

    def deal_verify_page(self, last_page_node, ig_input):
        self.store_screen_shoot('verify-page')
        if len(last_page_node.EditNodes) == 1:
            self.log_input("No need to click to send verification code")
        else:
            self.find_send_code_and_click(last_page_node)
            self.log_input("Wait for verification code to be sent...")
            time.sleep(10)
        try:
            verify_code = self.pick_verify_code(last_page_node)
        except:
            verify_code = ''
        if not verify_code:
            return False
        else:
            add_re = add_verify_code_into_input(ig_input, verify_code)
            return add_re

    def pick_verify_code(self, current_node) -> str:
        PEString = 'PhoneEmail'
        PString = 'Phone'
        EString = 'Email'
        judgeres = self.judge_phone_or_email(current_node)
        if judgeres == PEString:
            return self.SI.get_near_verify_codes()
        elif judgeres == PString:
            return self.SI.only_get_phone_code()
        elif judgeres == EString:
            code = self.SI.only_get_email_code()
            if not code:
                # If no verification code is found, try to process the verification link in the email
                self.SI.request_verify_links()
            return code

    def judge_phone_or_email(self, thisnode):
        PEString = 'PhoneEmail'
        PString = 'Phone'
        EString = 'Email'
        verifytypes = set()
        if thisnode.EditNodes:
            for e in thisnode.EditNodes:
                desc = ';'.join(e.get_desc())
                etype = sentence2type(desc)
                if etype:
                    verifytypes.add(etype[0][0])
            if 'Phone' in verifytypes and 'Email' in verifytypes:
                return PEString
            elif 'Phone' in verifytypes:
                return PString
            elif 'Email' in verifytypes:
                return EString
            else:
                return PEString

    def update_node(self, ui_node, text_input):
        # uinode.update_widgets_by_device(self.total_device.dump_raw_xml())
        ui_node.set_text_input(text_input)

    def handle_multi_box(self, class_name):
        count = 0
        try:
            for cb in self.device.get_elements_by_class_type(class_name):
                if not cb.info["checked"]:
                    cb.click()
                    count += 1
        except:
            traceback.print_exc()
        finally:
            return count

    def handle_check_box(self):
        return self.handle_multi_box('android.widget.CheckBox')

    def handle_radio_button(self):
        return self.handle_multi_box('android.widget.RadioButton')

    def get_tree_widget(self, page, deviceWidget):
        di = self.device.get_element_info(deviceWidget)
        format_bound = self.get_format_bound(di)
        for e in page.AllNodes:
            if e.attribute["classType"] == di["className"] and e.attribute["bound"] == format_bound:
                return e
        return None

    def get_format_bound(self, element_info):
        return [(element_info["bounds"]["left"], element_info["bounds"]["top"]),
                (element_info["bounds"]["right"], element_info["bounds"]["bottom"])]

    def get_resource_id(self, curNode, deviceWidget):
        di = self.device.get_element_info(deviceWidget)
        for e in curNode.AllNodes:
            if e.attribute["classType"] == di["className"] and is_same_bound(e.attribute["bound"], di["bounds"]):
                return e.attribute["resourceID"]
        return ""

    def my_send_keys(self, edit_element, content, sdkInt):
        if sdkInt >= 17:
            # not applicable for password editText under Android version 4.1
            edit_element.clear_text()
        edit_element.set_text(content)

    def up_down_swipe_element(self, device, btn):
        btnInfo = self.device.get_element_info(btn)
        btnBound = btnInfo["bounds"]
        btnWidth = btnBound["right"] - btnBound["left"]
        btnHeight = btnBound["bottom"] - btnBound["top"]
        device.swipe(btnBound["left"] + btnWidth / 2, btnBound["top"] + btnHeight / 2,
                     btnBound["left"] + btnWidth / 2, btnBound["top"] + btnHeight / 2 * 3)

    def up_down_swipe(self, device, formatBounds):
        btnWidth = formatBounds[1][0] - formatBounds[0][0]
        btnHeight = formatBounds[1][1] - formatBounds[0][1]
        device.swipe(formatBounds[0][0] + btnWidth / 2, formatBounds[0][1] + btnHeight / 2,
                     formatBounds[0][0] + btnWidth / 2, formatBounds[0][1] + btnHeight / 2 * 3)

    def send_input(self, text_input, last_node):
        self.log_input("TextInput:" + str(text_input))
        initEventCount = self.eventNum
        inevents = self.handle_check_box()
        self.add_event_count(inevents)
        inevents = self.handle_radio_button()
        self.add_event_count(inevents)
        if last_node.GenderNodes:
            self.device.click_ui2_element(self.get_click_element_by_node(last_node.GenderNodes[0]))
            self.add_event_count()
        if text_input:
            # Filter out edit node that does not require input
            if last_node.no_need_input():
                self.log_input("Events increment in sendInput: " + str(self.eventNum - initEventCount) + "\n")
                return last_node
            for editelement in self.device.get_elements_by_class_type("android.widget.EditText"):
                editelementNode = self.get_tree_widget(last_node, editelement)
                inputKeyHash = -1
                editelementId = ""
                if editelementNode is not None:
                    editelementId = editelementNode.attribute["resourceID"]
                    inputKeyHash = hash(editelementNode)
                dateKeywords = ['day', 'date', 'time']
                if editelementId and has_filter_key(split_resource_id(editelementId.lower()), dateKeywords):
                    inevents = self.handle_day_widget(self.device, editelement, self.sdkInt, text_input[inputKeyHash])
                    self.add_event_count(inevents)
                else:
                    if inputKeyHash not in text_input:
                        self.log_input("No exists key in TextInput: " + str(inputKeyHash))
                        continue
                    self.device.click_ui2_element(editelement)
                    self.add_event_count()
                    time.sleep(self.ui_waiting_duration)
                    # If a new box appears after click, click one randomly
                    tmp_node = XmlTree("", self.device.dump_raw_xml())
                    if len(tmp_node.EditNodes) != len(last_node.EditNodes):
                        if len(tmp_node.ClickableNodes) != 0:
                            self.device.click_element(tmp_node.ClickableNodes[0])
                            time.sleep(self.ui_waiting_duration)
                    try:
                        neweditelement = None
                        if editelementNode is not None:
                            neweditelement = self.get_click_element_by_node(editelementNode)
                    except WebDriverException:
                        self.log_input("WebDriverException in SendInput")
                        self.log_input("Events increment in sendInput: " + str(self.eventNum - initEventCount))
                        return -1
                    if editelementNode is not None and neweditelement is None:
                        # checkedTextview
                        checkElements = self.device.get_elements_by_class_type('android.widget.CheckedTextView')
                        if checkElements:
                            self.device.click_ui2_element(
                                checkElements[random.randint(0, len(checkElements) - 1)])
                            self.add_event_count()
                    else:
                        # Simulate the delete button before clearing, delete the text to a certain extent
                        self.device.press_del()
                        self.my_send_keys(editelement, text_input[inputKeyHash], self.sdkInt)
                        self.add_event_count()
            try:
                for editelement in self.device.get_elements_by_class_type('android.widget.EditText'):
                    editelementNode = self.get_tree_widget(last_node, editelement)
                    if editelementNode is not None and editelementNode.attribute['password'] == "false":
                        inputKeyHash = hash(editelementNode)
                        if inputKeyHash in text_input:
                            text_input[inputKeyHash] = self.device.get_element_info(editelement)['text']
                            logger.info(
                                "Update input dict: " + str(inputKeyHash) + " : " + str(text_input[inputKeyHash]))
                    else:
                        continue
            except:
                logger.info("Update input error")
                traceback.print_exc()

            self.log_input("Events increment in sendInput: " + str(self.eventNum - initEventCount))
            return last_node
        else:
            self.log_input("textInput is Empty!")
            self.log_input("Events increment in sendInput: " + str(self.eventNum - initEventCount))
            return last_node

    def add_event_count(self, num=1):
        self.eventNum += num
        if self.timeWorker:
            self.timeWorker.update_event_count(num)

    def handle_out_of_app(self):
        count = 0
        while self.device.get_current_package() != self.pkg_name:
            if count > 5:
                break
            un = XmlTree("", self.device.dump_raw_xml())
            if len(un.ButtonNodes) == 2 and 'allow' in un.ButtonNodes[1].attribute['text'].lower():
                self.log_input("Click Allow Button: " + un.ButtonNodes[1].attribute['resourceID'] + '--' +
                               un.ButtonNodes[1].attribute['text'])
                self.device.click_ui2_element(self.get_click_element_by_node(un.ButtonNodes[1]))
                self.add_event_count()
                count += 1
                continue
            count += 1
            self.device.press_back()
            self.add_event_count()
        if count > 5:
            self.log_input("over count in handling out of app")
            return False
        else:
            return True

    def log_input(self, my_input):
        try:
            if type(my_input) != str:
                self.exerciserLog.write(str(my_input) + '\n')
            else:
                self.exerciserLog.write(my_input + '\n')
        except:
            traceback.print_exc()

    def handle_day_widget(self, device, edit_element, sdk_int, date_string):
        count = 0
        self.device.click_ui2_element(edit_element)
        count += 1
        if '/' in date_string:
            tmpArr = date_string.split('/')
            yearStr = tmpArr[0]
            monthStr = tmpArr[1]
            dayStr = tmpArr[2]
        else:
            yearStr = '0000'
            monthStr = '10'
            dayStr = '10'
        es = self.device.get_elements_by_class_type("android.widget.EditText")
        if es:
            for e in es:
                tt = self.device.get_element_info(e)['text']
                texttype = date_str_type(tt)
                tmpNode = XmlTree("", self.device.dump_raw_xml())
                eid = self.get_resource_id(tmpNode, e)
                if 'day' in eid or texttype == 'Day':
                    self.my_send_keys(e, dayStr, sdk_int)
                    count += 1
                    if self.device.get_element_info(e)['text'] != dayStr:
                        break
                elif texttype == 'StrMonth':
                    self.my_send_keys(e, 'Jan', sdk_int)
                    count += 1
                    if self.device.get_element_info(e)['text'] != 'Jan':
                        break
                elif 'month' in eid or texttype == 'Day':
                    self.my_send_keys(e, dayStr, sdk_int)
                    count += 1
                    if self.device.get_element_info(e)['text'] != dayStr:
                        break
                elif 'year' in eid or texttype == 'Year':
                    self.my_send_keys(e, yearStr, sdk_int)
                    count += 1
                    if self.device.get_element_info(e)['text'] != yearStr:
                        break
                else:
                    continue
        okid = ''
        btns = self.device.get_elements_by_class_type("android.widget.Button")
        for btn in btns:
            btntext = self.device.get_element_info(btn)['text']
            if date_str_type(btntext) == "Year":
                countTime = abs(int(btntext.strip()) - int(yearStr))
                if countTime > 22:
                    countTime = 1
                else:
                    countTime += 1
                formatBounds = self.get_format_bound(self.device.get_element_info(btn))
                for i in range(countTime):
                    self.up_down_swipe(device, formatBounds)
                break
            elif date_str_type(btntext):
                self.device.click_ui2_element(btn)
                count += 1
                if btntext == self.device.get_element_info(btn)['text']:
                    self.up_down_swipe_element(device, btn)
                    count += 1
            if 'ok' in btntext or 'done' in btntext:
                tmpNode = XmlTree("", self.device.dump_raw_xml())
                okid = self.get_resource_id(tmpNode, btn)
        if okid:
            self.device.click_ui2_element(self.device.get_elements_by_resource_id(okid))
            count += 1
            return count
        else:
            for btn in btns:
                btntext = self.device.get_element_info(btn)['text'].lower()
                if 'ok' in btntext or 'done' in btntext:
                    self.device.click_ui2_element(btn)
                    count += 1
                    break
            return count


def check_mutate_state(last_node, this_node, new_toast):
    # 0 - no change, 1 - different from last UI, 2 - continuous ui mutate, 3 - alert mutate
    NO_CHANGE = 0
    NEW_UI = 1
    ALERT_MESSAGE = 2
    if not last_node.EditNodes:
        return NO_CHANGE
    if not this_node.compare_edit_node_id(last_node):
        return NEW_UI
    if new_toast:
        return ALERT_MESSAGE
    if this_node.ClassDict == last_node.ClassDict:
        return NO_CHANGE
    return ALERT_MESSAGE


def date_str_type(text):
    if text.isdigit():
        if len(text) == 4:
            return "Year"
        elif len(text) <= 2:
            return "Day"
        else:
            return ''
    else:
        if len(text) == 3:
            return "StrMonth"
        else:
            return ''


def get_toast(udid, toast_record):
    hook_tag = 'XposedHookToast: '
    logcat_lines = shell_cmd.execute('adb -s %s logcat -d XposedHookToast:D *:S' % udid, shell=True)[0]
    new_toasts = [line for line in logcat_lines if hook_tag in line and line not in toast_record]
    if not new_toasts:
        return toast_record, []
    toast_record += new_toasts
    toast_tag = new_toasts[-1].strip().split(hook_tag)[0]
    toast_contents = [line.strip().split(hook_tag)[-1] for line in new_toasts if
                      line.strip().split(hook_tag)[0] == toast_tag]
    return toast_record, toast_contents


def add_verify_code_into_input(text_input, verifycode):
    tag = get_input_by_type('VerifyCode')
    vs = [k for k in text_input if text_input[k] == tag]
    if len(vs) == 1:
        for k in text_input:
            if text_input[k] == tag:
                text_input[k] = verifycode
                return True
    elif len(vs) == len(verifycode):
        codes = [a for a in verifycode]
        c = 0
        for k in text_input:
            if text_input[k] == tag:
                text_input[k] = codes[c]
                c += 1
        return True
    else:
        return False


def log_text_to_file(file_operator, text_nodes):
    for tn in text_nodes:
        file_operator.write(tn.attribute['text'] + '\n')
    file_operator.write("------------------------------------\n")


def log_appear_text_to_file(file_operator, old_text_nodes, new_text_nodes):
    oset = set()
    for n in old_text_nodes:
        oset.add(n.attribute['text'])
    for n in new_text_nodes:
        if n.attribute['text'] not in oset:
            file_operator.write(n.attribute['text'] + '\n')
    file_operator.write("------------------------------------\n")
