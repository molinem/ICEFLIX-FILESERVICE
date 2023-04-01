#!/usr/bin/env python3

import logging

import sys
import threading
import time
import uuid
import os

#IceFlix
import Ice
import IceFlix

#------------------------------------------------
#                   FileHandler
#------------------------------------------------
class FileHandler(IceFlix.FileHandler):
    """When a user requests to open a file, the service will create a servant to handle its possible download"""

    def __init__(self, path):
        """Initialize parameters for open file"""
        self.path = path
        self.file = open(self.path, 'rb')

    def receive(self, size, userToken, current=None):
        """Receive the specified number of bytes from the file"""
        """Can throws -> Unauthorized"""
        #To Do
        return null

    def close(self, userToken, current=None):
        """Notify the server that the proxy for this file, won´t be used and will be removed"""
        """Can throws -> Unauthorized"""
        #To Do
        return null

#------------------------------------------------
#                   FileService
#------------------------------------------------
class FileService(IceFlix.FileService):

    def __init__(self, path):
        """Initialize parameters"""

    def openFile(self, mediaId, userToken, current=None):
        """"Given the media identifier, it will return a proxy to the file handler (FileHandler), which will enable downloading it"""
        """Can throws -> Unauthorized, WrongMediaId"""

    def uploadFile(self, uploader, adminToken, current=None):
        """Given the administrator token and a proxy for uploading files, it will store it in the directory and returns its identifier"""
        """Can throws -> Unauthorized"""

    def removeFile(self, mediaId, adminToken, current=None):
        """Give the identifier and the administrator token"""
        """Can throws -> Unauthorized, WrongMediaId"""