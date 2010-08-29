#
#  Copyright 2001 - 2010 Ludek Smid [http://www.ospace.net/]
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

import client
import gdata
from ige import log
import ige.version
import os
import sys
import urllib2
import webbrowser

def update(options):
    """Check if client version matches server version and update client
    if neccessary"""
    log.message("###########  Checking for update...")
    # check platform, only 'nt' is supported for now
    #if os.name != 'nt':
    #    log.message("Unsupported platform '%s' -- will not update" % os.name)
    #    return
    if "oslauncher" in sys.modules:
        log.message("Application launched from Outer Space Launcher -- will not update")
        return
    #if not hasattr(sys, "frozen"):
    #    log.message("Application not frozen using py2exe -- will not update")
    #    return
    # update mode
    if gdata.config.client.updatemode != None:
        updateMode = gdata.config.client.updatemode
    else:
        updateMode = 'normal'
        gdata.config.client.updatemode = updateMode
    # do not auto update alpha/beta versions
    if ige.version.version["status"].startswith("-alpha") \
        or ige.version.version["status"].startswith("-beta"):
        if updateMode != "force":
            log.message("Alpha or beta version detected -- set updatemode to 'force' to enable updates")
            return
        else:
            log.message("Forcing update")
    # quit if update is disabled
    if updateMode == 'never':
        return
    # compare server and client versions
    log.message("Retrieving server version")
    version = client.cmdProxy.getVersion()
    log.debug("Comparing server and client versions", version, ige.version.version)
    matches = True
    for i in ("major", "minor", "revision", "status", "svnRevision"):
        if ige.version.version[i] != version[i]:
            matches = False
    if matches:
        log.message("Versions match, no need to update")
        return
    # check if update URL exists
    action, url = version["clientURLs"].get(sys.platform, version["clientURLs"]["*"])
    log.message("Updating with", action, url)
    if action == "browser":
        # open webbrowser with given url    
        webbrowser.open(url)
        return
    elif action != "execute":
        log.message("Unsupported update action", action)
        return
    # ok, download and execute update
    proxies = {}
    if gdata.config.proxy.http != None:
        proxies['http'] = gdata.config.proxy.http
    log.debug('UPDATER', 'Using proxies', proxies)
    # create dialog
    progressDlg = dialog.ProgressDlg(gdata.app)
    progressDlg.display('Preparing download...', 0, 1)
    progressDlg.setProgress(None, 0, 1)
    # get file    
    try:
        # open URL
    	opener = urllib2.build_opener(urllib2.ProxyHandler(proxies))
        ifh = opener.open(url)
        log.debug("Retrieving", ifh.geturl())
        # download file
        total = int(ifh.info()["Content-Length"])
        filename = os.path.join(options.configDir, os.path.basename(ifh.geturl()))
        log.debug("Downloading file %s of size %d" % (filename, total) )
        ofh = open(filename, "wb")
        # download and report progress
        downloaded = 0
        while True:
        	data = ifh.read(100000)
        	if not data:
        		break
        	ofh.write(data)
        	downloaded += len(data)
        	log.debug("Download progress", downloaded, total)
        	progressDlg.setProgress("Downloading update...", downloaded, total)
        ifh.close()
        ofh.close()
    except urllib2.URLError:
        log.warning("Cannot download file")
        progressDlg.hide()
        return
    except Exception:
    	log.warning("Cannot download file")
    	progressDlg.hide()
    	return
    progressDlg.setProgress('Finishing update...')
    # now somehow handle file we downloaded
    if hasattr(os, "startfile"):
        # win 32 has startfile defined
        log.debug("Starting file", filename)
        os.startfile(os.path.normpath(filename))
        sys.exit(2)
    else:
        # other systems
        log.debug("Don't know what to do with", filename)
    progressDlg.hide()

