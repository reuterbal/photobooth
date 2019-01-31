<<<<<<< HEAD
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
import glob

import simple_http_server.server as server

class Webserver(object):
    """docstring for Webserver."""

    #As we may have only one server we can declare those variables globally
    root = os.path.dirname(os.path.abspath(__file__))
    p = Path(__file__).parents[2]
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
            str_image_list += "<img src='%s' width='100px' />" % i
            logging.debug(i)
        logging.debug(str_image_list)

        my_html_stream = open(my_html_file, 'r').read()
        my_html_stream = my_html_stream.replace("[load_images_from_directory]", str_image_list)

        return my_html_stream

    @request_map("{picture}")
    def return_picture(picture=PathValue()):
        my_pictures_path = "%s" %(Webserver.picture_dir)
        my_picture = "%s/%s" % (my_pictures_path, picture)
        logging.debug("Loading picture from: %s" %my_picture)
        return StaticFile(my_picture, "image/jpg")

    def run(self):
        server.start()
        return True
=======
#init
>>>>>>> 539ad3e539f9fdc8d5dbe3befe9a2e6d791561b5
