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
import pygame, pygame.time, pygame.mouse

import SkinableTheme
from Tooltip import Tooltip
import Const

# enable only if you want OpenGL support
#try:
#    from OpenGL.GL import *
#    from OpenGL.GLU import *
#except ImportError:
#    pass

def noop():
    pass

class Application:

    def __init__(self, update = noop, theme = SkinableTheme):
        self.theme = theme
        self.theme.init()
        self.updateFunc = update
        self.showBackground = True
        self.background = None
        self.redrawWidgets = {}
        self.cursorPos = (0, 0)
        self.windowSurfaceFlags = 0
        # status bar widget
        self.statusBar = None
        self.statusBarText = None
        # internal properties
        self.locale = 'en'
        self.windows = []
        self.focusedWindow = None
        self.activeWidget = None
        self.mouseOverWidget = None
        self.mouseOverCount = 0
        self.mouseOverThreshold = 3
        self.mouseLMBDouble = 0
        self.mouseRMBDouble = 0
        self.keyEvt = None
        self.keyCount = 0
        self.tooltip = Tooltip(self)
        self.focusedWidget = None
        self.cursorOn = 0
        self.cursorCount = 0
        self._fullUpdate = False
        # setup timer
        try:
             pygame.time.set_timer(Const.TIMEREVENT, 80)
        except pygame.error:
            pass

    def getApp(self):
        return self

    def _processTimerEvent(self, evt):
        # tooltips
        self.mouseOverCount += 1
        if self.mouseOverCount == self.mouseOverThreshold:
            # show tooltip
            if self.mouseOverWidget:
                self.tooltip.title = self.mouseOverWidget.tooltipTitle
                self.tooltip.text = self.mouseOverWidget.tooltip
                self.tooltip.rect = pygame.Rect(pygame.mouse.get_pos(), (100, 100))
        # cursor
        self.cursorCount += 1
        if self.cursorCount == 5:
            self.cursorOn = not self.cursorOn
            self.cursorCount = 0
            if self.focusedWidget:
                self.focusedWidget.onCursorChanged()
        # keyboard repeat
        if self.keyEvt:
            self.keyCount += 1
            if self.keyCount == 6:
                self.processEvent(self.keyEvt)
                self.keyCount = 4
        return Const.NoEvent

    def _processMouseWheel(self, evt):
        assert evt.button in (4, 5)
        # TODO find window to deliver mouse wheel events to
        if self.focusedWindow:
            if self.focusedWindow.rect.collidepoint(evt.pos):
                if evt.button == 4:
                    return self.focusedWindow.processMWUp(evt)
                else:
                    return self.focusedWindow.processMWDown(evt)
            else:
                return Const.NoEvent
        else:
            return evt

    def _processMouseButtonDown(self, evt):
        # mouse wheel
        if evt.button in (4, 5):
            return self._processMouseWheel(evt)
        # TODO double click
        # check if focused window is top level one
        if self.focusedWindow != self.windows[-1]:
            window = self.focusedWindow
            self.focusWindowAt(evt)
            # consume event, when focus has been changed
            if self.focusedWindow != window:
                return Const.NoEvent
        # left and right mouse button
        if self.focusedWindow:
            if self.focusedWindow.rect.collidepoint(evt.pos):
                if evt.button == 1:
                    return self.focusedWindow.processMB1Down(evt)
                elif evt.button == 3:
                    return self.focusedWindow.processMB3Down(evt)
            elif self.focusedWindow.modal:
                return Const.NoEvent
            elif self.focusedWindow.looseFocusClose:
                self.focusedWindow.hide()
                return self.focusWindowAt(evt)
            else:
                return self.focusWindowAt(evt)
        else:
            return self.focusWindowAt(evt)
        return evt

    def _processMouseButtonUp(self, evt):
        # left and right mouse button
        if self.focusedWindow and self.focusedWindow.rect.collidepoint(evt.pos):
            if evt.button == 1:
                return self.focusedWindow.processMB1Up(evt)
            elif evt.button == 3:
                return self.focusedWindow.processMB3Up(evt)
        return evt

    def _processMouseMotion(self, evt):
        if self.mouseOverCount < self.mouseOverThreshold:
            # just moving across widget does not trigger tooltip
            self.mouseOverCount = 0
        self.cursorPos = evt.pos
        if self.focusedWindow:
            return self.focusedWindow.processMMotion(evt)
        return evt

    def _processKeyDown(self, evt):
        self.keyEvt = evt
        self.keyCount = 0
        if self.focusedWidget:
            evt = self.focusedWidget.processKeyDown(evt)
        if evt != Const.NoEvent and self.focusedWindow:
            evt = self.focusedWindow.processKeyDown(evt)
        return evt

    def _processKeyUp(self, evt):
        self.keyEvt = None
        if self.focusedWidget:
            evt = self.focusedWidget.processKeyUp(evt)
        if evt != Const.NoEvent and self.focusedWindow:
            evt = self.focusedWindow.processKeyUp(evt)
        return evt

    def processEvent(self, evt):
        if evt.type == pygame.VIDEOEXPOSE:
            self.performFullUpdate()
        if not pygame.key.get_focused():
            return Const.NoEvent
        elif evt.type == Const.TIMEREVENT:
            self._processTimerEvent(evt)
        elif evt.type == pygame.MOUSEBUTTONDOWN:
            self._processMouseButtonDown(evt)
        elif evt.type == pygame.MOUSEBUTTONUP:
            self._processMouseButtonUp(evt)
        elif evt.type == pygame.MOUSEMOTION:
            self._processMouseMotion(evt)
        elif evt.type == pygame.KEYDOWN:
            self._processKeyDown(evt)
        elif evt.type == pygame.KEYUP:
            self._processKeyUp(evt)
        else:
            return evt

    def registerWindow(self, window):
        self.windows.append(window)
        self._fullUpdate = True

    def unregisterWindow(self, window):
        if window == self.focusedWindow:
            self.focusedWindow.hide()
        self.windows.remove(window)
        self._fullUpdate = True

    def moveWindowToFront(self, window):
        self.focusWindow(window)
        if window in self.windows:
            self.windows.remove(window)
        self.windows.append(window)
        self.performFullUpdate()

    def focusWindow(self, window):
        if self.focusedWindow:
            self.focusedWindow.focused = 0
        self.focusedWindow = window
        self.setFocus(None)
        if self.focusedWindow:
            self.focusedWindow.focused = 1

    def hideWindow(self, window):
        window.visible = 0
        self.performFullUpdate()
        self._fullUpdate = True
        if self.focusedWindow == window:
            self.focusedWindow.focused = 0
            self.focusedWindow = None
            # also unfocus widget
            self.setFocus(None)
            # find new window to focus
            index = len(self.windows) - 1
            while index >= 0:
                window = self.windows[index]
                if window.visible:
                    window.toFront()
                    return
                index -= 1

    def focusWindowAt(self, evt):
        # find window which has been clicked in
        index = len(self.windows) - 1
        while index >= 0:
            window = self.windows[index]
            if window.visible and window.rect.collidepoint(evt.pos):
                window.toFront()
                return Const.NoEvent
            index -= 1
        return evt

    def setFocus(self, widget):
        if self.focusedWidget != widget:
            if self.focusedWidget:
                self.focusedWidget.onFocusLost()
            self.focusedWidget = widget
            if widget:
                widget.onFocusGained()

    def setMouseOver(self, widget):
        if self.mouseOverWidget != widget:
            if self.mouseOverWidget:
                self.mouseOverWidget.onMouseOut()
                self.tooltip.text = None
                self.tooltip.title = None
                self.performFullUpdate()
            self.mouseOverWidget = widget
            self.mouseOverCount = 0
            if widget:
                widget.onMouseOver()
                self.tooltip.text = None
                self.tooltip.title = None
                self.performFullUpdate()
                widget.parent.setTempStatus(widget.statustip)
                return
            self.setTempStatus(None)

    def setStatus(self, text):
        self.statusBarText = text
        if self.statusBar and self.statusBar.text != text:
            self.statusBar.text = text
            self.redraw(self.statusBar)

    def setTempStatus(self, text):
        if self.statusBar:
            if text:
                self.statusBar.text = text
            else:
                self.statusBar.text = self.statusBarText

    def draw(self, surface):
        """Draw all windows onto supplied surface."""
        if self.showBackground:
            surface.blit(self.background, (0, 0))
        changed = []
        #@print "App Draw"
        for window in self.windows:
            if window.visible:
                if self.showBackground:
                    window._fullUpdate = True
                rect = window.draw(surface)
                #@print " ", window, rect
                if rect: changed.append(rect)
                window.__dict__['_changeReported'] = 0
            else:
                #@print " ", window, "invisible"
                pass
        if self.tooltip.title or self.tooltip.text:
            title, body = self.theme.drawTooltip(surface, self.tooltip)
            changed.append(title)
            changed.append(body)
        self.tooltip.__dict__['_changeReported'] = 0
        self.redrawWidgets = {}
        #@print "CHANGED", changed
        if self._fullUpdate or self.showBackground:
            #@print "FULL UPDATE"
            self._fullUpdate = False
            return [pygame.display.get_surface().get_rect()]
        return changed

    def drawOpenGL(self):
        for window in self.windows:
            if window.visible:
                window.draw(None)
                bitmap = pygame.image.tostring(window.surface, "RGBA", 1)
                width, height = window.surface.get_size()
                scrW, scrH = pygame.display.get_surface().get_size()
                x, y = window.rect.bottomleft
                glRasterPos2i(x, scrH - y)
                glDrawPixels(
                    width, height,
                    GL_RGBA,
                    GL_UNSIGNED_BYTE,
                    bitmap,
                )
        glFlush()

    def performFullUpdate(self):
        for window in self.windows:
            window._fullUpdate = True

    def drawCursor(self, surface):
        self.theme.drawCursor(surface, self.cursorPos)

    def update(self):
        if self.updateFunc:
            self.updateFunc()

    def redraw(self, widget, redrawParent = 0):
        self.redrawWidgets[widget] = None

    def needsUpdate(self):
        return len(self.redrawWidgets) > 0

    def exitLocal(self):
        evt = pygame.event.Event(Const.USEREVENT)
        evt.action = "localExit"
        pygame.event.post(evt)

    def exit(self):
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    def processAction(self, actionName, data = None, widget = None):
        """ There are no application wide actions supported yet."""
        return
