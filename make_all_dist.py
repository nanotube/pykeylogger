import version
import os
import sys

if raw_input("Current version is " + version.version + ". Is that correct? [Y/N] ") in ["y", "Y", "yes", "YES", "Yes"]:
    pass
else:
    sys.exit()

#delete old build dir.
print 'rd /S /Q build'
os.system('rd /S /Q build')

# create the exe 
print 'c:\Python24\python setup.py py2exe -b1'
os.system('c:\Python24\python setup.py py2exe -b1')

#pause to see output
#os.system('pause "done, press key to continue"')
print 'rename "dist" "pykeylogger""'
os.system('rename "dist" "pykeylogger""')

print 'copy ".\*.txt" ".\pykeylogger""'
os.system('copy ".\*.txt" ".\pykeylogger""')

#command = '\"\"C:\Progra~1\WinRAR\WinRAR.exe" a -r "pykeylogger' + version.version + '_win32.zip" "pykeylogger\"\"'
#print repr(command)
#os.system(command)
print '""C:\Progra~1\WinRAR\WinRAR.exe" a -r "pykeylogger' + version.version + '_win32.zip" "pykeylogger""'
os.system('""C:\Progra~1\WinRAR\WinRAR.exe" a -r "pykeylogger' + version.version + '_win32.zip" "pykeylogger""')

print 'mv "./pykeylogger' + version.version + '_win32.zip" "../pykeylogger' + version.version + '_win32.zip"'
os.system('mv "./pykeylogger' + version.version + '_win32.zip" "../pykeylogger' + version.version + '_win32.zip"')

print 'rd /S /Q pykeylogger'
os.system('rd /S /Q pykeylogger')
print 'rd /S /Q build'
os.system('rd /S /Q build')

#os.system('pause "done, now lets create the src dist"')
print '""C:\Progra~1\WinRAR\WinRAR.exe" a -r "pykeylogger' + version.version + '_src.zip" "keylogger.pyw" "logwriter.py" "setup.py" "version.py" "make_all_dist.py" "*.txt" "*.bat" "html""'
os.system('""C:\Progra~1\WinRAR\WinRAR.exe" a -r "pykeylogger' + version.version + '_src.zip" "keylogger.pyw" "logwriter.py" "setup.py" "version.py" "make_all_dist.py" "*.txt" "*.bat" "html""')

print 'mv "./pykeylogger' + version.version + '_src.zip" "../pykeylogger' + version.version + '_src.zip"'
os.system('mv "./pykeylogger' + version.version + '_src.zip" "../pykeylogger' + version.version + '_src.zip"')

#os.system('pause "now lets create the md5 sums"')
print '""C:\Progra~1\UnixUtils\md5sum.exe" "../pykeylogger' + version.version + '_src.zip" "../pykeylogger' + version.version + '_win32.zip" > "../pykeylogger' + version.version + '_md5sums.txt""'
os.system('""C:\Progra~1\UnixUtils\md5sum.exe" "../pykeylogger' + version.version + '_src.zip" "../pykeylogger' + version.version + '_win32.zip" > "../pykeylogger' + version.version + '_md5sums.txt""')

os.system('pause "done, press to key to exit""')
