# standard libraries
from socket import *
from select import *
from string import *
import sys
from getopt import getopt, GetoptError

# nonstandard library
import serial


#print usage, then exit
def usage():
    usagestring = """    tcp2Serial is a tcp server that listen on a tcp port and waiting for a client request. 
    It get's request from a client and forward incoming request to a serial port

Serial Options:
    -p   :  TCP port number that server listen on this port.
    -s   :  Specify serial port name.
            (0 for COM1, 1 for COM2 etc)
    -b   :  serial port baud rate.
    -f   :  Specify flow-control options

General Options:
    -h   :  Display this help messsage

"""
    print(usagestring)
    sys.exit(0)



#Function cleans up telnet's output for input into the serial port.
#Telnet is fancier than serial, so we have to strip some things out.
def cleanup_for_serial(text):
    
    #chr(255) is the "we are negotiating" leading bit.  If it is the first bit in
    #a packet, we do not want to send it on to the serial port
    if ord(text[:1]) == 255:
        return 

    #For some reason, windows likes to send "cr/lf" when you send a "cr".
    #Strip that so we don't get a double prompt.\
    text = replace(text, chr(13) + chr(10), chr(13))

    
    return text

#A connection is a class that forwards requests between TCP and Serial
class Connection:

    def __init__(self, socket, com):
        self.socket = socket
        self.com = com

    #Required, look it up
    def fileno(self):
        return self.socket.fileno()

    #Set up the TCP connection and do telnet negotiation
    def init_tcp(self):

        #telnet negotiation:  we don't want linemode
        data = chr(255) + chr(254) + chr(34)
        self.socket.send(data)

        #telnet negotation:  we don't want local echo
        data = chr(255) + chr(254) + chr(1)
        self.socket.send(data)

        #send the header
        self.socket.send("************************************************\r\n")
        self.socket.send("tcp2serial\r\n")
        self.socket.send("http:for updates       \r\n")
        self.socket.send("\r\n")
        self.socket.send("This program uses non-standard python libraries:\r\n")
        self.socket.send("   - pyserial by Chris Liechti\r\n")
        self.socket.send("   - pywin32 by Mark Hammond (et al)\r\n")
        self.socket.send("\r\n")
        self.socket.send("************************************************\r\n")

        self.socket.send("\r\n")
        self.socket.send("You are now connected to %s.\r\n" % self.com.portstr)
        

    #Receive some data from the telnet client
    def recv_tcp(self):
        data =  self.socket.recv(1024)
        return data


    #Send some data out to the serial port
    def send_serial(self,data):
        data = cleanup_for_serial(data)

        try:
            if ord(data) == 3:
                self.com.sendbreak()
                return
        except:
            pass


        self.com.write(data)


class Handler:
    def __init__(self):
        global port
        global com
        
        self.clist = [ ]
        self.tcpconnected = False
        self.serialconnected = False

        self.start_new_listener()
        
        print("TCP to Serial is up: telnet to localhost:%s to access %s." % (port, com.portstr))
        print("(Control-C to exit)")

    def start_new_listener(self):
        self.listener = socket(AF_INET, SOCK_STREAM)
        self.listener.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.listener.bind(('', port))
        self.listener.listen(32)

    def run(self):

        ready = self.clist[:]

        if self.listener:
            ready.append(self.listener)
            
        ready = select(ready, [], [], 0.1)[0]
        for conn in ready:
            if conn is self.listener:
                socket, address = self.listener.accept()


                global com

                try:
                    com.close()
                    com.open()
                except serial.SerialException:
                    print("Error opening serial port.  Is it in use?")
                    sys.exit(1)
                
                
                conn = Connection(socket, com)
                self.clist.append(conn)

                #set up our initial telnet environment"
                conn.init_tcp()

                #we don't need to listen anymore"
                self.listener = None

            else:
                #pull some data from tcp and send it to serial, if possible."
                data = conn.recv_tcp()
                if not data:
                    print("TCP connection closed.")
                    self.clist.remove(conn)
                    self.start_new_listener()

                    
                else:
                    conn.send_serial(data)



def main(argv=None):

    #Pull in our arguments if we were not spoonfed some
    if argv is None:
        argv = sys.argv

    #Parse our arguments
    try:
        options, args = getopt(argv[1:], "p:s:b:f:h")#, ["port=", "sName=", "baudrate=", "CC=", "OO=", "help="])
    except GetoptError:
        usage()
        return    


    global port    # int, the TCP port to listen on
    global com     # the serial connection itself


    #first, loop through and open the right port
    got_a_serial_port = False
    for o,a in options:
        if o in ("-s"):
            a = int(a)
            try:
                com = serial.Serial(a)
                #print "Serial port opened: %s" % (com.portstr)
                got_a_serial_port = True
            except:
                print("Couldn't open serial port: %s" % (a))
                print("This should be a numerical value.  0 == COM1, 1 == COM2, etc")
                sys.exit(1)
        if o in ("-h"):
            usage()
            return

    if not got_a_serial_port:
        # we don't have a port.  Fine, use the default.
        try:
            com = serial.Serial(0)
            #print "Serial port opened: %s" % (com.portstr)
        except:
            print("Couldn't open serial port: %s" % (0))
            sys.exit(1)


    # sensible defaults
    com.baudrate = 9600
    com.timeout = 0
    com.bytesize = serial.EIGHTBITS
    com.parity = serial.PARITY_NONE
    com.stopbits = serial.STOPBITS_ONE
    com.xonxoff = 0
    com.rtscts = 0
    port= 23      

    # now loop through the other options   
    for o,a in options:
        
        if o in ("-p"):
            a = int(a)
            if a < 1 or a > 65535:
                print("Invalid listening (tcp) port.  Valid ports are 1-65535")
                sys.exit(1)
            else:
                port = a
            
        if o in ("b"):
            a = int(a)
            if a in com.BAUDRATES:
                #print "Setting baudrate to %s." % (a)
                com.baudrate = a
            else:
                print("Valid baudrates are:", com.BAUDRATES)
                sys.exit(1)


        if o in ("-f"):
            FLOWS = ("xonxoff", "rtscts", "none")
            if a in FLOWS:
                #print "Setting flow control to %s" % (a)

                if a == "xonxoff":
                    com.xonxoff = True
                if a == "rtscts":
                    com.rtscts = True
            else:
                print("Valid flow-controls are:", FLOWS)
                sys.exit(1)

    # print out com's statistics
    print("------------------------")
    print("Serial Port Information:")
    print("------------------------")
    print("serial port name:     %s" % com.portstr)
    print("baudrate: %s" % com.baudrate)
    print("bytesize: %s" % com.bytesize)
    print("parity:   %s" % com.parity)
    print("stopbits: %s" % com.stopbits)
    print("timeout:  %s" % com.timeout)
    print("xonxoff:  %s" % com.xonxoff)
    print("rtscts:   %s" % com.rtscts)
    print("")
    print("------------------------")
    print("TCP/IP Port Information:")
    print("------------------------")
    print("host:     %s" % "localhost")
    print("port:     %s" % port)
    print("")


    # start up our run loop    
    connections = Handler()
    while 1:
        connections.run()


if __name__== "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Keyboard Interrupt")