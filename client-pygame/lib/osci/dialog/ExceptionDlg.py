#
#  Copyright 2001 - 2006 Ludek Smid [http://www.ospace.net/]
#
#  This file is part of IGE - Outer Space.
#
#  IGE - Outer Space is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  IGE - Outer Space is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with IGE - Outer Space; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

import pygameui as ui
from osci import gdata, client, versionString
import xmlrpclib, time, os, pygame, sys

class ExceptionDlg:

	def __init__(self, app):
		self.app = app
		self.createUI()

	def display(self, faultID, text):
		self.win.title = _('Unhandled exception: %s') % faultID
		self.faultID = faultID
		# add more informations
		more = [""]
		more.append("--- ADDITIONAL DATA ---")
		more.append("GMT date: %s" % time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime()))
		more.append("OS: %s" % os.name)
		more.append("Platform: %s" % sys.platform)
		more.append("OSCI version %s" % versionString)
		more.append("Pygame version %s" % pygame.version.ver)
		more.append("Python %s" % sys.version)
		try:
			more.append("turn: %d" % client.getTurn())
			more.append("player: %s [%d]" % (client.getPlayer().name, client.getPlayerID()))
		except AttributeError:
			pass
		text = text + "\n".join(more)
		#
		self.excText = text
		# dialog
		self.win.vText.text = text.split("\n")
		self.win.vSend.enabled = 1
		self.win.show()

	def hide(self):
		self.win.setStatus(_("Ready."))
		self.win.destroy()

	def onContinue(self, widget, action, data):
		self.win.destroy()

	def onClose(self, widget, action, data):
		self.win.destroy()
		self.app.exit()

	def onAbort(self, widget, action, data):
		self.win.destroy()
		import sys
		sys.exit(1)

	def onSend(self, widget, action, data):
		# post exception text
		# TODO support proxies
		url = "http://%s/RPC2" % gdata.config.game.server
		server = xmlrpclib.ServerProxy(url)
		server.issuemngr.reportIssue(self.faultID, self.excText)
		self.win.vSend.enabled = 0

	def createUI(self):
		w, h = gdata.scrnSize
		self.win = ui.Window(self.app,
			title = _('Unhandled exception'),
			modal = 1,
			escKeyClose = 1,
			movable = 0,
			rect = ui.Rect((w - 724) / 2, (h - 443) / 2, 724, 443),
			layoutManager = ui.SimpleGridLM(),
		)
		self.win.subscribeAction('*', self)
		s = ui.Scrollbar(self.win, layout = (35, 0, 1, 20))
		t = ui.Text(self.win, layout = (0, 0, 35, 20), id = "vText")
		t.attachVScrollbar(s)
		ui.Button(self.win, layout = (0, 20, 9, 1), text = _('Continue'),
			action = 'onContinue')
		ui.Button(self.win, layout = (9, 20, 9, 1), text = _('Close Application'),
			action = 'onClose')
		ui.Button(self.win, layout = (18, 20, 9, 1), text = _('Abort Application'),
			action = 'onAbort')
		ui.Button(self.win, layout = (27, 20, 9, 1), text = _('Send to server'),
			action = 'onSend', id = 'vSend', enabled = 0)
