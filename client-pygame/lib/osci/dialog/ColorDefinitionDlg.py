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
from osci import client, gdata, res
from ige import log

class ColorDefinitionDlg:

	def __init__(self, app):
		self.app = app
		self.createUI()

	def display(self, color = None, confirmAction = None):
		self.confirmAction = confirmAction
		if color == None:
			self.color = (0xff,0xff,0xff)
		else:
			self.color = color
		self.win.vR.text = hex(self.color[0])
		self.win.vG.text = hex(self.color[1])
		self.win.vB.text = hex(self.color[2])
		log.debug("ColorDefinitionDlg(%s,%s,%s)" % (self.win.vR.text,self.win.vG.text,self.win.vB.text))
		self.win.show()
		self.app.setFocus(self.win.vR)
		# colorbox
		self.win.vColor.color = self.color
		# register for updates
		if self not in gdata.updateDlgs:
			gdata.updateDlgs.append(self)

	def hide(self):
		self.win.setStatus(_("Ready."))
		self.win.hide()
		# unregister updates
		if self in gdata.updateDlgs:
			gdata.updateDlgs.remove(self)

	def update(self):
		self.show()

	def onOK(self, widget, action, data):
		try:
			r = int(self.win.vR.text,16)
			g = int(self.win.vG.text,16)
			b = int(self.win.vB.text,16)
			if not r in range(0,256):
				self.app.setFocus(self.win.vR)
				raise ValueError
			elif not g in range(0,256):
				self.app.setFocus(self.win.vG)
				raise ValueError
			elif not b in range(0,256):
				self.app.setFocus(self.win.vB)
				raise ValueError
		except ValueError:
			self.win.setStatus(_("Values must be hexa numbers between 0x00 - 0xff"))
			return
		self.hide()
		self.color = (r, g, b)
		if self.confirmAction:
			self.confirmAction()

	def onCancel(self, widget, action, data):
		self.color = None
		self.hide()

	def createUI(self):
		w, h = gdata.scrnSize
		cols = 10
		rows = 5
		width = cols * 20 + 5
		height = rows * 20 + 4
		self.win = ui.Window(self.app,
			modal = 1,
			escKeyClose = 1,
			movable = 0,
			title = _('Color Definition'),
			rect = ui.Rect((w - width) / 2, (h - height) / 2, width, height),
			layoutManager = ui.SimpleGridLM(),
			tabChange = True,
		)
		# creating dialog window
		self.win.subscribeAction('*', self)

		# R
		ui.Label(self.win,text = _("Red:"), align = ui.ALIGN_E, layout = (1, 0, 3, 1))
		ui.Entry(self.win, id = 'vR',align = ui.ALIGN_W,layout = (4, 0, 3, 1), orderNo = 1, reportValueChanged = True,)
		# G
		ui.Label(self.win,text = _("Green:"),align = ui.ALIGN_E,layout = (1, 1, 3, 1))
		ui.Entry(self.win, id = 'vG',align = ui.ALIGN_W,layout = (4, 1, 3, 1), orderNo = 2, reportValueChanged = True,)
		# B
		ui.Label(self.win,text = _("Blue:"),align = ui.ALIGN_E,layout = (1, 2, 3, 1))
		ui.Entry(self.win, id = 'vB',align = ui.ALIGN_W,layout = (4, 2, 3, 1), orderNo = 3, reportValueChanged = True,)

		# color example
		ui.ColorBox(self.win, id = 'vColor', layout = (8, 0, 2, 3), margins = (4, 3, 4, 4))

		#i.Title(self.win, layout = (0, 4, 2, 1))
		ui.TitleButton(self.win, layout = (0, 3, 5, 1), text = _("Cancel"), action = "onCancel")
		okBtn = ui.TitleButton(self.win, layout = (5, 3, 5, 1), text = _("OK"), action = 'onOK')
		self.win.acceptButton = okBtn

	def onValueChanged(self, widget, action, data):
		try:
			r = int(self.win.vR.text,16)
			g = int(self.win.vG.text,16)
			b = int(self.win.vB.text,16)
		except:
			return
		if not r in range(0,256) or not g in range(0,256) or not b in range(0,256):
			return
		self.win.vColor.color = (r, g, b)
