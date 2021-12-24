import os
from ftplib import FTP
from pathlib import Path
from Logger import logger
from config import directory, root


directory = directory.replace('../', '')
LOGGER = logger.getLogger(__name__)


class FTPServer:

    statuses = ['unlocked', 'locked']

    def __init__(self, host=None, timeout=20):
        self._host = host
        self._timeout = timeout
        self._ftp = FTP()


    def connectServer(self, username, password):
        self._ftp.connect(self._host, timeout=self._timeout)
        self._ftp.login(username, password)
        self._ftp.set_pasv(True)
        self.createPaths()
        LOGGER.info('Connected')
        return self._ftp

    def statusUnlocked(self):
        self._ftp.rename('locked', 'unlocked')

    def statusLocked(self):
        self._ftp.rename('unlocked', 'locked')

    def getStatus(self):
        for status in self._ftp.nlst():
            if status in FTPServer.statuses:
                return status

    def listdir(self, _path):
        dirs = []
        _path = _path.replace('//', '/')

        for item in self._ftp.mlsd(_path):
            if item[1]['type'] == 'dir':
                dirs.append(item[0])
            else:
                if item[0] != '.' and item[0] != '..':
                    self._nondirs.append(item[0])

        if self._nondirs:
            for file in self._ftp.mlsd(_path):
                if file[1]['type'] == 'file':
                    self._paths.append(_path)
        else:
            pass

        for subdir in sorted(dirs):
            self.listdir('{}/{}/'.format(_path, subdir))

    def getPathsAndFilename(self):
        return [x.replace('//', '/') for x in self._paths], [y for y in self._nondirs]


    def uploadTree(self, PATH):
        if self.getStatus() == 'unlocked':
            self.statusLocked()
            self.deleteTree(PATH)

            try:
                for path, dirs, files in os.walk(PATH):
                    relativeFtpPath = '{}'.format(path.replace('\\', '/'))
                    try:
                        self._ftp.mkd(relativeFtpPath)
                    except:
                        pass
                    for file in files:
                        pathFile = '{}/{}'.format(relativeFtpPath, file)
                        self._ftp.storbinary('STOR {}'.format(pathFile),
                                             open('{}/{}'.format(path, file), 'rb'))
                self.statusUnlocked()
                while directory.replace('/', '') not in os.listdir():
                    os.chdir('..')
                LOGGER.info('upl tree')
            except Exception as e:
                self.statusUnlocked()
                LOGGER.error(e)


    def downloadTree(self, _path):
        if self.getStatus() == 'unlocked':
            self.statusLocked()
            self.listdir(_path)

            pathsFTP = self.getPathsAndFilename()
            files, paths = pathsFTP[1], pathsFTP[0]

            try:
                for path in paths:
                    Path(path).mkdir(parents=True, exist_ok=True)

                for (path, filename) in zip(paths, files):
                    os.chdir(path)
                    with open(filename, 'wb') as file:
                        self._ftp.retrbinary('RETR ' + path + filename, file.write)
                    os.chdir('..')
                self.statusUnlocked()
                while directory.replace('/', '') not in os.listdir():
                    os.chdir('..')
                LOGGER.info('down tree')

            except Exception as e:
                LOGGER.warning(e)
                while directory.replace('/', '') not in os.listdir():
                    os.chdir('..')
                self.statusUnlocked()


    def deleteTree(self, _path):
        if directory.replace('/', '') in self._ftp.nlst():
            self.listdir(_path)

            pathsFTP = self.getPathsAndFilename()
            files, paths = pathsFTP[1], pathsFTP[0]

            if not paths:
                dirs = self._ftp.nlst(_path)
                del dirs[0]
                del dirs[0]

                for file in dirs:
                    try:
                        self._ftp.rmd(_path + file)
                        self._ftp.cwd('..')
                    except Exception as e:
                        LOGGER.warning(e)
                        self._ftp.cwd(root + _path + file)
                        self.deleteTree(root + _path + file)

            else:
                for (path, filename) in zip(paths, files):
                    SP = root + path + filename
                    self._ftp.delete(SP)
                    self._ftp.cwd('..')
                    self._ftp.rmd(root + path.rsplit("/", 1)[0])

            self._ftp.cwd(root)
            self._ftp.rmd(directory.replace('/', ''))
            LOGGER.info('Tree delete')


    def createPaths(self):
        self._paths = []
        self._nondirs = []

    def mkdir(self, nameDir):
        try:
            self._ftp.mkd(nameDir)
        except:
            LOGGER.error(f'Error create dir {nameDir}')


    def chdir(self, pathFTP):
        self._ftp.cwd(pathFTP)

    def getFileList(self):
        self._ftp.nlst()

    def checkDir(self, nameDir):
        if nameDir in self._ftp.nlst(root):
           pass
        else:
            self.mkdir(nameDir)
            self.uploadTree(nameDir)

    def createLocker(self):
        if 'unlocked' not in self._ftp.nlst() and 'locked' not in self._ftp.nlst():
            try:
                open('unlocked', 'wb').close()
                self._ftp.storbinary('STOR unlocked', open('unlocked', 'rb'))
                LOGGER.info('Create locker')
            except Exception as e:
                LOGGER.warning(e)

    def checkLocker(self):
        if 'locked' in self._ftp.nlst():
            self.statusUnlocked()

    def closeConnect(self):
        LOGGER.info('Disconnected')
        self._ftp.close()

    def __del__(self):
        self.closeConnect()