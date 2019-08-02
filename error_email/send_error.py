from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr
import smtplib

"""
爬虫发生异常时发送邮件通知
"""


def _format_addr(s):
    """

    :param s:
    :return:
    """
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr))


# 发送人地址
from_addr = 'your email'

# 邮箱密码
password = 'your password'

# 收件人地址
to_addr = ''

# 163网易邮件服务器地址
smtp_server = 'smtp.163.com'

# 设置邮件信息
# 第一种平文
msg = MIMEText('python 爬虫运行异常，异常信息为遇到 Http 403', 'plain', 'utf-8')


# 构造邮件
msg['from'] = _format_addr('Python绿色通道<%s>' % from_addr)
msg['to'] = _format_addr('Python绿色通道<%s>' % to_addr)
msg['subject'] = Header("Python绿色通道爬虫云星星状态", 'utf-8').encode()

# 发送邮件
server = smtplib.SMTP(smtp_server, 25)
server.login(from_addr, password)
server.sendmail(from_addr, [to_addr], msg.as_string())
server.quit()
