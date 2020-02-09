#
#  Copyright 2001 - 2016 Ludek Smid [http://www.ospace.net/]
#
#  This file is part of Outer Space.
#
#  Outer Space is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  Outer Space is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Outer Space; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

import pygameui as ui
from osci.StarMapWidget import StarMapWidget
from osci import gdata, res, client
import osci.messages
import ige.ospace.Const as Const
from NewMessageDlg import NewMessageDlg
from ConfirmDlg import ConfirmDlg
import time
from ige import log
import re

class MessagesDlg:

    def __init__(self, app):
        self.app = app
        self.createUI()
        #
        self.selectedObjID = None
        self.selectedForum = None
        self.selectedTopic = None
        self.selectedType = None
        self.newMessageDlg = NewMessageDlg(app)
        self.newMsgs = 0
        self.confirmDlg = ConfirmDlg(app)
        self.uignore = gdata.config.ignore.universe.split(',') if gdata.config.ignore.universe else []
        self.gignore = gdata.config.ignore.galaxy.split(',') if gdata.config.ignore.galaxy else []
        self.lignore = gdata.config.ignore.local.split(',') if gdata.config.ignore.local else []

    def display(self):
        self.show()
        self.win.show()
        # register for updates
        if self not in gdata.updateDlgs:
            gdata.updateDlgs.append(self)

    def hide(self):
        self.win.setStatus(_("Ready."))
        self.win.hide()
        # unregister updates
        if self in gdata.updateDlgs:
            gdata.updateDlgs.remove(self)

    def update(self):
        self.show()

    def show(self, updateForum = 1):
        self.newMsgs = 0
        #
        player = client.getPlayer()
        objList = [player.oid]
        objList.append(player.galaxy)
        objList.append(Const.OID_UNIVERSE)
        # show forums
        items = []
        colors = [gdata.sevColors[gdata.INFO], gdata.sevColors[gdata.MIN]]
        ## Inbox
        msgs, new = self.getMsgsNumber(player.oid, "INBOX",'local')
        self.newMsgs += new
        spec = gdata.mailboxSpec[Const.T_PLAYER, "INBOX"]
        item = ui.Item(_(spec[0]), tObjID=player.oid, tForum="INBOX",
                       tType=Const.T_PLAYER, tMsgs=_("%d / %d") % (new, msgs), foreground=colors[new > 0])
        items.append(item)
        # Events
        msgs, new = self.getMsgsNumber(player.oid, "EVENTS")
        self.newMsgs += new
        spec = gdata.mailboxSpec[Const.T_PLAYER, "EVENTS"]
        eventsItem = ui.Item(_(spec[0]), tObjID=player.oid, tForum="EVENTS",
                             tType=Const.T_PLAYER, tMsgs=_("%d / %d") % (new, msgs), foreground=colors[new > 0])
        items.append(eventsItem)
        # Outbox
        msgs, new = self.getMsgsNumber(player.oid, "OUTBOX")
        self.newMsgs += new
        spec = gdata.mailboxSpec[Const.T_PLAYER, "OUTBOX"]
        item = ui.Item(_(spec[0]), tObjID=player.oid, tForum="OUTBOX",
                       tType=Const.T_PLAYER, tMsgs=_("%d / %d") % (new, msgs), foreground=colors[new > 0])
        items.append(item)
        ## galaxy
        galaxyID = player.galaxy
        galaxy = client.get(galaxyID)
        # folder
        item = ui.Item(_("Galaxy %s") % galaxy.name, tObjID=Const.OID_NONE, tForum="", tMsgs="", foreground=colors[0])
        items.append(item)
        # news
        msgs, new = self.getMsgsNumber(galaxyID, "NEWS")
        self.newMsgs += new
        spec = gdata.mailboxSpec[Const.T_GALAXY, "NEWS"]
        item = ui.Item("   %s" % _(spec[0]), tObjID=galaxyID, tForum="NEWS",
                       tType=Const.T_GALAXY, tMsgs=_("%d / %d") % (new, msgs), foreground=colors[new > 0])
        items.append(item)
        # public
        msgs, new = self.getMsgsNumber(galaxyID, "PUBLIC",'galaxy')
        self.newMsgs += new
        spec = gdata.mailboxSpec[Const.T_GALAXY, "PUBLIC"]
        item = ui.Item("   %s" % _(spec[0]), tObjID=galaxyID, tForum="PUBLIC",
                       tType=Const.T_GALAXY, tMsgs=_("%d / %d") % (new, msgs), foreground=colors[new > 0])
        items.append(item)
        ## universe
        item = ui.Item(_("Outer Space"), tObjID=Const.OID_NONE, tForum="", tMsgs="", foreground=colors[0])
        items.append(item)
        # news
        msgs, new = self.getMsgsNumber(Const.OID_UNIVERSE, "NEWS")
        self.newMsgs += new
        spec = gdata.mailboxSpec[Const.T_UNIVERSE, "NEWS"]
        item = ui.Item("   %s" % _(spec[0]), tObjID=Const.OID_UNIVERSE, tForum="NEWS",
                       tType=Const.T_UNIVERSE, tMsgs=_("%d / %d") % (new, msgs), foreground=colors[new > 0])
        items.append(item)
        # public
        msgs, new = self.getMsgsNumber(Const.OID_UNIVERSE, "PUBLIC",'universe')
        self.newMsgs += new
        spec = gdata.mailboxSpec[Const.T_UNIVERSE, "PUBLIC"]
        item = ui.Item("   %s" % _(spec[0]), tObjID=Const.OID_UNIVERSE, tForum="PUBLIC",
                       tType=Const.T_UNIVERSE, tMsgs=_("%d / %d") % (new, msgs), foreground=colors[new > 0])
        items.append(item)
        #
        self.win.vForums.items = items
        self.win.vForums.itemsChanged()
        # find item to select
        found = 0
        for item in items:
            if item.tObjID == self.selectedObjID and item.tForum == self.selectedForum:
                self.win.vForums.selectItem(item)
                found = 1
                break
        if not found:
            self.win.vForums.selectItem(eventsItem)
        # display forum
        if updateForum:
            self.onForumSelected(None, None, None)
        # update mgs button
        gdata.mainGameDlg.updateMsgButton()

    def getMsgsNumber(self, objID, forum, forumtype='none'):
        try:
            messages = client.get(objID)._messages
        except AttributeError:
            log.debug("Suplying default messages for object", objID, forum)
            messages = {}
        new = 0
        msgs = 0
        for messageID in messages:
            message = messages[messageID]
            if ((forumtype == 'universe' and message["sender"] in self.uignore)
               or (forumtype == 'galaxy' and message["sender"] in self.gignore)
               or (forumtype == 'local' and message["sender"] in self.lignore)):
                continue
            if message["forum"] == forum:
                if message["readed"] == 0:
                    new += 1
                msgs += 1
        return msgs, new

    def _processMessage(self, message):
        # the old code had this to "regenerate topic from data". IDK what that means
        if "data" in message and message["topic"] == "EVENT":
            sourceID, msgID, locationID, turn, data = message["data"]
            message["topic"] = osci.messages.getMsgText(msgID, data).split("\n")[0]
        item = ui.Item(message["topic"])
        if "data" in message:
            sourceID, msgID, locationID, turn, data = message["data"]
            item.tLocationID = locationID
            item.tSourceID = sourceID
            obj = client.get(sourceID, noUpdate=1, publicOnly=1)  # Custom name in "sender"
            item.tSender = _('"%s"') % obj.customname if getattr(obj, 'customname', None) else message["sender"]
            foreground = gdata.sevColors[osci.messages.getMsgSeverity(msgID)]
            state = _(" ") if message["readed"] else _("N")
        else:
            item.tSender = message["sender"]
            if message["readed"]:
                foreground = gdata.sevColors[gdata.NONE]
                state = _("R") if message["replied"] else _(" ")
            else:
                foreground = gdata.sevColors[gdata.MIN]
                state = _("N")
        date = time.strftime(_("%m-%d %H:%M"), time.localtime(message["time"]))
        item.foreground = foreground
        item.tState = state
        item.tDate = date
        item.tDate_raw = message["time"]
        return item

    def onForumSelected(self, widget, action, data):
        selItem = self.win.vForums.selection[0]
        if selItem.tObjID == Const.OID_NONE:
            # select last valid
            for item in self.win.vForums.items:
                if item.tObjID == self.selectedObjID and item.tForum == self.selectedForum:
                    self.win.vForums.selectItem(item)
                    break
            return
        self.selectedObjID = selItem.tObjID
        self.selectedForum = selItem.tForum
        self.selectedType = selItem.tType
        self.win.vNewTopic.enabled = 1
        self.win.vAllReaded.enabled = 1
        self.win.vDeleteAll.enabled = 1
        player = client.getPlayer()
        playerid = player.oid
        objMessages = client.get(selItem.tObjID)._messages
        ids = objMessages.keys()
        ids.sort()
        ids.reverse()
        items = []
        for messageID in ids:
            message = objMessages[messageID]
            if message["forum"] == selItem.tForum:
                # ignore by universe, local (private messages), or galaxy
                if ((selItem.tObjID == Const.OID_UNIVERSE and message["sender"] in self.uignore)
                   or (selItem.tObjID == playerid and message["sender"] in self.lignore)
                   or (message["sender"] in self.gignore)):
                    continue

                item = self._processMessage(message)
                item.tMsgID = messageID
                item.tObjID = selItem.tObjID
                item.tForum = selItem.tForum
                item.tType = selItem.tType
                items.append(item)
        self.win.vMessages.items = items
        self.win.vMessages.itemsChanged()
        if self.selectedForum != "EVENTS":
            # reset messages scrollbar position
            self.win.vMessages.bar.slider.position = 0
        self.win.vMessages.itemsChanged()
        self.win.vMessage.text = [""]
        self.win.vReply.enabled = 0
        self.win.vNewTopic.enabled = gdata.mailboxSpec[selItem.tType, gdata.mailboxStripLang(selItem.tForum)][1] != None
        self.win.vDelete.enabled = len(self.win.vMessages.selection) > 0

    def onMessageSelected(self, widget, action, data):
        selItem = self.win.vMessages.selection[0]
        selItem.tState = " "
        message = client.get(selItem.tObjID)._messages[selItem.tMsgID]
        if "data" not in message:
            selItem.foreground = gdata.sevColors[gdata.NONE]
        self.win.vMessages.itemsChanged()
        message["readed"] = 1
        text = []
        if "data" in message:
            text = osci.messages.getFullMessageText(message).split("\n")

        if "text" in message:
            text.extend(message["text"].split("\n"))

        self.win.vMessage.text = text
        self.win.vMessage.offsetRow = 0
        self.win.vMessage.vertScrollbar.slider.position = 0
        self.win.vReply.enabled = gdata.mailboxSpec[selItem.tType, gdata.mailboxStripLang(selItem.tForum)][1] != None
        self.win.vDelete.enabled = 1
        self.show(updateForum = 0)

    def onNewTopic(self, widget, action, data):
        self.newMessageDlg.display(self, self.selectedObjID, self.selectedType, self.selectedForum)

    def onReply(self, widget, action, data):
        selItem = self.win.vMessages.selection[0]
        topic = client.get(selItem.tObjID)._messages[selItem.tMsgID]["topic"]
        self.newMessageDlg.display(self, self.selectedObjID, self.selectedType, self.selectedForum, selItem.tMsgID)

    def onRefresh(self, widget, action, data):
        client.getMessages()
        self.update()

    def onDelete(self, widget, action, data):
        selItem = self.win.vMessages.selection[0]
        del client.get(selItem.tObjID)._messages[selItem.tMsgID]
        self.update()

    def onDeleteAll(self, widget, action, data):
        self.confirmDlg.display(_("Delete all messages in this mailbox?"),
            _("Yes"), _("No"), self.onDeleteAllConfirmed)

    def onDeleteAllConfirmed(self):
        obj = client.get(self.selectedObjID)
        # must make list (changing directory)
        for messageID in obj._messages.keys():
            message = obj._messages[messageID]
            if message["forum"] == self.selectedForum:
                del obj._messages[messageID]
        self.update()

    def onAllReaded(self, widget, action, data):
        obj = client.get(self.selectedObjID)
        for messageID in obj._messages:
            message = obj._messages[messageID]
            if message["forum"] == self.selectedForum:
                message["readed"] = 1
        self.update()

    def onPostMenu(self, widget, action, data):
        selItem = self.win.vMessages.selection[0]
        if hasattr(selItem, "tLocationID"):
            self.eventPopup.show()

    def onShowLoc(self, widget, action, data):
        item = self.win.vMessages.selection[0]
        if item.tLocationID != Const.OID_NONE:
            obj = client.get(item.tLocationID, noUpdate=1)
            if hasattr(obj, "x"):
                gdata.mainGameDlg.win.vStarMap.highlightPos = (obj.x, obj.y)
                gdata.mainGameDlg.win.vStarMap.setPos(obj.x, obj.y)
                self.hide()
                return
        if item.tForum == "EVENTS" and re.match(('^%s(.*)')%(_('Research completed:')),item.text):
            gdata.mainGameDlg.researchDlg.display()
            return
        self.win.setStatus(_("Cannot show location"))

    def onShowLocDel(self, widget, action, data):
        self.onShowLoc(widget, action, data)
        self.onDelete(widget, action, data)

    def onShowSource(self, widget, action, data):
        item = self.win.vMessages.selection[0]
        if item.tForum == "EVENTS" and re.match(('^%s(.*)')%(_('Research completed:')),item.text):
            gdata.mainGameDlg.researchDlg.display()
            return
        if item.tSourceID != Const.OID_NONE:
            gdata.mainGameDlg.onSelectMapObj(None, None, item.tSourceID)
            #self.hide()
            return
        self.win.setStatus(_("Cannot show location"))

    def onShowSourceDel(self, widget, action, data):
        self.onShowSource(widget, action, data)
        self.onDelete(widget, action, data)

    def onClose(self, widget, action, data):
        self.hide()

    def createUI(self):
        w, h = gdata.scrnSize
        self.win = ui.Window(self.app,
                             modal=1,
                             escKeyClose=1,
                             titleOnly=w == 800 and h == 600,
                             movable=0,
                             title=_("Messages and events"),
                             rect=ui.Rect((w - 800 - 4 * (w != 800)) / 2, (h - 600 - 4 * (h != 600)) / 2, 800 + 4 * (w != 800), 580 + 4 * (h != 600)),
                             layoutManager=ui.SimpleGridLM())
        self.win.subscribeAction('*', self)
        # forums
        ui.Listbox(self.win, layout=(0, 0, 10, 27), id="vForums",
                   columns=((_("Channel"), "text", 5.5, ui.ALIGN_W), (_("#"), "tMsgs", 4.5, ui.ALIGN_E)),
                   columnLabels=1, action="onForumSelected", sortable=0)
        # topics
        ui.Listbox(self.win, layout=(10, 0, 30, 15), id="vMessages",
                   columns=((_(" "), "tState", 1, ui.ALIGN_NONE),
                            (_("Date"), "tDate", 4, ui.ALIGN_W),
                            (_("Sender"), "tSender", 7, ui.ALIGN_W),
                            (_("Subject"), "text", 0, ui.ALIGN_W)),
                   columnLabels=1, action="onMessageSelected", rmbAction="onPostMenu")
        # messages
        ui.Title(self.win, layout=(10, 15, 5, 1),
                 font="normal-bold", align=ui.ALIGN_W)
        ui.Button(self.win, layout=(15, 15, 5, 1), text=_("New subject"),
                  action="onNewTopic", id="vNewTopic", enabled=0)
        ui.Button(self.win, layout=(20, 15, 5, 1), text=_("Reply"),
                  action="onReply", id="vReply", enabled=0)
        ui.Button(self.win, layout=(25, 15, 5, 1), text=_("Read all"),
                  action="onAllReaded", id="vAllReaded", enabled=0)
        ui.Button(self.win, layout=(30, 15, 5, 1), text=_("Delete"),
                  action="onDelete", id="vDelete", enabled=0)
        ui.Button(self.win, layout=(35, 15, 5, 1), text=_("Delete all"),
                  action="onDeleteAll", id="vDeleteAll", enabled=0)
        s = ui.Scrollbar(self.win, layout=(39, 16, 1, 11))
        t = ui.Text(self.win, layout=(10, 16, 29, 11), id="vMessage", editable=0)
        t.attachVScrollbar(s)
        # status bar
        ui.TitleButton(self.win, layout=(30, 27, 5, 1), text=_('Refresh'), action='onRefresh')
        ui.TitleButton(self.win, layout=(35, 27, 5, 1), text=_('Close'), action='onClose')
        ui.Title(self.win, id='vStatusBar', layout=(0, 27, 30, 1), align=ui.ALIGN_W)
        # event menu
        self.eventPopup = ui.Menu(self.app, title=_("Message actions"),
                                  items=[ui.Item(_("Show location"), action="onShowLoc"),
                                         ui.Item(_("Show source"), action="onShowSource"),
                                         ui.Item(_("Show location and delete msg"), action="onShowLocDel"),
                                         ui.Item(_("Show source and delete msg"), action="onShowSourceDel"),
                                         ui.Item(_("Delete"), action="onDelete")])
        self.eventPopup.subscribeAction("*", self)
