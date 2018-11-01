# fiepipe User Guide

## Purpose

fiepipe or FIE Pipeline is a data and workflow managment system for working on/with digital assets.

Essentially, it is a system for accomplishing digital labor.  If work were being done on paper, and put into filing cabinets
it would not be digital labor, it would be physical labor.  We might even say that it's 'paper work.'  We'd have all kinds of
physically structured systems for managing it.  The file cabinets themselves, and the folders are examples.  The carbon paper based forms
are examples of the ways in which the physical restrictions and requirements structure the work.

But in the modern digital age, a lot (perhaps most) of our work is digital.  And in its digital form, we're left without the physical
touchstones of the past, that often defined the structure and purpose of the work system itself.  No longer does a 'thing' (digital asset)
need to be physically filed in a single folder.  No longer do we need three copies so that two might be filed in different places.
A digital asset
might be in a file folder.  It might not even be a file at all.  It might be a database entry.  It might be a collection of files.

fiepipe is an abstraction and implementation of the best-of-breed practices and systems, found in one of the most demanding and mature
digital asset based workflow industries in the world:  The Digital Visual Effects (VFX) and Animation industries.

The terrabytes
of data and thousands of workers need to constantly apply massive amounts of human and machine (digital) labor have resulted in decades
of development and use of complex digital workfow managment systems.  The likes of which are often not found outside those industries.
Though, they have crept into some aspects of the videogame development and aerospace industries.  Where they have not really spread, is to
the greater digital economy.  Everything from a small accounting firm to a fortune 500 company has really transitioned to a digital labor
based system for large amounts of the workflow.

fiepipe seeks to make these kinds of data/context centric workflows available to the average user such that they might use it for
themselves as individuals, and themselves as workers and themselves as companies, etc.

## Plugins

fiepipe is plugin based.  Therefore, the basic fiepipe system is a bit abstract.  But it becomes more concreate as you use it and configure
it.  This makes sense when you think of it as a data/context based system.  The better you specify what it is exactly you are working on, the 
more specific the options as to what you can do with that thing or within that context are.

## Shells

For now, fiepipe's UI is shell based.  It is meant to be able to expand to many kinds of UI and GUI.  But for now, the most complete
UI is a shell based ui which is often entered by running 'fiepipe' from the command line.  Some specific companies and entities may have
their own custom command.  For example, I publish my llc's company command as an example.  In my custom setup, you can also enter by running
my custom command, 'fiellc.'

* fiepipe shells are nested.  You enter shells from other shells.

* fiepipe shells self document.  You should always be able to type 'help' and get a general idea of what commands are available to you at 
any time.  And tab on a blank prompt will also list available commands.

* fiepipe commands are self documenting.  You should usually be able to type 'help [command]' where [command] is an available command, to get
a usage description for that command.

* fiepipe shells tab complete.  You should usually be able to use tab to complete partial entries and tab-tab to get a list of available tab
completions.

* fiepipe is context aware.  The prompt should usually help you understand your current context.

## The User

The outer most context which you get by running the fiepipe command, is the context of your user, on your machine.  The requirements being
that you can log in and run the fiepipe command.  Once you are actually sucessfuly doing this, you actually have quite a bit of autonomy with
regard to what a computer system will let you do.  This is generally known as 'user-space.'

what you do with fiepipe is up to you.  You can set up multiple identities and entities to work from.  As the user, that's your right and privledge.

Practically speaking, this is where more global or computer system-wide things get done.  Such as:

* setting up programs
* create/manage legal entities authoritatively
* register/manage legal entities you work in/with
* manage storage
* manage known ssh hosts

Most of the time, once you're set up, you will be here briefly just before you enter a legal entity shell.

For me, I usually just issue the 'le enter fie.us' command.

'le' is short for the legal_entities sub-command
'enter' is the command to enter a legal entity's context
'fie.us' is my legal entity's Fully Qualified Domain Name (fqdn)

Probably worth noting, I don't even type that much.  I type 'le[space][tab]en[tab]fi[tab][enter]' because tab completion is VERY nice.
If you're not used to it, you'll come to love it soon.

Running that command jumps me into a new shell context.

## Legal Entity



## Container

## Git Storage

### Root

### Asset

