import zlib
import base64
import sys
import os
import os.path
import imp
import locale

# for the OnDemandRotatingFileHandler class
from logging.handlers import BaseRotatingHandler
import time
try:
    import codecs
except ImportError:
    codecs = None

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
        "20090610_234620.app.log.1".
        
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
