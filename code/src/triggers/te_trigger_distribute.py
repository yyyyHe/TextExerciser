# -*- coding: utf-8 -*-
import os
import pykka
import time
import logging
from code.src import ApkListGenerator
from code.src.triggers.te_trigger.te_trigger import TETrigger
from code.src import globalConfig


class Dispatch(pykka.ThreadingActor):
    def __init__(self, queue: list, udid_list: list, op_throttle: int):
        super(Dispatch, self).__init__()
        self.app_queue = queue
        self.alive_workers = []
        self.start_time = time.time()
        self.udid_list = udid_list
        self.op_throttle = op_throttle
        self.logger = logging.getLogger('DispatchLogger')
        self.init_logger()
        self.record = {}
        if self.app_queue:
            for udid in self.udid_list:
                worker = Worker.start(name='worker-%s' % udid, udid=udid)
                self.record[worker] = udid
                self.alive_workers.append(worker)
            self.logger.info('Begin dispatch...')
            for worker in self.alive_workers:
                app = self.app_queue.pop()
                self.logger.info('Dispatch worker-%s : %s' % (self.record[worker], app))
                worker.tell({'app_path': app, 'current_worker': self.actor_ref, 'op_throttle': self.op_throttle})
            self.alive_workers_num = len(self.alive_workers)
            self.logger.info('Workers num: %s' % len(self.alive_workers))
        else:
            self.logger.error('App list is empty! End!')
            self.stop()

    def init_logger(self):
        formatter = logging.Formatter(fmt='%(asctime)s %(filename)s [line:%(lineno)d] %(levelname)s: %(message)s', datefmt='%a, %d %b %Y %H:%M:%S')
        print_handler = logging.StreamHandler()
        print_handler.setFormatter(formatter)
        print_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(print_handler)
        file_handler = logging.FileHandler(os.path.join(globalConfig.DispatcherLogPath, 'DispatchLog-%s.txt' % time.strftime('%m-%d', time.localtime())), mode='a', encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        self.logger.setLevel(logging.DEBUG)

    def on_receive(self, message: dict):
        return_worker = message.get('worker')
        fail_count = message.get('fail_count')
        error_flag = message.get('is_error')
        if error_flag:
            self.logger.error('%s finish testing %s with error!' % (return_worker.name, return_worker.appPath))
            self.app_queue.append(return_worker.appPath)
        else:
            self.logger.info('%s finish testing %s!' % (return_worker.name, return_worker.appPath))
        if len(self.app_queue) > 0:
            # Stop using the device
                if error_flag and fail_count >= 2:
                    self.logger.error('%s has failed twice, stop using!' % return_worker.name)
                    return_worker.actor_ref.stop()
                    self.alive_workers.remove(return_worker)
                    self.alive_workers_num = self.alive_workers_num - 1
                    if self.alive_workers_num == 0:
                        self.logger.info('No living worker, stop dispatcher!')
                        self.stop()
                else:
                    app = self.app_queue.pop()
                    self.logger.info('Dispatch %s : %s' % (return_worker.name, app))
                    return_worker.actor_ref.tell({'app_path': app, 'current_worker': self.actor_ref, 'op_throttle': self.op_throttle})
        else:
            self.logger.info('app queue is empty. Stop %s' % return_worker.name)
            return_worker.actor_ref.stop()
            self.alive_workers.remove(return_worker)
            self.alive_workers_num = self.alive_workers_num - 1
            if self.alive_workers_num == 0:
                self.logger.info('No living worker, stop dispatcher!')
                end_time = time.time()
                total = end_time - self.start_time
                hour = total / 3600
                minute = (total % 3600) / 60
                second = total % 60
                self.logger.info('Consume time : ' + str(hour) + 'h' + str(minute) + 'm' + str(second) + 's')
                self.stop()


class Worker(pykka.ThreadingActor):
    def __init__(self, name: str, udid: str):
        super(Worker, self).__init__()
        self.name = name
        self.appPath = ''
        self.udid = udid

    def on_receive(self, message: dict):
        fail_count = 0
        self.appPath = message.get('app_path')
        currentWork = message.get('current_worker')
        op_throttle = message.get('op_throttle')
        try:
            te_trigger = TETrigger(self.udid, op_throttle, self.appPath)
            te_trigger.run_trigger()
        except Exception as e:
            print(e)
            is_error = True
            fail_count += 1
            # Deal error of atx-agent
            os.system('adb -s %s reboot' % self.udid)
            time.sleep(120)
        else:
            fail_count -= 1
            is_error = False
        currentWork.tell({'worker': self, 'fail_count': fail_count, 'is_error': is_error})


class Task(object):
    def __init__(self, apk_dirs, con_log_path=globalConfig.TriggerLogPath):
        self.dir = apk_dirs
        self.appPath = ApkListGenerator(self.dir).get_need_run_list(con_log_path)

    def analyze(self, udid_list, op_throttle):
        dispatch = Dispatch.start(queue=self.appPath, udid_list=udid_list, op_throttle=op_throttle)
        while not dispatch.is_alive:
            pass
