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

from OpenGL.GL import *
from OpenGL.GLU import *

# pygame initialization
import pygame
from pygame.locals import *

#initialize SDL and prepare screen
def update():
	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
	rects = app.drawOpenGL()
	pygame.display.flip()

pygame.init()

screen = pygame.display.set_mode((800, 600), OPENGL | DOUBLEBUF, 32)
pygame.mouse.set_visible(1)
pygame.display.set_caption('PYGAME.UI 0.4 Test Client')

colorBlack = screen.map_rgb((0x00, 0x00, 0x00))
pygame.display.flip()

# create UI
import pygameui as ui

ui.SkinableTheme.setSkin("../OSSkin")
app = ui.Application(update, theme = ui.SkinableTheme)
app.windowSurfaceFlags = SWSURFACE

def echoHandler(widget, action, data):
	print 'ACTION', widget, action, data

popUpMenu = ui.Menu(app, title = "Test Menu",
	items = [
		ui.Item("Test 1", action = "MENU TEST", data = 1),
		ui.Item("Test 2", action = "MENU TEST", data = 2),
	],
)
popUpMenu.subscribeAction("*", echoHandler)

def menuHandler(widget, action, data):
	print "MENU"
	popUpMenu.show()

# create status window
progBars = []

for i in xrange(0, 2):
	win = ui.Window(app, font = 'large-bold')
	win.title = 'Test WINDOW 1X'
	#win.alwaysInBackground = 1
	win.rect = Rect(10 + 10 * i, 10 + 10 * i, 600, 500)
	win.layoutManager = ui.SimpleGridLM()
	win.rightButtonClose = 0
	w1 = ui.Button(win,
		text = '---',
		layout = (0, 0, 4, 1),
		tooltip = 'This is not real FPS counter.',
	)
	w1.subscribeAction('*', echoHandler)
	ui.Button(win,
		text = 'WEST (m)',
		statustip = 'This is super new button.',
		tooltip = 'Really?',
		align = ui.ALIGN_W,
		layout = (0, 1, 4, 1),
		rmbAction = "menu",
		action = "menu",
	).subscribeAction("menu", menuHandler)
	ui.Button(win,
		text = 'EAST',
		align = ui.ALIGN_E,
		layout = (0, 2, 4, 1)
	)
	ui.Button(win,
		text = 'NORTH',
		align = ui.ALIGN_N,
		layout = (0, 3, 4, 1)
	)
	ui.Button(win,
		text = 'SOUTH',
		align = ui.ALIGN_S,
		layout = (0, 4, 4, 1)
	)
	icon1 = pygame.image.load('img.png')
	icon2 = pygame.image.load('reddot.png')
	ui.Button(win,
		text = 'HELLO!',
		icons = (
			(icon1, ui.ALIGN_NW),
			(icon2, ui.ALIGN_NW),
			(icon2, ui.ALIGN_NE),
			(icon2, ui.ALIGN_SW),
			(icon2, ui.ALIGN_SE),
		),
		layout = (0, 5, 5, 2)
	)
	statusBar = ui.Label(win,
		align = ui.ALIGN_W,
		tooltip = 'This is a status bar which contains reports about...',
		layout = (0, 7, 6, 1),
	)
	app.statusBar = statusBar
	ui.Entry(win,
		align = ui.ALIGN_W,
		tooltip = 'Enter anything you like.',
		layout = (0, 8, 4, 1),
	).subscribeAction('*', echoHandler)
	x = 0
	for align in (ui.ALIGN_N, ui.ALIGN_S, ui.ALIGN_E, ui.ALIGN_W):
		ui.ArrowButton(win,
			direction = align,
			layout = (x, 9, 1, 1),
		)
		x += 1
	slider = ui.ScrollSlider(win,
		shown = 50,
		layout = (0, 10, 8, 1)
	)
	ui.ScrollSlider(win,
		shown = 10,
		layout = (0, 11, 8, 1)
	)
	ui.ScrollSlider(win,
		shown = 10,
		layout = (7, 0, 1, 10)
	)
	ui.Scrollbar(win,
		layout = (0, 12, 8, 1)
	).subscribeAction('*', echoHandler)
	ui.Scrollbar(win,
		layout = (6, 0, 1, 10)
	).subscribeAction('*', echoHandler)

	for x in xrange(8, 20, 2):
		for y in xrange(0, 10):
			ui.Button(win,
				text = '%d,%d' % (x, y),
				layout = (x, y, 2, 1),
				font = 'small',
				statustip = '%d,%d' % (x, y),
				enabled = (x + y) % 2
			)

	ui.Listbox(win,
		items = [ui.Item('One'), ui.Item('Two'), ui.Item('Three'), ui.Item('Four'),
			ui.Item('Five'), ui.Item('Six'), ui.Item('Seven'), ui.Item('Eight')],
		layout = (0, 13, 8, 7),
		multiselection = 1,
	).subscribeAction('*', echoHandler)

	ui.Listbox(win,
		items = [ui.Item('One', size = 1), ui.Item('Two', size = 2), ui.Item('Three', size = 3),
		ui.Item('Four', size = 4), ui.Item('Five', size = 5), ui.Item('Six', size = 6),
		ui.Item('Seven', size = 7), ui.Item('Eight', size = 8), ui.Item('Nine', size = 9)],
		columns = [('Name', 'text', 6, 0), ('Size', 'size', 6, ui.F_EDITABLE)],
		layout = (8, 13, 12, 7),
		columnLabels = 1,
	).subscribeAction('*', echoHandler)

	items = []
	for i in xrange(0, 100):
		items.append(ui.Item(str(i), tooltip = 'This is a tooltip', statustip = 'This is a statustip'))
	ui.ButtonArray(win,
		items = items,
		layout = (20, 13, 9, 6),
		buttonSize = (2, 2),
	)
	ui.Title(win,
		text = 'This is a title',
		align = ui.ALIGN_W,
		layout = (8, 12, 12, 1)
	)
	pBar = ui.ProgressBar(win, layout = (0, 20, 10, 1))
	progBars.append(pBar)
	scrlbar = ui.Scrollbar(win, layout = (28, 0, 1, 10))
	text = ui.Text(win, layout = (20, 0, 8, 10),
		text = [
			'This is a very looooong text which will be displayed in that text widget.',
			'And one more long line to show.',
			'And another one.',
			'And another one.',
			'And another one.',
			'And another one.',
			'And another one.'
		]
	)
	text.attachVScrollbar(scrlbar)
	app.setStatus('Ready.')

	win.show()

# init OpenGL
glViewport(0, 0, 800, 600)
glMatrixMode(GL_PROJECTION)
glLoadIdentity()
glOrtho(0, 800, 0, 600, -1, 1)
glClearColor(0.0, 0.0, 0.5, 0.0)
glPixelStorei(GL_PACK_ALIGNMENT, 1)
glPixelStorei(GL_UNPACK_ALIGNMENT, 1)

# create top bar
update()

fps = 0
frame = 0
time = pygame.time.get_ticks()
count = 0

# event loop
running = 1
while running:
	evt = pygame.event.wait()
	evts = pygame.event.get()
	evts.append(evt)

	for evt in evts:
		evt = app.processEvent(evt)
		if evt.type == QUIT:
			running = 0
			break
		if evt.type == KEYUP and evt.key == K_ESCAPE:
			running = 0
			break

	if app.needsUpdate():
		update()
		frame += 1

	now = pygame.time.get_ticks()
	if now - 1000 > time:
		time = now
		w1.text = u'FPS: %d' % frame
		frame = 0
	count += 1
	if count > 100: count = 0

	for pBar in progBars:
		pBar.value += 1
		if pBar.value > pBar.max:
			pBar.value = pBar.min
