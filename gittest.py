#!/usr/local/bin/python

import fiepipelib.shells.gitroot
import os
import git

def main():
    #cwd = os.getcwd()
    #g = git.Git(cwd)
    
    #repo = git.Repo(cwd)
    shell = fiepipelib.shells.gitroot.Shell()
    shell.cmdloop()
   

if __name__ == "__main__":
    main()
    