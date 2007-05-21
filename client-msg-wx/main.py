import wx
import sys
sys.path.insert(0, 'lib')
sys.path.insert(0, '../server/lib')

import gdata, client
from ige import log
import handler
import version as Ver
import os, os.path
import binascii

from LoginDlg import LoginDlg
from Messager import Messager
from config import Config

class App(wx.App):
	"""Application class."""

	def OnInit(self):
		if gdata.config.game.lastlogin != None:
			login = gdata.config.game.lastlogin
		else:
			login = ""
		if gdata.config.game.lastpasswordcrypted:
			password = binascii.a2b_base64(gdata.config.game.lastpasswordcrypted)
		else:
			password = ""
		if gdata.config.game.lastgameid != None:
			gameID = gdata.config.game.lastgameid
		else:
			gameID = 'Alpha'

		self.loginDlg = LoginDlg(None, -1, _("Login"), login, password, gameID)
		val = self.loginDlg.ShowModal()
		if val == wx.ID_OK:
			#game = str(self.loginDlg.game.GetValue())
			login = str(self.loginDlg.login.GetValue())
			password = str(self.loginDlg.password.GetValue())
			if client.login(gameID, login, password):
				client.updateDatabase()
				gdata.config.game.lastlogin = login
				# TODO: remove in 0.6
				gdata.config.game.lastpassword = None
				#
				gdata.config.game.lastpasswordcrypted = binascii.b2a_base64(password).strip()
				gdata.config.game.lastgameid = gameID
				self.frame = Messager(None, -1, _("OuterSpace Message Reader"))
				self.frame.Show()
				self.SetTopWindow(self.frame)
				self.setTimer()
			else:
				dlg = wx.MessageDialog(None, _("Login failed"), _("Error"), wx.OK | wx.ICON_EXCLAMATION)
				dlg.ShowModal()
				dlg.Destroy()

		self.loginDlg.Destroy()
		return True

	def setTimer(self):
		timerId = wx.NewId()
		self.timer = wx.Timer(self, timerId)
		wx.EVT_TIMER(self, timerId, self.OnTimer)
		self.timer.Start(1000)

	def OnTimer(self, event):
		client.keepAlive()

def main():
	log.message("Starting IGE - Outer Space Messager Client version", Ver.versionString)
	log.debug("sys.path =", sys.path)
	log.debug("os.name =", os.name)

    # create required directories
	if not os.path.exists('var'):
		os.mkdir('var')

    # parse configuration
	gdata.config = Config('var/osci.ini')

    # default configuration
	if gdata.config.game.server == None:
		gdata.config.game.server = 'www.ospace.net:9080'

    # prepare internationalization
	if gdata.config.client.language == None:
		gdata.config.client.language = 'en'

	language = gdata.config.client.language

	import gettext
	try:
		tran = gettext.translation('OSPACE', 'res', languages = [language])
	except IOError:
		log.warning('OSCI', 'Cannot find catalog for', language)
		log.message('OSCI', 'Installing null translations')
		tran = gettext.NullTranslations()

	tran.install(unicode = 1)
	log.message('OSCI', 'Translations installed for %s languaage' % language)

	# client
	from igeclient.IClient import IClientException

	client.initialize(gdata.config.game.server, handler)

	app = App(False)
	app.MainLoop()

	# write configuration
	log.debug("Saving configuration.")
	gdata.config.save('var/osci.ini')

	# logout
	client.logout()

	log.debug("Shut down")

if __name__ == '__main__':
	main()
