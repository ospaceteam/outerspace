#
#  Copyright 2001 - 2016 Ludek Smid [http://www.ospace.net/]
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

import pygame

import Const
from Widget import Widget, registerWidget

# keys mapping
mapping = {
    pygame.K_KP0: pygame.K_0, pygame.K_KP1: pygame.K_1, pygame.K_KP2: pygame.K_2, pygame.K_KP3: pygame.K_3, pygame.K_KP4: pygame.K_4,
    pygame.K_KP5: pygame.K_5, pygame.K_KP6: pygame.K_6, pygame.K_KP7: pygame.K_7, pygame.K_KP8: pygame.K_8, pygame.K_KP9: pygame.K_9,
    pygame.K_KP_DIVIDE: pygame.K_SLASH, pygame.K_KP_MULTIPLY: pygame.K_ASTERISK,
    pygame.K_KP_MINUS: pygame.K_MINUS, pygame.K_KP_PLUS: pygame.K_PLUS, pygame.K_KP_PERIOD: pygame.K_PERIOD,
    pygame.K_KP_ENTER: pygame.K_RETURN, pygame.K_KP_EQUALS: pygame.K_EQUALS,
}

class Entry(Widget):

    def __init__(self, parent, **kwargs):
        Widget.__init__(self, parent)
        # data
        self.__dict__['text'] = u''
        self.__dict__['cursorPos'] = 0
        self.__dict__['action'] = None
        self.__dict__['showChar'] = None
        self.__dict__['reportValueChanged'] = False
        # flags
        self.processKWArguments(kwargs)
        parent.registerWidget(self)

    def draw(self, surface):
        self.theme.drawEntry(surface, self)
        return self.rect

    def onCursorChanged(self):
        # force redraw
        self.cursorPos += 1
        self.cursorPos -= 1
        # super
        Widget.onCursorChanged(self)

    def processKeyDown(self, evt):
        try:
            # this is done to translate keypad codes to normal ones as
            # we don't have any special meaning for these
            evt.key = mapping[evt.key]
        except KeyError:
            pass

        if evt.key == pygame.K_BACKSPACE:
            if self.cursorPos > 0:
                self.text = '%s%s' % (self.text[:self.cursorPos - 1], self.text[self.cursorPos:])
                self.cursorPos -= 1
        elif evt.key == pygame.K_DELETE:
            if self.cursorPos < len(self.text):
                self.text = '%s%s' % (self.text[:self.cursorPos], self.text[self.cursorPos + 1:])
        elif evt.key == pygame.K_RETURN:
            self.app.setFocus(None)
        elif evt.key == pygame.K_ESCAPE:
            self.app.setFocus(None)
        elif evt.key == pygame.K_HOME:
            self.cursorPos = 0
        elif evt.key == pygame.K_END:
            self.cursorPos = len(self.text)
        elif evt.key == pygame.K_LEFT:
            if self.cursorPos > 0: self.cursorPos -= 1
        elif evt.key == pygame.K_RIGHT:
            if self.cursorPos < len(self.text): self.cursorPos += 1
        elif evt.key == pygame.K_TAB:
            pass
        elif hasattr(evt, 'unicode') and evt.unicode:
            # TODO this is ugly windows only hack needed for Win 9x and XP
            # char = unicode(chr(ord(evt.unicode)), 'cp1250')
            char = evt.unicode
            if self.text:
                self.text = u'%s%c%s' % (
                    self.text[:self.cursorPos], char, self.text[self.cursorPos:]
                )
            else:
                self.text = char
            self.cursorPos += 1
        if (self.reportValueChanged):
            self.processAction("onValueChanged")
        return Widget.processKeyDown(self, Const.NoEvent)

    def onFocusGained(self):
        Widget.onFocusGained(self)
        self.cursorPos = len(self.text)

    def onFocusLost(self):
        Widget.onFocusLost(self)
        self.processAction(self.action)

registerWidget(Entry, 'entry')
