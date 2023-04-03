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

#----------------------------
#        Announcements
#----------------------------
class Announcements(IceFlix.Announcement):
    def __init__(self, annon_event, time_to_cancel):
        self.service_id_announc = str(uuid.uuid4())
        self.myFileService = None #this will set up at RunFileService

        self.annon_event = annon_event
        self.time_to_cancel = time_to_cancel
        self.last_main_update = {}

    def update_time(self, service_id):
        """This method is for update time of services"""
        self.last_main_update[service_id] = time.time()    
        self.event.set()

    def announce(self, service, service_id, current=None):
        """This method is for check services and update list of services if we haven`t add yet"""
        logging.warning("[Announcement] -> Id Service--> %s", str(service_id))
        if not service_id in self.myFileService.main_list and service.ice_isA("::IceFlix::Main"):
            logging.warning("[Announcement] -> New main service has been detected with id--> %s", str(service_id))
            self.myFileService.main_list[service_id] = IceFlix.MainPrx.uncheckedCast(service)
            self.update_time(self, service_id)
            self.canceltimer.cancel()
        elif service_id in self.myFileService.main_list:
            """Update time"""
            self.update_time(self, service_id)
        else:
            logging.warning("[Announcement] -> The Announcement with id --> %s has been ignored", str(service_id))

#----------------------------
#        FileService
#----------------------------
class FileService(IceFlix.FileService):

    def __init__(self, path):
        """Initialize parameters"""
        self.service_id_file = str(uuid.uuid4())

        self.main_list = {}

    def get_main(self, current=None):
        #To-do
        return null

    def openFile(self, mediaId, userToken, current=None):
        """"Given the media identifier, it will return a proxy to the file handler (FileHandler), which will enable downloading it"""
        """Can throws -> Unauthorized, WrongMediaId"""
        #To-do

    def uploadFile(self, uploader, adminToken, current=None):
        """Given the administrator token and a proxy for uploading files, it will store it in the directory and returns its identifier"""
        """Can throws -> Unauthorized"""
        #To-do

    def removeFile(self, mediaId, adminToken, current=None):
        """Give the identifier and the administrator token"""
        """Can throws -> Unauthorized, WrongMediaId"""
        #To-do

#----------------------------
#        FileHandler
#----------------------------
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