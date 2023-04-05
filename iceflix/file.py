#!/usr/bin/env python3

import logging

import sys
import threading
import time
import uuid
import os
import random
import hashlib

#IceFlix
import Ice
import IceFlix

from functions_topics import getTopic_manager,get_topic

"""Sources:
    https://www.sqlitetutorial.net/sqlite-python/sqlite-python-select/
    https://uclm-esi.github.io/ssdd-lab/python_stdlib.html
    https://doc.zeroc.com/ice/3.7/the-slice-language/operations-on-object
    https://www.w3schools.com/python/python_ref_string.asp
    https://www.programiz.com/python-programming/methods/string/join
    https://docs.python.org/3/tutorial/datastructures.html
    https://vald-phoenix.github.io/pylint-errors/plerr/errors/basic/C0116.html
    https://www.w3schools.com/python/ref_func_abs.asp
    https://www.programiz.com/python-programming/methods/list/pop
    https://docs.pylint.org/
    https://bobbyhadz.com/blog/python-check-if-object-exists-in-list-of-objects """

#----------------------------
#        Announcements
#----------------------------
class Announcements(IceFlix.Announcement):
    def __init__(self, annon_event, time_to_cancel):
        self.service_id_announc = str(uuid.uuid4())
        self.myFileService = None #this will set up at RunFileService

        self.annon_event = annon_event
        self.time_to_cancel = time_to_cancel
        

    def update_time(self, service_id):
        """This method is for update time of services"""
        self.myFileService.last_main_update[service_id] = time.time()    
        self.event.set()

    def announce(self, service, service_id, current=None):
        """This method is for check services and update list of services if we haven`t add yet"""
        logging.warning("[Announcement] -> Id Service--> %s", str(service_id))
        if not service_id in self.myFileService.main_list and service.ice_isA("::IceFlix::Main"):
            logging.warning("[Announcement] -> New main service has been detected with id %s", str(service_id))
            self.myFileService.main_list[service_id] = IceFlix.MainPrx.uncheckedCast(service) #To MainPrx
            self.update_time(self, service_id)
            self.time_to_cancel.cancel()
        elif service_id in self.myFileService.main_list:
            """Update time"""
            self.update_time(self, service_id)
        else:
            logging.warning("[Announcement] -> The Announcement with id %s has been ignored", str(service_id))

#----------------------------
#        FileService
#----------------------------
class FileService(IceFlix.FileService):

    def __init__(self, path_resources):
        """Initialize parameters"""
        self.service_id_file = str(uuid.uuid4())

        self.path_resources = path_resources

        self.last_main_update = {}
        self.main_list = {}
        self.media_list_hash = {}

        self.make_hash_medias()

    def make_hash_medias(self, current=None):
        """Calculate hash sha256 of file, this will be used for identify the file"""
        for file in os.listdir(self.path_resources):
            path = os.path.join(self.path_resources, file)
            with open(path, 'rb') as file_object:
                file_id = file_object.read()
                file_hash = hashlib.sha256(file_id).hexdigest()
                self.media_list_hash[file_hash] = path

    def get_main_service(self, current=None):
        """Obtain one main services from list and check if is available"""
        if not self.main_list:
            logging.warning("[FileService] -> There isn´t any main available previusly stored")
            return None
        random_main = random.choice(list(self.main_list.keys())) #Select random main service from list
        if abs(self.last_main_update[random_main] - time.time()) > 12:
            logging.warning("[FileService] -> There isn´t any main available that aren´t expired")
            self.main_list.pop(random_main) #out to list
            return None
        return self.main_list[random_main]

    def exist_media_dictionary(self, media_id, current=None):
        """Check if the media id exist on the dictionary"""
        return media_id in self.media_list_hash
    
    def check_list_methods(self, user_token, current=None):
        """For check if there is some problem, used in openFile, uploadFile, removeFile"""
        main_prx = self.get_main_service()
        if main_prx is None:
            logging.warning("[FileService] -> There isn´t any main available")
        
        auth_prx = main_prx.getAuthenticator()
        if auth_prx is None:
            logging.warning("[FileService] -> There isn´t any authenticator available")
        
        if not auth_prx.isAuthorized(user_token):
            logging.warning("[FileService] -> There is a problem with your token")
            raise IceFlix.Unauthorized()

    def openFile(self, media_id, user_token, current=None):
        """"Given the media identifier, it will return a proxy to the file handler (FileHandler), which will enable downloading it"""
        """Can throws -> Unauthorized, WrongMediaId"""
        handler_prx = None
        self.check_list_methods(user_token)
        if self.exist_media_dictionary(media_id):
            file_hand = FileHandler(self.media_list_hash.get(media_id))
            file_hand_prx = self.adapter.addWithUUID(file_hand)
            handler_prx = IceFlix.FileHandlerPrx.uncheckedCast(file_hand_prx) #From ObjectPrx to FileHandlerPrx
        else:
            logging.warning("[FileService] -> The media id doesn´t exist in our records")
            raise IceFlix.WrongMediaId(media_id)
        return handler_prx
        
    def uploadFile(self, uploader, admin_token, current=None):
        """Given the administrator token and a proxy for uploading files, it will store it in the directory and returns its identifier"""
        """Can throws -> Unauthorized"""
        #To-do

    def removeFile(self, media_id, admin_token, current=None):
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

    def is_authorized(self, userToken, current=None):
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