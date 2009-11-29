# A very simple setup script to create an executable.
#
# Run the build process by entering 'setup.py py2exe' or
# 'python setup.py py2exe' in a console prompt.
#
# If everything works well, you should find a subdirectory named 'dist'
# containing some files, among them keylogger.exe and keylogger_debug.exe.


from distutils.core import setup
import sys

if len(sys.argv) > 1 and sys.argv[1] == 'py2exe':
    import py2exe

import version

setup(
    # The first three parameters are not required, if at least a
    # 'version' is given, then a versioninfo resource is built from
    # them and added to the executables.
    name = version.name,
    version = version.version,
    description = version.description,
    url = version.url,
    license = version.license,
    author = version.author,
    author_email = version.author_email,
    platforms = [version.platform],
    
    # The following doesn't work - for some reason bundling everything into one
    # exe causes the program to crash out on start.
    #~ options = {'py2exe': {'bundle_files': 1}},
    #~ zipfile = None,
    
    data_files = [("",[version.name+".ini",
                        version.name+".val",
                        version.name+"icon.ico",
                        version.name+"icon.svg",
                        version.name+"icon_big.gif",
                        "doc/CHANGELOG.TXT",
                        "doc/LICENSE.txt",
                        "doc/README.txt",
                        "doc/TODO.txt"])],
    # targets to build
    console = [
        {
            "script": "keylogger.pyw",
            "dest_base": version.name+"_debug",
            "icon_resources": [(0, version.name+"icon.ico")]
        }
    ],
    
    windows = [
       {
            "script": "keylogger.pyw",
            "dest_base": version.name,
            "icon_resources": [(0, version.name+"icon.ico")]
       }
    ],
    options={
        "py2exe":{
            "excludes": ["gtk"] # don't need this under windows
        }
    }
    )
