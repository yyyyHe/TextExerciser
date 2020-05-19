# -*- coding: utf-8 -*-
import src.base.shell_cmd as shell
from src.triggers.te_trigger.app import App
import uiautomator2 as u2
from uiautomator2 import Device as u2_device
from src.triggers.te_trigger.node import Node
from src.base.xml_builder import XmlTree
from src.base.node_info import Node as xml_node
from func_timeout import func_set_timeout
import logging
import time
import re


class U2Exception(Exception):
    def __init__(self):
        super().__init__(self)

    def __str__(self):
        return 'u2 init timeout!'


class Device:
    def __init__(self, udid: str, logger: logging):
        self.udid = udid
        self.logger = logger
        self.shell = shell
        try:
            # device in uiautomator2
            self.device = self.init_device()
        except:
            raise U2Exception()
        self.press_home()
        time.sleep(2)
        self.home_package = self.get_current_package()
        self.home_activity = self.get_current_activity()
        self.logger.info('Device home package is %s' % self.home_package)
        self.sdk = self.device.info['sdkInt']

    @func_set_timeout(30)
    def init_device(self) -> u2_device:
        self.restart_agent()
        return u2.connect(self.udid)

    def init_u2(self):
        self.logger.info('Init uiautomator2...')
        self.shell.execute('uiautomator2 -s %s init' % self.udid, quiet=True, use_shlex=False, shell=True)

    def start_connection_agent(self):
        self.shell.execute_simply('adb -s %s shell /data/local/tmp/atx-agent server --nouia' % self.udid)

    def stop_connection_agent(self):
        self.shell.execute_simply('adb -s %s shell /data/local/tmp/atx-agent server --stop' % self.udid)

    def restart_agent(self):
        self.logger.info('Restart atx-agent...')
        self.stop_connection_agent()
        self.start_connection_agent()

    def get_installed_apps(self) -> list:
        apps = []
        result, err = self.shell.execute('adb -s %s shell pm list packages -f' % self.udid, quiet=True, use_shlex=False, shell=True)
        app_line_re = re.compile('package:(?P<apk_path>.+)=(?P<package>[^=]+)')
        for app_line in result:
            match_re = app_line_re.match(app_line)
            if match_re:
                apps.append(match_re.group('package'))
        return apps

    def install_app(self, app: App) -> bool:
        if app.pkg_name in self.get_installed_apps():
            self.logger.info('App already exist, now uninstalling and install again...')
            self.uninstall_app(app)
        result, err = self.shell.execute('adb -s %s install %s' % (self.udid, app.app_path), quiet=True, use_shlex=False, shell=True)
        if app.pkg_name in self.get_installed_apps():
            self.logger.info('App installed successfully.')
            return True
        self.logger.error('App installed failed.\nFail Message:\n%s' % '\n'.join(result))
        return False

    def uninstall_app(self, app: App):
        self.shell.execute('adb -s %s uninstall %s' % (self.udid, app.pkg_name), quiet=True, use_shlex=False, shell=True)

    def start_app(self, app: App):
        self.device.app_start(app.pkg_name)

    def reboot(self):
        self.shell.execute_simply('adb -s %s reboot' % self.udid)

    def get_current_package_and_activity(self) -> dict:
        return self.device.app_current()

    def get_current_package(self) -> str:
        return self.get_current_package_and_activity()['package']

    def get_current_activity(self) -> str:
        return self.get_current_package_and_activity()['activity']

    def dump_raw_xml(self) -> str:
        return self.device.dump_hierarchy()

    def get_current_view_node(self) -> Node:
        return Node(XmlTree('', self.device.dump_hierarchy()), self.get_current_activity())

    def get_device(self) -> u2_device:
        return self.device

    def click_element(self, element: xml_node):
        position_x = (element.attribute['bound'][0][0] + element.attribute['bound'][1][0]) / 2
        position_y = (element.attribute['bound'][0][1] + element.attribute['bound'][1][1]) / 2
        self.device.click(position_x, position_y)

    def click_ui2_element(self, ui2_element):
        ui2_element.click()

    def press_back(self):
        self.device.press('back')

    def press_enter(self):
        self.device.press('enter')

    def press_home(self):
        self.device.press('home')

    def press_del(self):
        self.device.press("delete")

    def get_elements_by_class_type(self, class_type: str):
        return self.device(className=class_type)

    def get_elements_by_resource_id(self, resource_id: str):
        return self.device(resourceId=resource_id)

    def get_element_info(self, u2_element) -> dict:
        """
        uiautomator2 element info
        :param u2_element:
        :return: dict{attribute:value}
        """
        return u2_element.info

    def get_screen_shoot(self, path: str):
        self.device.screenshot(path)
