# -*- coding: utf-8 -*-
import argparse
import os
import json
from src import globalConfig


def main():
    """
    Entry of TE
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--apk', type=str, help='Your .apk file of the app you want to run')
    parser.add_argument('-f', '--folder', type=str, help='The folder including .apk files')
    parser.add_argument('-o', '--output', type=str, help='The output folder')
    parser.add_argument('-t', '--timeout', type=int, help='Timeout in seconds, default: 3600s')
    parser.add_argument('-c', '--count', type=int, help='The max mutate count, default: 10 times')
    parser.add_argument('-i', '--interval', type=int, help='"Interval in seconds between each two events, default: 3s')
    parser.add_argument('-d', '--device', nargs='+',
                        help='Devices to run TE. It supports multi devices working simultaneously, such as emulator-5554, emulator-5560 ...')
    parser.add_argument('-j', '--json', type=str,
                        help='Rewrite the config.json file and provide your account information(e.g. email, phone) to receive verify code.')
    parser.add_argument('--debug', action='store_true', help='Open debug switch to log run some time information.')
    args = parser.parse_args()
    op_throttle = args.interval if args.interval else 3
    devices = args.device if args.device else [line.split('\t')[0] for line in
                                               os.popen("adb devices", 'r', 1).read().split('\n') if
                                               len(line) != 0 and line.find('\tdevice') != -1]
    if args.output:
        globalConfig.LogPath = args.output
        globalConfig.UiLogPath = os.path.join(args.output, 'TELog')
        globalConfig.TriggerLogPath = os.path.join(args.output, 'TriggerLog')
        globalConfig.DispatcherLogPath = os.path.join(args.output, 'DispatcherLog')
    log_path = globalConfig.LogPath
    if not os.path.exists(log_path):
        os.mkdir(log_path)
    if not os.path.exists(globalConfig.DispatcherLogPath):
        os.mkdir(globalConfig.DispatcherLogPath)
    if not os.path.exists(globalConfig.TriggerLogPath):
        os.mkdir(globalConfig.TriggerLogPath)
    if not os.path.exists(globalConfig.UiLogPath):
        os.mkdir(globalConfig.UiLogPath)
    if args.timeout:
        globalConfig.TETimeout = args.timeout
    if args.count:
        globalConfig.MaxMutateTime = args.count
    j_path = args.json if args.json else os.path.join(os.path.dirname(__file__), '../config.json')
    interact_info = json.load(open(j_path, 'r'))
    globalConfig.EmailHost = interact_info['EmailHost']
    globalConfig.EmailAddress = interact_info['EmailAddress']
    globalConfig.EmailPwd = interact_info['EmailPwd']
    globalConfig.EmailPort = interact_info['EmailPort']
    globalConfig.PhoneNumber = interact_info['PhoneNumber']
    globalConfig.ReceiveSmsDeviceID = interact_info['ReceiveSmsDeviceID']
    if args.debug:
        globalConfig.Debug = True
    check_nltk()
    if args.apk:
        from src.triggers.te_trigger.te_trigger import TETrigger
        TETrigger(devices[0], op_throttle, args.apk).run_trigger()
    elif args.folder:
        from src.triggers.te_trigger_distribute import Task
        Task(args.folder).analyze(devices, op_throttle)
    else:
        print('You must provide an apk file to test.')


def check_nltk():
    try:
        import nltk
    except:
        print('Please use pip install -r requirements.txt first.')
        return False
    try:
        from nltk.corpus import stopwords
    except:
        print('Download stopwords from nltk...')
        nltk.download('stopwords')
        print('Done..')
    try:
        from nltk.tokenize import punkt
    except:
        print('Download punkt from nlkt...')
        nltk.download('punkt')
        print('Done..')
    return True


if __name__ == "__main__":
    main()
