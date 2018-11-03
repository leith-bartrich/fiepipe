# fiepipe Architecture

## Python Version

We write for Python 3.  Compatibility with Python 2 is secondary at best.

## Static Typing and Generics

We hint static types wherever possible.

See PEP 484 https://www.python.org/dev/peps/pep-0484/

We use generics from the typing package.

We prefer IDEs that accomplish code completion via static code analysis, that undersatnd PEP 484 and generics.  Currently that's WingIDE and PyCharm principally.

## Exceptions/Errors

Unlike a statically compiled language like C or Java, Python is interpreted at runtime.

Also, python async methodology implements the CanceledError as an exception.

As such, the old addage, "don't use exceptions for flow control" is irrelevant.

Python is a scripting language.  As such, stack traces are acceptable.

Therefore, it is always okay to raise exceptions.  It is important to be as descriptive as possible as one should assume any raised exception may be presented to the user.

## Async

Where appropriate, we use asynchronous programming in routines in order to allow a lively UI.

An asynchronous method should mark itself as being async by appending "_routine" to its function name to hint all consumers that
what they are calling is an async function.

Shells, for example, have a self.do_coroutine(do_my_thing_routine(foo, bar)) becasue we expect many async routines to be used within the shell's cmd loop.

## Plugins

We use pkgutils plugin system https://packaging.python.org/guides/creating-and-discovering-plugins/ wherever possible.

The shell ui system is largely built around an embedded plugin system, for example. 

It's worth pointing out, this implies that fiepipe and its plugins will use setup.py and pip for all install/deployment.  Even at development time. 

## Layers

We use a layer based system to develop fiepipe.  We do not use a traditional system such as MVC or MVVM or ECS.  However we are informed by these various evolving and traditional layered approaches.

Different subsystems may end up with more or less layers depending on their nature.  However, our basic layer structure is:

* Data
* Routines
* UI

### Data

The data layer is responsible for managing, loading and commiting data.  This can be to/from disk.  Or to/from a network service.  Or wherever data might come from.

The data layer tries to avoid doing all but the most mundane of processing to data.

e.g. The data layer might build a path from data with which to get other data.  But it probably should not execute business logic with it.

### Routines

Routines are where business logic and UI logic is executed.

A set of routines can imply a certain type of UI.

Routines may referencce or construct other routines and call them, or require that they be passed in, to run.

For example, we have a series of abstract routines for publishing notifications and collecting certain types of input.  Those particular routines are VERY close to the UI.  They imply UI functionality.  However, they do not actually touch UI direclty.  Their subclasses however, might. This allows higher level routines to be passed abstract UI routines in order to interact with the user, without knowing exactly what type of UI is really being used.  

Routines may reach into the data layer to do what they need to do.  They may reach into/callback to the UI as well. 

### UI

UI code is usually written to a specific Application toolkit of some kind.  Usually its the main-loop of the tool being run.  Eventually, the UI will reach a point where it needs to construct routines in order to call them.  Hopefully the UI's logic is as shallow as it can be.  UI may reach into the Data layer as well, in order to provide the routines the data they need to operate.

#### Shell

Shell UI is the default most well supported UI type that fiepipe implements currenlty.  We build our shell UI on top of cmd2.

## Systems

Typically, we implement a system as a package.  A typical structure might be:

* fiepipemypackage
  * data
    * mything.py
  * routines
    * ui
      * custominput_ui.py
    * mything.py
  * shell
    * ui
      * custominput_ui.py
    * mything.py
    
Within each mything.py file we implement the types relevant to 'mything' for that layer.

Usually the data layer imports neither of the other two layers.

The routines layer will probably import the data layer and its embedded, abstract ui routines.

The shell layer will probably import the routines layer, the data later and its own concrete implementations of the ui routines.

The user interacts via the logic in the ui layer.  It uses data to construct routines and call them.  Presumably the concrete UI routine implementations call back into the UI as neccesary.

### System hooks

Presumably, the system is hooked into the fiepipe system via the plugin system referenced above.

More concretely: The setup.py that was used to install the package, registered a plugin call that adds a shell in the mything.py file to another shell as a callable submenu, at runtime.   Therefore, when the user runs the parent shell, the new shell has already added itself as a sub-menu command and is inherently able to be run in the UI.

note: if you run "pip install -e ." in an appropriately structured python development project, it allow a developer to develop with the plugin system active on the development code.  This is how you develop/debug such a system easily.
