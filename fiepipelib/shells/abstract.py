import cmd2
import pkg_resources
import fiepipelib.localplatform
import sys
import fiepipelib.applauncher.genericlauncher
import types
import traceback
import logging
import abc
import fiepipelib.abstractmanager
import typing

class Shell(cmd2.Cmd):
    """An abstract base class for shells."""
    
    @abc.abstractmethod
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
        self.prompt = self.GetBreadCrumbsText() + ">"

    breadcrumbs_separator = '/'
        
    @abc.abstractmethod
    def GetBreadCrumbsText(self):
        raise NotImplementedError()

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

    def AddSubmenu(self, shell:cmd2.Cmd, name:str, aliases:list):
        cmd2.AddSubmenu(shell, name, aliases, 
                       reformat_prompt="{sub_prompt}", 
                       shared_attributes=None, 
                       require_predefined_shares=True, 
                       create_subclass=False, 
                       preserve_shares=False, 
                       persistent_history_file=None)(self.__class__)

    def ParseArguments(self,line:str):
        return cmd2.parse_quoted_string(line)

    def ArgumentExists(self,args:list,lookingFor:list):
        return self.IndexOfArgument(args,lookingFor) != -1
                
    def IndexOfArgument(self,args:list,lookingFor:list):
        """Returns the index of and arugment in the 
        """
        if len(args) == 0:
            return -1
        for i in range(0,len(args)):
            for a in lookingFor:
                if args[i] == a:
                    return i
        return -1

    def GetArgumentValue(self,args:list,lookingFor:list=[]):
        i = self.IndexOfArgument(args,lookingFor)
        if i == -1:
            return None
        if i > (len(args) - 2):
            return None
        return args[i+1]
        


class LocalManagedTypeCommand(Shell):
    """Abstract command for working with locaally managed types in a CRUD type manner.
    """
    
    _localUser = None
    
    def __init__(self, localUser:fiepipelib.localuser.localuser):
        self._localUser = localUser
        super().__init__()
    
    @abc.abstractmethod
    def GetManager(self) -> fiepipelib.abstractmanager.abstractlocalmanager :
        raise NotImplementedError()
    
    @abc.abstractmethod
    def ItemToName(self, item) -> str:
        raise NotImplementedError()
    
    @abc.abstractmethod
    def GetItemByName(self, name):
        raise NotImplementedError()

    @abc.abstractmethod
    def GetAllItems(self) -> typing.List:
        raise NotImplementedError()        
    
    def do_list(self, args):
        """Lists all items.
        
        Usage: list
        """
        allitems = self.GetAllItems()
        for i in allitems:
            self.poutput(self.ItemToName(i))
        
    @abc.abstractmethod
    def do_create(self,args):
        """Used to create the given type.  Likely an interactive process.
        """
        raise NotImplementedError()

    def type_complete(self,text,line,begidx,endidx):

        allitems = self.GetAllItems()
        
        ret = []
        
        for i in allitems:
            name = self.ItemToName(i)
            if name.startswith(text):
                ret.append(name)
        
        return ret

    complete_delete = type_complete
    
    def do_delete(self, args):
        """Deletes the given item.
        
        Usage: delete [name]
        
        arg name: The name of the item to delete.
        """
        if args == None:
            self.perror("No name given.")
            return
        if args == "":
            self.perror("No name given.")
            return

        self.DeleteItem(args)
        
    @abc.abstractmethod
    def DeleteItem(self, name:str):
        raise NotImplementedError()
    
    complete_enter = type_complete
    
    @abc.abstractmethod
    def GetShell(self, item) -> Shell:
        return NotImplementedError()
    
    def do_enter(self, args):
        """Enters a shell for working with the given item.
        
        Usage: enter [name]
        
        arg name: The name of the item to enter.
        """
        if args == None:
            self.perror("No name given.")
            return
        if args == "":
            self.perror("No name given.")
            return

        item = self.GetItemByName(args)
        shell = self.GetShell(item)
        shell.cmdloop()
        
