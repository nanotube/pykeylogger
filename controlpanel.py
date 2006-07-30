from Tkinter import *
import tkSimpleDialog, tkMessageBox
import ConfigParser
from tooltip import ToolTip

class PyKeyloggerControlPanel:
    def __init__(self, settings, mainapp):
        self.mainapp=mainapp
        self.settings=settings
        self.root = Tk()
        #self.root.config(height=20, width=20)
        #self.root.iconify()
        self.PasswordDialog()
        self.root.title("PyKeylogger Control Panel")
        # call the password authentication widget
        # if password match, then create the main panel
        self.InitializeMainPanel()
        self.root.mainloop()
        
    def InitializeMainPanel(self):
        #create the main panel window
        #root = Tk()
        #root.title("PyKeylogger Control Panel")
        # create a menu
        menu = Menu(self.root)
        self.root.config(menu=menu)

        actionmenu = Menu(menu)
        menu.add_cascade(label="Actions", menu=actionmenu)
        actionmenu.add_command(label="Flush write buffers", command=Command(self.mainapp.lw.FlushLogWriteBuffers, "Flushing write buffers at command from control panel."))
        actionmenu.add_command(label="Zip Logs", command=Command(self.mainapp.lw.ZipLogFiles))
        actionmenu.add_command(label="Send logs by email", command=Command(self.mainapp.lw.SendZipByEmail))
        actionmenu.add_command(label="Upload logs by FTP", command=self.callback) #do not have this method yet
        actionmenu.add_command(label="Upload logs by SFTP", command=self.callback) # do not have this method yet
        actionmenu.add_command(label="Delete logs older than " + self.settings['maxlogage'] + " days", command=Command(self.mainapp.lw.DeleteOldLogs))
        actionmenu.add_separator()
        actionmenu.add_command(label="Close Control Panel", command=self.root.destroy)
        actionmenu.add_command(label="Quit PyKeylogger", command=self.mainapp.stop)

        optionsmenu = Menu(menu)
        menu.add_cascade(label="Configuration", menu=optionsmenu)
        optionsmenu.add_command(label="General Settings", command=Command(self.CreateConfigPanel, "general"))
        optionsmenu.add_command(label="Email Settings", command=Command(self.CreateConfigPanel, "email"))
        optionsmenu.add_command(label="FTP Settings", command=Command(self.CreateConfigPanel, "ftp"))
        optionsmenu.add_command(label="SFTP Settings", command=Command(self.CreateConfigPanel, "sftp"))
        optionsmenu.add_command(label="Log Maintenance Settings", command=Command(self.CreateConfigPanel, "logmaintenance"))
        optionsmenu.add_command(label="Timestamp Settings", command=Command(self.CreateConfigPanel, "timestamp"))

        #self.root.mainloop()
        
    def PasswordDialog(self):
        #passroot=Tk()
        #passroot.title("Enter Password")
        mypassword = tkSimpleDialog.askstring("Enter Password", "enter it:", show="*")

    def callback(self):
        tkMessageBox.showwarning(title="Not Implemented", message="This feature has not yet been implemented")
        
    def CreateConfigPanel(self, section="general"):
        self.panelconfig = ConfigParser.SafeConfigParser()
        self.panelconfig.readfp(open(self.settings['configfile']))
        self.panelsettings = dict(self.panelconfig.items(section))
        self.configpanel = ConfigPanel(self.root, title=section + " settings", settings=self.panelsettings)
        # now we dump all this in a frame in root window in a grid

class ConfigPanel(tkSimpleDialog.Dialog):

    def __init__(self, parent, title=None, settings={}):
        self.settings=settings
        tkSimpleDialog.Dialog.__init__(self, parent, title)

    def body(self, master):
        
        index=0
        self.entrydict=dict()
        self.tooltipdict=dict()
        for key in self.settings.keys():
            if key.find("tooltip") == -1:
                Label(master, text=key).grid(row=index, sticky=W)
                self.entrydict[key]=Entry(master)
                self.entrydict[key].insert(END, self.settings[key])
                self.entrydict[key].grid(row=index, column=1)
                self.tooltipdict[key] = ToolTip(self.entrydict[key], follow_mouse=1, delay=500, text=self.settings[key + "tooltip"])
                index += 1
            
        
    
    def apply(self):
        pass
    #~ def __init__(self):
        #~ # create app window with sensitive data settings
        #~ # general password
        #~ # smtpusername
        #~ # smtppassword
        #~ # ftpusername
        #~ # ftppassword
        #~ # sftpusername
        #~ # sftppassword
        #~ pass

class Command:
    ''' A class we can use to avoid using the tricky "Lambda" expression.
    "Python and Tkinter Programming" by John Grayson, introduces this
    idiom.
    
    Thanks to http://mail.python.org/pipermail/tutor/2001-April/004787.html
    for this tip.'''

    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __call__(self):
        apply(self.func, self.args, self.kwargs)

if __name__ == '__main__':
    # some simple testing code
    settings={"bla":"mu", 'maxlogage': "2.0", "configfile":"pykeylogger.ini"}
    class BlankKeylogger:
        def stop(self):
            pass
        def __init__(self):
            self.lw=BlankLogWriter()
            
    class BlankLogWriter:
        def FlushLogWriteBuffers(self, message):
            pass
        def ZipLogFiles(self):
            pass
        def SendZipByEmail(self):
            pass
        def DeleteOldLogs(self):
            pass
        
    klobject=BlankKeylogger()
    myapp = PyKeyloggerControlPanel(settings, klobject)