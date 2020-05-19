# -*- coding: utf-8 -*-
from src.base import xml_parser


class App:
    def __init__(self, app_path: str):
        self.app_path = app_path
        self.manifest_info = xml_parser.Manifest(app_path)
        self.manifest_info.parse()
        self.pkg_name = self.manifest_info.package
        self.launch_activity = self.manifest_info.launchActivity[0]

    def show_app_info(self) -> str:
        return 'Testing App Info:\nPath: %s\nPackageName: %s\nMainActivity: %s' % (self.app_path, self.pkg_name, self.launch_activity)
