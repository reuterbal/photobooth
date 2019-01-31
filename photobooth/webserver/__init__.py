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
        logging.debug("My Root is: %s" % Webserver.root)
        #testdir = "%s/%s" %(Webserver.p, Webserver.picture_dir)
        testdir = "pictures"
        logging.debug(testdir)
        my_images_path = "%s" %(Webserver.picture_dir)
        my_html_file = "%s/templates/index.html" %Webserver.root

        image_list = []
        #for filename in glob.glob('%s/*.jpg' % Webserver.picture_dir): #assuming gif
            #image_list.append(filename)
        image_list=fnmatch.filter(os.listdir(Webserver.picture_dir), '*.jpg')
        str_image_list = ""
        for i in image_list:
            str_image_list += "<img src='%s' width='100px' />" % i
            logging.debug(i)
        logging.debug(str_image_list)
        my_image_list = ''.join(image_list)

        my_html_stream = open(my_html_file, 'r').read()
        my_html_stream = my_html_stream.replace("[load_images_from_directory]", str_image_list)
        logging.debug(my_html_file)
        return my_html_stream
        #return {"code": 0, "message": "success - images will be loaded from %s" %os.listdir(testdir)} # You can return a dictionary, a string or a `simple_http_server.simple_http_server.Response` object.

    @request_map("{picture}")
    def return_picture(picture=PathValue()):
        my_images_path = "%s" %(Webserver.picture_dir)
        my_picture = "%s/%s" % (my_images_path, picture)
        logging.debug("Loading picture from: %s" %my_picture)
        return StaticFile(my_picture, "image/jpg")



    def run(self):

        logging.debug("Change HTTP basepath %s" %Webserver.p)
        server.start()

        return True
