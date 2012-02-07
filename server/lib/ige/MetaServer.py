#
#  Copyright 2001 - 2012 Ludek Smid [http://www.ospace.net/]
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
#  along with IGE - Outer Space; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
import xmlrpclib
from ige import log

class WordpressMetaServer(object):
    """Instance of this class provides metaserver RPC interface"""
    
    def __init__(self, url):
        self.rpc = xmlrpclib.ServerProxy(url)
    
    def verifyPassword(self, login, password):
        """Called by Authentication module, returns 0 if password is valid"""
        try:
            return self.rpc.ospace.verify_user(login, password)
        except xmlrpclib.Fault, f:
            if f.faultString == "Bad login/pass combination.":
                return False
            log.warning("Cannot complete Wordpress XML-RPC call")
