# -*- coding: utf-8 -*-
import threading
import time
import os
import platform
import traceback
import subprocess
from code.src.base import xml_parser
from code.src import globalConfig


class Worker(threading.Thread):
    def __init__(self, udid, apk_path, log_path, package_name):
        threading.Thread.__init__(self)
        self.start_time = time.time()
        # Log Dir
        if not os.path.exists(log_path):
            os.mkdir(log_path)
        self.log_path = os.path.join(log_path, package_name)
        if not os.path.exists(self.log_path):
            os.mkdir(self.log_path)
        self.udid = udid
        self.package_name = package_name
        self.apk_path = apk_path
        self.activity_log = None
        self.taint_log = None
        self.activity_over_time_log = None
        self.function_over_time_log = None
        self.count_time_flag = False
        self.ella_output_log = None
        self.activity_set = set()
        self.method_set = set()
        self.all_activity_set = get_all_activity(self.apk_path)
        self.error_set = set()
        self.taint_set = set()
        self.event_count = 0
        self.running_state = True

    def run(self):
        if globalConfig.tcpDumpSwitch:
            self.start_tcp_dump()
        # Activity Log
        fpath = os.path.join(self.log_path, 'activityCoverage.txt')
        self.activity_log = open(fpath, 'w', buffering=1, encoding='utf-8')
        self.activity_log.write(str(self.all_activity_set) + '\n')
        self.activity_log.write('AllActivity: ' + str(len(self.all_activity_set)) + '\n')
        self.activity_log.write("==============================================================\n")
        # TaintDroid Log
        tpath = os.path.join(self.log_path, 'taintLog.txt')
        self.taint_log = open(tpath, 'w', buffering=1, encoding='utf-8')
        self.taint_log.write("udid:" + self.udid + "\n")
        self.taint_log.write("startTime:" + str(time.time()) + '\n')
        if self.count_time_flag:
            # Coverage change over time
            self.activity_over_time_log = open(os.path.join(self.log_path, 'CoverageOverTime.txt'), 'w', buffering=1,
                                               encoding='utf-8')
            self.activity_over_time_log.write(str(int(time.time() - self.start_time)) + ',0,0,0\n')
            # Function change over time
            self.functionOverTimeLog = open(os.path.join(self.log_path, 'functionOverTime.txt'), 'w', buffering=1)
            self.functionOverTimeLog.write(str(int(time.time() - self.start_time)) + ',0\n')
        time_activity = []
        loop_count = 0
        while self.running_state:
            try:
                activities = get_stack_activities(self.udid)
                for a in activities:
                    if a in self.activity_set or a not in self.all_activity_set:
                        continue
                    else:
                        self.activity_set.add(a)
                        self.activity_log.write(a + '\n')
                loop_count += 1
                #  record activity info every 10 min
                tc = (time.time() - self.start_time) // 600
                if len(time_activity) < tc:
                    time_activity.append('init')
                if time_activity and time_activity[-1] == 'init':
                    time_activity[-1] = str(len(self.activity_set))
                    self.activity_log.write(
                        str(len(time_activity) * 10) + " min -----------> " + time_activity[-1] + '\n')
                # log activity and function over time
                self.method_set = self.get_functions()
                if self.count_time_flag:
                    self.activity_over_time_log.write(
                        str(int(time.time() - self.start_time)) + ',' + str(self.event_count) + ',' + str(
                            len(self.activity_set)) + ',' + str(len(self.method_set)) + '\n')
                    self.functionOverTimeLog.write(
                        str(int(time.time() - self.start_time)) + ',' + str(len(self.method_set)) + '\n')
            except:
                self.activity_log.write(traceback.format_exc() + '\n')
        return

    def update_event_count(self, eventNum=1):
        self.event_count += eventNum

    def get_functions(self):
        if self.ella_output_log is None or not os.path.exists(self.ella_output_log):
            return set()
        lines = os.listdir(self.ella_output_log)
        if len(lines) > 1:
            coverage_file = ''
            for line in lines:
                if 'coverage' in line and line > coverage_file:
                    coverage_file = line
            if coverage_file:
                fpath = os.path.join(self.ella_output_log, coverage_file)
            else:
                fpath = os.path.join(self.ella_output_log, lines[0].strip())
        elif len(lines) == 1:
            fpath = os.path.join(self.ella_output_log, lines[0].strip())
        else:
            return set()
        mset = set()
        with open(fpath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            cc = 0
            for line in lines:
                line = line.strip()
                if not line or '#' in line:
                    pass
                else:
                    mset.add(line)
        return mset

    def end_thread(self, is_error=False, error_msg=''):
        self.running_state = False
        time.sleep(1)
        if is_error:
            self.cal_activity_coverage(is_error, error_msg)
        else:
            self.cal_activity_coverage()
        self.end_taint_log()
        if globalConfig.tcpDumpSwitch:
            self.end_tcp_dump()

    def end_thread_with_error(self, msg: str):
        self.end_thread(True, msg)

    def cal_activity_coverage(self, is_error=False, error_msg=''):
        if self.activity_log:
            self.activity_log.write("==============================================================\n")
            all_num = len(self.all_activity_set)
            this_num = len(self.activity_set)
            self.activity_log.write('AllActivity: ' + str(all_num) + '\n')
            self.activity_log.write('Monkey: ' + str(this_num) + '\n')
            self.activity_log.write('Coverage: ' + str(round(this_num * 100 / all_num)) + '%')
            if is_error:
                self.activity_log.write('=== ENDERROE: %s ===' % error_msg)
            self.activity_log.close()

    def end_taint_log(self):
        if self.taint_log:
            self.taint_log.write("endTime:" + str(time.time()))
            self.taint_log.close()

    def start_tcp_dump(self):
        cmd = ['adb', '-s', self.udid, 'shell', 'mkdir', '/sdcard/TcpDump']
        os.popen(' '.join(cmd))
        cmd = ['adb', '-s', self.udid, 'shell', '/data/local/tcpdump', '-X', '-s', '0', '-w',
               '/sdcard/TcpDump/' + self.package_name + '.pcap']
        os.popen(' '.join(cmd))

    def end_tcp_dump(self):
        kill_process(self.udid, '/data/local/tcpdump')
        cmd = ['adb', '-s', self.udid, 'pull', '/sdcard/TcpDump/' + self.package_name + '.pcap', self.log_path]
        os.popen(' '.join(cmd))


def kill_process(udid, processName):
    if platform.system() == "Linux":
        cmd = 'adb -s %s shell ps | grep %s' % (udid, processName)
    else:
        cmd = 'adb -s %s shell ps | findstr /C:%s' % (udid, processName)
    try:
        cmd_result = os.popen(cmd).readlines()
        if len(cmd_result) >= 1:
            for line in cmd_result:
                cmd_result_list = line.strip().split()
                if cmd_result_list[8] == processName:
                    print('processId:', cmd_result_list[1])
                    if os.system('adb -s %s shell kill %s' % (udid, str(cmd_result_list[1]))) == 0:
                        return True
                    else:
                        return False
                else:
                    print('Error kill', cmd_result_list[8])
    except Exception:
        traceback.print_exc()
        return True


def get_stack_activities(udid):
    cur_system = platform.system()
    if cur_system == 'Linux':
        out = subprocess.check_output(
            ('adb -s %s shell dumpsys activity activities | grep "Run #" ' % udid).split()).splitlines()
    else:
        out = os.popen('adb -s %s shell dumpsys activity activities | findstr /C:"Run #" ' % udid).readlines()
    activity_list = []
    if len(out) == 0:
        return activity_list
    for line in out:
        line = line.strip()
        if type(line) != str:
            try:
                line = line.decode()
            except:
                line = str(line)
        arr = line.split()
        if len(arr) >= 5:
            acty = arr[4]
            if acty.endswith('}'):
                acty = acty[:-1]
            sidx = acty.find('/')
            if acty[sidx + 1] == '.':
                activity_list.append(acty.replace('/', ''))
                activity_list.append(acty[sidx + 1:])
            else:
                activity_list.append(acty[sidx + 1:])
    return activity_list


def get_all_activity(apk_path):
    manifest_info = xml_parser.Manifest(apk_path)
    manifest_info.parse()
    return set([activity['name'] for activity in manifest_info.activities if 'name' in activity])
