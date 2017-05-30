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

from pygame.locals import *
from Const import *
from Widget import Widget, registerWidget

# keys mapping
mapping = {
    K_KP0: K_0, K_KP1: K_1, K_KP2: K_2, K_KP3: K_3, K_KP4: K_4,
    K_KP5: K_5, K_KP6: K_6, K_KP7: K_7, K_KP8: K_8, K_KP9: K_9,
    K_KP_DIVIDE: K_SLASH, K_KP_MULTIPLY: K_ASTERISK,
    K_KP_MINUS: K_MINUS, K_KP_PLUS: K_PLUS, K_KP_PERIOD: K_PERIOD,
    K_KP_ENTER: K_RETURN, K_KP_EQUALS: K_EQUALS,
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

        if evt.key == K_BACKSPACE:
            if self.cursorPos > 0:
                self.text = '%s%s' % (self.text[:self.cursorPos - 1], self.text[self.cursorPos:])
                self.cursorPos -= 1
        elif evt.key == K_DELETE:
            if self.cursorPos < len(self.text):
                self.text = '%s%s' % (self.text[:self.cursorPos], self.text[self.cursorPos + 1:])
        elif evt.key == K_RETURN:
            self.app.setFocus(None)
        elif evt.key == K_ESCAPE:
            self.app.setFocus(None)
        elif evt.key == K_HOME:
            self.cursorPos = 0
        elif evt.key == K_END:
            self.cursorPos = len(self.text)
        elif evt.key == K_LEFT:
            if self.cursorPos > 0: self.cursorPos -= 1
        elif evt.key == K_RIGHT:
            if self.cursorPos < len(self.text): self.cursorPos += 1
        elif evt.key == K_TAB:
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
        return Widget.processKeyDown(self, NoEvent)

    def onFocusGained(self):
        Widget.onFocusGained(self)
        self.cursorPos = len(self.text)

    def onFocusLost(self):
        Widget.onFocusLost(self)
        self.processAction(self.action)

registerWidget(Entry, 'entry')
