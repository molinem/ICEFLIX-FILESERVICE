#!/usr/bin/env python3

#pylint: disable=C0301
#pylint: disable=unused-argument
#pylint: disable=E0401
#pylint: disable=C0103

#E0401 -> Import
#C0301 -> Too Long
#C0103 -> Use "_"
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
    logging.error("[FileService] -> There is one error with import iceflix module")

from functions_topics import getTopic_manager,get_topic

YELLOW = "\033[93m"
GREEN = "\033[32m"
BLUE = "\033[34m"
CIAN = "\033[36m"
WHITE = "\033[37m"
MAGENTA = "\033[35m"

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
#        Announcements
#----------------------------
class Announcements(IceFlix.Announcement):
    """Class for announcements"""
    def __init__(self, annon_event, time_to_cancel):
        self.service_id_announc = str(uuid.uuid4())
        self.myFileService = None #this will set up at RunFileService

        self.annon_event = annon_event
        self.time_to_cancel = time_to_cancel


    def update_time(self, service_id):
        """This method is for update time of services"""
        self.myFileService.last_main_update[service_id] = time.time()
        self.annon_event.set()


    def announce(self, service, service_id, current=None):
        """This method is for check services and update list of services if we haven`t add yet"""
        logging.warning(f'{YELLOW}[Announcements] {YELLOW}-> {CIAN} Id service = {WHITE}%s', str(service_id))
        if not service_id in self.myFileService.main_list and service.ice_isA("::IceFlix::Main"):
            logging.warning(f'{YELLOW}[Announcements] {YELLOW}-> {CIAN} New main service has been detected with id {WHITE}%s', str(service_id))
            self.myFileService.main_list[service_id] = IceFlix.MainPrx.uncheckedCast(service) #To MainPrx
            self.update_time(service_id)
            self.time_to_cancel.cancel()
        elif service_id in self.myFileService.main_list:
            """Update time"""
            self.update_time(service_id)
        else:
            logging.warning(f'{YELLOW}[Announcements] {YELLOW}-> {CIAN} The Announcement with id {WHITE}%s {CIAN}has been ignored{WHITE}', str(service_id))



#----------------------------
#        FileService
#----------------------------
class FileService(IceFlix.FileService):

    def __init__(self, path_resources, annon_file_publish, adapter):
        """Initialize parameters"""
        self.service_id_file = str(uuid.uuid4())
        self.proxy = None
        self.adapter = adapter

        self.path_resources = path_resources
        self.annon_file_publish = annon_file_publish

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
            logging.warning(f'{WHITE}[FileService] {YELLOW}-> {CIAN} There isn´t any main available previusly stored')
            return None
        random_main = random.choice(list(self.main_list.keys())) #Select random main service from list
        if abs(self.last_main_update[random_main] - time.time()) > 12:
            logging.warning(f'{WHITE}[FileService] {YELLOW}-> {CIAN} There isn´t any main available that aren´t expired')
            self.main_list.pop(random_main) #out to list
            return None
        return self.main_list[random_main]


    def exist_media_dictionary(self, media_id, current=None):
        """Check if the media id exist on the dictionary"""
        return media_id in self.media_list_hash


    def check_list_methods(self, user_token, fun_admin, current=None):
        """For check if there is some problem, used in openFile, uploadFile, removeFile"""
        main_prx = self.get_main_service()
        if main_prx is None:
            logging.warning(f'{WHITE}[FileService] {YELLOW}-> {CIAN} There isn´t any main available')

        auth_prx = main_prx.getAuthenticator()
        if auth_prx is None:
            logging.warning(f'{WHITE}[FileService] {YELLOW}-> {CIAN} There isn´t any authenticator available')

        if not auth_prx.isAuthorized(user_token):
            logging.warning(f'{WHITE}[FileService] {YELLOW}-> {CIAN} There is a problem with your token')
            raise IceFlix.Unauthorized()

        ##Check if admin
        if fun_admin:
            if not auth_prx.isAdmin(user_token):
                logging.warning(f'{WHITE}[FileService] {YELLOW}-> {CIAN} Your token is not for admin user')
                raise IceFlix.Unauthorized()


    def openFile(self, media_id, user_token, current=None):
        """Given the media identifier, it will return a proxy to the file handler (FileHandler), which will enable downloading it"""
        """Can throws -> Unauthorized, WrongMediaId"""
        handler_prx = None
        self.check_list_methods(user_token,False)
        if self.exist_media_dictionary(media_id):
            file_hand = FileHandler(self.media_list_hash.get(media_id))
            file_hand_prx = self.adapter.addWithUUID(file_hand)
            handler_prx = IceFlix.FileHandlerPrx.uncheckedCast(file_hand_prx) #From ObjectPrx to FileHandlerPrx
        else:
            logging.warning(f'{WHITE}[FileService_OpenFile] {YELLOW}-> {CIAN}The media id doesn´t exist in our records')
            raise IceFlix.WrongMediaId(media_id)
        return handler_prx


    def uploadFile(self, uploader, admin_token, current=None):
        """Given the administrator token and a proxy for uploading files, it will store it in the directory and returns its identifier"""
        """Can throws -> Unauthorized"""
        size_for_section = 50
        file_id = None
        self.check_list_methods(admin_token,True)
        with tempfile.NamedTemporaryFile(delete=False) as temp_file: #Autoclose
            try:
                shutil.copyfileobj(uploader, temp_file, length=size_for_section) #copy from uploader object to temporal file
            except Ice.Exception:
                logging.warning(f'{WHITE}[FileService_UploadFile] {YELLOW}-> {CIAN}There is an error with copy file')
            temp_file.flush()
            temp_file.seek(0)
            file_id = hashlib.sha256(temp_file.read()).hexdigest()
            shutil.copy(temp_file.name, os.path.join(self.path_resources, file_id))
            os.unlink(temp_file.name) #remove temp file
        #Announced Files
        path_opt = self.path_resources + "/" + file_id
        self.media_list_hash[file_id] = path_opt

        ###Check
        all_resources = list(self.media_list_hash.keys())
        self.annon_file_publish.announceFiles(all_resources,self.service_id_file)
        logging.warning(f'{WHITE}[FileService_UploadFile] {YELLOW}-> {CIAN}Files has been announced')
        return file_id


    def removeFile(self, media_id, admin_token, current=None):
        """Give the identifier and the administrator token"""
        """Can throws -> Unauthorized, WrongMediaId"""
        self.check_list_methods(admin_token,True)
        if self.exist_media_dictionary(media_id):
            os.remove(self.media_list_hash[media_id])
            self.media_list_hash.pop(media_id)

            all_resources_up = list(self.media_list_hash.keys())
            self.annon_file_publish.announceFiles(all_resources_up,self.service_id_file)
        else:
            logging.warning(f'{WHITE}[FileService_RemoveFile] {YELLOW}-> {CIAN}The media id doesn´t exist in our records')
            raise IceFlix.WrongMediaId(media_id)


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


    def is_authorized(self, userToken, current=None):
        """Returns True if the userToken is authorized, False otherwise"""
        if self.get_main_service() is not None:
            main_prx = self.get_main_service()
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
            logging.warning(f'{MAGENTA}[FileHandler_Receive] {YELLOW}-> {CIAN}There is a problem with user token')
            raise IceFlix.Unauthorized()
        return part


    def close(self, userToken, current=None):
        """Notify the server that the proxy for this file, won´t be used and will be removed"""
        """Can throws -> Unauthorized"""
        if self.is_authorized(userToken):
            self.file.close()
        else:
            logging.warning(f'{MAGENTA}[FileHandler_Close] {YELLOW}-> {CIAN}There is a problem with user token')
            raise IceFlix.Unauthorized()


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


    def timer_kill(self, current=None):
        """If we haven´t got any main shutdown service"""
        logging.warning(f'{WHITE}[Announces] {YELLOW}-> {CIAN}Service will shutdown, there isn´t any main')
        self.broker.shutdown() # or better -> os._exit(os.EX_OK)


    def run(self, args):
        #Initialize
        time_v = 12
        self.broker = self.communicator()
        adapter = self.broker.createObjectAdapter("FileServiceAdapter")
        adapter.activate()

        #Topics
        topic_annon = get_topic(getTopic_manager(self.broker), "Announcements")
        topic_annon_for_files = get_topic(getTopic_manager(self.broker), "FileAvailabilityAnnounce")

        #For publish
        self.annon_publish = IceFlix.AnnouncementPrx.uncheckedCast(topic_annon.getPublisher())
        self.annon_my_files = IceFlix.FileAvailabilityAnnouncePrx.uncheckedCast(topic_annon_for_files.getPublisher())

        #Timer for kill if not main
        time_to_cancel_run = threading.Timer(time_v, self.timer_kill)
        time_to_cancel_run.start()
        annon_servant = Announcements(self.event_init, time_to_cancel_run)
        self.proxy_for_announce = adapter.addWithUUID(annon_servant)
        
        topic_annon.subscribeAndGetPublisher({}, self.proxy_for_announce) #Subscribe
        logging.warning(f'{GREEN}[RunFile] {YELLOW}-> {CIAN}Subscribed to topic announcements{WHITE}')

        #Set resources directory
        self.my_resources = self.broker.getProperties().getProperty("Directory")
        self.servant = FileService(self.my_resources, self.annon_my_files, adapter)
        annon_servant.myFileService = self.servant #Check

        self.my_proxy = adapter.addWithUUID(self.servant)
        self.servant.obtain_my_proxy(self.my_proxy)


        self.my_proxy = IceFlix.FileServicePrx.uncheckedCast(self.my_proxy) #Cast
        self.event_init.wait(time_v)
        if self.event_init.is_set():
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
