# TCP2Serial

[this repo](https://github.com/mobinamosannafat/tcp2serial.git) contains implementation of a tcp2Serial program. 

tcp2Serial is a tcp server that listen on a tcp port and waiting for a client request. 

It get's request from a client and forward incoming request to a serial port

This program is written using telnet

# Requirements

this script requires the use of "pyserial", which is licensed separately by its author.  

This library can be found at http://pyserial.sourceforge.net/

# How to use

You must specify the following arguments while running the program:

-TCP port number that server listen on this port

-Serial port name

-Serial port baud rate

-Flow-control options

Of course, Serial port baud rate and Flow-control options have default values and can not be entered
An example of running a program is as follows:

```sh
python tcp2serial.py -p 12000 -s 1
```

In the first run, for more information, run the program as follows to display the explanation for you:

```sh
python tcp2serial.py -h
```

# More information about the program



# Credits

- Danial Keimasi
