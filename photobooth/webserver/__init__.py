#Thanks to: https://github.com/keijack/python-simple-http-server
import logging
import os, fnmatch
from simple_http_server import request_map
from simple_http_server import Response
from simple_http_server import MultipartFile
from simple_http_server import Parameter
from simple_http_server import Parameters
from simple_http_server import Header
from simple_http_server import JSONBody
from simple_http_server import HttpError
from simple_http_server import StaticFile
from simple_http_server import Headers
from simple_http_server import Cookies
from simple_http_server import Cookie
from simple_http_server import Redirect
from simple_http_server import PathValue

from pathlib import Path
from time import localtime, strftime, time
import datetime
import requests
import configparser
import qrcode
import socket

import simple_http_server.server as server

class Webserver(object):
    """docstring for Webserver."""

    root = os.path.dirname(os.path.abspath(__file__))
    picture_dir = None
    html_header = None
    html_footer = None
    mailgun_api_key = None
    ip_address = None
    webserver_hostname = None
    webserver_port = None
    printer = None

    def get_html_stream(str_filename):
        my_html_file = "%s/templates/%s.html" %(Webserver.root, str_filename)
        return open(my_html_file, 'r').read()

    def get_picture_meta_information(picture):
        current_file = "%s/%s" %(Webserver.picture_dir,picture)
        stat = os.stat(current_file)
        current_picture_timestamp = None
        try:
            current_picture_timestamp = stat.st_birthtime
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            current_picture_timestamp = stat.st_mtime
        logging.debug(current_picture_timestamp)
        current_picture_datetime = datetime.datetime.fromtimestamp(current_picture_timestamp)
        current_picture_information = {
            "picture_name": picture,
            "picture_timestamp": str(current_picture_timestamp),
            "picture_datetime": str(current_picture_datetime)
        }

        return current_picture_information

    def get_full_html_stream(str_filename):
        my_stream = Webserver.html_header
        my_stream += Webserver.get_html_stream(str_filename)
        my_stream += Webserver.html_footer
        return my_stream

    def send_simple_message(name, email, message, filename, attachment):
        logging.debug("Send picture %s to %s with message \n %s" %(attachment, email, message))
        return requests.post(
            "https://api.mailgun.net/v3/oelegeirnaert.be/messages",
            auth=("api", Webserver.mailgun_api_key),
            files=[("inline", open(attachment,"rb"))],
            data={"from": ["Oele Geirnaert's Photobooth","mailer@oelegeirnaert.be"],
                  "to": [name, email],
                  "subject": "Picture sent from Oele Geirnaert's Photobooth",
                  "text": message,
                  "html": '<html><b>Hello ' + name + ',</b><p>'+ message + '</p><p>Here is your picture:</p><img src="cid:' + filename +'"></html>'
                  })

    def get_host_name():
        hostname = socket.gethostname()
        return hostname

    def get_ip_address():
        hostname = socket.gethostname()
        IPAddr = socket.gethostbyname(hostname)
        return IPAddr


    #As we may have only one server we can declare those variables globally
    def __init__(self, config, comm):
        super().__init__()
        self._config = config
        self._comm = comm

        path = config.get('Storage', 'basedir')
        Webserver.picture_dir = strftime(path, localtime())
        Webserver.html_header = Webserver.get_html_stream("header")
        Webserver.html_footer = Webserver.get_html_stream("footer")

        webserver_config = configparser.ConfigParser()
        webserver_config_filename = os.path.join(os.path.dirname(__file__), 'config.cfg')
        logging.debug("Reading config file from: %s" %webserver_config_filename)
        my_config = webserver_config.read(webserver_config_filename)
        Webserver.ip_address = webserver_config.get("Webserver", "ip_address")
        Webserver.webserver_hostname = Webserver.get_host_name()
        Webserver.mailgun_api_key = webserver_config.get("Mailgun", "api_secret")
        Webserver.webserver_port = webserver_config.get("Webserver", "port")
        Webserver.printer = webserver_config.get("Webserver", "printer")
        logging.debug(Webserver.mailgun_api_key)
        logging.debug(webserver_config.sections())


    @request_map("/favicon.ico")
    def _favicon():
        return StaticFile("%s/favicon.ico" % Webserver.root, "image/x-icon")

    @request_map("/")
    def index():
        logging.debug("Webserver root is: %s" % Webserver.root)
        return Webserver.get_full_html_stream("index")

    @request_map("last")
    def return_last_picture():
        Webserver.html_header = Webserver.get_html_stream("header")
        return Webserver.get_full_html_stream("last_picture")

    @request_map("show_qrs")
    def return_qrs():
        Webserver.html_header = Webserver.get_html_stream("header")
        return Webserver.get_full_html_stream("show_qrs")

    @request_map("slideshow")
    def start_slideshow():
        Webserver.html_header = Webserver.get_html_stream("header")
        return Webserver.get_full_html_stream("slideshow")

    @request_map("picture/{picture}")
    def return_single_picture(picture=PathValue()):
        Webserver.html_header = Webserver.get_html_stream("header")
        return Webserver.get_full_html_stream("single_picture")

    @request_map("settings")
    def start_slideshow():
        Webserver.html_header = Webserver.get_html_stream("header")
        return Webserver.get_full_html_stream("settings")

    @request_map("gallery")
    def start_slideshow():
        Webserver.html_header = Webserver.get_html_stream("header")
        return Webserver.get_full_html_stream("gallery")

    @request_map("css/{css_file}")
    def get_css_file(css_file=PathValue()):
        my_css_file = "%s/css/%s" %(Webserver.root, css_file)
        #my_css_stream = open(my_css_file, 'r').read()
        return StaticFile(my_css_file,  "text/css")

    @request_map("js/{js_file}")
    def get_js_file(js_file=PathValue()):
        my_js_file = "%s/js/%s" %(Webserver.root, js_file)
        return StaticFile(my_js_file, "text/javascript")

    @request_map("send/picture/{picture}", method="POST")
    def mail_picture(txt_email, txt_name, txt_message, picture=PathValue()):
        logging.debug("Post method mail picture to %s" %txt_name)
        my_pictures_path = "%s" %(Webserver.picture_dir)
        attachment = "%s/%s" % (my_pictures_path, picture)
        Webserver.send_simple_message(txt_name, txt_email, txt_message, picture, attachment)
        return Redirect("/")

    #method=["GET", "POST"]
    @request_map("/f/{function}/picture/{picture}")
    def return_picture(picture=PathValue(), function=PathValue()):
        logging.debug(function)
        my_pictures_path = "%s" %(Webserver.picture_dir)
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
            Webserver.html_header = Webserver.get_html_stream("header")
            return Webserver.get_full_html_stream("single_picture")
        if function == 'show_qr':
            qr_code_img_path = Webserver.generate_qr('show', picture)
            return StaticFile(qr_code_img_path, "image/jpg")
        if function == 'download_qr':
            qr_code_img_path = Webserver.generate_qr('download', picture)
            return StaticFile(qr_code_img_path, "image/jpg")
        if function == 'mail_qr':
            qr_code_img_path = Webserver.generate_qr('mail', picture)
            return StaticFile(qr_code_img_path, "image/jpg")
        if function == 'mail':
            logging.debug("Mail picture from: %s" %my_picture)
            my_return_stream =  Webserver.get_full_html_stream("frm_send_mail")
            my_return_stream = my_return_stream.replace("[picture_id]", picture)
            return my_return_stream
        if function == 'print':
            logging.debug("Print file %s ON: %s" %(my_picture, Webserver.printer))
            os.system("lpr -P %s %s" %(Webserver.printer, my_picture))
        else:
            return Redirect("/")


    def generate_qr(function, picture):
        link = "http://%s:%s/f/%s/picture/%s" %(Webserver.ip_address, Webserver.webserver_port,function, picture)
        img = qrcode.make(link)
        qr_code_path = "%s/%s/%s_%s.png" %(Webserver.root, 'qrcodes', function, picture)
        img.save(qr_code_path)
        return qr_code_path


    # @request_map("pictures/{picture}")
    # def return_picture(picture=PathValue()):
    #     my_pictures_path = "%s" %(Webserver.picture_dir)
    #     my_picture = "%s/%s" % (my_pictures_path, picture)
    #     logging.debug("Loading picture from: %s" %my_picture)
    #     return StaticFile(my_picture, "image/jpg")

    @request_map("api/get_picture/{picture}")
    def return_picture(picture=PathValue()):
        logging.debug("requesting information for picture %s" %picture)
        picture = "%s/%s" %(Webserver.picture_dir, picture)
        logging.debug(picture)
        picture_info = Webserver.get_picture_meta_information(picture)
        return picture_info

    @request_map("api/get_new_pictures/{last_picture_timestamp}")
    def return_new_pictures(last_picture_timestamp=PathValue()):
        logging.debug("URL Timeparam: %s" %last_picture_timestamp)
        image_list = []
        new_pictures = []
        all_pictures = []

        my_last_picture_datetime= None

        if last_picture_timestamp.lower() == "undefined":
            return {}
        if last_picture_timestamp.upper() != "ALL":
            try:
                my_last_picture_datetime = datetime.datetime.fromtimestamp(float(last_picture_timestamp))
            except:
                my_last_picture_datetime = datetime.datetime.now()
                logging.warn("No valid timestamp")


        image_list=fnmatch.filter(os.listdir(Webserver.picture_dir), '*.jpg')
        current_picture_timestamp = None
        current_picture_information = {}
        for i in image_list:
            current_picture_information = Webserver.get_picture_meta_information(i)
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

        thisdict =	{
                "time_param": str(last_picture_timestamp),
                "last_picture": last_picture_information,
                "new_pictures": return_pictures,
                "now_datetime": str(datetime.datetime.now()),
                "now_timestamp": str(time()),
                "number_of_pictures": len(return_pictures),
                "photobooth_status": "free"
                }
        return thisdict

    def run(self):
        server.start()
        return True
