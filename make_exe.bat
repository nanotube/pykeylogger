rem *** Used to create a Python exe  

setlocal
set VERSION=0.4

rem ***** get rid of all the old files in the build folder 
rd /S /Q build 
 
rem ***** create the exe 
c:\Python24\python setup.py py2exe 
 
rem **** pause so we can see the exit codes 
pause "done, press key to continue"

rem **** rename dist directory to 'pykeylogger'
rename "dist" "pykeylogger"

echo %VERSION%
pause "..."

"C:\Program Files\WinRAR\WinRAR.exe" a -r "pykeylogger%VERSION%_win32.zip" "pykeylogger"

pause "lets inspect the filename"

mv "./pykeylogger%VERSION%_win32.zip" "../pykeylogger%VERSION%_win32.zip"

rd /S /Q pykeylogger

endlocal

pause "done, press to key to exit"