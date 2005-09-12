rem *** create md5 sums for the dist files.

setlocal
set VERSION=0.4.1

"C:\Program Files\UnixUtils\md5sum.exe" "../pykeylogger%VERSION%_src.zip" "../pykeylogger%VERSION%_win32.zip" > "../pykeylogger%VERSION%_md5sums.txt"

endlocal

pause "done, press to key to exit"