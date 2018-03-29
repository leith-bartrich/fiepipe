import cmd2
import pkg_resources
import fiepipelib.localplatform
import sys
import fiepipelib.applauncher.genericlauncher
import types
import traceback
import logging

class Shell(cmd2.Cmd):
    """An abstract base class for shells."""

    def getPluginNameV1(self):
        """
        Returns a name for this shell plugin.  e.g. 'myshell'
        Which will be turned into 'fiepipelib.plugin.shell.myshell'
        Plugins are to be registered in the setup.py file as follows:
        
        entry_points={
            'fiepipe.plugin.shell.myshell.v1' : 'myshellplugin1 = myshellplugin1:plugin',
        },

        which will load the module myshellplugin1 and call the plugin methond, passing a single parameter
        which will be an instance of this shell before its command loop is run.

        note: To add a command to a shell, one needs to add it to the __class__, not the instance.
        e.g. shell.__class__.do_foo = foocommand
        This is because the base cmd class does all its name searching and mangling by
        listing the attributes of the class rather than the instance.  For whatever reason.
        """
        raise NotImplementedError()


    def __init__(self):
        self.allow_cli_args = False
        super().__init__()
        pluginname = self.getPluginNameV1()
        entrypoints = pkg_resources.iter_entry_points("fiepipe.plugin.shell." + pluginname + ".v1")
        for entrypoint in entrypoints:
            print(self.colorize("Loading shell plugin: " + entrypoint.name,'green'))
            method = entrypoint.load()
            method(self)

    def GetForkArgs(self) -> list:
        self.perror("This shell does not support forking.", exception_type=NotImplementedError, traceback_war=False)
        raise NotImplementedError()
            
    def do_fork(self, arg):
        """Forks a new shell in a new process.
        """
        args = [sys.executable,sys.modules[self.__class__.__module__].__file__]
        args.extend(self.GetForkArgs())
        launcher = fiepipelib.applauncher.genericlauncher.listlauncher(args)
        launcher.launch()

#    def perror(self, errmsg, exception_type=None, traceback_war=True):
#        if self.debug:
#            excinfo = sys.exc_info()
#            raise excinfo[1]
#            logging.exception(errmsg)
#        super().perror(errmsg,exception_type,traceback_war)

    def AskTrueFalseQuestion(self, question, tname="Y", fname="N"):
        while (True):
            i = str(self.pseudo_raw_input(question + " (" + tname + ":" + fname + "): "))
            if (i.lower() == tname.lower()):
                return True
            if (i.lower() == fname.lower()):
                return False
        
    def AskTrueFalseDefaultQuestion(self, question, default, tname="Y", fname="N"):
        defaultText = fname
        if default:
            defaultText = tname
        while (True):
            i = str(self.pseudo_raw_input(question + " (" + tname + ":" + fname + ") [" + defaultText + "]: "))
            if (i.lower() == tname.lower()):
                return True
            if (i.lower() == fname.lower()):
                return False
            if (i.isspace() or (i == "") or (i == None)):
                return default


    def AskStringQuestion(self,question):
        return str(self.pseudo_raw_input(question + ": "))

    def AskStringDefaultQuestion(self,question,default):
        answer = self.AskStringQuestion(question + " [" + default + "]")
        if answer == None:
            answer = default
        if  answer.isspace() or (answer == "") or (answer == None):
            answer = default
        return answer


    def do_exit(self,arg):
        """Exits this shell."""
        return self.do_quit(arg)

    def do_clear(self,arg):
        """Clears the console screen."""
        platform = fiepipelib.localplatform.GetLocalPlatform()
        assert isinstance(platform, fiepipelib.localplatform.localplatformbase)
        cmd = platform.getConsoleClearCommand()
        self.do_shell(cmd)
        
    def AddCommand(self, name:str, target:types.FunctionType, complete:types.FunctionType = None):
        """Dynamically adds a command to the given shell.
        
        Usually called from a plugin function so a plugin can add commands to a shell.
        
        @param name: a string name for the command.  "foo" not "do_foo"        
        @param target: A function (callable) of the typical "do" type foo(self,args)
        @param complete A function (callable) of the typical "complete" type.
        
        note: internally we use setattr to add to the __class__ of the instance.  This is neccesary to make
        cmd2 able to dynamically find the methods.
        """
        setattr(self.__class__, "do_" + name, target)
        if complete != None:
            setattr(self.__class__, "complete_" + name, complete)
        