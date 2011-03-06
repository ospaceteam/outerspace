#!/usr/bin/env python2.4
import sys
import os, os.path, glob
import shutil
import time
from optparse import OptionParser
import re

sys.path.append("server/lib")
import ige.version

baseDir = 'server/website/osclient/latest'

parser = OptionParser()
parser.add_option("-f", "--force", dest = "force", action = "store_true",
    default = False, help = "Bypass CVS checks")
parser.add_option("-v", "--version", dest = "version", action = "store",
    default = ige.version.versionString, help = "Set version (format N.N.N-S, default is %s)" % ige.version.versionString)
options, args = parser.parse_args()

## check version
import pysvn

svn = pysvn.Client()

print "#\n# Generating version info\n#"

entry = svn.info(".")

if entry.revision.kind == pysvn.opt_revision_kind.number:
    print 'Revision:', entry.revision.number
    print 'Version :', options.version
else:
    print "Cannot retrieve revision info"
    sys.exit(1)

# check for modified files
if not options.force:
    print "#\n# Checking for modified and unversioned files\n#"
    okToGo = True
    for status in svn.status(".", recurse = True):
        if status.text_status not in (pysvn.wc_status_kind.normal, pysvn.wc_status_kind.ignored):
            print "[%s] %s" % (status.text_status, status.path)
            okToGo = False

    if not okToGo:
        print
        print "Fix problems displayed above and re-run deploy.py script"
        sys.exit(1)

# make base directory
try:
    os.makedirs(baseDir)
except OSError:
    pass

# clean up old installation
try:
    shutil.rmtree(baseDir, ignore_errors=1)
except:
    pass

# make binary package - SDL client
os.chdir('client-pygame')
os.system('setup.py py2exe')
os.system('setup.py sdist')
os.chdir('..')
shutil.copytree('dist_win32', baseDir)

# generate checksums
import md5, stat

def chsums(fh, base, directory, globalChsum):
    filelist = os.listdir(directory)
    filelist.sort()
    for file in filelist:
        if file in ('checksum.files', 'checksum.global', 'var', 'files.html'):
            continue
        if base:
            filename = base + '/' + file
        else:
            filename = file
        absfilename = os.path.join(directory, file)
        if os.path.isfile(absfilename):
            f = open(absfilename, 'rb')
            data = f.read()
            f.close()
            globalChsum.update(data)
            myChsum = md5.new(data)
            print >>fh, myChsum.hexdigest(), filename, os.stat(absfilename)[stat.ST_SIZE]
        elif os.path.isdir(absfilename):
            chsums(fh, filename, os.path.join(directory, file), globalChsum)
        else:
            raise 'Unknow file type %s' % file

fh = open(os.path.join(baseDir, 'checksum.files'), 'w')
chsum = md5.new()
chsums(fh, None, baseDir, chsum)
fh.close()

fh = open(os.path.join(baseDir, 'checksum.global'), 'w')
print >>fh, chsum.hexdigest()
fh.close()

# compress files
def compress(base, directory):
    filelist = os.listdir(directory)
    filelist.sort()
    for file in filelist:
        if file in ('checksum.files', 'checksum.global', 'var', 'files.html'):
            continue
        if base:
            filename = base + '/' + file
        else:
            filename = file
        absfilename = os.path.join(directory, file)
        if os.path.isfile(absfilename):
            print 'BZIP2', os.path.normcase(absfilename)
            os.system('updater\\bzip2.exe %s' % os.path.normcase(absfilename))
        elif os.path.isdir(absfilename):
            compress(filename, os.path.join(directory, file))
        else:
            raise 'Unknow file type %s' % file

# create installation
for templateFile in ("setup.iss.template", "setup-fast.iss.template"):
    template = open(templateFile, "r").read()
    data = {
        "version": options.version,
    }
    open("setup.iss", "w").write(template % data)

    os.system("tools\\InnoSetup5\\iscc.exe setup.iss")

# create tech tree
# FIXME: disabled for now
#os.chdir("tools")
#os.system("techtree.bat")
#os.chdir("..")

print '#'
print '# Operation successfull'
print '#'
