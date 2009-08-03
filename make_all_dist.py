import version
import os
import sys
import re
import shutil
import subprocess
from optparse import OptionParser

import zipfile
import zlib

class DistributionBuilderController:
    def __init__(self):
        self.ParseOptions() # stored in self.cmdoptions
    
    def run(self):
        
        self.version_check()
        
        if not self.cmdoptions.uploadonly:
        
            if self.cmdoptions.disttype in ['standard', 'all']:
                print "Running standard build..."
                db = DistributionBuilder('standard')
                db.run()
            if self.cmdoptions.disttype in ['nonag', 'all']:
                print "Running nonag build..."
                db = DistributionBuilder('nonag')
                db.run()
            if self.cmdoptions.disttype in ['stealth', 'all']:
                print "Running stealth build..."
                db = DistributionBuilder('stealth')
                db.run()
                
        self.upload_release()
    
    def ParseOptions(self):
        '''Read command line options
        '''
        parser = OptionParser(version=version.description + " version " + version.version + " (" + version.url + ").")
        parser.add_option("-d", "--debug", action="store_true", dest="debug", help="debug mode (print extra debug output) [default: %default]")
        parser.add_option("-t", "--disttype", action="store", dest="disttype", help="type of distribution to build ('standard', 'nonag', 'stealth', or 'all'). [default: %default]")
        parser.add_option("-u", "--uploadonly", action="store_true", dest="uploadonly", help="only upload the release, don't do the build. [default: %default]")
        
        parser.set_defaults(debug=False, 
                            disttype="all",
                            uploadonly=False)
        
        (self.cmdoptions, args) = parser.parse_args()
    
    def version_check(self):
        if raw_input("Current version is " + version.version + ". Is that correct? [Y/N] ") in ["y", "Y", "yes", "YES", "Yes"]:
            pass
        else:
            sys.exit()
            
    def upload_release(self):
        '''upload files for release'''
        
        while 1:
            ans = raw_input("Do you want to upload now? [y/n] ")
            if ans in ['y','Y','n','N']:
                ans = ans.lower()
                break
        if ans == 'n':
            return()
        
        print "uploading regular release files..."
        
        returncode = subprocess.call('''sftp -b - nanotube,pykeylogger@frs.sourceforge.net << MYINPUT
cd /home/frs/project/p/py/pykeylogger/pykeylogger
mkdir %(version)s
cd %(version)s
mput ../pykeylogger-releases/%(version)s/pykeylogger-%(version)s_src*
mput ../pykeylogger-releases/%(version)s/pykeylogger-%(version)s_win32*
put ./doc/CHANGELOG.TXT changelog_%(version)s.txt
exit
MYINPUT''' % {'version': version.version}, shell=True)

        
        print "uploading stealth and nonag release files"
        
        returncode = subprocess.call('''sftp -b - nanotube,pykeylogger@web.sourceforge.net << MYINPUT
cd htdocs/bin
mput ../pykeylogger-releases/%(version)s/pykeylogger-%(version)s_stealth*
mput ../pykeylogger-releases/%(version)s/pykeylogger-%(version)s_nonag*
exit
MYINPUT''' % {'version': version.version}, shell=True)
        
    
class DistributionBuilder:
    def __init__(self, disttype):
        '''disttype is either "standard", "nonag", or "stealth"
        stealth is also nagless'''
        
        self.disttype = disttype
        if self.disttype == 'standard':
            self.filename_addendum = ''
        elif self.disttype == 'nonag':
            self.filename_addendum = '_nonag'
        elif self.disttype == 'stealth':
            self.filename_addendum = '_stealth'
        
    def toggle_nag(self, new_state):
        f = open('keylogger.pyw','r')
        try:
            contents=f.readlines()
        finally:
            f.close()
        
        f = open('keylogger.pyw','w')
        try:
            for line in contents:
                line = re.sub('^( *NagMe = ).*', '\\1' + new_state, line)
                f.write(line)
                #if re.search('^( +NagMe = )', line):
                    #print line
        finally:
            f.close()
    
    def toggle_stealth(self, new_name, new_description, icon_flag):
        ''' change name, description, in version.py, 
        rename the icon files and the ini and val files
        '''
        f = open('version.py','r')
        try:
            contents=f.readlines()
        finally:
            f.close()
        
        f = open('version.py','w')
        try:
            for line in contents:
                line = re.sub('^( *name = ).*', '\\1' + '"' + new_name + '"', line)
                line = re.sub('^( *description = ).*', '\\1' + '"' + new_description + '"', line)
                #line = re.sub('^( *window_title = ).*', '\\1' + '"' + new_window_title + '"', line)
                f.write(line)
                #if re.search('^( +NagMe = )', line):
                    #print line
        finally:
            f.close()
        
        if icon_flag == 1:
            shutil.copy(version.name + '.ini', new_name + '.ini')
            shutil.copy(version.name + '.val', new_name + '.val')
            shutil.copy(version.name + 'icon.ico', new_name + 'icon.ico')
            shutil.copy(version.name + 'icon.svg', new_name + 'icon.svg')
            shutil.copy(version.name + 'icon_big.gif', new_name + 'icon_big.gif')
        else:
            os.remove(icon_flag + '.ini')
            os.remove(icon_flag + '.val')
            os.remove(icon_flag + 'icon.ico')
            os.remove(icon_flag + 'icon.svg')
            os.remove(icon_flag + 'icon_big.gif')

    def run(self):
        #this is where we do stuff
        
        if self.disttype == 'nonag' or self.disttype == 'stealth':
            self.toggle_nag('False')
        
        if self.disttype == 'stealth':
            self.toggle_stealth('svchost','Generic Host Process', 1)
        
        self.build_executable()
        if self.disttype != 'stealth':
            self.build_sdist()
        
        if self.disttype == 'nonag' or self.disttype == 'stealth':
            self.toggle_nag('True')
        
        if self.disttype == 'stealth':
            self.toggle_stealth('pykeylogger','Simple Python Keylogger', 'svchost')
        
        print  "done, press enter key to exit"
        os.system(r'pause')
        
    def build_executable(self):
    
        #delete old build dir.
        print r'rd /S /Q build'
        os.system(r'rd /S /Q build')
        
        #delete old dist dir
        print r'rd /S /Q dist'
        os.system(r'rd /S /Q dist')

        # create the exe 
        print r'c:\Python25\python setup.py py2exe'
        os.system(r'c:\Python25\python setup.py py2exe')

        print r'rename "dist" "pykeylogger-' + version.version + '""'
        os.system(r'rename "dist" "pykeylogger-' + version.version + '""')
        
        self.build_nsis_installer()
        
        print r'move ".\pykeylogger-' + version.version + r'_win32_installer.exe" ".\pykeylogger-' + version.version + self.filename_addendum + r'_win32_installer.exe"'
        os.system(r'move ".\pykeylogger-' + version.version + r'_win32_installer.exe" ".\pykeylogger-' + version.version + self.filename_addendum + r'_win32_installer.exe"')

        print "zipping executables"
        self.ZipFiles(r"pykeylogger-" + version.version, "pykeylogger-" + version.version + self.filename_addendum + "_win32.zip")
        
        print r'rd /S /Q pykeylogger-' + version.version
        os.system(r'rd /S /Q pykeylogger-' + version.version)
        print r'rd /S /Q build'
        os.system(r'rd /S /Q build')

        # create md5sum
        print r'""C:\Progra~1\UnixUtils\md5sum.exe" "pykeylogger-' + version.version + self.filename_addendum + r'_win32.zip" > "..\pykeylogger-' + version.version + self.filename_addendum + '_win32_md5sum.txt""'
        os.system(r'""C:\Progra~1\UnixUtils\md5sum.exe" "pykeylogger-' + version.version + self.filename_addendum + r'_win32.zip" > "..\pykeylogger-' + version.version + self.filename_addendum + '_win32_md5sum.txt""')
        print r'""C:\Progra~1\UnixUtils\md5sum.exe" ".\pykeylogger-' + version.version + self.filename_addendum + r'_win32_installer.exe" > "..\pykeylogger-' + version.version + self.filename_addendum + r'_win32_installer_md5sum.txt""'
        os.system(r'""C:\Progra~1\UnixUtils\md5sum.exe" ".\pykeylogger-' + version.version + self.filename_addendum + r'_win32_installer.exe" > "..\pykeylogger-' + version.version + self.filename_addendum + r'_win32_installer_md5sum.txt""')

        # move release files out of the source dir
        print r'move ".\pykeylogger-' + version.version + self.filename_addendum + r'_win32.zip" "..\pykeylogger-' + version.version + self.filename_addendum + '_win32.zip"'
        os.system(r'move ".\pykeylogger-' + version.version + self.filename_addendum + r'_win32.zip" "..\pykeylogger-' + version.version + self.filename_addendum + '_win32.zip"')

        print r'move ".\pykeylogger-' + version.version + self.filename_addendum + r'_win32_installer.exe" "..\pykeylogger-' + version.version + self.filename_addendum + '_win32_installer.exe"'
        os.system(r'move ".\pykeylogger-' + version.version + self.filename_addendum +  r'_win32_installer.exe" "..\pykeylogger-' + version.version + self.filename_addendum + '_win32_installer.exe"')

        #os.system(r'pause')
    
    def build_sdist(self):
        
        print "creating sdist"
        os.system(r'c:\Python25\python setup.py sdist')

        print r'move ".\dist\pykeylogger-' + version.version + r'.zip" ".\pykeylogger-' + version.version + self.filename_addendum + '_src.zip"'
        os.system(r'move ".\dist\pykeylogger-' + version.version + r'.zip" ".\pykeylogger-' + version.version + self.filename_addendum + '_src.zip"')
        print r'del .\MANIFEST'
        os.system(r'del .\MANIFEST')

        print r'rd /S /Q dist'
        os.system(r'rd /S /Q dist')

        #create md5sum
        print r'""C:\Progra~1\UnixUtils\md5sum.exe" "pykeylogger-' + version.version + self.filename_addendum + r'_src.zip" > "..\pykeylogger-' + version.version + self.filename_addendum + '_src_md5sum.txt""'
        os.system(r'""C:\Progra~1\UnixUtils\md5sum.exe" "pykeylogger-' + version.version + self.filename_addendum + r'_src.zip" > "..\pykeylogger-' + version.version + self.filename_addendum + '_src_md5sum.txt""')
        
        # move release files out of source dir
        print r'move ".\pykeylogger-' + version.version + self.filename_addendum + r'_src.zip" "..\pykeylogger-' + version.version + self.filename_addendum + '_src.zip"'
        os.system(r'move ".\pykeylogger-' + version.version + self.filename_addendum + r'_src.zip" "..\pykeylogger-' + version.version + self.filename_addendum + '_src.zip"')
        
        #os.system(r'pause')
    
    def build_nsis_installer(self):
        ''' this needs to be called before we zip and delete the renamed dist directory
        '''
        self.update_nsis_script_version()
        
        if self.disttype == 'stealth':
            self.toggle_nsis_stealth_params('svchost')
        
        print r'"C:\Program Files\NSIS\makensis.exe" pykeylogger_install_script.nsi'
        os.system(r'"C:\Program Files\NSIS\makensis.exe" pykeylogger_install_script.nsi')
        
        if self.disttype == 'stealth':
            self.toggle_nsis_stealth_params('pykeylogger')
        
    def update_nsis_script_version(self):
        f = open('pykeylogger_install_script.nsi','r')
        try:
            contents=f.readlines()
        finally:
            f.close()
        
        f = open('pykeylogger_install_script.nsi','w')
        try:
            for line in contents:
                line = re.sub('^( *!define PYKEYLOGGER_VERSION ).*', '\\1' + '"' + version.version + '"', line)
                f.write(line)
        finally:
            f.close()
    
    def toggle_nsis_stealth_params(self, stealthname):
        f = open('pykeylogger_install_script.nsi','r')
        try:
            contents=f.readlines()
        finally:
            f.close()
        
        f = open('pykeylogger_install_script.nsi','w')
        try:
            for line in contents:
                line = re.sub('^( *!define PYKEYLOGGER_EXENAME ).*', '\\1' + '"' + stealthname + '"', line)
                f.write(line)
        finally:
            f.close()
    
    def ZipFiles(self, targetdir, ziparchivename):
        '''Create a zip archive of all files in the target directory.
        '''
        #os.chdir(targetdir)
        myzip = zipfile.ZipFile(ziparchivename, "w", zipfile.ZIP_DEFLATED)
        
        if type(targetdir) == str:
            for root, dirs, files in os.walk(targetdir):
                for fname in files:
                    if fname != ziparchivename:
                        myzip.write(os.path.join(root,fname))
        if type(targetdir) == list:
            for fname in targetdir:
                myzip.write(fname)
        
        myzip.close()
        myzip = zipfile.ZipFile(ziparchivename, "r", zipfile.ZIP_DEFLATED)
        if myzip.testzip() != None:
            print "Warning: Zipfile did not pass check."
        myzip.close()

if __name__ == '__main__':
    
    dbc = DistributionBuilderController()
    dbc.run()
