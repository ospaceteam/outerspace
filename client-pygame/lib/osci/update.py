#
#  Copyright 2001 - 2006 Ludek Smid [http://www.ospace.net/]
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

import time, urllib, shutil, os, os.path, sys, string, glob
from ige import log
import dialog, gdata

totalSize = 0
downloadedSize = 0
progressDlg = None
currentFilename = None

def checkForUpdate():
    global totalSize, downloadedSize, progressDlg, currentFilename
    # check platform, only 'nt' is supported for now
    if os.name != 'nt':
        log.message("Unsupported platform '%s' -- will not update" % os.name)
        return
    if "oslauncher" in sys.modules:
        log.message("Application launched from Outer Space Launcher -- will not update")
        return
    if not hasattr(sys, "frozen"):
        log.message("Application not frozen using py2exe -- will not update")
        return
    # remove old update directory
    try:
        shutil.rmtree('_update')
    except:
        pass
    # update mode
    if gdata.config.client.updatemode != None:
        updateMode = gdata.config.client.updatemode
    else:
        updateMode = 'normal'
        gdata.config.client.updatemode = updateMode
    # quit if update is disabled
    if updateMode == 'never':
        return
    # force update on every start. TODO remove - just for Alfa/Beta testing
    updateMode = 'always'
    # check for config
    if gdata.config.client.updateurl == None:
        gdata.config.client.updateurl = 'http://www.ospace.net/files/osclient/latest/'
    url = gdata.config.client.updateurl
    # check for last update
    if gdata.config.client.lastupdate != None:
        lastUpdate = gdata.config.client.lastupdate
    else:
        lastUpdate = 'NEVER'
    now = time.strftime('%Y-%m-%d')
    log.debug('UPDATER', 'Checking last update. Last update:', lastUpdate)
    if lastUpdate == now and updateMode != 'always':
        return
    # init dialog
    progressDlg = dialog.ProgressDlg(gdata.app)
    progressDlg.display('Updating client', 0, 1)
    progressDlg.setProgress('Checking for updates...', 0, 1)
    # read global checksum
    log.debug('UPDATER', 'Downloading %schecksum.global' % url)
    # create urlopener
    proxies = {}
    if gdata.config.proxy.http != None:
        proxies['http'] = gdata.config.proxy.http
    log.debug('UPDATER', 'Using proxies', proxies)
    urlopener = urllib.FancyURLopener(proxies)
    try:
        fh = urlopener.open(url + 'checksum.global')
        latestChsum = fh.read()
        fh.close()
        latestChsum = latestChsum.strip()
    except IOError:
        # cannot update
        log.warning('UPDATER', 'Cannot download file.')
        progressDlg.hide()
        return
    log.debug('UPDATER', 'Downloading checksum.global')
    try:
        fh = open('checksum.global', 'r')
        myChsum = fh.read()
        fh.close()
        myChsum = myChsum.strip()
    except IOError:
        myChsum = None
    log.debug('UPDATER', 'Global chsums:', latestChsum, myChsum)
    if latestChsum == myChsum:
        updateConfig()
        progressDlg.hide()
        return
    # load files chsums
    progressDlg.setProgress('Selecting files to update...', 0, 1)
    log.debug('UPDATER', 'Downloading %schecksum.files' % url)
    try:
        fh = urlopener.open(url + 'checksum.files')
        latestData = fh.read()
        fh.close()
    except IOError:
        log.warning('UPDATER', 'Cannot download file.')
        progressDlg.hide()
        return
    log.debug('UPDATER', 'Downloading checksum.files')
    try:
        fh = open('checksum.files', 'r')
        myData = fh.read()
        fh.close()
    except IOError:
        myData = ''
    # parse
    latestChsums = {}
    recipe = []
    retrieve = []
    totalSize = 0
    for line in latestData.split('\n'):
        if not line: continue
        chsum, file, size = line.strip().split(' ')
        size = int(size)
        latestChsums[file] = (chsum, size)
    for line in myData.split('\n'):
        if not line: continue
        chsum, file, size = line.strip().split(' ')
        size = int(size)
        if latestChsums.has_key(file):
            # file remains, check, if update shall be performed
            if latestChsums[file][0] != chsum or not os.path.exists(file):
                retrieve.append((file, latestChsums[file][1]))
                totalSize += latestChsums[file][1]
                recipe.append('C%s' % file)
            del latestChsums[file]
        else:
            # remove old file
            recipe.append('D%s' % file)
    # new files
    for file in latestChsums.keys():
        retrieve.append((file, latestChsums[file][1]))
        totalSize += latestChsums[file][1]
        recipe.append('C%s' % file)
    # log
    #@log.debug('UPDATER', 'Retrieve', retrieve)
    #@log.debug('UPDATER', 'Total length', totalSize)
    #@log.debug('UPDATER', 'Recipe', recipe)
    # retrieve file by file
    downloadedSize = 0
    for filename, size in retrieve:
        currentFilename = os.path.basename(filename)
        fileUrl = '%s%s' % (url, filename)
        log.debug('UPDATER', 'Downloading', fileUrl)
        progressDlg.setProgress('Downloading file %s...' % currentFilename, downloadedSize, totalSize)
        targetFile = os.path.join('_update', filename)
        try:
            os.makedirs(os.path.dirname(targetFile))
        except OSError:
            pass
        try:
            urlopener.retrieve(fileUrl, targetFile, retrieveCallback)
        except IOError:
            log.warning('UPDATER', 'Cannot download file.')
            progressDlg.hide()
            return
        downloadedSize += size
    # finish
    progressDlg.setProgress('Finishing upgrade...')
    updateConfig()
    # save latest checksums
    fh = open('checksum.global', 'w')
    fh.write(latestChsum)
    fh.close()
    fh = open('checksum.files', 'w')
    fh.write(latestData)
    fh.close()
    # save update
    header = ['_update', '.', 'osc.exe', str(len(recipe))]
    header.extend(recipe)
    fh = open('.update', 'w')
    fh.write(string.join(header, '\n'))
    fh.close()
    # copy update program (if possible)
    try:
        shutil.copy2('_update/update.exe', '.')
        os.remove('_update/update.exe')
    except IOError:
        pass
    # delete data files
    # decide if this is needed
    #log.warning('UPDATER', 'Deleting data files...')
    #for filename in glob.glob('var/[0-9]*.data'):
    #	os.remove(filename)
    #for filename in glob.glob('var/[0-9]*.timestamp'):
    #	os.remove(filename)
    # execute update program
    # TODO does not work os.spawnv(os.P_NOWAIT, 'update.exe', ())
    os.startfile('update.exe')
    progressDlg.hide()
    log.warning('UPDATER', 'Exitting...')
    sys.exit(1)

def retrieveCallback(blocks, blockSize, total):
    global totalSize, downloadedSize, progressDlg, currentFilename
    fProgr = min(blocks * blockSize, total)
    progressDlg.setProgress('Downloading file %s... [%3d %%]' %
        (currentFilename, fProgr * 100 / total), downloadedSize + fProgr, totalSize)
    #@log.debug('UPDATER', 'Progress', blocks, blockSize, total)

def updateConfig():
    # set last update
    now = time.strftime('%Y-%m-%d')
    gdata.config.client.lastupdate = now
    # write configuration
    gdata.config.save('var/osci.ini')
