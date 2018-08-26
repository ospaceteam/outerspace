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

import traceback
import time
import os
import log
import ige
import ige.version
from medusa import igerpc_handler, http_server, asyncore, logger, status_handler
from medusa import filesys, default_handler, counter, producers, xmlrpc_handler

callMap = {}
objMap = {}
registeredGames = {}

running = 0

def ping(obj):
    return True, None

## Handlers
def versionHandler(obj):
    result = {}
    result.update(ige.version.version)
    result["clientURLs"] = ige.version.clientURLs
    return result, None

def getRegisteredGamesHandler(obj):
    return registeredGames, None

## IGE RPC medusa handler
class igerpc(igerpc_handler.igerpc_handler):

    def __init__(self):
        igerpc_handler.igerpc_handler.__init__(self)
        self.seriousExcCounter = counter.counter()

    def call(self, packet):
        global callMap
        global running

        try:
            params = [packet.sid]
            params.extend(packet.params)
            packet.result, packet.messages = callMap[intern(packet.method)](*params)
            packet.method = None
            packet.params = None
            return packet
        except ige.NoAccountException, e:
            raise e
        except ige.GameException, e:
            raise e
        except ige.SecurityException, e:
            raise e
        except ige.CreatePlayerException, e:
            raise e
        except ige.ServerStatusException, e:
            raise e
        except ige.NoSuchObjectException, e:
            raise e
        except asyncore.ExitNow, e:
            raise e
        except Exception, e:
            log.warning('Cannot complete RPC call')
            self.seriousExcCounter.increment()
            raise e

    def status (self):
        return producers.simple_producer (
            '<li>%s' % status_handler.html_repr (self)
            + '<ul>'
            + '  <li><b>Total Commands:</b> %s' % self.commandCounter
            + '  <li><b>Completed:</b> %s' % self.completedCounter
            + '  <li><b>Serious Exceptions:</b> %s' % self.seriousExcCounter
            + '  <li><b>Total Exceptions:</b> %s' % self.exceptionsCounter
            + '</ul>'
            )

## XML RPC medusa handler
class xmlrpc(xmlrpc_handler.xmlrpc_handler):

    IDENT = 'XML RPC Request Handler'

    def __init__(self):
        xmlrpc_handler.xmlrpc_handler.__init__(self)
        self.commandCounter = counter.counter()
        self.completedCounter = counter.counter()
        self.exceptionsCounter = counter.counter()
        self.seriousExcCounter = counter.counter()

    def call(self, method, params):
        log.debug('CALL', method, params)
        try:
            instanceName, methodName = method.split('.')
            return getattr(objMap[instanceName], 'rpc_%s' % methodName)(*params)
            #except ige.NoAccountException, e:
            #    raise e
            #except ige.GameException, e:
            #    raise e
            #except ige.SecurityException, e:
            #    raise e
            #except ige.ServerStatusException, e:
            #    raise e
        except asyncore.ExitNow, e:
            raise e
        except Exception, e:
            log.warning('Cannot complete RPC call')
            self.seriousExcCounter.increment()
            raise e

    def status (self):
        return producers.simple_producer (
            '<li>%s' % status_handler.html_repr (self)
            + '<ul>'
            + '  <li><b>Total Commands:</b> %s' % self.commandCounter
            + '  <li><b>Completed:</b> %s' % self.completedCounter
            + '  <li><b>Serious Exceptions:</b> %s' % self.seriousExcCounter
            + '  <li><b>Total Exceptions:</b> %s' % self.exceptionsCounter
            + '</ul>'
            )

    def __repr__ (self):
        return '<%s at %x>' % (
            self.IDENT,
            id (self)
            )

## Public interface
def init(clientMngr, bookingMngr):
    global callMap

    callMap['ping'] = ping
    callMap['login'] = clientMngr.login
    callMap['logout'] = clientMngr.logout
    callMap['hello'] = clientMngr.hello
    callMap['createAccount'] = clientMngr.createAccount
    callMap['changePassword'] = clientMngr.changePassword
    callMap['getAccountData'] = clientMngr.getAccountData
    callMap['shutdown'] = clientMngr.serverShutdown
    callMap['cleanupSessions'] = clientMngr.cleanupSessions
    callMap['exportAccounts'] = clientMngr.exportAccounts
    callMap['getVersion'] = versionHandler
    callMap['getRegisteredGames'] = getRegisteredGamesHandler
    callMap['getBookingAnswers'] = bookingMngr.get_booking_answers
    callMap['getBookingOffers'] = bookingMngr.get_booking_offers
    callMap['toggleBooking'] = bookingMngr.toggle_booking
    callMap['createPrivateBooking'] = bookingMngr.create_private_booking
    callMap['deletePrivateBooking'] = bookingMngr.delete_private_booking

def register(game):
    global callMap

    callMap[game.gameID + '.selectPlayer'] = game.selectPlayer
    callMap[game.gameID + '.execute'] = game.execute
    callMap[game.gameID + '.createNewPlayer'] = game.createNewPlayer
    callMap[game.gameID + '.takeOverAIPlayer'] = game.takeOverAIPlayer
    callMap[game.gameID + '.takeOverPirate'] = game.takeOverPirate
    callMap[game.gameID + '.getActivePositions'] = game.getActivePositions
    callMap[game.gameID + '.getStartingPositions'] = game.getStartingPositions
    callMap[game.gameID + '.getTurnData'] = game.getTurnData
    callMap[game.gameID + '.turnFinished'] = game.turnFinished
    callMap[game.gameID + '.processTurn'] = game.processTurn
    callMap[game.gameID + '.backup'] = game.backup
    callMap[game.gameID + '.commitDatabases'] = game.commitDatabases

    global registeredGames
    registeredGames[game.gameID] = game.gameName


def xmlrpcPublish(name, obj):
    objMap[name] = obj

class emptyLogger:

    def log(self, data):
        pass
        #log.debug("MEDUSA", data)

def start(configDir):
    global running

    # install signal handler for SIGTERM
    import signal

    def signalHandler(signum, frame):
        global running

        log.message("RECEIVED SIGNAL", signum)
        running = 0

    signal.signal(signal.SIGTERM, signalHandler)

    # create server
    logger = emptyLogger()
    server = http_server.http_server('', 9080, logger_object = logger)

    fsys = filesys.os_filesystem (os.path.join(configDir, 'website'))
    default = default_handler.default_handler (fsys)
    server.install_handler(default)

    handler = igerpc()
    server.install_handler(handler)

    handler = xmlrpc()
    server.install_handler(handler)

    status = status_handler.status_extension([server])
    server.install_handler(status)

    running = 1

    # get poll function
    import select
    if hasattr(select, "poll"):
        poll = asyncore.poll3
    else:
        poll = asyncore.poll

    # main loop
    try:
        while running:
            poll(timeout = 1.0)
    except KeyboardInterrupt:
        log.message("KeyboardInterrupt")
    except asyncore.ExitNow:
        log.message("ExitNow")
    except:
        traceback.print_exc()
