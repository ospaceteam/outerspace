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

import re
import types

import pygame

import Const
from Widget import registerWidget
from MetaWidget import MetaWidget
from Scrollbar import Scrollbar
from Entry import Entry
from Button import Button

class Listbox(MetaWidget):

    def __init__(self, parent, **kwargs):
        MetaWidget.__init__(self, parent)
        # data
        self.__dict__["items"] = []
        self.__dict__["labels"] = []
        self.__dict__["action"] = None
        self.__dict__["rmbAction"] = None
        self.__dict__["hoverAction"] = None
        self.__dict__["multiselection"] = 0
        self.__dict__["selection"] = []
        self.__dict__["highlight"] = None
        self.__dict__["columns"] = [('Item', 'text', 0, Const.ALIGN_W)]
        self.__dict__["columnLabels"] = 0
        self.__dict__["scrollBar"] = 1
        self.__dict__["sortedBy"] = (None, 1)
        self.__dict__["sortable"] = 1
        self.__dict__["_labels"] = []
        self.__dict__["_buttons"] = []
        self.__dict__["_entries"] = []
        # flags
        self.processKWArguments(kwargs)
        parent.registerWidget(self)

        # create widgets
        self.bar = Scrollbar(self, action = 'onScroll')
        self.bar.subscribeAction('*', self)
        if not self.scrollBar:
            self.bar.visible = 0

        # precreate some objects
        # guess number of rows (TODO Enable it)
        # rows = self.layout[3] - 1
        rows = 0
        for item in self.columns:
            label = Button(self, action = 'onSortByColumn')
            label.subscribeAction('*', self)
            self._buttons.append(label)
            for i in xrange(0, rows):
                label = Button(self, action = 'onItemSelect', rmbAction = "onRmbItemSelect", hoverAction = "onItemHighlight", style = "listitem", toggle = 1)
                label.subscribeAction('*', self)
                self._labels.append(label)

    def layoutWidgets(self):
        gx, gy = self.theme.getGridParams()
        r = self.rect
        self.bar.rect = pygame.Rect(r.width - gx, 0, gx, r.height)

        self.labels = []
        rows = r.height / gy
        startRow = 0
        bIndex = 0
        lIndex = 0
        eIndex = 0
        if self.columnLabels:
            rowLabels = []
            y = 0
            x = 0
            remains = (r.width - gx) / gx
            for title, name, width, flags in self.columns:
                if len(self._buttons) <= bIndex:
                    label = Button(self, action = 'onSortByColumn')
                    label.subscribeAction('*', self)
                    self._buttons.append(label)
                label = self._buttons[bIndex]
                bIndex += 1
                label.set(text = title, align = flags & Const.ALIGN_MASK,
                    data = name, visible = 1)
                if width == 0 or width > remains: width = remains
                label.rect = pygame.Rect(x, y, width * gx, gy)
                x += width * gx
                remains -= width
            startRow = 1
        for row in xrange(startRow, rows):
            rowLabels = []
            y = row * gy
            x = 0
            remains = (r.width - gx) / gx
            for title, name, width, flags in self.columns:
                if flags & Const.F_EDITABLE:
                    if len(self._entries) <= eIndex:
                        label = Entry(self, align = Const.ALIGN_E, action = 'onNewValue')
                        label.subscribeAction('*', self)
                        self._entries.append(label)
                    label = self._entries[eIndex]
                    eIndex += 1
                    label._listboxColumn = name
                    label.visible = 1
                    label.redraw()
                else:
                    if len(self._labels) <= lIndex:
                        label = Button(self, action = 'onItemSelect', rmbAction = "onRmbItemSelect", hoverAction = "onItemHighlight", style = "listitem", toggle = 1)
                        label.subscribeAction('*', self)
                        self._labels.append(label)
                    label = self._labels[lIndex]
                    lIndex += 1
                    label.set(align = flags & Const.ALIGN_MASK, visible = 1)
                    label.redraw()
                if width == 0 or width > remains: width = remains
                label.rect = pygame.Rect(x, y, width * gx, gy)
                x += width * gx
                remains -= width
                rowLabels.append(label)
            self.labels.append(rowLabels)
        while lIndex < len(self._labels):
            self._labels[lIndex].visible = 0
            lIndex += 1
        while bIndex < len(self._buttons):
            self._buttons[bIndex].visible = 0
            bIndex += 1
        while eIndex < len(self._entries):
            self._entries[eIndex].visible = 0
            eIndex += 1

        self.bar.slider.position = 0
        self.bar.slider.min = 0
        if self.columnLabels:
            self.bar.slider.shown = rows - 1
        else:
            self.bar.slider.shown = rows

        self.itemsChanged()

    def onScroll(self, widget, action, data):
        self.itemsChanged()

    def selectItem(self, item):
        if item:
            if self.multiselection:
                if item in self.selection:
                    item.selected = 0
                    self.selection.remove(item)
                    if item.index != None:
                        self._setListIndex(item.index, item)
                else:
                    item.selected = 1
                    self.selection.append(item)
                    if item.index != None:
                        self._setListIndex(item.index, item)
            else:
                if self.selection:
                    for tmp in self.selection:
                        tmp.selected = 0
                        if tmp.index != None:
                            self._setListIndex(tmp.index, tmp)
                item.selected = 1
                if item.index != None:
                    self._setListIndex(item.index, item)
                self.selection = [item]
            return 1
        return 0

    def highlightItem(self, item, highlighted):
        if item is not None:
            self.highlight = item
            self.highlight.highlighted = highlighted
            self._setListIndex(item.index, item)
            return 1
        else:
            self.highlight = None
            return 0

    def onItemSelect(self, widget, action, data):
        if self.selectItem(widget.data):
            self.processAction(self.action, widget.data)

    def onRmbItemSelect(self, widget, action, data):
        if self.selectItem(widget.data):
            self.processAction(self.rmbAction, widget.data)

    def onItemHighlight(self, widget, action, data):
        if self.highlightItem(widget.data, data):
            self.processAction(self.hoverAction, widget.data if data else None)

    def onNewValue(self, widget, action, data):
        value = widget.text
        t = type(getattr(widget.data, widget._listboxColumn))
        try:
            if t == types.IntType: value = int(value)
            elif t == types.FloatType: value = float(value)
            elif t == types.StringType: value = str(value)
            elif t == types.UnicodeType: pass
            elif t == types.LongType: value = long(value)
            else:
                self._setListIndex(widget.data.index, widget.data)
                return
        except ValueError:
            self._setListIndex(widget.data.index, widget.data)
            return
        setattr(widget.data, widget._listboxColumn, value)

    def setSort(self, column):
        if not self.sortable:
            return

        if self.sortedBy[0] == column:
            self.sortedBy = (self.sortedBy[0], not self.sortedBy[1])
        else:
            self.sortedBy = (column, 1)

        self.itemsChanged()

    def onSortByColumn(self, widget, action, data):
        self.setSort(widget.data)

    def _setListIndex(self, rowIndex, item):
        if rowIndex < len(self.labels):
            if item.selected and item not in self.selection:
                self.selection.append(item)
            if not item.selected and item in self.selection:
                self.selection.remove(item)
            columnIndex = 0
            for title, name, width, flags in self.columns:
                label = self.labels[rowIndex][columnIndex]
                label.text = item.getAsString(name)
                label.tooltip = item.tooltip
                label.tooltipTitle = item.tooltipTitle
                label.statustip = item.statustip
                label.font = item.font
                label.foreground = item.foreground
                label.enabled = 1
                if name == 'text':
                    label.icons = item.icons
                label.data = item
                label.pressed = item.selected
                label.highlighted = item.highlighted
                columnIndex += 1

    def _naturalSort(self, items, attr, reverse):
        """ Code inspired by https://blog.codinghorror.com/sorting-for-humans-natural-sort-order/
        Converts strings to lists of strings and numbers, always in STR, NUM, STR, NUM order (first STR
        might be empty).
        """

        convert = lambda text: int(text) if text.isdigit() else text.lower()
        alphaNum = lambda key: [ convert(c) for c in re.split('([0-9]+)', unicode(key)) ]
        keyF = lambda a: alphaNum(getattr(a, attr))
        items.sort(key=keyF, reverse = reverse)

    def itemsChanged(self):
        if self.items and self.sortable and self.sortedBy[0] != None:
            if hasattr(self.items[0], self.sortedBy[0] + "_raw"):
                sortAttr = self.sortedBy[0] + "_raw"
            else:
                sortAttr = self.sortedBy[0]
            self._naturalSort(self.items, sortAttr, not self.sortedBy[1])

        self.bar.slider.max = max(1, len(self.items))
        index = 0
        pos = int(self.bar.slider.position)
        if pos >= len(self.items) - len(self.labels): pos = max(0, len(self.items) - len(self.labels))
        # clear selection without triggering widget update
        self.__dict__['selection'] = []
        for item in self.items:
            item.index = None
            # reconstruct selection
            if item.selected:
                self.selection.append(item)
        for item in self.items[pos:pos + len(self.labels)]:
            item.index = index
            index2 = 0
            if index < len(self.labels):
                for title, name, width, flags in self.columns:
                    label = self.labels[index][index2]
                    label.text = item.getAsString(name)
                    label.tooltip = item.tooltip
                    label.tooltipTitle = item.tooltipTitle
                    label.statustip = item.statustip
                    label.font = item.font
                    label.enabled = 1
                    label.foreground = item.foreground
                    if name == 'text':
                        label.icons = item.icons
                    label.data = item
                    label.pressed = item.selected
                    index2 += 1
            else:
                break
            index += 1
        while index < len(self.labels):
            index2 = 0
            for title, name, width, flags in self.columns:
                label = self.labels[index][index2]
                label.text = None
                label.icons = None
                label.data = None
                label.tooltip = None
                label.tooltipTitle = None
                label.statustip = None
                label.foreground = None
                label.background = None
                label.enabled = 0
                label.pressed = 0
                index2 += 1
            index += 1

        #self.parent.redraw(self)

    def getSelection(self):
        return self.selection

    def setSelection(self, selection):
        self.selection = selection
        self.itemsChanged()

    def unselectAll(self):
        if self.selection:
            for item in self.selection:
                item.selected = 0
                item.highlighted = 0
                if item.index != None:
                    self._setListIndex(item.index, item)

    def addItem(self, item):
        if item not in self.items:
            self.items.append(item)

    def delItem(self, item):
        self.items.remove(item)
        self.itemsChanged()

    def delItemByIndex(self, index):
        del self.items[index]
        self.itemsChanged()

    def setItems(self, items):
        self.items = items
        self.itemsChanged()

    # redirect mouse wheel events to the scollbar
    def processMWUp(self, evt):
        return self.bar.processMWUp(evt)

    def processMWDown(self, evt):
        return self.bar.processMWDown(evt)

    def drawMetaWidget(self, surface):
        return self.theme.drawListbox(surface, self)

registerWidget(Listbox, 'listbox')
