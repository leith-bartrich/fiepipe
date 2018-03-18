fiepipe
By Bradley Friedman, FIE LLC

DESCRIPTION:

fiepipe is a set of scripts and libraries meant to be a pipeline/workflow
system for people and legal entities to organize both complex and simple
computer systems and networks.

It has its roots in the world of digital visual effects (VFX) and
animation as practiced at companies large and small through the late
1990s through the mid 2010s.

However, it is not simply for those industries.  Rather, it is an abstraction
and refactoring of general digital asset workflows.  As more and more work
becomes digital (not physical) in nature, the work de-facto becomes:
digital labor on digital assets and requires digital workflow managment.

Therefore, all the best practices of working in digital VFX and animation
become relevant.  And therefore fiepipe becomes relevant.

STATUS:

fiepipe is currently in pre-alpha stage.

I'm trying to build it and use it myself.  I expect to code it while I use it.
I guarontee nothing.  Use it at your own risk.  And probably, if you want to use
it, you'd do well to contact me.


INSTALL:

For now, there are two recomended ways to install fiepipe directly.  Either
to just use it, or to develop it while you use it.

Installs are aqcuired via github through pip and use a standard setup.py file.
This should be secure because you are trusting HTTPS (not HTTP) to guarontee that github is
actually github (and not an impostor or man in the middle).  And in turn you trust github
to guarontee that I'm me.  And you in turn trust me.


INSTALL FOR USE:

To just install it for use, issue a command to pip which tells it to install from github.

For example, the master branch from my development repository:

pip install git+https://github.com/leith-bartrich/fiepipe.git@master

upgrades can be acquired using pip's -U or --upgrade flag:

pip install -U git+https://github.com/leith-bartrich/fiepipe.git@master


INSTALL FOR DEVELOPMENT:

Development installs can be acquired similarly by using the -e  or --editable flag.

pip install -e git+https://github.com/leith-bartrich/fiepipe.git@master

you may need to ocassionally run the setup.py file in develop mode to update the developer install like such:

python setup.py develop

