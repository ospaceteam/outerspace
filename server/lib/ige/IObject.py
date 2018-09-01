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
import types

import Const
import log

from ige import GameException, SecurityException
from ige.IDataHolder import IDataHolder

def public(access):
    """ Decorator to mark methods public with appropriate access level. """
    def public_decorator(func):
        func.public = True
        func.accLevel = access
        return func
    return public_decorator

class IObject:

    typeID = Const.T_OBJECT
    forums = []

    def __init__(self, gameMngr):
        self.gameMngr = gameMngr
        self._cmd = gameMngr.cmdPool

    def cmd(self, obj):
        return self._cmd[obj.type]

    def new(self, type):
        obj = IDataHolder()
        self._cmd[type].init(obj)
        return obj

    def init(self, obj):
        # call superclass
        pass
        # define new attributes
        obj.oid = Const.OID_NONE
        obj.type = self.typeID
        obj.owner = Const.OID_NONE
        obj.compOf = Const.OID_NONE
        obj.name = u'Unnamed'
        # not needed
        # obj.accRights = {}

    def getReferences(self, tran, obj):
        return None

    def upgrade(self, tran, obj):
        # call update method
        try:
            self.cmd(obj).update(tran, obj)
        except:
            log.warning("Cannot execute update method on", obj.oid)
        refObj = self.new(obj.type)
        new = refObj.__dict__.keys()
        old = obj.__dict__.keys()
        changed = 0
        # change attributes
        # remove old
        for attr in old:
            if attr in new:
                new.remove(attr)
            else:
                log.debug('IObject', 'Upgrade - del', obj.oid, obj.type, attr)
                delattr(obj, attr)
                changed = 1
        # set new
        for attr in new:
            log.debug('IObject', 'Upgrade - new', obj.oid, obj.type, attr)
            setattr(obj, attr, getattr(refObj, attr))
            changed = 1

    def update(self, tran, obj):
        pass

    def loadDOMAttrs(self, obj, elem):
        for index in xrange(0, elem.attributes.length):
            attr = elem.attributes.item(index)
            if hasattr(obj, attr.nodeName):
                attrType = type(getattr(obj, attr.nodeName))
                if attrType == types.IntType:
                    value = int(attr.nodeValue)
                elif attrType == types.FloatType:
                    value = float(attr.nodeValue)
                elif attrType == types.UnicodeType:
                    value = attr.nodeValue
                elif attrType == types.StringType:
                    value = attr.nodeValue
                else:
                    raise 'Unsupported attribute type %s' % attrType
                setattr(obj, attr.nodeName, value)
            else:
                raise GameException('Unsupported attribute %s' % attr.nodeName)

    @public(Const.AL_INFO)
    def getInfo(self, tran, obj):
        return obj

    @public(Const.AL_INFO)
    def get(self, tran, obj):
        return self.cmd(obj).getInfo(tran, obj)

    @public(Const.AL_NONE)
    def getPublicInfo(self, tran, obj):
        result = IDataHolder()
        result.oid = obj.oid
        return result

    @public(Const.AL_ADMIN)
    def set(self, tran, obj, attr, value):
        if hasattr(obj, attr):
            setattr(obj, attr, value)
            return 1
        raise GameException('No such attribute.')


    ## messaging api
    @public(Const.AL_NONE)
    def sendMsg(self, tran, obj, message):
        if tran.session.cid != Const.OID_ADMIN:
            message["sender"] = tran.session.nick
            message["senderID"] = tran.session.cid
        # check attributes
        if "forum" not in message:
            raise GameException("Forum not specified.")
        if message["forum"] not in self.forums:
            raise GameException("No such forum.")
        if "topic" not in message:
            raise GameException("Topic not specified.")
        if "data" not in message and "text" not in message:
            raise GameException("Text or structured data not specified.")
        # check permissions
        if tran.session.cid != Const.OID_ADMIN and \
            not self.canSendMsg(tran, obj, message["senderID"], message["forum"]):
            raise SecurityException("You cannot send message to this entity.")
        #
        message["recipient"] = obj.name
        message["recipientID"] = obj.oid
        # send message
        return tran.gameMngr.msgMngr.send(tran.gameMngr.gameID, obj.oid, message)

    @public(Const.AL_ADMIN)
    def sendAdminMsg(self, tran, obj, message):
        # check attributes
        if "forum" not in message:
            raise GameException("Forum not specified.")
        if message["forum"] not in self.forums:
            raise GameException("No such forum.")
        if "topic" not in message:
            raise GameException("Topic not specified.")
        if "data" not in message and "text" not in message:
            raise GameException("Text or structured data not specified.")
        #
        message["recipient"] = obj.name
        message["recipientID"] = obj.oid
        # send message
        return tran.gameMngr.msgMngr.send(tran.gameMngr.gameID, obj.oid, message)

    @public(Const.AL_NONE)
    def getMsgs(self, tran, obj, lastID = -1):
        if not self.canGetMsgs(tran, obj, tran.session.cid):
            raise SecurityException("You cannot read messages of this entity.")
        # get messages
        return tran.gameMngr.msgMngr.get(tran.gameMngr.gameID, obj.oid, lastID)

    @public(Const.AL_NONE)
    def deleteMsgs(self, tran, obj, ids):
        if not self.canManageMsgs(tran, obj, tran.session.cid):
            raise SecurityException("You cannot manage messages of this entity.")
        # get messages
        return tran.gameMngr.msgMngr.delete(tran.gameMngr.gameID, obj.oid, ids)

    @public(Const.AL_ADMIN)
    def deleteOldMsgs(self, tran, obj):
        for forum in self.forums:
            tran.gameMngr.msgMngr.deleteOld(tran.gameMngr.gameID, obj.oid, forum, maxAge = self.forums[forum])

    def canSendMsg(self, tran, obj, oid, forum):
        return 0

    def canGetMsgs(self, tran, obj, oid):
        return oid == obj.oid

    def canManageMsgs(self, tran, obj, oid):
        return oid == obj.oid or oid == Const.OID_ADMIN

    def getMailboxName(self, tran, obj):
        return (tran.gameMngr.gameID, obj.oid)
