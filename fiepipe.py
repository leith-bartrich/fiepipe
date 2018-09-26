#!/usr/local/bin/python

import fiepipelib.localplatform.routines.localplatform
import fiepipelib.localuser.routines.localuser
import fiepipelib.shells.fiepipe


def main():
    # TODO register fie.us and populate the public key from somewhere authoritative.
    platform = fiepipelib.localplatform.routines.localplatform.get_local_platform_routines()
    localuser = fiepipelib.localuser.routines.localuser.LocalUserRoutines(platform)
    shell = fiepipelib.shells.fiepipe.Shell(localuser)
    shell.cmdloop()


if __name__ == "__main__":
    main()
