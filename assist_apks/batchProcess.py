# -*- coding: utf-8 -*-
import os


def get_device_info():
    device_names=[]
    device_udids=[]
    content = os.popen('adb devices -l').readlines()
    for line in content:
        tmparry = line.strip().split()
        if len(tmparry)==6:
            device_names.append(tmparry[2].split(':')[1])
            device_udids.append(tmparry[0])
    return device_udids,device_names


def get_device_version(udidlist):
    version_list=[]
    for udid in udidlist:
        content = os.popen('adb -s '+udid+' shell getprop ro.build.version.release').readlines()
        if len(content) == 1:
            version_list.append(content[0].strip())
    return version_list


def install_ap_ps(udidlist, apklist):
    for udid in udidlist:
        for apkpath in apklist:
            res = os.popen('adb -s '+udid+' install "'+apkpath+'"').read()
            print(res)


if __name__ == "__main__":
    udids, names=get_device_info()
    apklist=['disableflagsecure(GodEye).apk', 'com.wparam.nullkeyboard.apk', 'smsObserver.apk', 'UIAutoFuzzHook.apk']
    install_ap_ps(udids, apklist)



