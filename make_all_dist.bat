rem *** Used to create a Python exe  

setlocal
set VERSION=0.4.1

rem ***** get rid of all the old files in the build folder 
rd /S /Q build 
 
rem ***** create the exe 
c:\Python24\python setup.py py2exe 
 
rem **** pause so we can see the exit codes 
pause "done, press key to continue"

rem **** rename dist directory to 'pykeylogger'
rename "dist" "pykeylogger"

echo %VERSION%
pause "You didnt forget to edit the version, did you?..."

"C:\Program Files\WinRAR\WinRAR.exe" a -r "pykeylogger%VERSION%_win32.zip" "pykeylogger"

mv "./pykeylogger%VERSION%_win32.zip" "../pykeylogger%VERSION%_win32.zip"

rd /S /Q pykeylogger

pause "done, now lets create the scr dist"

"C:\Program Files\WinRAR\WinRAR.exe" a -r "pykeylogger%VERSION%_src.zip" "keylogger.pyw" "logwriter.py" "setup.py" "*.txt" "*.bat" "html"

mv "./pykeylogger%VERSION%_src.zip" "../pykeylogger%VERSION%_src.zip"

rd /S /Q pykeylogger

pause "now lets create the md5 sums"

"C:\Program Files\UnixUtils\md5sum.exe" "../pykeylogger%VERSION%_src.zip" "../pykeylogger%VERSION%_win32.zip" > "../pykeylogger%VERSION%_md5sums.txt"

endlocal

pause "done, press to key to exit"
