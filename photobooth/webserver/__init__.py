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
from time import localtime, strftime
import datetime

import simple_http_server.server as server

class Webserver(object):
    """docstring for Webserver."""

    #As we may have only one server we can declare those variables globally
    root = os.path.dirname(os.path.abspath(__file__))
    picture_dir = None

    def __init__(self, config, comm):
        super().__init__()
        self._config = config
        self._comm = comm

        path = config.get('Storage', 'basedir')
        Webserver.picture_dir = strftime(path, localtime())

    @request_map("/favicon.ico")
    def _favicon():
        return StaticFile("%s/favicon.ico" % Webserver.root, "image/x-icon")

    @request_map("/")
    def index():
        logging.debug("Webserver root is: %s" % Webserver.root)

        my_html_file = "%s/templates/index.html" %Webserver.root

        image_list = []
        image_list=fnmatch.filter(os.listdir(Webserver.picture_dir), '*.jpg')
        str_image_list = ""
        for i in image_list:
            str_image_list += """<div class='picture_box'>
            <img src='show/picture/%s' class='picture' />
            <a href='download/picture/%s' class='btn btn-primary picture-btn download'>Download Picture</a>
            <a href='delete/picture/%s' class='btn btn-danger picture-btn delete'>Delete Picture</a>
            </div>
            """ %(i,i,i)
            logging.debug(i)
        logging.debug(str_image_list)

        my_html_stream = open(my_html_file, 'r').read()
        my_html_stream = my_html_stream.replace("[load_images_from_directory]", str_image_list)

        return my_html_stream

    @request_map("slideshow")
    def start_slideshow():
        my_html_file = "%s/templates/slideshow.html" %Webserver.root
        my_html_stream = open(my_html_file, 'r').read()
        return my_html_stream

    @request_map("{function}/picture/{picture}")
    def return_picture(picture=PathValue(), function=PathValue()):
        logging.debug(function)
        my_pictures_path = "%s" %(Webserver.picture_dir)
        my_picture = "%s/%s" % (my_pictures_path, picture)
        logging.debug("Download picture from: %s" %my_picture)
        if function == 'download':
            return StaticFile(my_picture, "application/octet-stream")
        if function == 'show':
            return StaticFile(my_picture, "image/jpg")
        if function == 'delete':
            os.remove(my_picture)
            return Redirect("/")
        if function == '':
            return Redirect("/")

    # @request_map("pictures/{picture}")
    # def return_picture(picture=PathValue()):
    #     my_pictures_path = "%s" %(Webserver.picture_dir)
    #     my_picture = "%s/%s" % (my_pictures_path, picture)
    #     logging.debug("Loading picture from: %s" %my_picture)
    #     return StaticFile(my_picture, "image/jpg")

    @request_map("api/get_new_pictures/{last_picture_timestamp}")
    def return_new_pictures(last_picture_timestamp=PathValue()):
        logging.debug("URL Timeparam: %s" %last_picture_timestamp)
        my_last_picture_timestamp = datetime.datetime.now()
        try:
            if last_picture_timestamp == 'undefined':
                my_last_picture_timestamp = datetime.datetime.now()
            else:
                my_last_picture_timestamp = datetime.datetime.fromtimestamp(int(last_picture_timestamp))
        except:
            my_last_picture_timestamp = datetime.datetime.now()
            logging.warn("No valid timestamp")

        image_list = []
        new_pictures = []
        image_list=fnmatch.filter(os.listdir(Webserver.picture_dir), '*.jpg')
        image_list.sort()
        for i in image_list:
            current_file = "%s/%s" %(Webserver.picture_dir,i)
            stat = os.stat(current_file)
            current_picture_timestamp = None
            try:
                current_picture_timestamp = stat.st_birthtime
            except AttributeError:
                # We're probably on Linux. No easy way to get creation dates here,
                # so we'll settle for when its content was last modified.
                current_picture_timestamp = stat.st_mtime
            logging.debug(current_picture_timestamp)
            current_picture_timestamp = datetime.datetime.fromtimestamp(current_picture_timestamp)
            print("current picture timestamp %s vs last picture timestamp %s" %(current_picture_timestamp, my_last_picture_timestamp))
            if current_picture_timestamp > my_last_picture_timestamp:
                logging.debug("Send picture")
                new_pictures.append(i)

        thisdict =	{
                "last_picture_timestamp": str(my_last_picture_timestamp),
                "new_pictures": new_pictures
                }
        return thisdict

    def run(self):
        server.start()
        return True
