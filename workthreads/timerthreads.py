from threading import Thread, Event
import logging
import time
import re

class BaseTimerClass(Thread):
    '''This is the base class for timer (delay) based threads.
    
    Timer-based threads are ones that do not need to be looking at
    keyboard-mouse events to do their job.
    '''
    def __init__(self, settings, cmdoptions, mainthread, *args, **kwargs):
        Thread.__init__(self)
        self.finished = Event()
        
        self.settings = settings # settings dict
        self.cmdoptions = cmdoptions # cli options dict
        self.mainthread = mainthread # reference to main thread
        self.args = args # arguments, if any, to pass to task_function
        self.kwargs = kwargs # keyword args, if any, to pass to task_function
        
        self.interval = None # set this in derived class
        
    def cancel(self):
        '''Stop the iteration'''
        self.finished.set()
    
    def task_function(self):
        '''to be overridden by derived classes'''
        pass
    
    def run(self):
        while not self.finished.isSet():
            self.finished.wait(self.interval)
            if not self.finished.isSet():
                self.task_function(*self.args, **self.kwargs)
                
        self.finished.set() # just in case :)

        
class LogRotator(BaseTimerClass):
    '''This rotates the logfiles for the specified loggers.
    
    This is also one of the simplest time-based worker threads, so would
    serve as a good example if you want to write your own.
    '''
    
    def __init__(self, *args, **kwargs):
        '''Takes an extra argument: loggers_to_rotate, a list names.'''
        BaseTimerClass.__init__(self, *args, **kwargs)
        
        self.interval = \
            float(self.settings['Log Maintenance']['Log Rotation Interval'])*60*60
        
        self.task_function = self.rotate_logs

    def rotate_logs(self, loggers_to_rotate):
        
        for loggername in loggers_to_rotate:
            logger = logging.getLogger(loggername)
            for handler in logger.handlers:
                try:
                    handler.doRollover()
                except AttributeError:
                    logging.getLogger('').debug("Logger %s, handler %r, "
                        "is not capable of rollover." % (loggername, handler))

        
class LogFlusher(BaseTimerClass):
    '''Flushes the logfile write buffers to disk for the specified loggers.'''
    def __init__(self, *args, **kwargs):
        '''Takes two extra arguments: list of logger names to flush, and
        log message string.'''
        BaseTimerClass.__init__(self, *args, **kwargs)
        
        self.interval = self.settings['Log Maintenance']['Flush Interval']
        
        self.task_function = self.flush_log_write_buffer
        
    def flush_log_write_buffer(self, loggers_to_flush, 
            log_message="Logger %s: flushing file write buffers with timer."):
        '''Flushes all relevant log buffers.
        
        log_message must contain one string format placeholder '%s'
        to take the logger name. See default argument value for an example.
        This string is customizable so that manual flushing can use a 
        different message.
        '''
        for loggername in loggers_to_flush:
            logger = logging.getLogger(loggername)
            logging.getLogger('').debug("Logger %s: flushing file write "
                        "buffers due to timer." % loggername)
            for handler in logger.handlers:
                handler.flush()

class OldLogDeleter(BaseTimerClass):
    '''Deletes old logs.
    
    Walks the log directory tree and removes old logfiles.

    Age of logs to delete is specified in .ini file settings.
    '''
    def __init__(self, *args, **kwargs):
        '''Takes an extra argument: list of base log names work on.'''
        BaseTimerClass.__init__(self, *args, **kwargs)
        
        self.interval = float(self.settings['Log Maintenance']['Age Check Interval'])*60*60
        
        self.task_function = self.delete_old_logs

    def delete_old_logs(self, list_of_filenames):
        logdir = self.settings['General']['Log Directory']
        max_log_age = float(self.settings['Log Maintenance']['Max Log Age'])*24*60*60
        filename_re = re.compile(r'(' + r'|'.join(list_of_filenames) + r')')
        for dirpath, dirnames, filenames in os.walk(logdir):
            for fname in filenames:
                if filename_re.search(fname):
                    filepath = os.path.join(dirpath, fname)
                    testvalue = time.time() - os.path.getmtime(filepath) > max_log_age
                
                if testvalue:
                    try:
                        os.remove(filepath)
                    except:
                        logging.getLogger('').debug("Error deleting old log "
                        "file: %s" % filepath)


class EmailLogSender(BaseTimerClass):
    '''Send log files by email to address[es] specified in .ini file.
    
    If log zipper is not enabled, we zip things here. Then email out all
    the zips.
    '''
    
    def __init__(self, *args, **kwargs):
        '''Takes an extra argument: list of base log names work on.'''
        BaseTimerClass.__init__(self, *args, **kwargs)
        
        self.interval = float(self.settings['E-mail']['Email Interval'])*60*60
        
        self.task_function = self.send_email

    def send_email(self):
        pass
    
    def SendZipByEmail(self):
        '''Send the zipped logfile archive by email, using mail settings specified in the .ini file
        '''
        # basic logic flow:
        #~ if autozip is not enabled, just call the ziplogfiles function ourselves
        
        #~ read ziplog.txt (in a try block) and check if it conforms to being a proper zip filename
        #~ if not, then print error and get out
        
        #~ in a try block, read emaillog.txt to get latest emailed zip, and check for proper filename
            #~ if fail, just go ahead with sending all available zipfiles
        
        #~ do a os.listdir() on the dirname, and trim it down to only contain our zipfiles
            #~ and moreover, only zipfiles with names between lastemailed and latestzip, including latestzip,
            #~ but not including lastemailed.
        
        #~ send all the files in list
        
        #~ write new lastemailed to emaillog.txt
        
        self.PrintDebug("Sending mail to " + self.settings['E-mail']['SMTP To'] + "\n")
        
        if self.settings['Zip']['Zip Enable'] == False or os.path.isfile(os.path.join(self.settings['General']['Log Directory'], "ziplog.txt")) == False:
            self.ZipLogFiles()
        
        try:
            ziplog = open(os.path.join(self.settings['General']['Log Directory'], "ziplog.txt"), 'r')
            latestZipFile = ziplog.readline()
            ziplog.close()
            if not self.CheckIfZipFile(latestZipFile):
                self.PrintDebug("latest zip filename does not match proper filename pattern. something went wrong. stopping.\n")
                return
        except:
            self.PrintDebug("Unexpected error opening ziplog.txt: " + str(sys.exc_info()[0]) + ", " + str(sys.exc_info()[1]) + "\n")
            return
        
        try:
            latestZipEmailed = "" #initialize to blank, just in case emaillog.txt doesn't get read
            emaillog = open(os.path.join(self.settings['General']['Log Directory'], "emaillog.txt"), 'r')
            latestZipEmailed = emaillog.readline()
            emaillog.close()
            if not self.CheckIfZipFile(latestZipEmailed):
                self.PrintDebug("latest emailed zip filename does not match proper filename pattern. something went wrong. stopping.\n")
                return
        except:
            self.PrintDebug("Error opening emaillog.txt: " + str(sys.exc_info()[0]) + ", " + str(sys.exc_info()[1]) + "\nWill email all available log zips.\n")
        
        zipFileList = os.listdir(self.settings['General']['Log Directory'])
        self.PrintDebug(str(zipFileList))
        if len(zipFileList) > 0:
            # removing elements from a list while iterating over it produces undesirable results
            # so we do the os.listdir again to iterate over
            for filename in os.listdir(self.settings['General']['Log Directory']):
                if not self.CheckIfZipFile(filename):
                    zipFileList.remove(filename)
                    self.PrintDebug("removing " + filename + " from zipfilelist because it's not a zipfile\n")
                # we can do the following string comparison due to the structured and dated format of the filenames
                elif filename <= latestZipEmailed or filename > latestZipFile:
                    zipFileList.remove(filename)
                    self.PrintDebug("removing " + filename + " from zipfilelist because it's not in range\n")
        
        self.PrintDebug(str(zipFileList))
        
        # set up the message
        msg = MIMEMultipart()
        msg['From'] = self.settings['E-mail']['SMTP From']
        msg['To'] = COMMASPACE.join(self.settings['E-mail']['SMTP To'].split(";"))
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = self.settings['E-mail']['SMTP Subject']

        msg.attach( MIMEText(self.settings['E-mail']['SMTP Message Body']) )

        if len(zipFileList) == 0:
            msg.attach( MIMEText("No new logs present.") )

        if len(zipFileList) > 0:
            for file in zipFileList:
                part = MIMEBase('application', "octet-stream")
                part.set_payload( open(os.path.join(self.settings['General']['Log Directory'], file),"rb").read() )
                Encoders.encode_base64(part)
                part.add_header('Content-Disposition', 'attachment; filename="%s"'
                               % os.path.basename(file))
                msg.attach(part)

        # set up the server and send the message
        # wrap it all in a try/except, so that everything doesn't hang up
        # in case of network problems and whatnot.
        try:
            mysmtp = smtplib.SMTP(self.settings['E-mail']['SMTP Server'], self.settings['E-mail']['SMTP Port'])
            
            if self.cmdoptions.debug: 
                mysmtp.set_debuglevel(1)
            if self.settings['E-mail']['SMTP Use TLS'] == True:
                # we find that we need to use two ehlos (one before and one after starttls)
                # otherwise we get "SMTPException: SMTP AUTH extension not supported by server"
                # thanks for this solution go to http://forums.belution.com/en/python/000/009/17.shtml
                mysmtp.ehlo()
                mysmtp.starttls()
                mysmtp.ehlo()
            if self.settings['E-mail']['SMTP Needs Login'] == True:
                mysmtp.login(self.settings['E-mail']['SMTP Username'], myutils.password_recover(self.settings['E-mail']['SMTP Password']))
            sendingresults = mysmtp.sendmail(self.settings['E-mail']['SMTP From'], self.settings['E-mail']['SMTP To'].split(";"), msg.as_string())
            self.PrintDebug("Email sending errors (if any): " + str(sendingresults) + "\n")
            
            # need to put the quit in a try, since TLS connections may error out due to bad implementation with
            # socket.sslerror: (8, 'EOF occurred in violation of protocol')
            # Most SSL servers and clients (primarily HTTP, but some SMTP as well) are broken in this regard: 
            # they do not properly negotiate TLS connection shutdown. This error is otherwise harmless.
            # reference URLs:
            # http://groups.google.de/group/comp.lang.python/msg/252b421a7d9ff037
            # http://mail.python.org/pipermail/python-list/2005-August/338280.html
            try:
                mysmtp.quit()
            except:
                pass
            
            # write the latest emailed zip to log for the future
            if len(zipFileList) > 0:
                zipFileList.sort()
                emaillog = open(os.path.join(self.settings['General']['Log Directory'], "emaillog.txt"), 'w')
                emaillog.write(zipFileList.pop())
                emaillog.close()
        except:
            self.PrintDebug('Error sending email.', exc_info=True)
            pass # better luck next time


        
if __name__ == '__main__':
    # some basic testing code
    class TestTimerClass(BaseTimerClass):
        def __init__(self, *args, **kwargs):
            BaseTimerClass.__init__(self, *args, **kwargs)
            self.interval = 1
            
            self.task_function = self.print_hello
        
        def print_hello(self, name='bob', *args):
            print "hello, %s" % name
            print args
            
    ttc = TestTimerClass('some stuff','more stuff','even more stuff', 'myname', 'some other name')
    ttc.start()
    time.sleep(5)
    ttc.cancel()

    ttc = TestTimerClass('some stuff','more stuff','even more stuff')
    ttc.start()
    time.sleep(5)
    ttc.cancel()
