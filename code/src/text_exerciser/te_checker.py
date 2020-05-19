# -*- coding: utf-8 -*-
import traceback
from code.src import Device
from code.src import TextExerciser
import time
import os
from code.src import globalConfig
from code.src import Node


class TEChecker:
    """
    TE entry
    """

    def __init__(self, udid, test_pkg, automation_name, device: Device, time_worker, graph, ui_waiting_duration):
        self.udid = udid
        self.device = device.device
        self.total_device = device
        self.testPkg = test_pkg
        self.sdkInt = self.total_device.sdk
        self.exploredNodeList = []
        self.automationName = automation_name
        self.timeWorker = time_worker
        self.checkNodeRecord = []
        self.exceptionPages = []
        self.graph = graph
        self.ui_waiting_duration = ui_waiting_duration
        # package folder
        self.logPath = os.path.join(globalConfig.UiLogPath, test_pkg)
        self.exerciserLog = open(os.path.join(self.logPath, globalConfig.ExerciseLogName), 'w', errors='ignore',
                                 buffering=1, encoding='utf-8')
        self.lukasRawTextLog = open(os.path.join(self.logPath, globalConfig.LukasRawTextLogName), 'w', errors='ignore',
                                    buffering=1, encoding='utf-8')
        self.appearTextLog = open(os.path.join(self.logPath, globalConfig.AppearTextLogName), 'w', errors='ignore',
                                  buffering=1, encoding='utf-8')
        self.chaoticLog = open(os.path.join(self.logPath, globalConfig.ChaoticLogName), 'w', errors='ignore',
                               buffering=1, encoding='utf-8')
        self.improveLog = open(os.path.join(self.logPath, globalConfig.ImprovementLogName), 'w', errors='ignore',
                               buffering=1, encoding='utf-8')
        self.register_info = []
        globalConfig.OUTPUT_MODE = self.chaoticLog
        global logger
        logger = globalConfig.te_logger

    def send_input(self, node: Node):
        TE = TextExerciser(self.device, self.udid, self.testPkg, self.sdkInt,
                           self.logPath, self.exerciserLog, self.lukasRawTextLog, self.appearTextLog,
                           self.timeWorker, self.graph, self.ui_waiting_duration, self.register_info)
        TE.send_input(node.last_ig_input, node.page)

    def check_for_exercise(self, start_node: Node) -> (bool, Node or None):
        event_count = 0
        if self.total_device.get_current_package() != self.testPkg:
            return False, None
        try:
            cur_node = start_node.page
            if not cur_node.EditNodes:
                self.exerciserLog.write("No EditTexts!")
                return False, None
            self.checkNodeRecord.append(cur_node)
            if globalConfig.translateSwitch:
                globalConfig.TETranslateON = True
            self.exerciserLog.write("*************startTime:" + str(time.time()) + '\n')
            TE = TextExerciser(self.total_device, self.udid, self.testPkg, self.sdkInt,
                               self.logPath, self.exerciserLog, self.lukasRawTextLog, self.appearTextLog,
                               self.timeWorker, self.graph, self.ui_waiting_duration, self.register_info)
            # log Activity and Method at beginning of TE handler
            self.log_improvement_to_file('begin')
            back_node = None
            try:
                result, back_node = TE.page_handle(start_node)
            except:
                print("PageHandler Exception")
                traceback.print_exc()
                if not cur_node.in_pages(self.exceptionPages):
                    self.exceptionPages.append(cur_node)
                result = False
            event_count += TE.eventNum
            self.log_improvement_to_file('end')
            self.exerciserLog.write("result:" + str(result) + '\n')
            self.exerciserLog.write("Add Event: " + str(TE.eventNum) + "\n")
            self.exerciserLog.write("*************endTime:" + str(time.time()) + '\n')
            logger.info("text_exerciser:" + str(result))
            return result, back_node
        except:
            print("Except in checkForTextExerciser")
            traceback.print_exc()
            return False, None
        finally:
            globalConfig.TETranslateON = False

    def log_improvement_to_file(self, flag):
        if not self.timeWorker:
            self.improveLog.write("None Object: timeWorker!!!!!")
            return
        if flag == 'begin':
            self.improveLog.write("*************\n")
            self.improveLog.write("Before TE:\n")
        else:
            self.improveLog.write("After TE:\n")
        self.improveLog.write(
            "Activity," + str(len(self.timeWorker.activity_set)) + ',' + str(self.timeWorker.activity_set) + '\n')
        self.improveLog.write(
            "Method," + str(len(self.timeWorker.method_set)) + '\n')
        if flag == 'end':
            self.improveLog.write("*************\n")

    def end_te_checker(self):
        # End Log
        self.exerciserLog.close()
        self.lukasRawTextLog.close()
        self.appearTextLog.close()
        self.chaoticLog.close()
        self.improveLog.close()
