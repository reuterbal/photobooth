#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Photobooth - a flexible photo booth software
# Copyright (C) 2019  Balthasar Reuter <photobooth at re - web dot eu>
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

# This webserver was contributed by
# @oelegeirnaert (https://github.com/oelegeirnaert)
# see https://github.com/reuterbal/photobooth/pull/103
# based on https://github.com/keijack/python-simple-http-server

import datetime
import fnmatch
import logging
import os

from time import localtime, strftime, time

from simple_http_server import request_map
from simple_http_server import PathValue, StaticFile
from simple_http_server import Redirect

import simple_http_server.server as server


def get_template(name):

    html_file = '{}/templates/{}.html'.format(SimpleHttpServer.webroot, name)
    return open(html_file, 'r').read()


def get_html_stream(filename):

    return (SimpleHttpServer.html_header + get_template(filename) + 
            SimpleHttpServer.html_footer)

def get_picture_metadata(filename):
    current_file = '{}/{}'.format(SimpleHttpServer.picture_path, filename)
    stat = os.stat(current_file)
    picture_timestamp = None
    try:
        picture_timestamp = stat.st_birthtime
    except AttributeError:
        # We're probably on Linux. No easy way to get creation dates here,
        # so we'll settle for when its content was last modified.
        picture_timestamp = stat.st_mtime
    picture_datetime = datetime.datetime.fromtimestamp(picture_timestamp)
    picture_information = {
        "picture_name": filename,
        "picture_timestamp": str(picture_timestamp),
        "picture_datetime": str(picture_datetime)
    }

    return picture_information


class SimpleHttpServer:

    webroot = os.path.dirname(os.path.abspath(__file__))
    picture_path = None

    html_header = None
    html_footer = None

    def __init__(self, config):

        basedir = config.get('Storage', 'basedir')
        SimpleHttpServer.picture_path = strftime(basedir, localtime())

        SimpleHttpServer.html_header = get_template('header')
        SimpleHttpServer.html_footer = get_template('footer')

    def run(self):

        server.start()

def run(config):

    logging.debug('Starting SimpleHttpServer')
    webserver = SimpleHttpServer(config)
    webserver.run()


@request_map('css/{filename}')
def get_css_file(filename=PathValue()):

    return StaticFile('{}/css/{}'.format(SimpleHttpServer.webroot, filename),
                      'text/css')

@request_map('js/{filename}')
def get_js_file(filename=PathValue()):

    return StaticFile('{}/js/{}'.format(SimpleHttpServer.webroot, filename),
                      'text/javascript')


@request_map("/favicon.ico")
def _favicon():

    return StaticFile('{}/favicon.ico'.format(SimpleHttpServer.webroot),
                      'image/x-icon')

@request_map('api/get_picture/{filename}')
def return_picture(filename=PathValue()):

    filename = '{}/{}'.format(SimpleHttpServer.picture_path, filename)
    return get_picture_metadata(filename)


@request_map("api/get_new_pictures/{last_picture_timestamp}")
def return_new_pictures(last_picture_timestamp=PathValue()):

    image_list = []
    new_pictures = []
    all_pictures = []

    my_last_picture_datetime = None

    if last_picture_timestamp.lower() == "undefined":
        return {}
    if last_picture_timestamp.upper() != "ALL":
        try:
            my_last_picture_datetime = datetime.datetime.fromtimestamp(float(last_picture_timestamp))
        except:
            my_last_picture_datetime = datetime.datetime.now()
            logging.warn("No valid timestamp")

    image_list = fnmatch.filter(os.listdir(SimpleHttpServer.picture_path), '*.jpg')
    current_picture_timestamp = None
    current_picture_information = {}
    for i in image_list:
        current_picture_information = get_picture_metadata(i)
        current_picture_timestamp = float(current_picture_information['picture_timestamp'])
        if my_last_picture_datetime is not None:
            print("current picture timestamp %s vs last picture timestamp %s" %(current_picture_timestamp, last_picture_timestamp))
            logging.debug("last picture timestamp: %s" %last_picture_timestamp)
            if current_picture_timestamp > float(last_picture_timestamp) and last_picture_timestamp.upper() != "ALL":
                logging.debug("Send picture")
                new_pictures.append(current_picture_information)
        all_pictures.append(current_picture_information)

    last_picture_information = max(all_pictures, key=lambda x:x['picture_timestamp'])

    return_pictures = []
    if last_picture_timestamp.upper() == "ALL":
        return_pictures = all_pictures
    else:
        return_pictures = new_pictures

    return_pictures = sorted(return_pictures, key=lambda k: k['picture_timestamp'])

    thisdict =  {
            "time_param": str(last_picture_timestamp),
            "last_picture": last_picture_information,
            "new_pictures": return_pictures,
            "now_datetime": str(datetime.datetime.now()),
            "now_timestamp": str(time()),
            "number_of_pictures": len(return_pictures),
            "photobooth_status": "free"
            }
    return thisdict

@request_map("/f/{function}/picture/{picture}")
def return_picture(picture=PathValue(), function=PathValue()):
    logging.debug(function)
    my_pictures_path = "%s" %(SimpleHttpServer.picture_path)
    my_picture = "%s/%s" % (my_pictures_path, picture)
    if function == 'download':
        logging.debug("Download picture from: %s" %my_picture)
        return StaticFile(my_picture, "application/octet-stream")
    if function == 'show':
        logging.debug("Show picture from: %s" %my_picture)
        return StaticFile(my_picture, "image/jpg")
    if function == 'delete':
        logging.debug("Delete picture from: %s" %my_picture)
        os.remove(my_picture)
        return Redirect("/")
    if function == 'single':
        return get_html_stream("single_picture")
    # if function == 'show_qr':
    #     qr_code_img_path = Webserver.generate_qr('show', picture)
    #     return StaticFile(qr_code_img_path, "image/jpg")
    # if function == 'download_qr':
    #     qr_code_img_path = Webserver.generate_qr('download', picture)
    #     return StaticFile(qr_code_img_path, "image/jpg")
    # if function == 'mail_qr':
    #     qr_code_img_path = Webserver.generate_qr('mail', picture)
    #     return StaticFile(qr_code_img_path, "image/jpg")
    if function == 'mail':
        logging.debug("Mail picture from: %s" %my_picture)
        my_return_stream =  get_html_stream("frm_send_mail")
        my_return_stream = my_return_stream.replace("[picture_id]", picture)
        return my_return_stream
    # if function == 'print':
    #     logging.debug("Print file %s ON: %s" %(my_picture, SimpleHttpServer.printer))
    #     os.system("lpr -P %s %s" %(SimpleHttpServer.printer, my_picture))
    else:
        return Redirect("/")


@request_map('/')
def index():

    return get_html_stream('index')

@request_map("/last")
def return_last_picture():
    
    return get_html_stream('last')

@request_map('/gallery')
def gallery():

    return get_html_stream('gallery')


# def send_simple_message(name, email, message, filename, attachment):
#     logging.debug("Send picture %s to %s with message \n %s" %(attachment, email, message))
#     return requests.post(
#         "https://api.mailgun.net/v3/oelegeirnaert.be/messages",
#         auth=("api", Webserver.mailgun_api_key),
#         files=[("inline", open(attachment,"rb"))],
#         data={"from": ["Oele Geirnaert's Photobooth","mailer@oelegeirnaert.be"],
#               "to": [name, email],
#               "subject": "Picture sent from Oele Geirnaert's Photobooth",
#               "text": message,
#               "html": '<html><b>Hello ' + name + ',</b><p>'+ message + '</p><p>Here is your picture:</p><img src="cid:' + filename +'"></html>'
#               })


# @request_map("show_qrs")
# def return_qrs():
#     Webserver.html_header = Webserver.get_html_stream("header")
#     return Webserver.get_full_html_stream("show_qrs")

# @request_map("slideshow")
# def start_slideshow():
#     Webserver.html_header = Webserver.get_html_stream("header")
#     return Webserver.get_full_html_stream("slideshow")

# @request_map("picture/{picture}")
# def return_single_picture(picture=PathValue()):
#     Webserver.html_header = Webserver.get_html_stream("header")
#     return Webserver.get_full_html_stream("single_picture")

# @request_map("settings")
# def start_slideshow():
#     Webserver.html_header = Webserver.get_html_stream("header")
#     return Webserver.get_full_html_stream("settings")

# @request_map("send/picture/{picture}", method="POST")
# def mail_picture(txt_email, txt_name, txt_message, picture=PathValue()):
#     logging.debug("Post method mail picture to %s" %txt_name)
#     my_pictures_path = "%s" %(picture_path)
#     attachment = "%s/%s" % (my_pictures_path, picture)
#     Webserver.send_simple_message(txt_name, txt_email, txt_message, picture, attachment)
#     return Redirect("/")


# def generate_qr(function, picture):
#     link = "http://%s:%s/f/%s/picture/%s" %(Webserver.ip_address, Webserver.webserver_port,function, picture)
#     img = qrcode.make(link)
#     qr_code_path = "%s/%s/%s_%s.png" %(root, 'qrcodes', function, picture)
#     img.save(qr_code_path)
#     return qr_code_path


