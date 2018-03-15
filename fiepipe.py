#!/usr/local/bin/python

import fiepipelib.shells.fiepipe
import fiepipelib.localplatform
import fiepipelib.localuser



def main():
    #TODO register fie.us and populate the public key from somewhere authoritative.
    platform = fiepipelib.localplatform.GetLocalPlatform()
    localuser = fiepipelib.localuser.localuser(platform)
    shell = fiepipelib.shells.fiepipe.Shell(localuser)
    shell.cmdloop()
   

if __name__ == "__main__":
    main()
    