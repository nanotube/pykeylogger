from optparse import OptionParser

class LogParser:
    def __init__(self):
        self.ParseOptions()
        
        self.log = open(self.options.filename, 'rU')
        
        #print repr(self.log.newlines)
        self.ParseLog()
        
    def ParseLog(self):
        
        #while (self.line != ''):
        #    self.line = self.log.readline()
        self.line = self.log.readlines()
        print self.line[0:2]
        print repr(self.log.newlines)
        
    def ParseOptions(self):
        parser = OptionParser(version="%prog version 0.3")
        parser.add_option("-f", "--file", action="store", dest="filename", help="read log data from FILENAME [default: %default]")
        parser.add_option("-b", "--parsebackspace", action="store_true", dest="parseBackspace", help="translate backspaces into deleted characters")
        parser.add_option("-e", "--parsedelete", action="store_true", dest="parseDelete", help="translate delete characters and arrow keys into deleted characters")
        parser.add_option("-a", "--parsearrows", action="store_true", dest="parseArrows", help="take into account arrows and home/end")
        parser.add_option("-d", "--debug", action="store_true", dest="debug", help="debug mode (print output to console instead of the log file)")
                  
        parser.set_defaults(filename="C:\Temp\log.txt",
                            parseBackspace=True,
                            parseDelete=False,
                            parseArrows=False,
                            debug=False)

        (self.options, args) = parser.parse_args()

if __name__ == '__main__':
    lp = LogParser()