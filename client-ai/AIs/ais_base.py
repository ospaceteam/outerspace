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
from ige import log
from ige.ospace import Const
from ige.ospace import Rules
from ige.ospace import Utils

import ai_tools as tool

class AI(object):
    def __init__(self, client):
        self.client = client
        self.db = client.db
        self.player = client.getPlayer()

        tool.tool_parseDB(self.client, self.db)

    def economy_manager(self):
        raise NotImplementedError

    def defense_manager(self):
        raise NotImplementedError

    def offense_manager(self):
        raise NotImplementedError

    def research_manager(self):
        raise NotImplementedError

    def diplomacy_manager(self):
        raise NotImplementedError

    def run(self):
        self.economy_manager()
        self.defense_manager()
        self.offense_manager()
        self.research_manager()
        self.diplomacy_manager()
        
