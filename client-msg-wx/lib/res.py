import gdata
import glob, math
from ige.ospace.Const import *

smallStarImgs = None
techImgs = None
bigStarImgs = None
planetImgs = None
cmdInProgressImg = None
loginLogoImg = None
structProblemImg = None
structOffImg = None
icons = {}

def getUnknownName():
	return _('[Unknown]')

def getNA():
	return _('N/A')

def formatTime(time):
	time = int(math.ceil(time))
	sign = ''
	if time < 0:
		time = - time
		sign = '-'
	days = time / 24
	hours = time % 24
	return '%s%d:%02d' % (sign, days, hours)

def formatBE(b, e):
	return '%d / %d' % (b, e)
