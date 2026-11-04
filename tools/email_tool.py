#!/usr/bin/env python3
"""
邮箱工具 - 探索者-α 自主注册账号用
功能：检查收件箱、提取验证码
通过 credential_proxy 调用，不直接读取凭证文件
"""
import imaplib
import re
import sys
from datetime import datetime
from email.header import decode_header, make_header
from email.parser import BytesParser
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from tool_registry import tool
from tools.credential_proxy import _creds


def _email_cred() -> dict:
    """从凭证代理获取邮箱配置"""
    c = _creds().get("email", {})
    if not c or not c.get('username') or not c.get('password'):
        raise RuntimeError("email 凭证未配置")
    return c


def decode_str(s):
    if not s:
        return ''
    return str(make_header(decode_header(s or '')))


@tool(description="获取最近 N 封邮件的摘要（发件人/主题/日期/正文片段），用于人工排查。",
      category="email",
      when_not_to_use="自动提取验证码、发送邮件、删除邮件",
      disambiguation="只读最近邮件摘要；自动提取验证码用 extract_code，发送邮件需单独配置 SMTP")
def fetch_recent(count=5):
    e = _email_cred()
    mail = imaplib.IMAP4_SSL(e['imap_host'], e.get('imap_port', 993))
    mail.login(e['username'], e['password'])
    mail.select('INBOX')
    status, data = mail.search(None, 'ALL')
    ids = data[0].split()
    msgs = []
    for mid in reversed(ids[-count:]):
        status, msgdata = mail.fetch(mid, '(RFC822)')
        raw = msgdata[0][1]
        msg = BytesParser().parsebytes(raw)
        subject = decode_header(msg.get('Subject', ''))[0] if isinstance(msg.get('Subject'), list) else decode_str(msg.get('Subject', ''))
        from_ = decode_str(msg.get('From', ''))
        date = msg.get('Date', '')
        body = ''
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == 'text/plain':
                    body = part.get_payload(decode=True).decode('utf-8', 'ignore')
                    break
        else:
            body = msg.get_payload(decode=True).decode('utf-8', 'ignore') if msg.get_payload(decode=True) else ''
        msgs.append({'from': from_, 'subject': subject, 'date': date, 'body': body[:2000]})
    mail.logout()
    return msgs


@tool(description="从最近邮件中自动提取验证码（4-8位数字），支持指定发件人/主题过滤。",
      category="email",
      when_not_to_use="只看邮件摘要、发送邮件、管理邮箱",
      disambiguation="自动提取验证码；只看摘要用 fetch_recent，发送邮件需单独配置 SMTP")
def extract_code(text):
    """从文本中提取验证码：4-8位数字，优先匹配常见关键词附近"""
    patterns = [
        r'(?:verification|verify|code|验证码|安全码|OTP|PIN)[^0-9]{0,40}(\d{4,8})',
        r'(\d{4,8})\s*(?:is your|是你的|code)',
        r'(?:\b\d{6}\b)',
        r'(?:\b\d{4,8}\b)',
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(1)
    return None


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'check'
    site = None
    if '--site' in sys.argv:
        site = sys.argv[sys.argv.index('--site') + 1].lower()

    msgs = fetch_recent(5)
    if not msgs:
        print("(收件箱为空)")
        return

    if cmd == 'check':
        for m in msgs:
            print(f"[{m['date']}] From: {m['from']} | Subject: {m['subject']}")
            print(f"  Body: {m['body'][:300]}")
            print()
    elif cmd == 'subject':
        m = msgs[0]
        print(f"From: {m['from']}\nSubject: {m['subject']}\nDate: {m['date']}\n\n{m['body'][:1500]}")
    elif cmd == 'code':
        pool = [m for m in msgs if not site or site in m['from'].lower() or site in m['subject'].lower()]
        if not pool:
            print(f"(最近5封里没有来自 {site} 的邮件，验证码可能还没到)")
            return
        for m in pool:
            code = extract_code(f"{m['subject']} {m['body']}")
            if code:
                print(f"CODE:{code} (from: {m['from']}, subject: {m['subject']})")
                return
        print("(未在最近邮件中找到验证码，邮件可能还没到)")
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
