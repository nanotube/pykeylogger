##############################################################################
##
## PyKeylogger: Simple Python Keylogger for Windows
## Copyright (C) 2009  nanotube@users.sf.net
##
## http://pykeylogger.sourceforge.net/
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License
## as published by the Free Software Foundation; either version 3
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.
##
##############################################################################

from Tkinter import *
import webbrowser
import tkSimpleDialog
import ScrolledText
import version

BASE_SF_URL = "http://pykeylogger.sourceforge.net"

class SupportScreen(tkSimpleDialog.Dialog):
    
    def __init__(self, parent, title = None):
        tkSimpleDialog.Dialog.__init__(self, parent, title)

    def body(self, master):
        self.t = ScrolledText.ScrolledText(master)
        self.t['font'] = 'arial 10'
        self.t.pack()
        self.t.tag_configure("href", foreground='blue', underline=1)
        self.t.tag_bind("href", "<Button-1>", self.openHREF)
        self.t.tag_bind("href", "<Enter>", self.show_hand_cursor)
        self.t.tag_bind("href", "<Leave>", self.show_arrow_cursor)
        self.t.config(cursor="arrow", bg="white", wrap=WORD)
        self.t.insert(END,
           "Welcome to PyKeylogger, a versatile backup and system monitoring "
           "solution. \n\n"
           "PyKeylogger is Free Open Source Software, licensed under the "
           "Gnu General Public License. "
           "You can download the source code from ")
        self.t.insert(END,
           "http://sourceforge.net/projects/pykeylogger", "href")
        self.t.insert(END,
           "\n\nHit 'Lcontrol-Rcontrol-F12' to bring up the Control Panel "
           "(default password is blank). More help is in the Help menu.\n\n"
           "Since I am but a poor grad student, you are strongly encouraged "
           "to donate to this open source project. So strongly, in fact, that "
           "this program is limited to 4 days of use, and presents you with "
           "this nag screen every time you start it. There is good logic "
           "behind why this is being done. If you are curious, you will find "
           "the following link very informative: ")
        self.t.insert(END, "http://hackvan.com/pub/stig/articles/why-do-people-register-shareware.html", "href")
        self.t.insert(END,
           "\n\nThere are two ways to get rid of the nag and expiration: \n"
           "1. Donate to PyKeylogger by following the simple instructions at ")
        self.t.insert(END, BASE_SF_URL + "/Download_Instructions", "href")
        self.t.insert(END,
           " and you will get a binary build of PyKeylogger without any "
           "nagging, by E-mail, HTTP, or FTP.")
        self.t.insert(END,
           "\n\n 2. Get the project source code, the supporting libraries, "
           "then find and toggle the nag control. You can then run "
           "PyKeylogger from source, or even build your own executable. "
           "Detailed instructions for this approach are available at ")
        self.t.insert(END, BASE_SF_URL + "/Installation_Instructions", "href")
        self.t.insert(END,
           "\n\nFinally, I encourage you to use this software responsibly, "
           "keeping to the law and your own moral code.")
        self.t.config(state=DISABLED)

    def show_hand_cursor(self, event):
        self.t.config(cursor="hand2")
    
    def show_arrow_cursor(self, event):
        self.t.config(cursor="arrow")

    def buttonbox(self):
        """Adds standard button box.
        
           Override if you don't want the standard buttons."""
        
        box = Frame(self)

        #w = Button(box, text="OK", width=10, command=self.ok, default=ACTIVE)
        #w.pack(side=LEFT, padx=5, pady=5)
        w = Button(box, text="Continue", width=10,
                   command=self.cancel, default=ACTIVE)
        w.pack(side=LEFT, padx=5, pady=5)

        self.bind("<Return>", self.cancel)
        self.bind("<Escape>", self.cancel)

        box.pack()

    def openHREF(self, event):
        start, end = self.t.tag_prevrange("href",
           self.t.index("@%s,%s" % (event.x, event.y)))
        #print "Going to %s..." % t.get(start, end)
        webbrowser.open(self.t.get(start, end))


class ExpirationScreen(tkSimpleDialog.Dialog):
    def __init__(self, parent, title = None):
        tkSimpleDialog.Dialog.__init__(self, parent, title)

    def body(self, master):
        self.t = ScrolledText.ScrolledText(master)
        self.t['font'] = 'arial 10'
        self.t.pack()
        self.t.tag_configure("href", foreground='blue', underline=1)
        self.t.tag_bind("href", "<Button-1>", self.openHREF)
        self.t.tag_bind("href", "<Enter>", self.show_hand_cursor)
        self.t.tag_bind("href", "<Leave>", self.show_arrow_cursor)
        self.t.config(cursor="arrow", bg="white", wrap=WORD)
        self.t.insert(END,
           "Thank you for using PyKeylogger, a versatile backup and system "
           "monitoring solution.")
        self.t.insert(END,
           "\n\nAs you may remember from reading the \"welcome screen\", "
           "this binary expires after 4 days of use, as a method of "
           "encouraging donations to this open source software project. "
           "This installation of PyKeylogger has now *EXPIRED*. There are two "
           "ways to restore PyKeylogger's functionality: \n\n "
           "1. Donate to PyKeylogger by following the simple instructions at ")
        self.t.insert(END, BASE_SF_URL + "/Download_Instructions", "href")
        self.t.insert(END,
           " and you will get a binary build of PyKeylogger without any "
           "nagscreens or expiration, by E-mail, HTTP, or FTP.")
        self.t.insert(END,
           "\n\n 2. Get the project source code, the supporting libraries, "
           "then find and toggle the nag control. You can then run "
           "PyKeylogger from source, or even build your own executable. "
           "Detailed instructions for this approach are available at ")
        self.t.insert(END, BASE_SF_URL + "/Installation_Instructions", "href")
        self.t.insert(END,
           "\n\nIf you run into any trouble, feel free to ask for help on the "
           "PyKeylogger forums: ")
        self.t.insert(END,
           "http://sourceforge.net/forum/?group_id=147501", "href")
        self.t.config(state=DISABLED)

    def show_hand_cursor(self, event):
        self.t.config(cursor="hand2")
    
    def show_arrow_cursor(self, event):
        self.t.config(cursor="arrow")

    def buttonbox(self):
        """Adds standard button box.
        
           Override if you don't want the standard buttons."""
        
        box = Frame(self)

        #w = Button(box, text="OK", width=10, command=self.ok, default=ACTIVE)
        #w.pack(side=LEFT, padx=5, pady=5)
        w = Button(box, text="Continue", width=10,
                   command=self.cancel, default=ACTIVE)
        w.pack(side=LEFT, padx=5, pady=5)

        self.bind("<Return>", self.cancel)
        self.bind("<Escape>", self.cancel)

        box.pack()

    def openHREF(self, event):
        start, end = self.t.tag_prevrange("href",
           self.t.index("@%s,%s" % (event.x, event.y)))
        #print "Going to %s..." % t.get(start, end)
        webbrowser.open(self.t.get(start, end))

class AboutDialog(tkSimpleDialog.Dialog):
    def __init__(self, parent, title = None):
        tkSimpleDialog.Dialog.__init__(self, parent, title)

    def body(self, master):
        self.t = ScrolledText.ScrolledText(master)
        self.t['font'] = 'arial 10'
        self.t.pack()
        self.t.tag_configure("href", foreground='blue', underline=1)
        self.t.tag_configure("h1", foreground='black', underline=1,
           font=('Arial', 16, 'bold'))
        self.t.tag_configure("h2", foreground='black', underline=0,
           font=('Arial', 14, 'bold'))
        self.t.tag_configure("h3", foreground='#33CCCC', underline=0,
           font=('Arial', 10, 'bold'))
        self.t.tag_configure("emph", foreground='black', underline=0,
           font=('Arial', 10, 'italic'))
        self.t.tag_bind("href", "<Button-1>", self.openHREF)
        self.t.tag_bind("href", "<Enter>", self.show_hand_cursor)
        self.t.tag_bind("href", "<Leave>", self.show_arrow_cursor)
        self.t.config(cursor="arrow", bg="white", wrap=WORD)
        self.t.insert(END, "PyKeylogger - Simple Python Keylogger", "h1")
        self.t.insert(END, "\nVersion " + version.version + "\n")
        self.t.insert(END,
           "  by " + version.author + " <" + version.author_email + ">",
           "emph")
        self.t.insert(END, "\n\nLicense: " + version.license + ", ")
        self.t.insert(END, "http://www.gnu.org/copyleft/gpl.html", "href")
        self.t.insert(END, "\n\nProject site: ")
        self.t.insert(END, version.url, "href")
        self.t.insert(END, "\n\nContributors", "h2")
        self.t.insert(END, "\n\nTim Alexander <dragonfyre13@gmail.com>", "h3")
        self.t.insert(END,
           "\nThe initial implementation of event hooking and image capture "
           "on click under GNU/Linux, using the python-xlib library.")
        self.t.insert(END, "\n\nSupporting Libraries:", "h2")
        self.t.insert(END, "\n\nPython, ")
        self.t.insert(END, "http://www.python.org", "href")
        self.t.insert(END, "\nPython Imaging Library (PIL), ")
        self.t.insert(END, "http://www.pythonware.com/products/pil/", "href")
        self.t.insert(END, "\npy2exe, ")
        self.t.insert(END, "http://www.py2exe.org/", "href")
        self.t.insert(END, "\nConfigObj, ")
        self.t.insert(END,
           "http://www.voidspace.org.uk/python/configobj.html", "href")
        self.t.insert(END, "\nPyHook, ")
        self.t.insert(END, "http://sourceforge.net/projects/uncassist", "href")
        self.t.insert(END, "\nPython for Windows Extensions (PyWin32), ")
        self.t.insert(END, "http://sourceforge.net/projects/pywin32/", "href")
        self.t.insert(END, "\npython-xlib, ")
        self.t.insert(END, "http://python-xlib.sourceforge.net/", "href")
        self.t.insert(END,
           "\n\nA big thank you goes out to all of the people behind these "
           "numerous software packages that make PyKeylogger possible!")

        self.t.config(state=DISABLED)

    def show_hand_cursor(self, event):
        self.t.config(cursor="hand2")
    
    def show_arrow_cursor(self, event):
        self.t.config(cursor="arrow")

    def buttonbox(self):
        """Adds standard button box.
        
           Override if you don't want the standard buttons."""
        
        box = Frame(self)

        #w = Button(box, text="OK", width=10, command=self.ok, default=ACTIVE)
        #w.pack(side=LEFT, padx=5, pady=5)
        w = Button(box, text="Continue", width=10,
                   command=self.cancel, default=ACTIVE)
        w.pack(side=LEFT, padx=5, pady=5)

        self.bind("<Return>", self.cancel)
        self.bind("<Escape>", self.cancel)

        box.pack()

    def openHREF(self, event):
        start, end = self.t.tag_prevrange("href",
           self.t.index("@%s,%s" % (event.x, event.y)))
        #print "Going to %s..." % t.get(start, end)
        webbrowser.open(self.t.get(start, end))


if __name__ == '__main__':
    # test code
    root=Tk()
    root.withdraw()
    warn=SupportScreen(root, title="Please Support PyKeylogger")
    root.quit()
    root.destroy()
    
    root=Tk()
    root.withdraw()
    warn=ExpirationScreen(root, title="PyKeylogger Has Expired")
    root.quit()
    root.destroy()
    
    root=Tk()
    root.withdraw()
    warn=AboutDialog(root, title="About PyKeylogger")
    root.quit()
    root.destroy()
