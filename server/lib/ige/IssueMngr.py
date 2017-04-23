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

import log
import smtplib
from email.mime.text import MIMEText

class IssueMngr:

    def __init__(self):
        pass

    def rpc_reportIssue(self, faultID, text):
        # log it
        log.message("ISSUE:\n", text)
        # send it
        try:
            msg = MIMEText(text)
            msg["Subject"] = "Outer Space Issue %s" % faultID
            msg["From"] = "game_alpha@ospace.net"
            msg["To"] = "qark@ospace.net"
            smtp = smtplib.SMTP("localhost")
            smtp.sendmail(
                "game_alpha@ospace.net",
                ["qark@ospace.net"],
                msg.as_string()
            )
            smtp.quit()
        except:
            log.warning("Cannot send issue by e-mail")
        return 1

    def shutdown(self):
        pass
