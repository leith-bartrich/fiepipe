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

Installs are generally aqcuired via github and use a standard setup.py file.
This should be secure because you are trusting HTTPS (not HTTP) to guarontee that github is
actually github (and not an impostor or man in the middle).  And in turn you trust github
to guarontee that I'm me.  And you in turn trust me.


INSTALL FOR USE:

To just install it system wide for use, issue a command to pip which tells it to install from github.

For example, the master branch from my development repository:

pip install git+https://github.com/leith-bartrich/fiepipe.git@master

upgrades can be acquired using pip's -U or --upgrade flag:

pip install -U fiepipe

As fiepipe is alpha software, you may want to install it in a python virtual environment instead, to keep
your system python clean.  Or to test new versions.


INSTALL FOR DEVELOPMENT:

Development installs typically don't originate fully from pip because you're likely forking the
source-code yourself.  Meaning: you probably have to check it out yourself from a specific
account or repository becasue you're developing.

Once you've checked out the code, you can use pip or the setup.py file.

pip is often better at getting precompiled versions of dependenies from pypi.  A pip
install for development might be:

pip install -e .

Or, running setup.py yourself might look like:

python setup.py develop

you may need to ocassionally re-run the setup.py file in develop mode if you edit the setup.py file
in a way that requires it.

Similarly to standard installs, you may find python virtual environments very useful here to keep
a development version and production version separate from one another.