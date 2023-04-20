import configparser
import smtplib
import time
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class Email:
    def __init__(self, sender_email, sender_password, host_server, receiver_email, subject, body):
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.receiver_email = receiver_email
        self.subject = subject
        self.body = body
        self.host_server = host_server

    def send_email(self):
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = self.receiver_email
        msg['Subject'] = self.subject

        msg.attach(MIMEText(self.body, 'plain'))

        server = smtplib.SMTP(self.host_server, 587)
        server.starttls()
        server.login(self.sender_email, self.sender_password)
        text = msg.as_string()
        server.sendmail(self.sender_email, self.receiver_email, text)
        server.quit()

    def send_email_with_attachment(self, file_path):
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = self.receiver_email
        msg['Subject'] = self.subject
        self.body = open(file_path, 'r', encoding='utf8').read()
        msg.attach(MIMEText(self.body, 'plain'))

        output_file = file_path.replace('md', 'html')
        # md_2_html(file_path, output_file)
        with open(output_file, "rb") as attachment:
            part = MIMEApplication(attachment.read())
            part.add_header('Content-Disposition', 'attachment', filename=output_file.split('/')[-1])
            msg.attach(part)

        server = smtplib.SMTP_SSL(self.host_server, 465)
        server.login(self.sender_email, self.sender_password)
        text = msg.as_string()
        server.sendmail(self.sender_email, self.receiver_email, text)
        server.quit()

    def send_email_with_delay(self, delay_in_seconds):
        time.sleep(delay_in_seconds)
        self.send_email()

import markdown
def md_2_html(input_file, output_file):
    with open(input_file, 'r', encoding='utf8') as f:
        text = f.read()
        html = markdown.markdown(text)
    with open(output_file, 'w', encoding='utf8') as w:
        w.write(html)

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config.ini')

    host_server = config.get('Email', 'HOST_SERVER')
    host_password = config.get('Email', 'HOST_PASSWORD')
    sender_email = config.get('Email', 'SENDER')

    myemail = Email(
        sender_email=sender_email,
        sender_password=host_password,
        host_server=host_server,
        receiver_email='',
        subject='今天的论文更新',
        body='今天的论文更新',
    )

    myemail.send_email_with_attachment('./Output/2023_04_05.md')
