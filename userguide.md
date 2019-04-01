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

## No/Little System Wide Setup

fiepipe is meant to be able to be installed by a user to their own user-space resources using only a recent version of Python if need be.  This is purposful.  It is intended that individuals be able to use it at a company, for their own personal workflow, even if the
company has not adopted it.

Therefore, there is very little system wide setup neccesary or even available.  A user is an island for the most part, by default, and opts in to entities and resources.

Though, a system administrator can do the install and provide it system wide.  They can also install plugins system wide.  Those plugins can be very entity specific in nature.

The majority of sharing or infrastructure functionality is meant to be handled over the network, rather than between users on a single system.

A custom company command/plugin is always capable of automatically setting up network resources and local resources.  And this is the preferred way to ensure the availability of standardized and shared resources within a fiepipe system.

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

And really, any job I'd have over the years, would need its own legal entity.  Either that company would define one, or I might need
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
managing lists of them between computers.  But we won't get into them right now.  Separate from the methods I've included in fiepipe for
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

From within the entity, we can interact with the containers command.

In VFX/Anim land, people are used to 'Projects.'  For them, a contaienr is analagous to a 'Project.'  However, a 'Project' is only one thing you might have in a container.

Things a container might be:

 * A Project
 * A Department
 * An Organizational Unit
 
A compartment is meant to be subscribed to.

e.g. I am an accountant and I currenlty subscribe to the following containers:

  * acct_2017
  * acct_2018
  * acct_2019

in the same company, someone else might be a contractor and only subscribe to:
  
  * project_a
  
Projects are identified by a unique ID internally.  The short names we use locally to refer to projects can collide if need be.  Though, two projects by the same name at the same fqdn really should not exist on the system at the same time.

Projects have short descriptions, in addition to their names, for convenience.

Usually containers are shared and hold top level configuration information.  They are meant to be updated infrequently by those in authority.

To work within a container, you enter it.  Typically, a command like `cnt enter foo` will enter the foo container.

## Git Storage

Within a container, on a desktop, we typically move on to using the Git Storage system to start working on data and with tools.  The Git Storage system consists of two primary storage entities:

  * Roots
  * Assets
  
Both Roots and Assets are based on git repositories. https://git-scm.com/

fiepipe seeks to abstract your interactions with git.  However, we also try and maintain compatibility with git workflow.

A git root is just a top level git repository and worktree.  A git asset is just a git submodule in that worktree.

Typically, from the container, I use the 'roots' command to work with, and get into a root.  

### Root

A root can be thought of as a storage volume.

A container might have multiple roots, because it might have reason to maintain multiple volumes.  For example:

  * a 'work' root, to be used by workers on workstations
  * a 'data' root to be used by a database server
  * a 'wiki' root to be served by a wiki web server 

A root has two parts.  A shared part, and an optional local configuration.

#### Shared

The shared part of the root is stored in the container, which itself is shared from someone in authority.  If you administer the container, you'll need to create the root and then publish the contaienr with the new shared root information in it.  The shared root
consists of a unique id, a name, and a description.

Everyone who has been given a copy of the container, knows that the root exists.  But that doesn't mean they have access to it.

#### Local configuration

Usuallly, if a user actually intends to use the root, they need to configur it locally.  This can be done with the following command: `roots configure foo` where foo is the name of the root to configure.

A local configuration contains an id, the local storage volume to use, and a subpath to put its worktree in.  Once you actually configure a root, you can try and enter it.

typically done with the command `roots enter foo`

#### Roots vs Assets

A root is typically not very featureful.

An asset is far more featureful and configurable.

It is technically possible to live entirely within the root and never create or use an asset.  But it is not recommended when possible.

Roots can have deep structure within which to nest assets.

Assets can nest other assets.  But when possible, it's probably best to keep assets shallow.

e.g.:

* root (root)
  * char.betty (asset)
  * char.sam (asset)
  
or:

* root (root)
  * chars (dir)
    * betty (asset)
    * sam (asset)
  
rather than:
 
*root (root)
  * chars (asset)
    * betty (asset)
    * sam (asset)


consider the usefulness of something a bit deeper like:

*root (root)
  * char.betty (asset)
  * char.betty.3d.maya (asset)
  * char.betty.young (asset)
  * char.betty.young.3d.maya (asset)
  * char.sam (asset)
  
or:

*root (root)
  * 3d (dir)
    * char.betty (asset)
    * char.sam (asset)
    * action.foo.A (asset)
    * action.foo.B (asset)
    * shot.foo.A (asset)
    * shot.foo.B (asset)
    * shot.foo.C (asset)
    * shot.foo.D (asset)
    * shot.foo.E (asset)
  * editorial (dir)
    * edit.sequence.foo (asset)
  * 2d (dir)
    * comp.foo.0001 (asset)
    * comp.foo.0002 (asset)
    * comp.foo.0003 (asset)
  * postoffice (dir)
    * vendor01 (dir)
      * in (dir)
        * delivery.in.vendor01.2018.11.02.01 (asset)
      * out (dir)
        * delivery.out.vendor01.2018.11.02.01 (asset)
        * delivery.out.vendor01.2018.11.02.02 (asset)
      
#### init

When you create a root, as an administrator of a container, you need to initialize the root.  You can do it two ways.  Either with `init_new`, or `init_new_split`

A split root keeps its git repository on a separate volume from the worktree, wheras the simpler version of the command just keeps the repository on the same volume as the worktree.  If you have a smaller fast volume and a larger slow volume, the split version might be good for you.

Generally, if someone else already created the project and the root, you probably don't want to init it.  Rather, you want to clone it from some kind of shared source.  See the gitlab section for clone commands to fetch/clone an existing root.

#### checkout_from_split

In the odd situation where you need to checkout an existing root from a repository on a different volume you can do so here.  One such situation might be where the repository is on an external drive you are moving between two systems.  Which is a crude but effective sneaker-net approach to shared containers.

#### commit

Generally, when you publish a set of changes to the project, you'll commit those changes from the root.

The `commit_all` command looks at all the modified assets and the root and commits the changes.  It asks for a commmit message, which should describe the changes you made.

Note: you don't have to commit the whole tree.  You can commit individual assets if you really want to.  But the commit from the root helps lay down a consistent version of the whole project tree for others to be able to reference.

#### add

Various add commands help you add files to the root for tracking.

### Asset

Assets can be created, modified and entered from the assets subcommand of the root.  They are typically referenced by their path, but in some cases can be referenced by id.

e.g. `assets enter my.asset`

e.g. `assets enter chars/sally`

If an asset is nested, you might not be able to use it unless its parent asset is first pulled locally.

Assets are directories on disk.  However, they need to either be created before they're used, or pulled local before they are used.  Simialr to the need to either init or clone a root.  To create a brand new asset, one uses the `assets create_asset path/to/asset` command.  However, more often, one wants to pull down the current version of the asset from some kind of shared network storage.  See the GitLab server section to see how to `checkout_asset` or `checkout_branch` to acquire a local checkout of an asset.

Once an asset is on disk, it's free to be used by any applications or tools that are available on the system.  Even those that are not
aware of fiepipe at all.

#### add

Just like the root, an asset has a series of add commands with which to add files for tracking.

#### can_commit

The `can_commit` command will check if the current asset is set up to succesfully commit.  And further, tries to explain why not, if not.

#### Aspects

Typically, assets use 'aspects' to be useful.  Aspects typically register themselves as subcommands via the plugin system.  Depending on how they work they'll magically make themselves availale when relevant.

Aspects usually need to be 'configured' to be used within an asset.  Usually this means they put a named .json file in the asset_configs directory of the asset.  The contents of the .json file are aspect specific.  But the existence of the file is what flags wheather and aspect is active or not in a asset.  Usually you don't have to do this manually.  The aspect command itself usually has a `configure` command and other commands to manage its configuration.

e.g. `houdini configure`

e.g. `houdini add_project houdini/project_01/`

e.g. `houdini open h17`


### GitLab Server

fiepipe has implemented support for centralized sharing\syncing of data and meta-data using GitLab as a server.

To be clear, fiepipe is not meant to be limited to GitLab, but we are implementing GitLab first.

The "gitlab_servers" command allows the user to keep track of a list of named servers and login credentials.

There are gitlab commands located at various levels in other systems that use these servers.


### Structure

Structure is what makes a generic storage system, intuitive, predictable and organized.

Typically, a storage root will opt-in to a type of project structure, via a plug-in command on its
root.  The project structure will likely branch out to mange the assets and their contents.

A root may opt-in to multiple structures if those structures don't conflict.

The specifics of any particular structure is something that's up to the developer of said structure plugin.
But generally, you'd expect project management tools along the lines of: 'ingest_delivery', 'manage_production_asset.'

A primary goal of fiepipe, is to provide enough configurability and capability, to allow a well built project structure
to be powerful and easy to use.


## Auto-Manager

The AutoManager is meant to handle as much management and overhead of a user's containers and storage, as possible.
It is tightly integrated with the Structure system.

The AutoManager tries to be verbose and carefully fail/inform of problems such that it does not destroy your work.  It
tries to provide you the opportunity to fix problems early.

### Auto-Creation

The AutoManager will try to automatically create and commit any new/missing project structure locally.

### Auto root push and pull

The AutoManager will try and push any changes to the root structure early and often, so that users don't diverge.
It will pull changes as early as possible as well, again, to avoid divergence.  One reason why it's good to use assets
that exist in a deep root structure, is so that the root structure can be kept very light and be pushed and pulled
frequently to reflect the existence of those assets.  This relieves the storage root from be responsible for managing
the assets internal (file) data.

The best way to keep a project from being overwhelmed with bad asset creation and organization, is to limit a
user's permission to push to the root on the GitLab server.  The auto manager will properly inform a user if they've
created a local asset that they don't have permission to push.

In order to better manage asset creation more granular-ly, It can be useful to run a asset creation daemon on a central
server that has permission to create assets and push to the root, and can take/manage requests to do so intelligently.

### Auto-Update

The AutoManager will try and detect assets that you have checked out, that you are not working on.  It will try and pull
changes made to those assets down proactively, so you have them and don't need to worry about checking for them.  This
too may help avoid divergence, as you're less likely to work into old data/organization.

### Plugin Hooks

The AutoManager routine will call out to plugins at various stages to allow plugin developers and entity command
developers to effect its behavior.

    - fiepipe.plugin.automanager.pre_automanage_fqdn
        - await method(feedback_ui, fqdn)
    - fiepipe.plugin.automanager.pre_automanage_container
        - await method(feedback_ui, legal_entity_config, container_id)
    - fiepipe.plugin.automanager.pre_automanage_root
        - await method(feedback_ui, legal_entity_config, container_config, root_id)

Some things a plugin developer might do here:

    -If the FQDN is my legal entity, I use DNS to lookup the gitlab server URL and put it in the registry
