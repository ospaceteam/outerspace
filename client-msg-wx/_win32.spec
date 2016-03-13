a = Analysis(
	[
		os.path.join(HOMEPATH,'support\\_mountzlib.py'),
		os.path.join(HOMEPATH,'support\\useUnicode.py'),
		'main.py'
	],
   pathex=['lib', '../server/lib', '../client-pygame/lib']
)

# create distribution directory
try:
	os.mkdirs('dist_win32')
except:
	pass


# split PURE into os files and deps
import os, os.path

mydir = os.path.dirname(os.getcwd())

os = TOC()
deps = TOC()

for module, filename, type in a.pure:
	if filename[:len(mydir)] == mydir:
		os.append((module, filename, type))
	else:
		deps.append((module, filename, type))

ospyz = PYZ(os, name = "build_win32/osclib.pyz")
depspyz = PYZ(deps, name = "build_win32/deps.pyz")

exe = EXE(
	depspyz,
	a.scripts,
	exclude_binaries=1,
	name='build_win32/oscmsg.exe',
	icon='../client-pygame/res/bigicon.ico',
	debug=0,
	console=0,
	upx=0,
)

coll = COLLECT(
	exe,
	ospyz,
	a.binaries,
	upx=0,
	name='dist_win32'
)
