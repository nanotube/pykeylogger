##############################################################################
##
## PyKeylogger: Simple Python Keylogger for Windows
## Copyright (C) 2009  nanotube@users.sf.net
##
## http://pykeylogger.sourceforge.net/
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License
## as published by the Free Software Foundation; either version 3
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.
##
##############################################################################

import zlib
import base64
import sys
import os
import os.path
import imp
import locale
from validate import ValidateError, VdtValueError
import re

# for the OnDemandRotatingFileHandler class
from logging.handlers import BaseRotatingHandler
import time
try:
    import codecs
except ImportError:
    codecs = None

# used to store the settings dict and make it globally accessible.
_settings = {}
# used to store the cmdoptions dict and make it globally accessible.
_cmdoptions = {}
# used to store a reference to the main thread and make it globally 
# accessible
_mainapp = {}

def password_obfuscate(password):
    return base64.b64encode(zlib.compress(password))
def password_recover(password):
    return zlib.decompress(base64.b64decode(password))

# the following two functions are from the py2exe wiki:
# http://www.py2exe.org/index.cgi/HowToDetermineIfRunningFromExe
def main_is_frozen():
    return (hasattr(sys, "frozen") or # new py2exe
            hasattr(sys, "importers") or # old py2exe
            imp.is_frozen("__main__")) # tools/freeze

def get_main_dir():
    if main_is_frozen():
        return os.path.dirname(sys.executable)
    #return os.path.dirname(sys.argv[0])
    return sys.path[0]

def to_unicode(x):
    """Try to convert the input to utf-8."""
    
    # return empty string if input is None
    if x is None:
        return ''
    
    # if this is not a string, let's try converting it
    if not isinstance(x, basestring):
        x = str(x)
        
    # if this is a unicode string, encode it and return
    if isinstance(x, unicode):
        return x.encode('utf-8')
    
    # now try a bunch of likely encodings
    encoding = locale.getpreferredencoding()
    try:
        ret = x.decode(encoding).encode('utf-8')
    except UnicodeError:
        try:
            ret = x.decode('utf-8').encode('utf-8')
        except UnicodeError:
            try:
                ret = x.decode('latin-1').encode('utf-8')
            except UnicodeError:
                ret = x.decode('utf-8', 'replace').encode('utf-8')
    return ret

class VdtValueDetailError(ValidateError):
    def __init__(self, value, reason):
        ValidateError.__init__(self, "the value '%s' is unacceptable.\n"
                "Reason: %s" % (value, reason))
    

def validate_log_filename(value):
    '''Check for logfile naming restrictions.
    
    These restrictions are in place to avoid conflicts with internal
    file operations.
    
    Log filenames cannot:
    * End in '.zip'
    * Start with '_internal_'
    
    This function gets plugged into an instance of validate.Validator.
    '''
    if not value.startswith('_internal_') and \
            not value.endswith('.zip'):
        return value
    else:
        raise VdtValueDetailError(value, 
                "filename cannot end in '.zip' or start with '_internal_'")

def validate_image_filename(value):
    '''Check for logfile naming restrictions.
    
    These restrictions are in place to avoid conflicts with internal
    file operations and ensure unique click image filenames.
    
    Image filenames:
    * Cannot start with '_internal_'
    * Must contain %time% variable somewhere.
    
    This function gets plugged into an instance of validate.Validator.
    '''
    if not value.startswith('_internal_') and \
            re.search(r'%time%', value):
        return value
    else:
        raise VdtValueDetailError(value, 
                "filename cannot start with '_internal_' and must contain "
                "'%time%' to ensure uniqueness")

class OnDemandRotatingFileHandler(BaseRotatingHandler):
    '''Handler which allows the rotating of the logfile on demand.
    
    Old logs are renamed with a datetime prefix.
    '''
    
    def __init__(self, filename, mode='a', 
                timestring_format="%Y%m%d_%H%M%S", prefix=True, encoding=None):
        '''Open the specified file and use it as the stream for logging.

        File grows indefinitely, until rollover is called.

        A rollover will close the stream; rename the file to a new name, 
        with a prefix or suffix (prefix if prameter prefix=True)
        to the filename of the current date and time, in the format specified 
        by timestring_format; and open a fresh log file.
        
        For example, with a base file name of "app.log", and other arguments 
        as default, a rolled-over logfile might have a name of
        "20090610_234620.app.log".
        
        The file being written to is always "app.log".
        
        timestring_format is a format string, as described for time.strftime().
        '''
        BaseRotatingHandler.__init__(self, filename, mode, encoding)
        self.timestring_format = timestring_format
        self.prefix = prefix

    def doRollover(self):
        '''Do a rollover, as described in __init__().'''
        
        dirname, filename = os.path.split(self.baseFilename)
        if self.prefix:
            new_filename = time.strftime(self.timestring_format) + \
                            '.' + filename
        else:
            new_filename = filename + '.' + \
                            time.strftime(self.timestring_format)
        newpath = os.path.join(dirname, new_filename)
        
        self.acquire()
        try:
            self.stream.close()
            os.rename(self.baseFilename, newpath)
            if self.encoding:
                self.stream = codecs.open(self.baseFilename, 'w', 
                                            self.encoding)
            else:
                self.stream = open(self.baseFilename, 'w')
        finally:
            self.release()
    
    def shouldRollover(self, record):
        '''Always return 0, since all rollovers are on demand.
        
        This method is here just for compatibility with the 
        BaseRotatingHandler class definition.
        '''
        return 0

    
