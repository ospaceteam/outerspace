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

import Const
from WordUtils import *
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

    def deleteSelection(self):
        # we have some selection
        if self.selection:
            # one-line selection
            if self.selection.first[0] == self.selection.last[0]:
                # text before selection
                textBefore = self.text[self.selection.last[0]][:self.selection.first[1]]
                # text after selection
                textAfter = self.text[self.selection.last[0]][self.selection.last[1]:]
                # store new text without selection
                self.text[self.selection.last[0]] = u'%s%s' % (textBefore, textAfter)
            else:
                # handle multi-line selection
                # delete end of selection
                self.text[self.selection.last[0]] = self.text[self.selection.last[0]][self.selection.last[1]:]
                # delete fully selected rows
                start = self.selection.first[0]+1
                for row in range(start,self.selection.last[0]):
                    self.text.pop(start)
                # delete selection on first row
                self.text[self.selection.first[0]] = self.text[self.selection.first[0]][:self.selection.first[1]]
                # join the rows that are spanned
                self.text[self.selection.first[0]] = u'%s%s' % (self.text[self.selection.first[0]], self.text[self.selection.first[0]+1])
                del self.text[self.selection.first[0]+1]
            # move cursor to selection begining
            self.cursorColumn = self.selection.first[1]
            self.cursorRow = self.selection.first[0]
            # clear selection
            self.selection.deselect()

    def _processBackspace(self, evt):
        if self.selection:
            self.deleteSelection()
        elif self.cursorColumn > 0:
            self.text[self.cursorRow] = u'%s%s' % (self.text[self.cursorRow][:self.cursorColumn - 1], self.text[self.cursorRow][self.cursorColumn:])
            self.cursorColumn -= 1
        else:
            if self.cursorRow > 0:
                self.cursorColumn = len(self.text[self.cursorRow - 1])
                self.text[self.cursorRow - 1] = u'%s%s' % (self.text[self.cursorRow - 1], self.text[self.cursorRow])
                del self.text[self.cursorRow]
                self.cursorRow -= 1

    def _processDelete(self, evt):
        if self.selection:
            self.deleteSelection()
        elif self.cursorColumn < len(self.text[self.cursorRow]):
            self.text[self.cursorRow] = u'%s%s' % (self.text[self.cursorRow][:self.cursorColumn], self.text[self.cursorRow][self.cursorColumn + 1:])
        elif self.cursorRow < len(self.text) - 1:
            self.text[self.cursorRow] = u'%s%s' % (self.text[self.cursorRow], self.text[self.cursorRow + 1])
            del self.text[self.cursorRow + 1]

    def _processLeft(self, evt):
        if evt.mod & pygame.KMOD_SHIFT:
            self.selection.select(self.cursorRow, self.cursorColumn)
        if evt.mod & pygame.KMOD_CTRL:
            # move one word left
            # take words on line
            words = splitter(self.text[self.cursorRow])
            if len(words) == 0:
                #move to previous line
                if self.cursorRow > 0:
                    self.cursorRow -= 1
                    words2 = splitter(self.text[self.cursorRow])
                    if len(words2) > 0:
                        #move cursor to begining of last word
                        self.cursorColumn = words2[-1][1]
                    else:
                        #no words on line, so move cursor to the end of line
                        self.cursorColumn = len(self.text[self.cursorRow])
                else:
                    #we are on first line, so move cursor to begining of line
                    self.cursorColumn = 0
            idxs = getIdxFromColumn(words, self.cursorColumn)
            if idxs != (-1, -1):
                if idxs[0] == -1:
                    #cursor is before first word, jump to beginig of last word on previous line
                    if self.cursorRow > 0:
                        self.cursorRow -= 1
                        words2 = splitter(self.text[self.cursorRow])
                        if len(words2) > 0:
                            #move cursor to begining of last word
                            self.cursorColumn = words2[-1][1]
                        else:
                            #no words on line, so move cursor to the end of line
                            self.cursorColumn = len(self.text[self.cursorRow])
                    else:
                        #we are on first line, so move cursor to begining of line
                        self.cursorColumn = 0
                elif idxs[0] == idxs[1]:
                    #we are inside word, so move cursor to begining of word
                    self.cursorColumn = words[idxs[0]][1]
                elif idxs[1] == -1:
                    #cursor is after last word, we must jump to begining of last word
                    self.cursorColumn = words[idxs[0]][1]
                else:
                    #cursor is between words, we must jump to begining of left word
                    self.cursorColumn = words[idxs[0]][1]
        elif self.cursorColumn > 0: self.cursorColumn -= 1
        elif self.cursorRow > 0:
            self.cursorRow -= 1
            self.cursorColumn = len(self.text[self.cursorRow])
        if evt.mod & pygame.KMOD_SHIFT:
            self.selection.select(self.cursorRow, self.cursorColumn)
        else:
            self.selection.deselect()

    def _processRight(self, evt):
        if evt.mod & pygame.KMOD_CTRL:
            # move one word right
            # take words on line
            words = splitter(self.text[self.cursorRow])
            if len(words) == 0:
                #move to next line
                if self.cursorRow < len(self.text) - 1:
                    self.cursorRow += 1
                    words2 = splitter(self.text[self.cursorRow])
                    if len(words2) > 0:
                        self.cursorColumn = words2[0][1]
                    else:
                        #on next line are only separators (or is empty), so move to column 0
                        self.cursorColumn = 0
                else:
                    #we are on last line, so move cursor to end of line
                    self.cursorColumn = len(self.text[self.cursorRow])
            idxs = getIdxFromColumn(words, self.cursorColumn)
            if idxs != (-1, -1):
                if idxs[0] == idxs[1] or self.cursorColumn == words[idxs[1]][1]:
                    #cursor is inside of word or is on begining of word, so move on begining of next word
                    if idxs[1] + 1 < len(words):
                        #there is next word on line
                        self.cursorColumn = words[idxs[1] + 1][1]
                    else:
                        #we must jump to begining first word on next line
                        if self.cursorRow < len(self.text) - 1:
                            self.cursorRow += 1
                            words2 = splitter(self.text[self.cursorRow])
                            if len(words2) > 0:
                                self.cursorColumn = words2[0][1]
                            else:
                                #on next line are only separators (or is empty), so move to column 0
                                self.cursorColumn = 0
                        else:
                            #we are on last line, so move cursor to end of line
                            self.cursorColumn = len(self.text[self.cursorRow])
                elif idxs[0] == -1:
                    #cursor is before first word, jump to beginig of fist word
                    self.cursorColumn = words[idxs[1]][1]
                elif idxs[1] == -1:
                    #cursor is after last word, we must jump to begining first word on next line
                    if self.cursorRow < len(self.text) - 1:
                        self.cursorRow += 1
                        words2 = splitter(self.text[self.cursorRow])
                        if len(words2) > 0:
                            self.cursorColumn = words2[0][1]
                        else:
                            #on next line are only separators (or is empty), so move to column 0
                            self.cursorColumn = 0
                    else:
                        #we are on last line, so move cursor to end of line
                        self.cursorColumn = len(self.text[self.cursorRow])
                else:
                    #cursor is between words
                    self.cursorColumn = words[idxs[1]][1]
        elif self.cursorColumn < len(self.text[self.cursorRow]): self.cursorColumn += 1
        elif self.cursorRow < len(self.text):
            # move to the next row
            if self.cursorRow < len(self.text) - 1:
                self.cursorRow += 1
                self.cursorColumn = 0
        if evt.mod & pygame.KMOD_SHIFT:
            self.selection.select(self.cursorRow,self.cursorColumn)
        else:
            self.selection.deselect()

    def _processUp(self, evt):
        if self.cursorRow > 0:
            self.cursorRow -= 1
            self.cursorColumn = min(self.cursorColumn, len(self.text[self.cursorRow]))

        if self.cursorRow - self.offsetRow < 0:
            self.vertScrollbar.onButton1(self, "", "")

        if evt.mod & pygame.KMOD_SHIFT:
            self.selection.select(self.cursorRow,self.cursorColumn)
        else:
            self.selection.deselect()

    def _processDown(self, evt):
        if self.cursorRow < len(self.text) - 1:
            self.cursorRow += 1
            self.cursorColumn = min(self.cursorColumn, len(self.text[self.cursorRow]))

        if self.cursorRow - self.offsetRow >= self.theme.getTextDrawLines(self):
            self.vertScrollbar.onButton2(self, "", "")

        if evt.mod & pygame.KMOD_SHIFT:
            self.selection.select(self.cursorRow,self.cursorColumn)
        else:
            self.selection.deselect()

    def _processHome(self, evt):
        self.cursorColumn = 0
        if evt.mod & pygame.KMOD_SHIFT:
            self.selection.select(self.cursorRow, self.cursorColumn)
        else:
            self.selection.deselect()

    def _processEnd(self, evt):
        self.cursorColumn = len(self.text[self.cursorRow])
        if evt.mod & pygame.KMOD_SHIFT:
            self.selection.select(self.cursorRow, self.cursorColumn)
        else:
            self.selection.deselect()

    def _processReturn(self, evt):
        text1 = self.text[self.cursorRow][self.cursorColumn:]
        text2 = self.text[self.cursorRow][:self.cursorColumn]
        self.text[self.cursorRow] = text1
        self.text.insert(self.cursorRow, text2)
        self.cursorRow += 1
        self.cursorColumn = 0

    def _processUnicode(self, evt):
        char = evt.unicode
        self.text[self.cursorRow] = u'%s%c%s' % (
            self.text[self.cursorRow][:self.cursorColumn], char, self.text[self.cursorRow][self.cursorColumn:]
        )
        self.cursorColumn += 1

    def _processNumKeyboard(self, evt):
        self.text[self.cursorRow] = u'%s%c%s' % (
            self.text[self.cursorRow][:self.cursorColumn], MAPPING[evt.key], self.text[self.cursorRow][self.cursorColumn:]
        )
        self.cursorColumn += 1

    def wrapDeleteSelection(self, func, evt, deleteOnly=False):
        if self.selection:
            self.deleteSelection()
            if deleteOnly: return
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



