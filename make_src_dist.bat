rem *** Used to create a Python exe  

setlocal
set VERSION=0.4.1

"C:\Program Files\WinRAR\WinRAR.exe" a -r "pykeylogger%VERSION%_src.zip" "keylogger.pyw" "logwriter.py" "setup.py" "*.txt" "*.bat" "html"

pause "lets inspect the filename"

mv "./pykeylogger%VERSION%_src.zip" "../pykeylogger%VERSION%_src.zip"

rd /S /Q pykeylogger

endlocal

pause "done, press to key to exit"