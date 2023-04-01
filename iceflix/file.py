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
        #To Do
        return null

    def close(self, userToken, current=None):
        """Notify the server that the proxy for this file, won´t be used and will be removed"""
        #To Do
        return null
