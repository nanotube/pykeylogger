rem *** Create zip file with source distribution

setlocal
set VERSION=0.4.2

"C:\Program Files\WinRAR\WinRAR.exe" a -r "pykeylogger%VERSION%_src.zip" "keylogger.pyw" "logwriter.py" "setup.py" "*.txt" "*.bat" "html"

mv "./pykeylogger%VERSION%_src.zip" "../pykeylogger%VERSION%_src.zip"

endlocal

pause "done, press to key to exit"