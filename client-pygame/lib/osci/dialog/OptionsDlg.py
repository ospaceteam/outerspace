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
import re, pygame
from osci import gdata
from ige.ospace.Const import *
import os, os.path

class OptionsDlg:
	"""Displays options dialog.

	Dialog can change display flags, display resolution, client language
	and proxy settings.
	Proxy can have one of following formats:
	http://username:password@host:port
	http://username@host:port
	http://host:port
	http://host
	where port must be integer value.
	Options are saved to file imediately, after users press OK button.
	"""
	def __init__(self, app):
		self.app = app
		self.createUI()

	def display(self, caller = None):
		self.caller = caller
		self.show()
		# show window
		if not self.win.visible:
			self.win.show()

	def hide(self):
		self.win.setStatus(_("Ready."))
		self.win.hide()

	def update(self):
		if self.win.visible:
			self.show()

	def show(self):
		# reading display flags
		if gdata.config.display.flags != None:
			strFlags = gdata.config.display.flags.split(' ')
			self.win.vSWSurface.checked = 0
			self.win.vHWSurface.checked = 0
			self.win.vDoublebuf.checked = 0
			self.win.vFullscreen.checked = 0
			if 'swsurface' in strFlags:
				self.win.vSWSurface.checked = 1
			if 'hwsurface' in strFlags:
				self.win.vHWSurface.checked = 1
			if 'doublebuf' in strFlags:
				self.win.vDoublebuf.checked = 1
			if 'fullscreen' in strFlags:
				self.win.vFullscreen.checked = 1

		# reading resolution info
		if gdata.config.display.resolution != None:
			width, height = gdata.config.display.resolution.split('x')
			self.win.vSmallRes.pressed = 0
			self.win.vMediumRes.pressed = 0
			self.win.vLargeRes.pressed = 0
			if width == '800' and height == '600':
				self.win.vSmallRes.pressed = 1
			elif width == '1024' and height == '768':
				self.win.vMediumRes.pressed = 1
			elif width == '1280' and height == '1024':
				self.win.vLargeRes.pressed = 1

		# reading client language
		if gdata.config.client.language != None:
			lang = gdata.config.client.language
			self.win.vEnglish.pressed = 0
			self.win.vCzech.pressed = 0
			if lang == 'en':
				self.win.vEnglish.pressed = 1
			elif lang == 'cs':
				self.win.vCzech.pressed = 1

		# reading proxy settings
		if gdata.config.proxy.http != None:
			proxy = gdata.config.proxy.http
			m = re.match('^http://(.*?):(.*?)@(.*?):(\d+)', proxy)
			host = ''
			port = ''
			username = ''
			password = ''
			if m == None:
				m = re.match('^http://(.*?)@(.*?):(\d+)', proxy)
				if m == None:
					m = re.match('^http://(.*?):(\d+)', proxy)
					if m == None:
						m = re.match('^http://(.*?)', proxy)
						if m != None:
							host = m.group(1)
					else:
						host = m.group(1)
						port = m.group(2)
				else:
					username = m.group(1)
					host = m.group(2)
					port = m.group(3)
			else:
				username = m.group(1)
				password = m.group(2)
				host = m.group(3)
				port = m.group(4)

			self.win.vProxyHost.text = host
			self.win.vProxyPort.text = port
			self.win.vProxyUsername.text = username
			self.win.vProxyPassword.text = password

		self.win.vTheme.text = _("Select Theme")
		self.win.vTheme2.text = gdata.config.client.theme
		self.win.vTheme.action = "onSelectTheme"

		# reading defaults
		if gdata.config.defaults.reportfinalization != None:
			val = gdata.config.defaults.reportfinalization
			self.win.vReportFin.checked = val == 'yes'

		if gdata.config.defaults.showredirects != None:
			val = gdata.config.defaults.showredirects
			self.win.vRedirects.checked = val == 'yes'

		if gdata.config.defaults.showcoords != None:
			val = gdata.config.defaults.showcoords
			self.win.vCoords.checked = val == 'yes'

		if gdata.config.defaults.highlights != None:
			val = gdata.config.defaults.highlights
			self.win.vHighlights.checked = val == 'yes'
			
		if gdata.config.defaults.displayhelp != None:
			val = gdata.config.defaults.displayhelp
			self.win.vDisplayHelp.checked = val == 'yes'

		self.win.vAutoLogin.enabled = False
		if gdata.savePassword:
			self.win.vSavePassword.enabled = True
			self.win.vSavePassword.checked = True
			self.win.vAutoLogin.enabled = True
		elif (gdata.config.game.lastpasswordcrypted != None) and (gdata.config.game.lastpasswordcrypted != ''):
			self.win.vSavePassword.enabled = True
			self.win.vSavePassword.checked = False
		else:
			self.win.vSavePassword.enabled = False
			self.win.vSavePassword.checked = False

		if gdata.config.game.autologin != None:
			val = gdata.config.game.autologin
			if self.win.vAutoLogin.enabled:
				self.win.vAutoLogin.checked = val == 'yes'

		# sounds/music
		if gdata.config.defaults.sound != None:
			val = gdata.config.defaults.sound
		else:
			val = "yes"
		self.win.vSoundEnabled.checked = val == "yes"
		self.win.vSoundVolume.slider.min = 0
		self.win.vSoundVolume.slider.max = 110
		if gdata.config.defaults.soundvolume != None:
			val = float(gdata.config.defaults.soundvolume)
		else:
			val = 100
		self.win.vSoundVolume.slider.position = val

		if gdata.config.defaults.music != None:
			val = gdata.config.defaults.music
		else:
			val = "yes"
		self.win.vMusicEnabled.checked = val == "yes"
		self.win.vMusicVolume.slider.min = 0
		self.win.vMusicVolume.slider.max = 110
		if gdata.config.defaults.musicvolume != None:
			val = float(gdata.config.defaults.musicvolume)
		else:
			val = 100
		self.win.vMusicVolume.slider.position = val

	def onCancel(self, widget, action, data):
		self.hide()
		if self.caller:
			self.caller.display()

	def onOK(self, widget, action, data):
		#set display flags
		flags = ''
		if self.win.vHWSurface.checked:
			flags += 'hwsurface '

		if self.win.vSWSurface.checked:
			flags += 'swsurface '

		if self.win.vDoublebuf.checked:
			flags += 'doublebuf '

		if self.win.vFullscreen.checked:
			flags += 'fullscreen '

		gdata.config.display.flags = flags

		# set client language
		if self.win.vEnglish.pressed:
			gdata.config.client.language = 'en'
		else:
			gdata.config.client.language = 'cs'

		#sel selected display resolution
		if self.win.vSmallRes.pressed:
			gdata.config.display.resolution = '800x600'
		elif self.win.vMediumRes.pressed:
			gdata.config.display.resolution = '1024x768'
		elif self.win.vLargeRes.pressed:
			gdata.config.display.resolution = '1280x1024'

		# set proxy
		host = self.win.vProxyHost.text
		port = self.win.vProxyPort.text
		username = self.win.vProxyUsername.text
		password = self.win.vProxyPassword.text

		proxy = ''
		# host must be always present
		if len(host) > 0:
			proxy += host
			if len(port) > 0:
				proxy += ':'
				proxy += port
			if len(password) > 0 and len(username):
				proxy = username + ':' + password + '@' + proxy
			elif len(username) > 0:
				proxy = username + '@' + proxy

			if len(proxy) > 0:
				proxy = 'http://' + proxy

		if len(proxy) > 0:
			gdata.config.proxy.http = proxy
		else:
			# if host not present, delete proxy section
			gdata.config.proxy = None

		# defaults
		if self.win.vReportFin.checked:
			gdata.config.defaults.reportfinalization = 'yes'
		else:
			gdata.config.defaults.reportfinalization = 'no'

		if self.win.vRedirects.checked:
			gdata.config.defaults.showredirects = 'yes'
		else:
			gdata.config.defaults.showredirects = 'no'

		if self.win.vCoords.checked:
			gdata.config.defaults.showcoords = 'yes'
		else:
			gdata.config.defaults.showcoords = 'no'

		if self.win.vHighlights.checked:
			gdata.config.defaults.highlights = 'yes'
		else:
			gdata.config.defaults.highlights = 'no'
		
		if self.win.vDisplayHelp.checked:
			gdata.config.defaults.displayhelp = 'yes'
		else:
			gdata.config.defaults.displayhelp = 'no'
			
		if self.win.vAutoLogin.checked:
			gdata.config.game.autologin = 'yes'
		else:
			gdata.config.game.autologin = 'no'

		if self.win.vSavePassword.checked:
			gdata.savePassword = True
		else:
			gdata.savePassword = False
			gdata.config.game.lastpasswordcrypted = None

		gdata.config.defaults.sound = ("no", "yes")[int(self.win.vSoundEnabled.checked)]
		gdata.config.defaults.soundvolume = self.win.vSoundVolume.slider.position
		gdata.config.defaults.music = ("no", "yes")[int(self.win.vMusicEnabled.checked)]
		gdata.config.defaults.musicvolume = self.win.vMusicVolume.slider.position
		ui.SkinableTheme.enableMusic(self.win.vMusicEnabled.checked)
		ui.SkinableTheme.enableSound(self.win.vSoundEnabled.checked)

		self.hide()
		if self.caller:
			self.caller.display()	# Redisplay login dlg
		elif gdata.mainGameDlg:
			gdata.mainGameDlg.update() # redraw screen (highlights etc)


	def onSmallRes(self, widget, action, data):
		self.win.vLargeRes.pressed = 0
		self.win.vMediumRes.pressed = 0

	def onMediumRes(self, widget, action, data):
		self.win.vSmallRes.pressed = 0
		self.win.vLargeRes.pressed = 0

	def onLargeRes(self, widget, action, data):
		self.win.vSmallRes.pressed = 0
		self.win.vMediumRes.pressed = 0

	def onEnglish(self, widget, action, data):
		self.win.vCzech.pressed = 0
		self.win.vEnglish.pressed = 1

	def onCzech(self, widget, action, data):
		self.win.vEnglish.pressed = 0
		self.win.vCzech.pressed = 1

	def onSelectTheme(self, widget, action, data):
		items = []
		themeDir = "res/themes"
		for term in os.listdir(themeDir):
			if os.path.isfile(os.path.join(themeDir, term, "config.ini")) and not term.startswith("."):
				item = ui.Item(term, tTheme = term)
				items.append(item)
		self.twin.vThemes.items = items
		self.twin.vThemes.itemsChanged()
		self.twin.show()

	def onThemeCancel(self, widget, action, data):
		self.twin.hide()

	def onThemeSelected(self, widget, action, data):
		self.recipientObjID = []
		text = ""
		if not self.twin.vThemes.selection:
			return
		curTheme = self.twin.vThemes.selection[0].tTheme
		# set theme for ui
		ui.SkinableTheme.setSkin(os.path.join("res/themes", curTheme))
		ui.SkinableTheme.loadMusic(gdata.config.defaults.mymusic)
		ui.SkinableTheme.playMusic()
		# all OK? (no exception) -> store settings
		gdata.config.client.theme = curTheme
		self.win.vTheme2.text = curTheme
		self.twin.hide()

	def onChangeMusicVolume(self, widget, action, data):
		ui.SkinableTheme.setMusicVolume(float(self.win.vMusicVolume.slider.position) / 100.0)

	def onChangeSoundVolume(self, widget, action, data):
		ui.SkinableTheme.enableSound(self.win.vSoundEnabled.checked)
		ui.SkinableTheme.setVolume(self.win.vSoundVolume.slider.position / 100.0)

	def onChangeSavePassword(self, widget, action, data):
		if self.win.vSavePassword.checked:
			self.win.vAutoLogin.enabled = True
		else:
			self.win.vAutoLogin.enabled = False
			self.win.vAutoLogin.checked = False
			
	def createUI(self):
		screenWidth, screenHeight = gdata.scrnSize
		# size of dialog in layout metrics (for SimpleGridLM)
		cols = 33
		rows = 16
		# dialog width and height in pixels
		width = cols * 20 + 5
		height = rows * 20 + 4
		#creating dialog window
		self.win = ui.Window(self.app,
			modal = 1,
			escKeyClose = 1,
			movable = 0,
			title = _("Options"),
			rect = ui.Rect((screenWidth - width) / 2, (screenHeight - height) / 2, width, height),
			layoutManager = ui.SimpleGridLM(),
		)
		self.win.subscribeAction('*', self)
		# first row is window title
		rows -= 1

		# Resolution
		ui.Title(self.win, layout = (1, 1, 5, 1), text = _('Resolution'),
			align = ui.ALIGN_NONE, font = 'normal-bold')
		ui.Button(self.win, layout = (1, 2, 5, 1), text = '800x600', id = 'vSmallRes',
			toggle = 1, action = 'onSmallRes')
		ui.Button(self.win, layout = (1, 3, 5, 1), text = '1024x768', id = 'vMediumRes',
			toggle = 1, action = 'onMediumRes')
		ui.Button(self.win, layout = (1, 4, 5, 1), text = '1280x1024', id = 'vLargeRes',
			toggle = 1, action = 'onLargeRes')

		# Languages
		ui.Title(self.win, layout = (1, 6, 5, 1), text = _('Language'),
			align = ui.ALIGN_NONE, font = 'normal-bold')
		ui.Button(self.win, layout = (1, 7, 5, 1), text = _('English'), id = 'vEnglish',
			toggle = 1, action = 'onEnglish')
		ui.Button(self.win, layout = (1, 8, 5, 1), text = _('Czech'), id = 'vCzech',
			toggle = 1, action = 'onCzech')

		# Theme
		ui.Title(self.win, layout = (1, 10, 5, 1), text = _('Themes'),
			align = ui.ALIGN_NONE, font = 'normal-bold')
		ui.Button(self.win, layout = (1, 11, 5, 1), id = "vTheme", align = ui.ALIGN_W)
		ui.ActiveLabel(self.win, layout = (1, 12, 5, 1), id = "vTheme2", align = ui.ALIGN_W)
		width = 304  # 15 * 20 + 4
		height = 264 # 13 * 20 + 4
		self.twin = ui.Window(self.app,
			modal = 1,
			escKeyClose = 1,
			titleOnly = 0,
			movable = 0,
			title = _("Select theme"),
			rect = ui.Rect((screenWidth - width) / 2, (screenHeight - height) / 2, width, height),
			layoutManager = ui.SimpleGridLM(),
		)
		self.twin.subscribeAction('*', self)

		# rename
		ui.Listbox(self.twin, layout = (0, 0, 15, 11), id = 'vThemes', columnLabels = 0,
			columns = ((None, 'text', 0, ui.ALIGN_W),), multiselection = 0, sortedBy=('text', 1))
		# status bar + submit/cancel
		ui.TitleButton(self.twin, layout = (10, 11, 5, 1), text = _("Select"), action = 'onThemeSelected')
		ui.TitleButton(self.twin, layout = (5, 11, 5, 1), text = _("Cancel"), action = 'onThemeCancel')
		ui.Title(self.twin, id = 'vStatusBar', layout = (0, 11, 5, 1), align = ui.ALIGN_W)

		# Screen flags
		ui.Title(self.win, layout = (7, 1, 5, 1), text = _('Display flags'),
			align = ui.ALIGN_NONE, font = 'normal-bold')
		ui.Check(self.win, layout = (7, 2, 5, 1), text = _('Fullscreen'), id = 'vFullscreen',
			checked = 0)
		ui.Check(self.win, layout = (7, 3, 5, 1), text = _('Double buf.'), id = 'vDoublebuf',
			checked = 0)
		ui.Check(self.win, layout = (7, 4, 5, 1), text = _('HW surface'), id = 'vHWSurface',
			checked = 0)
		ui.Check(self.win, layout = (7, 5, 5, 1), text = _('SW surface'), id = 'vSWSurface',
			checked = 0)

		# Defaults
		ui.Title(self.win, layout = (7, 7, 25, 1), text = _('Default settings'),
			align = ui.ALIGN_NONE, font = 'normal-bold')
		ui.Check(self.win, layout = (7, 8, 8, 1), text = _('Report finalization'), id = 'vReportFin',
			checked = 0)
		ui.Check(self.win, layout = (7, 9, 8, 1), text = _('Show redirects'), id = 'vRedirects',
			checked = 1)
		ui.Check(self.win, layout = (15,8,8,1), text = _('Show coordinates'), id = 'vCoords',
			checked = 1)
		ui.Check(self.win, layout = (15,9,8,1), text = _('Players highlight'), id = 'vHighlights',
			checked = 1)
		ui.Check(self.win, layout = (23, 8, 9, 1), text = _('Display help/tooltip'), id = 'vDisplayHelp',
			checked = 1)

		# Login settings
		ui.Title(self.win, layout = (7,11, 15, 1), text = _('Login settings'),
			align = ui.ALIGN_NONE, font = 'normal-bold')
		ui.Check(self.win, layout = (15,12,8,1), text = _('Auto-login'), id = 'vAutoLogin',
			checked = 0)
		ui.Check(self.win, layout = (7,12,8,1), text = _('Remember password'), id = 'vSavePassword',
			checked = 0, action = "onChangeSavePassword")

		# proxy settings
		ui.Title(self.win, layout = (13, 1, 9, 1), text = _('Proxy'), font = 'normal-bold')
		ui.Label(self.win, layout = (13, 2, 4, 1), text = _('Host:'), align = ui.ALIGN_E)
		ui.Entry(self.win, layout = (17, 2, 5, 1), id = 'vProxyHost', align = ui.ALIGN_W)
		ui.Label(self.win, layout = (13, 3, 4, 1), text = _('Port:'), align = ui.ALIGN_E)
		ui.Entry(self.win, layout = (17, 3, 5, 1), id = 'vProxyPort', align = ui.ALIGN_W)
		ui.Label(self.win, layout = (13, 4, 4, 1), text = _('Username:'), align = ui.ALIGN_E)
		ui.Entry(self.win, layout = (17, 4, 5, 1), id = 'vProxyUsername', align = ui.ALIGN_W)
		ui.Label(self.win, layout = (13, 5, 4, 1), text = _('Password:'), align = ui.ALIGN_E)
		ui.Entry(self.win, layout = (17, 5, 5, 1), id = 'vProxyPassword', align = ui.ALIGN_W)

		# sound options
		ui.Title(self.win, layout = (23, 1, 9, 1), text = _('Sound / Music'), font = 'normal-bold')
		ui.Check(self.win, layout = (23, 2, 9, 1), text = _('Sounds'), id = 'vSoundEnabled',
			checked = 1)
		ui.Scrollbar(self.win, layout = (23, 3, 9, 1), id = 'vSoundVolume',
			action = "onChangeSoundVolume")
		ui.Check(self.win, layout = (23, 4, 9, 1), text = _('Music'), id = 'vMusicEnabled',
			checked = 1)
		ui.Scrollbar(self.win, layout = (23, 5, 9, 1), id = 'vMusicVolume',
			action = "onChangeMusicVolume")

		# dialog bottom line
		ui.Title(self.win, layout = (0, rows - 1, cols - 10, 1))
		ui.TitleButton(self.win, layout = (cols - 10, rows - 1, 5, 1), text = _("Cancel"), action = 'onCancel')
		ui.TitleButton(self.win, layout = (cols - 5, rows - 1, 5, 1), text = _("OK"), action = 'onOK')
