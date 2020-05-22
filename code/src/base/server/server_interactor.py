# -*- coding: utf-8 -*-
import imaplib
import json
import re
import time
import difflib
from src.text_exerciser.mutate.nlp import regulations
import urllib.request
from src.base import shell_cmd as shell
from email.parser import Parser
from email.header import decode_header
from src import globalConfig


class ServerInteractor:
    def __init__(self, pkg_name, host=globalConfig.EmailHost, username=globalConfig.EmailAddress, password=globalConfig.EmailPwd,
                 port=globalConfig.EmailPort):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.connection = None
        self.verify_code_record = []
        self.getCount = 0
        self.pkg_name = pkg_name

    def cal_similarity(self, title: str):
        if not isinstance(title, str):
            return 0
        return difflib.SequenceMatcher(None, self.pkg_name, title).quick_ratio()

    def connect_server(self):
        try:
            self.connection = imaplib.IMAP4_SSL(self.host, self.port)
        except Exception:
            self.connection = imaplib.IMAP4(self.host, self.port)
        try:
            self.connection.login(self.username, self.password)
        except Exception as err:
            print('mailbox connecting failed', err)

    def close_connection(self):
        if self.connection is not None:
            self.connection.logout()

    def get_near_verify_codes(self) -> str:
        phone_code = self.only_get_phone_code()
        email_code = self.only_get_email_code()
        if phone_code and email_code:
            return phone_code
        else:
            return email_code if email_code else phone_code

    def only_get_phone_code(self) -> str:
        self.getCount += 1
        return self.get_near_verify_codes_from_phone()

    def only_get_email_code(self) -> str:
        self.getCount += 1
        return self.get_near_verify_codes_from_email()

    def get_near_verify_codes_from_phone(self, num: int = 5):
        logcat_lines = shell.execute('adb -s %s logcat -d XposedHookToast:D *:S' % globalConfig.ReceiveSmsDeviceID, shell=True)[0]
        codes = {}
        for line in list(reversed(logcat_lines))[:num]:
            if 'HyySmsGettingJsonStr:' not in line:
                continue
            body = line.split('HyySmsGettingJsonStr:')[-1]
            code = match_verify_code(body)
            if code is not None and code not in self.verify_code_record:
                codes[code] = self.cal_similarity(body)
        if codes:
            return max(codes, key=codes.get)
        else:
            return ''

    def get_near_verify_codes_from_email(self, num: int = 4) -> str:
        if self.connection is None:
            self.connect_server()
        self.connection.select('INBOX')
        status, response = self.connection.search(None, 'ALL')
        msg_nums = response[0].split()
        listlength = len(msg_nums)
        codes = {}
        for i in range(1, listlength + 1):
            if i >= num:
                break
            _, data = self.connection.fetch(msg_nums[listlength - i], 'RFC822')
            text = data[0][1].decode('utf-8', errors='ignore')
            message = Parser().parsestr(text)
            content = get_content(message)
            if content == 'Content_type Error':
                continue
            subject = decode_str(message.get('Subject')).lower()
            # match title with pkg_name
            rank = self.cal_similarity(subject)
            code = match_verify_code(subject)
            if code is not None:
                if code not in self.verify_code_record:
                    self.verify_code_record.append(code)
                    self.close_connection()
                    codes[code] = rank
            else:
                code = match_verify_code(content)
                if code is not None and code not in self.verify_code_record:
                    self.verify_code_record.append(code)
                    self.close_connection()
                    codes[code] = rank
        if codes:
            return max(codes, key=codes.get)
        else:
            return ''

    def request_verify_links(self, num: int = 4):
        """
        deal with link in email
        """
        if self.connection is None:
            self.connect_server()
        t1 = time.time()
        self.connection.select('INBOX')
        status, response = self.connection.search(None, 'ALL')
        msg_nums = response[0].split()
        listlength = len(msg_nums)
        for i in range(1, listlength + 1):
            if i >= num:
                break
            _, data = self.connection.fetch(msg_nums[listlength - i], 'RFC822')
            text = data[0][1].decode('utf-8', errors='ignore')
            message = Parser().parsestr(text)
            subject = decode_str(message.get('Subject'))
            if 'code' in subject.lower():
                continue
            content = get_content(message)
            if content == 'Content_type Error':
                continue
            elif 'verify' in subject.lower() or 'confirm' in subject.lower():
                # click verify link
                urlList = find_all_url(content)
                for u in urlList:
                    urllib.request.urlopen(u)
        print("requestVerifyLinks", time.time() - t1)


def get_content(message):
    """
    Read the email
    """
    res = ''
    if message.is_multipart():
        parts = message.get_payload()
        for n, part in enumerate(parts):
            res += get_content(part)
            return res
    else:
        content_type = message.get_content_type()
        if content_type == 'text/plain' or content_type == 'text/html':
            content = message.get_payload(decode=True)
            charset = guess_charset(message)
            if charset:
                # if charset == 'gb2312':
                #     charset = 'gb18030'
                content = content.decode(charset, 'ignore')
            res += content
        else:
            print('Attachment: %s' % content_type)
            res = 'Content_type Error'
        return res


def guess_charset(msg):
    charset = msg.get_charset()
    if charset is None:
        content_type = msg.get('Content-Type', '').lower()
        pos = content_type.find('charset=')
        if pos >= 0:
            charset = content_type[pos + 8:].strip()
    return charset


def decode_str(s):
    value, charset = decode_header(s)[0]
    if charset:
        value = value.decode(charset)
    return value


def match_verify_code(string):
    """
    find verify code
    """
    if not isinstance(string, str):
        return None
    res = re.findall(r'(?<!\d)\d{6}(?!\d)', string)
    if not res:
        res = re.findall(r'(?<!\d)\d{4}(?!\d)', string)
    if res:
        return res[0]
    else:
        return None


def find_all_url(string):
    res = re.findall(regulations.URL_REGEX, string, re.IGNORECASE)
    return set(res)
