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

### Data

### Routines

### UI

#### Shell
