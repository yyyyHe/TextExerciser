# -*- coding: utf-8 -*-
import shutil
import traceback
from src.base import con_logcat
from src.triggers.te_trigger.app import App
from src.triggers.te_trigger.device import Device
from src.triggers.te_trigger.node import Node
from src.triggers.te_trigger.graph import Graph
from src.triggers.te_trigger.edge import Edge
from src import globalConfig
from func_timeout import func_set_timeout
from src.base.node_info import Node as xml_node
from src.text_exerciser.te_checker import TEChecker
import func_timeout
import logging
import random
import time
import sys
import os


TE_LOGGER = None


def make_log_dir(path: str):
    folder = os.path.exists(path)
    if not folder:
        os.mkdir(path)
    else:
        shutil.rmtree(path)
        while True:
            if not os.path.exists(path):
                os.mkdir(path)
                break
            else:
                time.sleep(1)


class TETrigger:
    """
    UI Exploration class
    """
    def __init__(self, udid: str, op_throttle: int, app_path: str):
        """
        @param op_throttle: event interval
        """
        self.udid = udid
        self.app_path = app_path
        self.app = App(app_path)
        # init log folder
        self.con_log_path = os.path.join(globalConfig.TriggerLogPath, self.app.pkg_name)
        self.ui_log_path = os.path.join(globalConfig.UiLogPath, self.app.pkg_name)
        make_log_dir(self.con_log_path)
        make_log_dir(self.ui_log_path)
        # logger
        self.trigger_logger, self.te_logger = self.init_logger()
        globalConfig.te_logger = self.te_logger
        try:
            self.device = Device(udid, self.trigger_logger)
        except Exception as e:
            self.trigger_logger.error('Init device failed!')
            raise e
        self.automation_name = 'Uiautomator2'
        self.graph = Graph()
        self.ui_waiting_duration = op_throttle
        self.element_trying_count = 3
        self.log_worker = con_logcat.Worker(self.device.udid, self.app.app_path, globalConfig.TriggerLogPath, self.app.pkg_name)
        self.log_worker.setDaemon(True)
        sys.setrecursionlimit(1500)
        # TEChecker
        self.te_checker = TEChecker(self.device.udid, self.app.pkg_name, self.automation_name, self.device,
                                    self.log_worker, self.graph, self.ui_waiting_duration)

    def init_logger(self) -> tuple:
        level = logging.DEBUG if globalConfig.Debug else logging.INFO
        trigger_logger = logging.getLogger('TriggerLogger-%s' % self.app.pkg_name)
        formatter = logging.Formatter(fmt='%(name)s:    %(filename)s [line:%(lineno)d] %(levelname)s: %(message)s')
        print_handler = logging.StreamHandler()
        print_handler.setFormatter(formatter)
        print_handler.setLevel(level)
        trigger_logger.addHandler(print_handler)
        file_handler = logging.FileHandler(os.path.join(self.con_log_path, 'trigger_runtime_log.txt'), mode='a', encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        trigger_logger.addHandler(file_handler)
        trigger_logger.setLevel(logging.DEBUG)
        te_logger = logging.getLogger('TeLogger-%s' % self.app.pkg_name)
        formatter = logging.Formatter(fmt='%(name)s:    %(filename)s [line:%(lineno)d] %(levelname)s: %(message)s')
        print_handler = logging.StreamHandler()
        print_handler.setFormatter(formatter)
        print_handler.setLevel(level)
        te_logger.addHandler(print_handler)
        file_handler = logging.FileHandler(os.path.join(self.ui_log_path, 'te_runtime_log.txt'), mode='a', encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        te_logger.addHandler(file_handler)
        te_logger.setLevel(logging.DEBUG)
        return trigger_logger, te_logger

    def start_app_main_page(self):
        self.device.start_app(self.app)

    def is_within_app(self) -> bool:
        return self.device.get_current_package() == self.app.pkg_name

    def is_device_home(self) -> bool:
        return self.device.get_current_package() == self.device.home_package

    def is_permission_page(self) -> bool:
        return 'android.packageinstaller' in self.device.get_current_package()

    def start_app(self) -> bool:
        if self.device.install_app(self.app):
            self.start_app_main_page()
            time.sleep(self.ui_waiting_duration)
            count = 4
            while count > 0 and not self.device.get_current_view_node().clickable_elements:
                count -= 1
                time.sleep(self.ui_waiting_duration)
            if self.is_permission_page():
                self.handle_permission_alert(self.device.get_current_view_node())
                time.sleep(self.ui_waiting_duration)
            if self.is_within_app():
                self.trigger_logger.info('Start app successfully!')
                return True
            self.trigger_logger.error('Can not start app!')
        else:
            self.trigger_logger.error('Installation failed!')
        return False

    def get_need_explore_sub_nodes(self, node: Node, element: xml_node) -> [Node]:
        sub_nodes = self.graph.get_sub_nodes(node, Edge(Edge.TYPE_TRIGGER, element, Edge.ACTION_CLICK))
        return [sub_node for sub_node in sub_nodes if sub_node.get_unclicked_elements()]

    def process_elements(self, elements: [xml_node]) -> [xml_node]:
        sorted_elements = []
        back_elements = []
        for element in elements:
            if element.is_log_out():
                self.trigger_logger.info('Meet log out element!')
            elif element.is_back():
                self.trigger_logger.info('Meet back element!')
                back_elements.append(element)
            else:
                sorted_elements.append(element)
        random.shuffle(sorted_elements)
        sorted_elements.extend(back_elements)
        return sorted_elements

    def handle_permission_alert(self, node: Node):
        count = 8
        while count > 0 and self.is_permission_page():
            count -= 1
            for element in node.clickable_elements:
                if 'allow' in element.attribute['text'].lower():
                    e_id, e_class = element.attribute['resourceID'], element.attribute['classType']
                    self.trigger_logger.info('Handle permission alert, click %s' % e_id if e_id else e_class)
                    self.device.click_element(element)
                    break
            time.sleep(self.ui_waiting_duration)
            node = self.device.get_current_view_node()

    @func_set_timeout(globalConfig.BackFindTimeout)
    def back_to_node(self, current_node: Node, target_node: Node) -> bool:
        if current_node.is_same_node(target_node):
            return True
        if self.graph.is_has_path(target_node, current_node):
            self.device.press_back()
            time.sleep(self.ui_waiting_duration)
            current_node = self.graph.get_node(self.device.get_current_view_node())
            return self.back_to_node(current_node, target_node)
        elif self.graph.is_has_path(current_node, target_node):
            if current_node.last_ig_input is not None:
                self.te_checker.send_input(current_node)
            next_node = list(self.graph.get_path_between(target_node, current_node))[1]
            for trans_edge in self.graph.get_edge(current_node, next_node):
                trans_action = trans_edge.action
                if trans_action == Edge.ACTION_ERROR:
                    continue
                elif trans_action == Edge.ACTION_ENTER:
                    self.device.press_enter()
                    time.sleep(self.ui_waiting_duration)
                    current_node = self.graph.get_node(self.device.get_current_view_node())
                    return self.back_to_node(current_node, target_node)
                else:
                    element = current_node.get_element_by_index(trans_edge.get_element_index())
                    self.device.click_element(element)
                    time.sleep(self.ui_waiting_duration)
                    current_node = self.graph.get_node(self.device.get_current_view_node())
                    return self.back_to_node(current_node, target_node)
        else:
            return False
        return False

    @func_set_timeout(globalConfig.TETimeout)
    def explore_app(self):
        self.trigger_logger.info('Begin to explore the app...')
        root_node = self.device.get_current_view_node()
        self.graph.add_root_node(root_node)
        self.explore_current_node(root_node)

    def explore_current_node(self, source_node: Node):
        self.trigger_logger.info('Explore the node %s , activity %s' % (source_node.id, source_node.activity))
        # Recursively explore UI(page)
        while True:
            # deal with the situation where the page jumps out of the app
            if not self.is_within_app():
                if self.is_permission_page():
                    self.trigger_logger.info('Meet a permission alert!')
                    # Processing permission application window
                    self.handle_permission_alert(source_node)
                    time.sleep(self.ui_waiting_duration)
                    source_node = self.graph.get_node(self.device.get_current_view_node())
                elif self.is_device_home():
                    self.trigger_logger.info('Wrong back to device home, restart app main page...')
                    # If it jump to the desktop, restart main activity of the app
                    self.start_app_main_page()
                    time.sleep(self.ui_waiting_duration)
                    source_node = self.graph.get_node(self.device.get_current_view_node())
                else:
                    # if jump to the browser and other circumstances,
                    # keep clicking back until return to the app or back to the desktop, and then return
                    while True:
                        if self.is_within_app() or self.is_device_home():
                            break
                        self.trigger_logger.info('Out off app! Press back now...')
                        self.device.press_back()
                        time.sleep(2 * self.ui_waiting_duration)
                    return
            # Determine whether it need to call TE
            if source_node.is_has_edit and source_node.is_need_exercise():
                self.trigger_logger.info('There is edit box in this page, invoke text_exerciser...')
                try:
                    result, back_node = self.te_checker.check_for_exercise(source_node)
                    if back_node is not None:
                        # Back to the target node, and update the status of the node on the path from back_node to source_node
                        nodes_in_path = self.graph.get_path_between(source_node, back_node)
                        self.trigger_logger.info('Need to back...')
                        self.trigger_logger.info('Prepare to back...')
                        for i, ui_node in enumerate(nodes_in_path):
                            ui_node.reset_exercised_state()
                            if i < len(nodes_in_path) - 1:
                                for edge in self.graph.get_edge(ui_node, nodes_in_path[i + 1]):
                                    ui_node.get_element_by_index(edge.get_element_index()).attribute['is_clicked'] = False
                        try:
                            self.trigger_logger.info('Begin to back...')
                            self.back_to_node(source_node, back_node)
                            self.trigger_logger.info('Back finish!')
                        except:
                            print(traceback.format_exc())
                            self.trigger_logger.info('Timeout! Can not back.')
                    trans_edge = None
                except Exception:
                    self.trigger_logger.error('TE bugs!', exc_info=True)
                    trans_edge = Edge(Edge.TYPE_TE, None, Edge.ACTION_ERROR)
            else:
                elements = source_node.get_unclicked_elements()
                if not elements:
                    for element in source_node.clickable_elements:
                        e_id, e_count = element.attribute['resourceID'], element.attribute['explore_count']
                        if self.get_need_explore_sub_nodes(source_node, element) and e_count <= self.element_trying_count:
                            self.trigger_logger.info('Element %s has sub node needed to explore，reset the click status' % e_id)
                            element.attribute['is_clicked'] = False
                            elements.append(element)
                    if not elements:
                        self.trigger_logger.info('Finish Current Page explosion, press back!')
                        self.device.press_back()
                        time.sleep(self.ui_waiting_duration)
                        return
                element = self.process_elements(elements)[0]
                e_id, e_class = element.attribute['resourceID'], element.attribute['classType']
                tag = e_id if e_id else e_class
                try:
                    self.device.click_element(element)
                    element.attribute['is_clicked'] = True
                    element.attribute['explore_count'] += 1
                    self.trigger_logger.info('Click element %s' % tag)
                    trans_edge = Edge(Edge.TYPE_TRIGGER, element, Edge.ACTION_CLICK)
                except Exception:
                    source_node = self.graph.get_node(self.device.get_current_view_node())
                    self.trigger_logger.warning('Can not find target element, UI may has changed!')
                    continue
            time.sleep(self.ui_waiting_duration)
            tmp_node = self.device.get_current_view_node()
            if source_node.is_same_node(tmp_node):
                self.trigger_logger.info('Nothing changed, try to explore next element!')
                continue
            self.trigger_logger.info('Ui status has changed!')
            next_node = self.graph.get_node(tmp_node)
            if self.is_within_app() and trans_edge is not None:
                self.graph.add_nodes_with_edge(source_node, next_node, trans_edge)
            self.explore_current_node(next_node)
            source_node = self.graph.get_node(self.device.get_current_view_node())

    def run_trigger(self):
        self.log_worker.start()
        try:
            if self.start_app():
                self.explore_app()
                self.log_worker.end_thread()
            else:
                self.trigger_logger.error('Stop testing!')
                self.log_worker.end_thread_with_error('StartFailed')
        except func_timeout.FunctionTimedOut:
            self.trigger_logger.info('Timeout!')
            self.log_worker.end_thread()
        except Exception as e:
            self.trigger_logger.error('Something error!', exc_info=True)
            self.log_worker.end_thread_with_error('UnkonwnError')
            self.trigger_logger.info('Finish test.')
            self.device.uninstall_app(self.app)
            raise e
        self.trigger_logger.info('Finish test.')
        self.device.uninstall_app(self.app)
        self.te_checker.end_te_checker()
