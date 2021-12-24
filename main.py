import os
import ftplib
from time import sleep
from Logger import logger
from server import FTPServer
from config import host, user, password, root, directory, timeout, flag



LOGGER = logger.getLogger(__name__)
if flag == True:
    os.chdir('..')


def connect():
    ftp = FTPServer(host, timeout)
    ftp.connectServer(user, password)

    ftp.chdir(root)
    ftp.createLocker()
    ftp.checkLocker()
    ftp.checkDir(directory.replace('/', ''))
    return ftp


def updateServer():
    ftp = connect()
    try:

        if directory.replace('/', '') not in os.listdir():
            ftp.downloadTree(directory)

        ftp.uploadTree(directory)
        sleep(timeout)
        ftp.downloadTree(directory)

    except ftplib.error_temp as e:
        LOGGER.error(e)
        ftp.closeConnect()
        ftp = connect()
        ftp.downloadTree(directory)

LOGGER.info('Start work')
while True:
    try:
        updateServer()
    except Exception as e:
        LOGGER.warning(e)
    except:
        break
LOGGER.info('Finish work')