import sys
sys.path.append("../../tools")

a = Analysis(
	[
		os.path.join(HOMEPATH,'support\\_mountzlib.py'),
		os.path.join(HOMEPATH,'support\\useUnicode.py'),
		'main.py'
	],
   pathex=['lib', '../server/lib']
)

targetDir = "dist_src/OSMessageCenter"

# create distribution directory
import os, os.path, glob
import ShellUtils

try:
	ShellUtils.rmtree(os.path.join(targetDir), ignore_errors=1)
except:
	pass

try:
	os.mkdirs(targetDir)
except:
	pass

# split PURE into os files and deps

mydir = os.path.dirname(os.getcwd())

try:
	ShellUtils.rmtree(targetDir)
except:
	pass

for module, filename, type in a.pure:
	if filename[:len(mydir)] == mydir:
		# print "Processing", module
		# copy
		baseDir = os.path.dirname(filename)
		baseFile = os.path.basename(filename)[:-1]
		if baseFile != "__init__.py":
			# copy regular file
			dst = "%s.py" % (os.path.join(targetDir, module.replace(".", "/")))
		else:
			# copy __init__ file
			dst = os.path.join(targetDir, module.replace(".", "/"), "__init__.py")

		src = os.path.join(baseDir, baseFile)
		try:
			os.makedirs(os.path.dirname(dst))
		except OSError:
			pass
		ShellUtils.copy2(src, dst)
	else:
		pass
		# print "Skipping", module

# copy osc.py
ShellUtils.copy2("osc.py", os.path.join(targetDir, "osc.py"))

# copy res dir
ShellUtils.copytree("res", os.path.join(targetDir, "res"))

# copy tech spec
#serverSpec = "../server/lib/ige/ospace/Rules"
#for file in glob.glob("%s/*.xml" % serverSpec):
#	ShellUtils.copy2(file, os.path.join(targetDir, 'ige/ospace/Rules', os.path.basename(file)))

# copy other files
ShellUtils.copy2("../ChangeLog.txt", os.path.join(targetDir, "ChangeLog.txt"))
ShellUtils.copy2("../README_cz.txt", os.path.join(targetDir, "README_cz.txt"))
ShellUtils.copy2("../README_en.txt", os.path.join(targetDir, "README_en.txt"))
ShellUtils.copy2("../LICENSE.TXT", os.path.join(targetDir, "LICENSE.TXT"))

# create packages
origDir = os.getcwd()
os.chdir("dist_src")
os.system("tar czf OSMessageCenter.tar.gz OSMessageCenter/*")
os.system("zip -9 -r OSMessageCenter.zip OSMessageCenter/*")
os.chdir(origDir)
