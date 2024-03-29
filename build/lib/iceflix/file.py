#!/usr/bin/env python3

#pylint: disable=C0301
#pylint: disable=unused-argument
#pylint: disable=E0401
#pylint: disable=C0103
#pylint: disable=W1203
#pylint: disable=W0602

#E0401 -> Error with import
#C0301 -> Too Long
#C0103 -> Use "_"
#W1203 -> Use % (formatting in logging functions)
#W0602 -> Use directly global variables

import logging

import sys
import threading
import time
import uuid
import os
import random

#Hash
import hashlib

#File
import shutil
import tempfile

#IceFlix
try:
    import Ice
    Ice.loadSlice(os.path.join(os.path.dirname(__file__), "iceflix.ice"))
    import IceFlix # pylint:disable=import-error
except ImportError:
    logging.warning("[FileService] -> There is one error with import iceflix module")

#from functions_topics import getTopic_manager,get_topic
from iceflix import functions_topics

YELLOW = "\033[93m"
GREEN = "\033[32m"
BLUE = "\033[34m"
CIAN = "\033[36m"
WHITE = "\033[37m"
MAGENTA = "\033[35m"


LOG_FORMAT = '%(asctime)s - %(levelname)-7s - %(message)s'
logging.basicConfig(level=logging.WARNING,format=LOG_FORMAT)


last_authenticator_update = {}
authenticator_list = {}

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
    https://docs.python.org/es/3/library/shutil.html
    https://docs.python.org/3/library/tempfile.html
    https://docs.pylint.org/
    https://www.section.io/engineering-education/how-to-perform-threading-timer-in-python/
    https://bobbyhadz.com/blog/python-check-if-object-exists-in-list-of-objects """

#----------------------------
#        FileService
#----------------------------
class FileService(IceFlix.FileService):
    """File service main operations"""

    def __init__(self, path_resources, annon_file_publish, adapter):
        """Initialize parameters"""
        self.service_id_file = str(uuid.uuid4())
        self.proxy = None
        self.adapter = adapter

        self.path_resources = path_resources
        self.annon_file_publish = annon_file_publish

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


    def get_authenticator_service(self, current=None):
        """Obtain one authenticator from list and check if is available"""
        global last_authenticator_update
        global authenticator_list
        if not authenticator_list:
            logging.warning(f'{WHITE}[FileService] {YELLOW}-> {CIAN} There isn´t any authenticator available previusly stored')
            return None
        random_authenticator = random.choice(list(authenticator_list.keys())) #Select random authenticator service from list

        if abs(last_authenticator_update[random_authenticator] - time.time()) > 12:
            logging.warning(f'{WHITE}[FileService] {YELLOW}-> {CIAN} There isn´t any authenticator available they are expired')
            authenticator_list.pop(random_authenticator) #out to list
            return None
        return authenticator_list[random_authenticator]


    def exist_media_dictionary(self, media_id, current=None):
        """Check if the media id exist on the dictionary"""
        return media_id in self.media_list_hash


    def check_list_methods(self, user_token, fun_admin, current=None):
        """For check if there is some problem, used in openFile, uploadFile, removeFile"""
        auth_prx = self.get_authenticator_service()
        is_correct = True

        if auth_prx is not None:
            if not auth_prx.isAuthorized(user_token):
                logging.warning(f'{WHITE}[FileService] {YELLOW}-> {CIAN} There is a problem with your token')
                raise IceFlix.Unauthorized()
        else:
            is_correct = False

        ##Check if admin
        if is_correct and fun_admin:
            if not auth_prx.isAdmin(user_token):
                logging.warning(f'{WHITE}[FileService] {YELLOW}-> {CIAN} Your token is not for admin user')
                raise IceFlix.Unauthorized()
        return is_correct


    def openFile(self, media_id, user_token, current=None):
        """Given the media identifier, it will return a proxy to the file handler (FileHandler), which will enable downloading it - Can throws -> Unauthorized, WrongMediaId"""
        handler_prx = None
        correct = self.check_list_methods(user_token,False)
        if correct:
            if self.exist_media_dictionary(media_id):
                file_hand = FileHandler(self.media_list_hash.get(media_id))
                file_hand_prx = self.adapter.addWithUUID(file_hand)
                handler_prx = IceFlix.FileHandlerPrx.uncheckedCast(file_hand_prx) #From ObjectPrx to FileHandlerPrx
            else:
                logging.warning(f'{WHITE}[FileService_OpenFile] {YELLOW}-> {CIAN}The media id doesn´t exist in our records')
                raise IceFlix.WrongMediaId(media_id)
        else:
            logging.warning(f'{WHITE}[FileService_OpenFile] {YELLOW}-> {CIAN}We can´t check security with authenticator service')
        return handler_prx


    def uploadFile(self, uploader, admin_token, current=None):
        """Given the administrator token and a proxy for uploading files, it will store it in the directory and returns its identifier - Can throws -> Unauthorized"""
        size_for_section = 50
        id_file = None
        correct_up = self.check_list_methods(admin_token,True)
        if correct_up:
            with tempfile.NamedTemporaryFile(delete=False) as temp_file: #Autoclose
                while 1:
                    try:
                        receive_data = uploader.receive(size_for_section)
                    except Ice.Exception:
                        logging.warning(f'{WHITE}[FileService_UploadFile] {YELLOW}-> {CIAN}There is an error with receive data but it return id_file')
                        return id_file
                    if not receive_data:
                        break #There isn´t any more data available
                    temp_file.write(receive_data)

                temp_file.flush()
                temp_file.seek(0)

                id_file = hashlib.sha256(temp_file.read()).hexdigest()
                shutil.copyfile(temp_file.name, os.path.join(self.path_resources, id_file))
                os.unlink(temp_file.name) #remove temp file
                uploader.close()

            #Announced Files
            path_opt = os.path.join(self.path_resources,id_file)
            self.media_list_hash[id_file] = path_opt

            all_resources = list(self.media_list_hash.keys())
            self.annon_file_publish.announceFiles(all_resources,self.service_id_file)
            logging.warning(f'{WHITE}[FileService_UploadFile] {YELLOW}-> {CIAN}Files has been announced')
        else:
            logging.warning(f'{WHITE}[FileService_UploadFile] {YELLOW}-> {CIAN}We can´t check security with authenticator service')
        return id_file


    def removeFile(self, media_id, admin_token, current=None):
        """Give the identifier and the administrator token - Can throws -> Unauthorized, WrongMediaId"""
        correct_rem = self.check_list_methods(admin_token,True)
        if correct_rem:
            if self.exist_media_dictionary(media_id):
                os.remove(self.media_list_hash[media_id])
                self.media_list_hash.pop(media_id)

                all_resources_up = list(self.media_list_hash.keys())
                logging.warning(f'{WHITE}[FileService_RemoveFile] {YELLOW}-> {CIAN}The media has been removed')
                self.annon_file_publish.announceFiles(all_resources_up,self.service_id_file)
            else:
                logging.warning(f'{WHITE}[FileService_RemoveFile] {YELLOW}-> {CIAN}The media id doesn´t exist in our records')
                raise IceFlix.WrongMediaId(media_id)
        else:
            logging.warning(f'{WHITE}[FileService_RemoveFile] {YELLOW}-> {CIAN}We can´t check security with authenticator service')


    def obtain_my_proxy(self, my_proxy, current=None):
        """Proxy of servant"""
        self.proxy = my_proxy
        return self.proxy

#----------------------------
#        FileHandler
#----------------------------
class FileHandler(IceFlix.FileHandler):
    """When a user requests to open a file, the service will create a servant to handle its possible download"""

    def __init__(self, path):
        """Initialize parameters for open file"""
        self.service_id_file_handler = str(uuid.uuid4())

        self.path = path
        self.file = open(self.path, 'rb')


    def get_authenticator_hand(self, current=None):
        """Obtain one authenticator"""
        global last_authenticator_update
        global authenticator_list
        if not authenticator_list:
            logging.warning(f'{WHITE}[FileHandler] {YELLOW}-> {CIAN} There isn´t any authenticator available previusly stored')
            return None
        random_authenticator_hand = random.choice(list(authenticator_list.keys()))
        if abs(last_authenticator_update[random_authenticator_hand] - time.time()) > 12:
            logging.warning(f'{WHITE}[FileHandler] {YELLOW}-> {CIAN} There isn´t any authenticator available they are expired')
            authenticator_list.pop(random_authenticator_hand)
            return None
        return authenticator_list[random_authenticator_hand]


    def is_authorized(self, userToken, current=None):
        """Returns True if the userToken is authorized, False otherwise"""
        auth_pr = self.get_authenticator_hand()
        good_auth = False
        if auth_pr is not None:
            if auth_pr.isAuthorized(userToken):
                good_auth = True
        return good_auth


    def receive(self, size, userToken, current=None):
        """Receive the specified number of bytes from the file - Can throws -> Unauthorized"""
        part = None
        if self.is_authorized(userToken):
            part = self.file.read(size)
        else:
            logging.warning(f'{MAGENTA}[FileHandler_Receive] {YELLOW}-> {CIAN}There is a problem with user token not is administrator')
            raise IceFlix.Unauthorized()
        return part


    def close(self, userToken, current=None):
        """Close File and check if is authorized - Can throws -> Unauthorized"""
        if self.is_authorized(userToken):
            self.file.close()
        else:
            logging.warning(f'{MAGENTA}[FileHandler_Close] {YELLOW}-> {CIAN}There is a problem with user token')
            raise IceFlix.Unauthorized()


#----------------------------
#        FileUploader
#----------------------------
class FileUploader(IceFlix.FileUploader):
    """Class for upload files"""
    def __init__(self, path):
        """Initialize parameters"""
        self.service_id_file_uploader = str(uuid.uuid4())
        self.path = path
        self.file = open(self.path, 'rb')


    def receive(self, size, current=None):
        """Receive the specified number of bytes from the file"""
        part = None
        part = self.file.read(size)
        return part


    def close(self, current=None):
        """Close File"""
        self.file.close()


#----------------------------
#        Announcements
#----------------------------
class Announcements(IceFlix.Announcement):
    """Class for announcements"""
    def __init__(self, annon_event):
        """Initialize class parameters"""
        self.service_id_announc = str(uuid.uuid4())
        self.annon_event = annon_event


    def update_time(self, service_id):
        global last_authenticator_update
        """This method is for update time of services"""
        last_authenticator_update[service_id] = time.time()
        self.annon_event.set()


    def announce(self, service, service_id, current=None):
        """This method is for check services and update list of services if we haven`t add yet"""
        global authenticator_list
        logging.warning(f'{YELLOW}[Announcements] {YELLOW}-> {CIAN} Id service = {WHITE}%s', str(service_id))
        if service_id in authenticator_list:
            self.update_time(service_id)
        if not service_id in authenticator_list and service.ice_isA("::IceFlix::Authenticator"):
            logging.warning(f'{YELLOW}[Announcements] {YELLOW}-> {CIAN} New authenticator service has been detected with id {WHITE}%s', str(service_id))
            authenticator_list[service_id] = IceFlix.AuthenticatorPrx.uncheckedCast(service) #To AuthenticatorPrx
            self.update_time(service_id)
        else:
            logging.warning(f'{YELLOW}[Announcements] {YELLOW}-> {CIAN} The Announcement with id {WHITE}%s {CIAN}has been ignored{WHITE}', str(service_id))


#----------------------------
#        Run File Service
#----------------------------
class RunFile(Ice.Application):
    """Run File service"""
    def __init__(self):
        """Main parameters"""
        self.id_service_run = str(uuid.uuid4())
        self.broker = None
        self.servant = None
        self.my_proxy = None
        self.proxy_for_announce = None
        self.annon_publish = None
        self.annon_my_files = None
        self.event_init = threading.Event()
        self.my_resources = None

    ## see other option to improve
    def annon_sent(self, current=None):
        """Send announces every ten seconds"""
        time_every_announce = 10
        self.annon_publish.announce(self.my_proxy, self.id_service_run) #From Announcements
        logging.warning(f'{WHITE}[Announces] {YELLOW}-> {CIAN}Service was announced')
        time_annon_sent = threading.Timer(time_every_announce, self.annon_sent) #thread
        time_annon_sent.daemon = True
        time_annon_sent.start() #thread running in background


    def annon_files_others(self, current=None):
        """Send announces from our files"""
        time_every_announce_files = 20
        our_files = list(self.servant.media_list_hash.keys())
        #Announce Files
        self.annon_my_files.announceFiles(our_files, self.id_service_run)
        logging.warning(f'{WHITE}[Announces] {YELLOW}-> {CIAN}Our files was announced')
        time_annon_sent = threading.Timer(time_every_announce_files, self.annon_files_others) #thread
        time_annon_sent.daemon = True
        time_annon_sent.start() #thread running in background


    def run(self, args):
        #Initialize
        self.broker = self.communicator()
        adapter = self.broker.createObjectAdapter("FileServiceAdapter")
        adapter.activate()

        #Topics
        topic_annon = functions_topics.get_topic(functions_topics.getTopic_manager(self.broker), "Announcements")
        topic_annon_for_files = functions_topics.get_topic(functions_topics.getTopic_manager(self.broker), "FileAvailabilityAnnounce")

        #For publish
        self.annon_publish = IceFlix.AnnouncementPrx.uncheckedCast(topic_annon.getPublisher())
        self.annon_my_files = IceFlix.FileAvailabilityAnnouncePrx.uncheckedCast(topic_annon_for_files.getPublisher())

        annon_servant = Announcements(self.event_init)
        self.proxy_for_announce = adapter.addWithUUID(annon_servant)

        topic_annon.subscribeAndGetPublisher({}, self.proxy_for_announce) #Subscribe
        logging.warning(f'{GREEN}[RunFile] {YELLOW}-> {CIAN}Subscribed to topic announcements{WHITE}')

        #Set resources directory
        self.my_resources = self.broker.getProperties().getProperty("Directory")
        self.servant = FileService(self.my_resources, self.annon_my_files, adapter)

        self.my_proxy = adapter.addWithUUID(self.servant)
        self.servant.obtain_my_proxy(self.my_proxy)

        self.my_proxy = IceFlix.FileServicePrx.uncheckedCast(self.my_proxy)

        self.annon_sent() #Announce (10 seconds)
        self.annon_files_others() #FileAvailabityAnnounce (20 seconds)

        self.shutdownOnInterrupt()
        self.broker.waitForShutdown()

        #Unsubscribe for topic Announcements
        topic_annon.unsubscribe(self.proxy_for_announce)
        logging.warning(f'{GREEN}[RunFile] {YELLOW}-> {CIAN}Unsubscribed for topic announcements')

        return 0


if __name__ == '__main__':
    sys.exit(RunFile().main(sys.argv))
