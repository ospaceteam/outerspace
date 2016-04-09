#
#  Copyright 2001 - 2016 Ludek Smid [http://www.ospace.net/]
#
#  This file is part of Outer Space.
#
#  Outer Space is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  Outer Space is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Outer Space; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
import json
import os
import shutil
import tarfile

from ige import log

class AIRecord:
    def __init__(self):
        pass

    def __getattr__(self, name):
        return None

    def __repr__(self):
        return str(self.__dict__)

class AIRecordEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, AIRecord):
            return {'__class__':'AIRecord', '__value__':obj.__dict__}
        else:
            return json.JSONEncoder.default(obj)

def aiRecordDecoder(class_dict):
    if '__class__' in class_dict:
        if class_dict['__class__'] == 'AIRecord':
            obj = AIRecord()
            obj.__dict__ = class_dict['__value__']
            return obj
    # else
    return class_dict

class AIList:
    """ Class used to parse and work with list of ai players [which is then
    used by run_ai.py].

    It creates file in config directory, named ais_list.<gameName> which
    contains json representation of list of AI players of the particular
    game.

    Data dumps used by ai clients are recommended to be saved to the directory
    <configDir>/ai_data/<gameName>/<galaxy_name>/
    to be processed correctly.

    """

    def __init__(self, configDir, gameName):
        self.configDir = configDir
        self.gameName = gameName
        self.records = []
        # parsing the file
        self.listname = "ais_list.{0}".format(self.gameName)
        try:
            self.records = json.load(open(os.path.join(self.configDir, self.listname), "r"), object_hook=aiRecordDecoder)
        except Exception, e:
            listfile = open(os.path.join(self.configDir, self.listname), "a")
            listfile.close()

    def _save(self):
        json.dump(self.records, open(os.path.join(self.configDir, self.listname), "w"), cls=AIRecordEncoder)

    def add(self, login, password, aiType):
        """ It adds new line to the ais_list. Now without galaxy_name,
        because game doesn't know yet, to which galaxy will the player go.

        """
        record = AIRecord()
        record.login = login
        record.password = password
        record.aiType = aiType
        self.records.append(record)
        self._save()

    def remove(self, login):
        """ Removes the line associated with login.

        """
        for record in self.records[:]:
            if record.gameName == self.gameName and record.login == login:
                self.records.remove(record)
        self._save()

    def getAll(self):
        return self.records

    def getLogins(self):
        return self.records

    def removeAll(self):
        self.records = []
        self._save()

    def setGalaxy(self, login, galaxyName):
        """ Add [or change] the galaxy information to the record associated
        with login.

        """
        for record in self.records:
            if record.login == login:
                record.galaxyName = galaxyName
        try:
            os.makedirs(os.path.join(self.configDir, "ai_data", self.gameName, galaxyName))
        except OSError:
            pass
        self._save()
        return

    def finishGalaxy(self, galaxyName):
        """ Removes galaxy directory, and all player data contained within.

        """
        shutil.rmtree(os.path.join(self.configDir, 'ai_data', self.gameName, galaxyName))
        return

    def backup(self, backupPath):
        """ Creates bzip2 archive of ais_list file and ai_data directory

        """
        log.debug('Creating backup {0}-ais.osbackup'.format(backupPath))
        tar = tarfile.open('{0}-ais.osbackup'.format(backupPath), 'w:bz2')
        tar.add(os.path.join(self.configDir, self.listname))
        tar.add(os.path.join(self.configDir, 'ai_data', self.gameName))
        tar.close()

    def restore(self, backupPath):
        """ Extracts data of the ai players, as well as the ais_list file.

        """
        os.remove(os.path.join(self.configDir, self.listname))
        shutil.rmtree(os.path.join(self.configDir, 'ai_data', self.gameName))
        log.message('Restoring AI backup {0}'.format(backupPath))
        tar = tarfile.open(backupPath, 'r:bz2')
        tar.extractall()
        tar.close()
        self.records = []
        # parsing the file
        try:
            self.records = json.load(open(os.path.join(self.configDir, self.listname), "r"), object_hook=aiRecordDecoder)
        except Exception, e:
            listfile = open(os.path.join(self.configDir, self.listname), "a")
            listfile.close()
        log.message('AI backup restored')

