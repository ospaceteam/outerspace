import gdata
from ige import log
import wx

# module globals
progressDlg = None

def onInitConnection():
	pass

def onConnInitialized():
	pass

def onCmdBegin():
	gdata.cmdInProgress = 1

def onCmdEnd():
	gdata.cmdInProgress = 0

def onUpdateStarting():
	global progressDlg
	log.debug("onUpdateStarting")
	if not progressDlg:
		progressDlg = wx.ProgressDialog(_('Progress'), _('Updating OSCI database...'), 100)

def onUpdateProgress(curr, max, text = None):
	global progressDlg
	log.debug("onUpdateProgress")
	progressDlg.Update(curr * 100 / max, text)

def onUpdateFinished():
	global progressDlg
	log.debug("onUpdateFinished")
	try:
		progressDlg.Close()
		progressDlg.Destroy()
		progressDlg = None
	except:
		log.warning("Cannot close ProgressDialog window")

def onNewMessages(number):
	#gdata.mainGameDlg.messagesDlg.update()
	global newMessages
	newMessages = 1

def onWaitingForResponse():
	pass

def createGameAccount():
	pass