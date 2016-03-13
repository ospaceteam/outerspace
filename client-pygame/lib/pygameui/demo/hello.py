#
#  Copyright 2001 - 2006 Ludek Smid [http://www.ospace.net/]
#
#  This file is part of Pygame.UI.
#
#  Pygame.UI is free software; you can redistribute it and/or modify
#  it under the terms of the Lesser GNU General Public License as published by
#  the Free Software Foundation; either version 2.1 of the License, or
#  (at your option) any later version.
#
#  Pygame.UI is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  Lesser GNU General Public License for more details.
#
#  You should have received a copy of the Lesser GNU General Public License
#  along with Pygame.UI; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

import sys
sys.path.append('../..')

# pygame initialization
import pygame, pygame.font
from pygame.locals import *

#initialize SDL and prepare screen
pygame.display.init()
pygame.font.init()
screen = pygame.display.set_mode((800, 600), SWSURFACE, 16)
pygame.mouse.set_visible(1)
pygame.display.set_caption('Hello World')
pygame.display.update()

# create UI
import pygameui as ui

def actionHandler(widget, action, data):
	if action == 'action1':
		win.idButton.text = 'Thank you'
		win.idButton.tooltip = 'Press ESC to quit.'
		win.idButton.action = 'action2'
	else:
		win.idButton.text = 'Oh, thank you'
		win.idButton.tooltip = 'Press ESC to quit.'
		win.idButton.action = 'action1'

ui.SkinableTheme.setSkin("../OSSkin")
app = ui.Application()

win = ui.Window(app,
	title = 'Hello',
	rect = Rect(0, 0, 170, 120),
	layoutManager = ui.SimpleGridLM(),
	rightButtonClose = 1
)
ui.Button(win,
		id = 'idButton',
		text = 'Press Me',
		layout = (1, 1, 6, 1),
		tooltip = 'This is tooltip.',
		action = 'action1'
	)
ui.Label(win,
	text = 'Press ESC to quit.',
	layout = (1, 3, 6, 1),
)
win.subscribeAction('*', actionHandler)
win.show()

# event loop
while 1:
	evt = pygame.event.wait()

	evt = app.processEvent(evt)

	if evt.type == QUIT:
		break
	if evt.type == KEYUP and evt.key == K_ESCAPE:
		break
	if app.needsUpdate():
		screen.fill((0, 0, 0))
		rects = app.draw(screen)
		print "UPDATE", rects
		#pygame.display.update()
		pygame.display.update(rects)
