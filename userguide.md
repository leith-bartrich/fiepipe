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

A legal entity can be thought of two ways.

1. It's a company or individual.
2. It's a legal piece or fraction of yourself.

Remember that within your user on your computer system, you are master of your domain.
As long as the kernal allows it, the computer will do as you say.  So if you say you are the president of Microsoft, the computer
and the fiepipe system will believe you.  Other computers, services and users might not and you can't force them to.  But within
userspace, you are king.  In the
most extreme situation, you can modify the source code to whatever you are running, to force such a belief.  Therefore, there's
not much
point in designing software that pretends you don't have that power.

So, within my system, when I run fiepipe, I probably have two legal entities registered and ready to work with.

* fie.us
* bradley.friedman.private

Actually that might even be too simplistic.  I might have this setup:

* fie.us
* bradley.friedman.private
* ny.friedmans.private
* fl.friedmans.private
* methodstudios.com

The fie.us entity is perhaps easiest to understand.  That's my LLC and my work at my LLC belongs in that context.  My projects and such.

The bradley.friedman.private entity is separate and represents me, as an individual.  I'd keep my medical stuff here, obviously.

The ny.friedmans.private entity would be the entity for my nuclear family that I grew up with.  It's a place for shared things.

The fl.friedmans.private entity would be the entity I set up for my new nuclear family as an adult.  Again, a place for shared things.

The methodstudios.com entity is where I used to work.

Any really, any job I'd have over the years, would need its own legal entity.  Either that company would define one, or I might need
to create one.  When I was at work on a work computer, the company's legal entity might be installed for me.  But even on my home
machine, I'd be likely
to create it.  Just to hold on to documents that I should keep with regard to the aspect of my life that belongs to that entity.
For example,
I might need to keep my employment contract in such an entity even if I am forbidden to have anything work related outside the office.
There's still a need for it.

This is not the same as having a client.  As a consultant working under my fie.us banner, I might have plenty of different clients.
But there are other organizational structure to keep them separate within the fie.us legal entity.

Also, I don't have to create every legal entity on every computer.  My work computers probably just have fie.us on them.

And going forward, I'll probably stick to the simpler fie.us and bradley.friedman.private entities for my examples.

Keep in mind, we have not actually set up any sharing or syncing or servers.  There are tools for sharing legal entities and
managing lists of them between computers.  But we won't get into them right now.  Separate from the methods I've inlcuded in fiepip for
accomplishing managment of legal entities across computers, its also possible to author custom plugins for doing that as well.

### authority

There are tools for managing authorty over a legal entity.

This is the literal creation of a legal entity and you should not be doing it unless you are that actual legal entity.

For example, I own fie.us.  So I do actually manage the authoritative legal entity for fie.us.  But if I hire someone, they are not the authority.  They instead, want to register the legal entity (covered later.)

A legal entity authority contains private encryption keys that allow you to sign and delegate authority.  So that others may verify that you did indeed sign and delegate those things.

You keep your authority information SECRET.  LOCKED UP.  IN A SAFE. OFFLINE.  AIR GAPPED.  etc.

### registry

Usually, you'll be working with registered legal entities.  Which usually are just referred to as legal entitties.

A registered legal entity contains public encryption keys that can be used to verify that the authority signed and delegated its authority to third parites.  Though the registration itself does not inherently prove you are authorized.

By registering a legal entity, you are agreeing that the legal entity is subordinate and agrees to the authority that issued it.

You generally make your legal entity registry public and widely available.  It contains information on how to interact with you and how to authenticate that you are you.  It does not actually contain any private or confidential information.  It has no authority itself.

Again, since a user can force their own computer to believe anything they tell it to, there is no reason to pretend that they can't pretend to be you on their own computer.  The danger would be if they could make other computers that they don't control, believe they were you.  And that is why legal entity authority is separate form legal entity registration.

### the exception

When you are truly creating a version of the legal entity that should NOT subordinate itself to an existing authority, you need to be the authority.  You are creating a compartmentalized version of the entity.  You might do this because:

* you truly are setting up a classified or confidential compartment/system for the legal entity
* you have a need to control a compartment because its your
  * employment contract
  * medical insurance information
  * tax information
  * etc

## Container

## Git Storage

### Root

### Asset

