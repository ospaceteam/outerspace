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

import unittest
import Const
from WordUtils import splitter
from Widget import Widget, registerWidget
import pygame.key

# keys mapping
MAPPING = {
    pygame.K_KP0: '0', pygame.K_KP1: '1', pygame.K_KP2: '2', pygame.K_KP3: '3', pygame.K_KP4: '4',
    pygame.K_KP5: '5', pygame.K_KP6: '6', pygame.K_KP7: '7', pygame.K_KP8: '8', pygame.K_KP9: '9',
}


class Selection(object):
    """ Object to hold and pre-process information about selected area of the text.
    """
    def __init__(self):
        self._start = None
        self._end = None

    @property
    def first(self):
        """ Returns coordinates of the beginning of the selection """
        return min(self._start, self._end)

    @property
    def last(self):
        """ Returns coordinates of the ending of the selection """
        return max(self._start, self._end)

    def select(self, row, column):
        if self._start is None:
            self._start = (row, column)
        self._end = (row, column)

    def deselect(self):
        self._start = self._end = None

    def __nonzero__(self):
        return self._start is not None and self._end is not None


class Text(Widget):
    """Text edit widget."""

    def __init__(self, parent, **kwargs):
        Widget.__init__(self, parent)
        # data
        self.__dict__['text'] = [""]
        self.__dict__['offsetRow'] = 0
        self.__dict__['cursorRow'] = 0
        self.__dict__['cursorColumn'] = 0
        self.__dict__['action'] = None
        self.__dict__['editable'] = 1
        self.__dict__['vertScrollbar'] = None
        self.__dict__['selection'] = Selection()
        # flags
        self.processKWArguments(kwargs)
        parent.registerWidget(self)

    def draw(self, surface):
        self.theme.drawText(surface, self)
        return self.rect

    def attachVScrollbar(self, scrollbar):
        self.vertScrollbar = scrollbar
        scrollbar.subscribeAction("*", self)
        scrollbar.action = "onScroll"
        scrollbar.slider.min = 0
        scrollbar.slider.max = len(self.text) + 100
        scrollbar.slider.position = self.offsetRow
        scrollbar.slider.shown = 1

    def onScroll(self, widget, action, data):
        self.offsetRow = self.vertScrollbar.slider.position

    def onCursorChanged(self):
        # force redraw
        self.cursorColumn += 1
        self.cursorColumn -= 1
        # super
        Widget.onCursorChanged(self)

    def _deleteSelection(self):
        assert self.selection

        # one-line selection
        if self.selection.first[0] == self.selection.last[0]:
            textBefore = self.text[self.selection.last[0]][:self.selection.first[1]]
            textAfter = self.text[self.selection.last[0]][self.selection.last[1]:]
            self.text[self.selection.last[0]] = textBefore + textAfter
        else:
            # handle multi-line selection
            # delete end of selection
            self.text[self.selection.last[0]] = self.text[self.selection.last[0]][self.selection.last[1]:]
            # delete fully selected rows
            del self.text[self.selection.first[0] + 1:self.selection.last[0]]
            # delete selection on first row
            self.text[self.selection.first[0]] = self.text[self.selection.first[0]][:self.selection.first[1]]
            # join the rows that are spanned
            self.text[self.selection.first[0]] = self.text[self.selection.first[0]] + self.text[self.selection.first[0] + 1]
            del self.text[self.selection.first[0] + 1]
        # move cursor to selection begining
        self.cursorColumn = self.selection.first[1]
        self.cursorRow = self.selection.first[0]
        # clear selection
        self.selection.deselect()

    def _processBackspace(self, evt):
        if self.selection:
            self._deleteSelection()
        elif self.cursorColumn > 0:
            self.text[self.cursorRow] = self.text[self.cursorRow][:self.cursorColumn - 1] + self.text[self.cursorRow][self.cursorColumn:]
            self.cursorColumn -= 1
        elif self.cursorRow > 0:
            self.cursorColumn = len(self.text[self.cursorRow - 1])
            self.text[self.cursorRow - 1] = self.text[self.cursorRow - 1] + self.text[self.cursorRow]
            del self.text[self.cursorRow]
            self.cursorRow -= 1

    def _processDelete(self, evt):
        if self.selection:
            self._deleteSelection()
        elif self.cursorColumn < len(self.text[self.cursorRow]):
            self.text[self.cursorRow] = self.text[self.cursorRow][:self.cursorColumn] + self.text[self.cursorRow][self.cursorColumn + 1:]
        elif self.cursorRow < len(self.text) - 1:
            self.text[self.cursorRow] = self.text[self.cursorRow] + self.text[self.cursorRow + 1]
            del self.text[self.cursorRow + 1]

    def _processLeft(self, evt):
        if evt.mod & pygame.KMOD_CTRL:
            # move one word left
            # take words on line
            words = splitter(self.text[self.cursorRow][:self.cursorColumn])
            if len(words) == 0:
                if self.cursorRow == 0:
                    # we are on first line, so move cursor to begining of line
                    self.cursorColumn = 0
                else:
                    # move to previous line and try again
                    self.cursorRow -= 1
                    self.cursorColumn = len(self.text[self.cursorRow])
                    self._processLeft(evt)
                return
            # we must jump to begining of last word
            self.cursorColumn = words[-1][1]
        elif self.cursorColumn > 0:
            self.cursorColumn -= 1
        elif self.cursorRow > 0:
            self.cursorRow -= 1
            self.cursorColumn = len(self.text[self.cursorRow])

    def _processRight(self, evt):
        if evt.mod & pygame.KMOD_CTRL:
            # move one word right
            # take words on line
            words = splitter(self.text[self.cursorRow][self.cursorColumn:])
            if len(words) == 0:
                if self.cursorRow == len(self.text) - 1:
                    # we are on last line, so move cursor to end of line
                    self.cursorColumn = len(self.text[self.cursorRow])
                else:
                    self.cursorRow += 1
                    self.cursorColumn = 0
                    self._processRight(evt)
                return
            # we jump to the end of the first word
            self.cursorColumn += words[0][2]
        elif self.cursorColumn < len(self.text[self.cursorRow]):
            self.cursorColumn += 1
        elif self.cursorRow < len(self.text):
            # move to the next row
            if self.cursorRow < len(self.text) - 1:
                self.cursorRow += 1
                self.cursorColumn = 0

    def _processUp(self, evt):
        if self.cursorRow > 0:
            self.cursorRow -= 1
            self.cursorColumn = min(self.cursorColumn, len(self.text[self.cursorRow]))
        else:
            self.cursorColumn = 0

        if self.vertScrollbar and self.cursorRow - self.offsetRow < 0:
            self.vertScrollbar.onButton1(self, "", "")

    def _processDown(self, evt):
        if self.cursorRow < len(self.text) - 1:
            self.cursorRow += 1
            self.cursorColumn = min(self.cursorColumn, len(self.text[self.cursorRow]))
        else:
            self.cursorColumn = len(self.text[self.cursorRow])

        if self.vertScrollbar and self.cursorRow - self.offsetRow >= self.theme.getTextDrawLines(self):
            self.vertScrollbar.onButton2(self, "", "")

    def _processHome(self, evt):
        self.cursorColumn = 0

    def _processEnd(self, evt):
        self.cursorColumn = len(self.text[self.cursorRow])

    def _processReturn(self, evt):
        text1 = self.text[self.cursorRow][self.cursorColumn:]
        text2 = self.text[self.cursorRow][:self.cursorColumn]
        self.text[self.cursorRow] = text1
        self.text.insert(self.cursorRow, text2)
        self.cursorRow += 1
        self.cursorColumn = 0

    def _processUnicode(self, evt):
        char = evt.unicode
        self.text[self.cursorRow] = self.text[self.cursorRow][:self.cursorColumn] + char + self.text[self.cursorRow][self.cursorColumn:]
        self.cursorColumn += 1

    def _processNumKeyboard(self, evt):
        self.text[self.cursorRow] = self.text[self.cursorRow][:self.cursorColumn] + MAPPING[evt.key] + self.text[self.cursorRow][self.cursorColumn:]
        self.cursorColumn += 1

    def wrapDeleteSelection(self, func, evt, deleteOnly=False):
        if self.selection:
            self._deleteSelection()
            if deleteOnly:
                return
        func(evt)

    def wrapSelect(self, func, evt):
        if evt.mod & pygame.KMOD_SHIFT:
            self.selection.select(self.cursorRow, self.cursorColumn)
            func(evt)
            self.selection.select(self.cursorRow, self.cursorColumn)
        else:
            func(evt)

    def processKeyUp(self, evt):
        # consume pygame.K_RETURN (acceptButton on Window will not work)
        # can be choosable on construction?
        if evt.key == pygame.K_RETURN:
            return Const.NoEvent
        else:
            return Widget.processKeyUp(self, evt)

    def processKeyDown(self, evt):
        if not self.editable:
            return Widget.processKeyDown(self, evt)

        # process keys
        if evt.key == pygame.K_BACKSPACE:
            self.wrapDeleteSelection(self._processBackspace, evt, deleteOnly=True)

        elif evt.key == pygame.K_DELETE:
            self.wrapDeleteSelection(self._processDelete, evt, deleteOnly=True)

        elif evt.key == pygame.K_ESCAPE:
            self.app.setFocus(None)

        elif evt.key == pygame.K_LEFT:
            self.wrapSelect(self._processLeft, evt)

        elif evt.key == pygame.K_RIGHT:
            self.wrapSelect(self._processRight, evt)

        elif evt.key == pygame.K_UP:
            self.wrapSelect(self._processUp, evt)

        elif evt.key == pygame.K_DOWN:
            self.wrapSelect(self._processDown, evt)

        elif evt.key == pygame.K_TAB:
            pass

        elif evt.key == pygame.K_HOME:
            self.wrapSelect(self._processHome, evt)

        elif evt.key == pygame.K_END:
            self.wrapSelect(self._processEnd, evt)

        elif evt.key == pygame.K_RETURN:
            self.wrapDeleteSelection(self._processReturn, evt)

        elif hasattr(evt, 'unicode') and evt.unicode:
            self.wrapDeleteSelection(self._processUnicode, evt)

        elif evt.key in MAPPING:
            self.wrapDeleteSelection(self._processNumKeyboard, evt)

        return Widget.processKeyDown(self, Const.NoEvent)

    def onFocusGained(self):
        Widget.onFocusGained(self)
        self.cursorRow = len(self.text) - 1
        self.cursorColumn = len(self.text[self.cursorRow])

    def onFocusLost(self):
        Widget.onFocusLost(self)
        self.processAction(self.action)

    # redirect mouse wheel events to the scollbar
    def processMWUp(self, evt):
        if self.vertScrollbar:
            return self.vertScrollbar.processMWUp(evt)

    def processMWDown(self, evt):
        if self.vertScrollbar:
            return self.vertScrollbar.processMWDown(evt)


registerWidget(Text, 'text')


class TextTestCase(unittest.TestCase):
    def setUp(self):
        class Evt:
            def __init__(self, key, letter="", mod=0):
                self.key = key
                self.unicode = unicode(letter)
                self.mod = mod

        class App:
            def __init__(self):
                self.theme = "Test"

        class Parent:
            def __init__(self):
                self.app = App()

            def getApp(self):
                return self.app

            def redraw(self, *args, **kwargs):
                return

            def registerWidget(self, *args, **kwargs):
                return

        self.parent = Parent()
        self.txt = Text(self.parent)
        self.txt.text = ["Zero line", "One line", "Two line", "", "", "Five line"]
        self.txt.offsetRow = 0
        self.txt.cursorRow = 0
        self.txt.cursorColumn = 0
        self.txt.action = None
        self.txt.editable = 1
        self.txt.vertScrollbar = None
        self.txt.selection = Selection()
        self.Evt = Evt

    def tearDown(self):
        pass

    def test_dummy(self):
        self.txt.cursorColumn = 3
        self.txt.cursorRow = 2
        self.assertEqual(self.txt.text, ["Zero line", "One line", "Two line", "", "", "Five line"])
        self.assertEqual(self.txt.cursorColumn, 3)
        self.assertEqual(self.txt.cursorRow, 2)

    def test_input(self):
        self.txt.cursorColumn = 3
        self.txt.cursorRow = 2
        for letter in " quite expanded":
            Text.processKeyDown(self.txt, self.Evt(None, letter=letter))
        self.assertEqual(self.txt.text, ["Zero line", "One line", "Two quite expanded line", "", "", "Five line"])
        self.assertEqual(self.txt.cursorColumn, 18)

    def test_numpad_input(self):
        self.txt.cursorColumn = 3
        self.txt.cursorRow = 2
        for key in [pygame.K_KP0, pygame.K_KP4, pygame.K_KP4, pygame.K_KP8]:
            Text.processKeyDown(self.txt, self.Evt(key))
        self.assertEqual(self.txt.text, ["Zero line", "One line", "Two0448 line", "", "", "Five line"])
        self.assertEqual(self.txt.cursorColumn, 7)

    def test_backspace(self):
        evt = self.Evt(pygame.K_BACKSPACE)
        self.txt.cursorColumn = 3
        self.txt.cursorRow = 2
        for x in range(4):
            Text.processKeyDown(self.txt, evt)
        self.assertEqual(self.txt.text, ["Zero line", "One line line", "", "", "Five line"])
        self.assertEqual(self.txt.cursorColumn, 8)
        self.assertEqual(self.txt.cursorRow, 1)
        # first character
        self.txt.cursorColumn = 0
        self.txt.cursorRow = 0
        Text.processKeyDown(self.txt, evt)
        self.assertEqual(self.txt.text, ["Zero line", "One line line", "", "", "Five line"])
        self.assertEqual(self.txt.cursorColumn, 0)
        self.assertEqual(self.txt.cursorRow, 0)

    def test_delete(self):
        evt = self.Evt(pygame.K_DELETE)
        self.txt.cursorColumn = 3
        self.txt.cursorRow = 2
        for x in range(6):
            Text.processKeyDown(self.txt, evt)
        self.assertEqual(self.txt.text, ["Zero line", "One line", "Two", "", "Five line"])
        self.assertEqual(self.txt.cursorColumn, 3)
        self.assertEqual(self.txt.cursorRow, 2)
        for x in range(3):
            Text.processKeyDown(self.txt, evt)
        self.assertEqual(self.txt.text, ["Zero line", "One line", "Twoive line"])
        self.assertEqual(self.txt.cursorColumn, 3)
        self.assertEqual(self.txt.cursorRow, 2)
        # last character
        self.txt.cursorColumn = 11
        Text.processKeyDown(self.txt, evt)
        self.assertEqual(self.txt.text, ["Zero line", "One line", "Twoive line"])
        self.assertEqual(self.txt.cursorColumn, 11)
        self.assertEqual(self.txt.cursorRow, 2)

    def test_return(self):
        evt = self.Evt(pygame.K_RETURN)
        self.txt.cursorColumn = 3
        self.txt.cursorRow = 2
        Text.processKeyDown(self.txt, evt)
        self.assertEqual(self.txt.text, ["Zero line", "One line", "Two", " line", "", "", "Five line"])
        self.assertEqual(self.txt.cursorColumn, 0)
        self.assertEqual(self.txt.cursorRow, 3)
        Text.processKeyDown(self.txt, evt)
        self.assertEqual(self.txt.text, ["Zero line", "One line", "Two", "", " line", "", "", "Five line"])
        self.assertEqual(self.txt.cursorColumn, 0)
        self.assertEqual(self.txt.cursorRow, 4)

    def test_up(self):
        evt = self.Evt(pygame.K_UP)
        self.txt.cursorColumn = 3
        self.txt.cursorRow = 5
        for x in range(3):
            Text.processKeyDown(self.txt, evt)
        self.assertEqual(self.txt.cursorColumn, 0)
        self.assertEqual(self.txt.cursorRow, 2)
        self.txt.cursorColumn = 3
        Text.processKeyDown(self.txt, evt)
        self.assertEqual(self.txt.cursorColumn, 3)

    def test_down(self):
        evt = self.Evt(pygame.K_DOWN)
        self.txt.cursorColumn = 3
        self.txt.cursorRow = 1
        Text.processKeyDown(self.txt, evt)
        self.assertEqual(self.txt.cursorColumn, 3)
        for x in range(3):
            Text.processKeyDown(self.txt, evt)
        self.assertEqual(self.txt.cursorColumn, 0)
        self.assertEqual(self.txt.cursorRow, 5)

    def test_left(self):
        evt = self.Evt(pygame.K_LEFT)
        self.txt.cursorColumn = 3
        self.txt.cursorRow = 2
        Text.processKeyDown(self.txt, evt)
        self.assertEqual(self.txt.cursorColumn, 2)
        for x in range(12):
            Text.processKeyDown(self.txt, evt)
        self.assertEqual(self.txt.cursorColumn, 9)
        self.assertEqual(self.txt.cursorRow, 0)

    def test_right(self):
        evt = self.Evt(pygame.K_RIGHT)
        self.txt.cursorColumn = 3
        self.txt.cursorRow = 2
        Text.processKeyDown(self.txt, evt)
        self.assertEqual(self.txt.cursorColumn, 4)
        for x in range(12):
            Text.processKeyDown(self.txt, evt)
        self.assertEqual(self.txt.cursorColumn, 5)
        self.assertEqual(self.txt.cursorRow, 5)

    def test_selection_movement(self):
        evt = self.Evt(pygame.K_RIGHT, mod=pygame.KMOD_RSHIFT)
        self.txt.cursorColumn = 3
        self.txt.cursorRow = 2
        for x in range(10):
            Text.processKeyDown(self.txt, evt)
        self.assertEqual(self.txt.text, ["Zero line", "One line", "Two line", "", "", "Five line"])
        self.assertEqual(self.txt.selection.first, (2, 3))
        self.assertEqual(self.txt.selection.last, (5, 2))

        evt = self.Evt(pygame.K_LEFT, mod=pygame.KMOD_LSHIFT)
        for x in range(3):
            Text.processKeyDown(self.txt, evt)
        self.assertEqual(self.txt.selection.first, (2, 3))
        self.assertEqual(self.txt.selection.last, (4, 0))

        evt = self.Evt(pygame.K_UP, mod=pygame.KMOD_LSHIFT)
        for x in range(3):
            Text.processKeyDown(self.txt, evt)
        self.assertEqual(self.txt.selection.first, (1, 0))
        self.assertEqual(self.txt.selection.last, (2, 3))

    def test_selection_delete(self):
        evt = self.Evt(pygame.K_DOWN, mod=pygame.KMOD_LSHIFT)
        self.txt.cursorColumn = 3
        self.txt.cursorRow = 0
        Text.processKeyDown(self.txt, evt)
        Text.processKeyDown(self.txt, self.Evt(pygame.K_DELETE))
        self.assertEqual(self.txt.text, ["Zer line", "Two line", "", "", "Five line"])
        self.assertIs(self.txt.selection.first, None)
        self.assertIs(self.txt.selection.last, None)

        evt = self.Evt(pygame.K_RIGHT, mod=pygame.KMOD_LSHIFT)
        for x in range(3):
            Text.processKeyDown(self.txt, evt)
        Text.processKeyDown(self.txt, self.Evt(pygame.K_DELETE))
        self.assertEqual(self.txt.text, ["Zerne", "Two line", "", "", "Five line"])

        evt = self.Evt(pygame.K_DOWN, mod=pygame.KMOD_LSHIFT)
        for x in range(4):
            Text.processKeyDown(self.txt, evt)
        Text.processKeyDown(self.txt, self.Evt(pygame.K_DELETE))
        self.assertEqual(self.txt.text, ["ZerFive line"])

    def test_selection_backspace(self):
        evt = self.Evt(pygame.K_DOWN, mod=pygame.KMOD_LSHIFT)
        self.txt.cursorColumn = 3
        self.txt.cursorRow = 0
        Text.processKeyDown(self.txt, evt)
        Text.processKeyDown(self.txt, self.Evt(pygame.K_BACKSPACE))
        self.assertEqual(self.txt.text, ["Zer line", "Two line", "", "", "Five line"])
        self.assertIs(self.txt.selection.first, None)
        self.assertIs(self.txt.selection.last, None)

    def test_selection_return(self):
        evt = self.Evt(pygame.K_DOWN, mod=pygame.KMOD_LSHIFT)
        self.txt.cursorColumn = 3
        self.txt.cursorRow = 0
        Text.processKeyDown(self.txt, evt)
        Text.processKeyDown(self.txt, self.Evt(pygame.K_RETURN))
        self.assertEqual(self.txt.text, ["Zer", " line", "Two line", "", "", "Five line"])
        self.assertIs(self.txt.selection.first, None)
        self.assertIs(self.txt.selection.last, None)

    def test_move_word_left(self):
        evt = self.Evt(pygame.K_LEFT, mod=pygame.KMOD_LCTRL)
        self.txt.cursorColumn = 3
        self.txt.cursorRow = 5
        for x in range(2):
            Text.processKeyDown(self.txt, evt)
        self.assertEqual(self.txt.text, ["Zero line", "One line", "Two line", "", "", "Five line"])
        self.assertEqual(self.txt.cursorColumn, 4)
        self.assertEqual(self.txt.cursorRow, 2)
        Text.processKeyDown(self.txt, evt)
        self.assertEqual(self.txt.cursorColumn, 0)
        self.assertEqual(self.txt.cursorRow, 2)

    def test_move_word_right(self):
        evt = self.Evt(pygame.K_RIGHT, mod=pygame.KMOD_RCTRL)
        self.txt.cursorColumn = 1
        self.txt.cursorRow = 0
        Text.processKeyDown(self.txt, evt)
        self.assertEqual(self.txt.text, ["Zero line", "One line", "Two line", "", "", "Five line"])
        self.assertEqual(self.txt.cursorColumn, 4)
        self.assertEqual(self.txt.cursorRow, 0)
        for x in range(4):
            Text.processKeyDown(self.txt, evt)
        self.assertEqual(self.txt.cursorColumn, 3)
        self.assertEqual(self.txt.cursorRow, 2)
        for x in range(2):
            Text.processKeyDown(self.txt, evt)
        self.assertEqual(self.txt.cursorColumn, 4)
        self.assertEqual(self.txt.cursorRow, 5)
