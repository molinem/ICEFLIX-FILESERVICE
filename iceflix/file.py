#!/usr/bin/env python3

import logging

import sys
import threading
import time
import uuid
import os
import random

#IceFlix
import Ice
import IceFlix

from functions_topics import getTopic_manager,get_topic


#------------------------------------------------
#                   FileService
#------------------------------------------------
class FileService(IceFlix.FileService):

    def __init__(self, path):
        """Initialize parameters"""
        self.service_id = str(uuid.uuid4())

    def get_main(self, current=None):
        #To-do
        return null

    def openFile(self, mediaId, userToken, current=None):
        """"Given the media identifier, it will return a proxy to the file handler (FileHandler), which will enable downloading it"""
        """Can throws -> Unauthorized, WrongMediaId"""

    def uploadFile(self, uploader, adminToken, current=None):
        """Given the administrator token and a proxy for uploading files, it will store it in the directory and returns its identifier"""
        """Can throws -> Unauthorized"""

    def removeFile(self, mediaId, adminToken, current=None):
        """Give the identifier and the administrator token"""
        """Can throws -> Unauthorized, WrongMediaId"""

#------------------------------------------------
#                   FileHandler
#------------------------------------------------
class FileHandler(IceFlix.FileHandler):
    """When a user requests to open a file, the service will create a servant to handle its possible download"""

    def __init__(self, path):
        """Initialize parameters for open file"""
        self.service_id = str(uuid.uuid4())

        self.path = path
        self.file = open(self.path, 'rb')

    def is_authorized(self, userToken):
        """Returns True if the userToken is authorized, False otherwise"""
        if self.get_main() is not None:
            main_prx = self.get_main()
            if main_prx is not None:
                auth_prx = main_prx.getAuthenticator()
                if auth_prx.isAuthorized(userToken):
                    return True
        return False

    def receive(self, size, userToken, current=None):
        """Receive the specified number of bytes from the file"""
        """Can throws -> Unauthorized"""
        part = None
        if self.is_authorized(userToken):
            part = self.file.read(size)
        else:
            logging.error("[FileHandler] -> There is a problem with user token")
            raise IceFlix.Unauthorized()
        return part

    def close(self, userToken, current=None):
        """Notify the server that the proxy for this file, won´t be used and will be removed"""
        """Can throws -> Unauthorized"""
        if self.is_authorized(userToken):
            self.file.close()
        else:
            logging.error("[FileHandler] -> There is a problem with user token")
            raise IceFlix.Unauthorized()