# tweak PYTHONPATH
import sys
sys.path.insert(0, 'lib')
sys.path.insert(0, '../server/lib')

from distutils.core import setup

havePy2Exe = False
try:
    import py2exe
    havePy2Exe = True
except ImportError:
    pass

import glob
import shutil
import os
import stat

# copy server library
if not os.path.exists("libsrvr"):
    shutil.copytree("../server/lib", "libsrvr")
else:
    sys.path.append("libsrvr")


# collect data files
data_files = []
data_files.append(
    (
        ".",
        ["../ChangeLog.txt", "../COPYING", "../README", "../README_CZ"]
    )
)

# resources
for root, dirs, files in os.walk('res'):
    try:
        dirs.remove(".svn")
    except ValueError:
        pass
    if files:
        data_files.append((root, [os.path.join(root, file) for file in files]))

data_files.append(
    (
        "res/techspec",
        [
            "../server/lib/ige/ospace/Rules/techs.spf",
            "../server/lib/ige/ospace/Rules/Tech.spf",
        ]
    )
)

if havePy2Exe:
    data_files.append((".", ["../updater/update.exe"]))

# version
from osci import version

# generate up-to-date rules
import ige.ospace.Rules

# setup
setup(
    name = 'OuterSpace',
    version = '%d.%d.%d%s' % version,
    description = 'Client for IGE - Outer Space game',
    author = "Ludek Smid",
    author_email = "qark@ospace.net",
    maintainer = 'Ludek Smid',
    maintainer_email = 'qark@ospace.net',
    url = 'http://www.ospace.net/',
    windows = [
        {
            "script": "osc.pyw",
            "icon_resources": [(1, "res/smallicon.ico"), (1, "res/bigicon.ico")]
        }
    ],
    data_files = data_files,
    package_dir = {"osci": "lib/osci", "pygameui": "lib/pygameui", "": "libsrvr"},
    packages = ["osci", "osci.dialog", "pygameui", "igeclient", "ige", "ige.ospace", "ige.ospace.Rules"],
    py_modules = ["log"],
    scripts = ["osc.py"],
)

# cleanup
def onerror(func, path, err):
    if func is os.remove:
        os.chmod(path, stat.S_IWRITE)
        os.remove(path)

shutil.rmtree("libsrvr", onerror = onerror)
