# -*- coding: utf-8 -*-
from code.src import globalConfig
import os


class ApkListGenerator(object):
    """
    Get apk list
    """
    def __init__(self, apk_path: str) -> None:
        super().__init__()
        self.apk_path = apk_path

    def get_need_run_list(self, log_path: str = globalConfig.TriggerLogPath) -> list:
        has_ran_apks = set(os.listdir(log_path))
        apks = set([apk[:-4] for apk in os.listdir(self.apk_path)])
        all_need_run_apks = ['%s/%s.apk' % (self.apk_path, apk) for apk in apks - has_ran_apks]
        print('All apk number: %s\nHas ran apk number: %s\nFinal need run number: %s' % (len(apks), len(has_ran_apks), len(all_need_run_apks)))
        return all_need_run_apks

