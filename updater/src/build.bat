set PATH=%PATH%;c:\bcc55\bin
set WXWIN=d:\development\wx232
set BCCDIR=c:\bcc55

make -f makefile.b32 FINAL=1
upx --best update.exe
copy update.exe ..
make -f makefile.b32 clean