import version
import os
import sys

if raw_input("Current version is " + version.version + ". Is that correct? [Y/N] ") in ["y", "Y", "yes", "YES", "Yes"]:
    pass
else:
    sys.exit()

#delete old build dir.
print r'rd /S /Q build'
os.system(r'rd /S /Q build')

# create the exe 
print r'c:\Python24\python setup.py py2exe -b1'
os.system(r'c:\Python24\python setup.py py2exe -b1')

#pause to see output
#os.system('pause "done, press key to continue"')
print r'rename "dist" "pykeylogger""'
os.system(r'rename "dist" "pykeylogger""')

print r'copy ".\*.txt" ".\pykeylogger""'
os.system(r'copy ".\*.txt" ".\pykeylogger""')

print r'copy ".\run_exe_pykeylogger_with_cmdoptions.bat" ".\pykeylogger""'
os.system(r'copy ".\run_exe_pykeylogger_with_cmdoptions.bat" ".\pykeylogger""')

#command = '\"\"C:\Progra~1\WinRAR\WinRAR.exe" a -r "pykeylogger' + version.version + '_win32.zip" "pykeylogger\"\"'
#print repr(command)
#os.system(command)
print r'""C:\Progra~1\WinRAR\WinRAR.exe" a -r "pykeylogger' + version.version + '_win32.zip" "pykeylogger""'
os.system(r'""C:\Progra~1\WinRAR\WinRAR.exe" a -r "pykeylogger' + version.version + '_win32.zip" "pykeylogger""')

print r'mv "./pykeylogger' + version.version + '_win32.zip" "../pykeylogger' + version.version + '_win32.zip"'
os.system(r'mv "./pykeylogger' + version.version + '_win32.zip" "../pykeylogger' + version.version + '_win32.zip"')

print r'rd /S /Q pykeylogger'
os.system(r'rd /S /Q pykeylogger')
print r'rd /S /Q build'
os.system(r'rd /S /Q build')

#os.system('pause "done, now lets create the src dist"')
print r'""C:\Progra~1\WinRAR\WinRAR.exe" a -r "pykeylogger' + version.version + '_src.zip" "keylogger.pyw" "logwriter.py" "setup.py" "version.py" "make_all_dist.py" "*.txt" "*.bat" "html""'
os.system(r'""C:\Progra~1\WinRAR\WinRAR.exe" a -r "pykeylogger' + version.version + '_src.zip" "keylogger.pyw" "logwriter.py" "setup.py" "version.py" "make_all_dist.py" "*.txt" "run_exe_pykeylogger_with_cmdoptions.bat" "run_pykeylogger_with_cmdoptions.bat" "html""')

print r'mv "./pykeylogger' + version.version + '_src.zip" "../pykeylogger' + version.version + '_src.zip"'
os.system(r'mv "./pykeylogger' + version.version + '_src.zip" "../pykeylogger' + version.version + '_src.zip"')

#os.system('pause "now lets create the md5 sums"')
print r'""C:\Progra~1\UnixUtils\md5sum.exe" "../pykeylogger' + version.version + '_src.zip" "../pykeylogger' + version.version + '_win32.zip" > "../pykeylogger' + version.version + '_md5sums.txt""'
os.system(r'""C:\Progra~1\UnixUtils\md5sum.exe" "../pykeylogger' + version.version + '_src.zip" "../pykeylogger' + version.version + '_win32.zip" > "../pykeylogger' + version.version + '_md5sums.txt""')

os.system(r'pause "done, press to key to exit""')
