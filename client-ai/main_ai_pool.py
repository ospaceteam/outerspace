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

from main_ai import runAIClient

def runAIPool(options):
    import copy
    import sys
    import os
    import time
    import tempfile
    import traceback
    import multiprocessing
    import re
    import copy

    from ai_parser import AIList


    games = []
    if options.game:
        games.append(options.game)
    else:
        # support for games autodetect is not implemented
        raise NotImplementedError

    aiPool = multiprocessing.Pool(processes = options.procs)

    results = []
    for gameName in games:
        aiList = AIList(options.configDir)
        for record in aiList.getAll():
            optAI = copy.copy(options)
            optAI.configDir = os.path.join(options.configDir, 'ai_data', gameName)
            optAI.login = record.login
            optAI.password = record.password
            optAI.ai = record.aiType
            optAI.game = gameName
            optAI.test = False
            results.append(aiPool.apply_async(runAIClient, [optAI]))
    aiPool.close()
    for result in results:
        try:
            result.get()
        except Exception as exc:
            # having pass or continue here prevents exception from being printed
            # What the actual hell?
            True
    aiPool.join()
    sys.exit()

