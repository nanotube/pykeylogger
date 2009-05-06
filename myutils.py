import zlib
import base64
import sys
import os.path
import imp
import locale

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
    
