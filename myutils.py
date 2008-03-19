import zlib
import base64
import sys
import imp

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
