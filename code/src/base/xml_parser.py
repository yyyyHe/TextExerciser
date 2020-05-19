# -*- coding: utf-8 -*-
from code.src.base import shell_cmd


class A(object):
    def __init__(self, line):
        if 'android:' in line:
            self.key = line[line.find("android:") + 8:line.find("(")]
        else:
            self.key = line[line.find('A: ') + 3:line.find('=')]
        if 'type 0x1' in line:
            if 'Raw' in line:
                self.value = int(line[line.find(")0x") + 3:line.find(" (Raw")], 16)
            else:
                self.value = int(line[line.find(")0x") + 3:], 16)
        elif 'Raw:' in line:
            self.value = line[line.find('="') + 2:line.find('" (Raw')]
        elif '=@0x' in line:
            self.value = line[line.find('=@0x') + 1:]
        else:
            self.value = ""


class E(object):
    def __init__(self, startline):
        self.startline = startline
        self.category = startline[startline.find(': ') + 2:startline.find(' (')]
        self.As = []
        self.Es = []
        self.father = None
        self.level = startline.find('E:')


class Manifest(object):
    def __init__(self, apkpath):
        self.apkpath = apkpath
        self.activities = []
        self.services = []
        self.providers = []
        self.receivers = []
        self.permissions = []
        self.package = ''
        self.launchActivity = []

    def get_content_with_aapt(self):
        out, err = shell_cmd.execute('aapt d xmltree ' + '"' + self.apkpath + '"' + ' AndroidManifest.xml', quiet=True)
        if len(err) > 0 or len(out) < 1:
            return ""
        return out

    def parse(self):
        content = self.get_content_with_aapt()
        e = None
        a = None
        e_all = []
        for line in content:
            if ' E: ' in line:
                if not e:
                    e = E(line)
                    e_all.append(e)
                else:
                    ne = E(line)
                    if ne.level > e.level:
                        e.Es.append(ne)
                        ne.father = e
                        e = ne
                    else:
                        f = False
                        while e.father:
                            e = e.father
                            if ne.level > e.level:
                                e.Es.append(ne)
                                ne.father = e
                                f = True
                                break
                        if not f:
                            e = ne
                            e_all.append(e)
                        else:
                            e = ne
            if ' A: ' in line:
                na = A(line)
                e.As.append(na)
                if na.key == 'name' and na.value == 'android.intent.category.LAUNCHER':
                    e_father = e.father
                    e_grandfather = e_father.father
                    for each_a in e_grandfather.As:
                        if each_a.key == 'name':
                            self.launchActivity.append(each_a.value)

        e_all_manifest = e_all[0].Es
        for a in e_all[0].As:
            if a.key == 'package':
                self.package = a.value
        e_all_application = None
        for e in e_all_manifest:
            if e.category == 'application' and not e_all_application:
                e_all_application = e.Es
            if e.category == 'uses-permission':
                self.permissions.append(e.As[0].value)

        for e in e_all_application:
            if e.category == 'activity':
                activity = {}
                for a in e.As:
                    activity[a.key] = a.value
                self.activities.append(activity)
            if e.category == 'provider':
                provider = {}
                for a in e.As:
                    provider[a.key] = a.value
                self.providers.append(provider)
            if e.category == 'service':
                service = {}
                for a in e.As:
                    service[a.key] = a.value
                self.services.append(service)
            if e.category == 'receiver':
                receiver = {}
                for a in e.As:
                    receiver[a.key] = a.value
                self.receivers.append(receiver)
