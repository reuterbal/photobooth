#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Photobooth - a flexible photo booth software
# Copyright (C) 2018  Balthasar Reuter <photobooth at re - web dot eu>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import logging
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import formatdate
from email import encoders

from pathlib import Path

from .WorkerTask import WorkerTask


def send_mail(send_from, send_to, subject, message, picture, filename,
              server, port, is_auth, username, password, is_tls):
    """Compose and send email with provided info and attachments.

    Based on https://stackoverflow.com/a/16509278

    Args:
        send_from (str): from name
        send_to (str): to name
        subject (str): message title
        message (str): message body
        picture (jpg byte_data): ByteIO data of the JPG picture
        filename (str): Filename of picture
        server (str): mail server host name
        port (int): port number
        is_auth (bool): server requires authentication
        username (str): server auth username
        password (str): server auth password
        is_tls (bool): use TLS mode
    """
    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = send_to
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(MIMEText(message))

    part = MIMEBase('application', "octet-stream")
    part.set_payload(picture.getbuffer())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition',
                    'attachment; filename="{}"'.format(filename))
    msg.attach(part)

    smtp = smtplib.SMTP(server, port)
    if is_tls:
        smtp.starttls()
    if is_auth:
        smtp.login(username, password)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.quit()


class PictureMailer(WorkerTask):

    def __init__(self, config):

        super().__init__()

        self._sender = config.get('Mailer', 'sender')
        self._recipient = config.get('Mailer', 'recipient')
        self._subject = config.get('Mailer', 'subject')
        self._message = config.get('Mailer', 'message')

        self._server = config.get('Mailer', 'server')
        self._port = config.getInt('Mailer', 'port')
        self._is_auth = config.getBool('Mailer', 'use_auth')
        self._user = config.get('Mailer', 'user')
        self._password = config.get('Mailer', 'password')
        self._is_tls = config.getBool('Mailer', 'use_tls')

    def do(self, picture, filename):

        logging.info('Sending picture to %s', self._recipient)
        send_mail(self._sender, self._recipient, self._subject, self._message,
                  picture, Path(filename).name, self._server, self._port,
                  self._is_auth, self._user, self._password, self._is_tls)
