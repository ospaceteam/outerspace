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
import copy
import json
import os

from ige import log

class AIRecord:
    def __init__(self):
        pass

    def __getattr__(self, name):
        return None

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return hash(self) == hash(other)

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

    It creates file in config directory, named ais_list which
    contains json representation of list of AI players of particular server.

    Data dumps used by ai clients are recommended to be saved to the directory
    <configDir>/ai_data/
    to be processed correctly.

    """

    def __init__(self, configDir):
        self.configDir = configDir
        self.records = []
        # parsing the file
        self.listname = "ais_list"
        try:
            self.records = json.load(open(os.path.join(self.configDir, self.listname), "r"), object_hook=aiRecordDecoder)
        except Exception, e:
            listfile = open(os.path.join(self.configDir, self.listname), "a")
            listfile.close()

    def save(self):
        json.dump(self.records, open(os.path.join(self.configDir, self.listname), "w"), cls=AIRecordEncoder, indent=2)

    def add(self, login, password, aiType):
        """ It adds new entry to the ais_list.

        """
        if login in self.getLogins():
            # great, account already exists
            return
        record = AIRecord()
        record.login = login
        record.password = password
        record.aiType = aiType
        self.records.append(record)

    def getAll(self):
        return self.records

    def getLogins(self):
        return map(lambda x: x.login, self.records)

    def removeAll(self):
        self.records = []

