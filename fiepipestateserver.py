#!/usr/local/bin/python

import fiepipelib.stateserver
import rpyc
import rpyc.utils.server
import sys
import fiepipelib.ports

def main():
    server = rpyc.utils.server.ThreadedServer(service=ServiceFactory,hostname="localhost",port=fiepipelib.ports.SERVER_STATE_PORT)
    print("Starting State Server: ")
    server.start()

def ServiceFactory():
    ret = fiepipelib.stateserver.Server()
    #TODO: configure it here.
    return ret

if __name__ == "__main__":
    main()

