import abc
import asyncio
import json
import subprocess
import sys
import types
import typing

import cmd2
import pkg_resources

from fieuishell.FeedbackUI import ShellFeedbackUI
from fieuishell.ModalInputUI import InputModalShellUI
from fieuishell.ModalTrueFalseDefaultQuestionUI import ModalTrueFalseDefaultQuestionShellUI
from fieuishell.ModalTrueFalseQuestionUI import ModalTrueFalseQuestionShellUI

from cmd2_submenu import submenu
from cmd2.cmd2 import Cmd, parse_quoted_string


class Shell(cmd2.Cmd):
    """An abstract base class for routine UI based shells."""

    _feedbackUI: ShellFeedbackUI = None

    def get_feedback_ui(self) -> ShellFeedbackUI:
        if self._feedbackUI is None:
            self._feedbackUI = ShellFeedbackUI(self)
        return self._feedbackUI

    _trueFalseQuestionModalUI: ModalTrueFalseQuestionShellUI = None

    def get_true_false_question_modal_ui(self) -> ModalTrueFalseQuestionShellUI:
        if self._trueFalseQuestionModalUI is None:
            self._trueFalseQuestionModalUI = ModalTrueFalseQuestionShellUI(self)
        return self._trueFalseQuestionModalUI

    _trueFalseDefaultQuestionModelUI: ModalTrueFalseDefaultQuestionShellUI = None

    def get_true_false_default_question_modal_ui(self) -> ModalTrueFalseDefaultQuestionShellUI:
        if self._trueFalseDefaultQuestionModelUI is None:
            self._trueFalseDefaultQuestionModelUI = \
                ModalTrueFalseDefaultQuestionShellUI(self)
        return self._trueFalseDefaultQuestionModelUI

    _variable_commands: typing.Dict[str, "VarCommand"] = None

    def get_variable_commands(self):
        return self._variable_commands

    def add_variable_command(self, var_command: "VarCommand", name: str, aliases: typing.List[str],
                             listed: bool = True):
        if self._variable_commands is None:
            self._variable_commands = {}
        self._variable_commands[name] = var_command
        if listed:
            self.add_submenu(var_command, name, aliases)

    def do_print_variables(self, args):
        for name, var in self.get_variable_commands().items():
            self.poutput(name + " : " + var.value_to_print_string())

    def print_json_data(self, data: typing.Dict):
        s = json.dumps(data, indent=4, sort_keys=True)
        self.poutput(s)

    def do_coroutine(self, coro):
        """Runs a single co-routine synchonously.
        Returns the result.  Throws an exception
        if the co-routine throws an exception.  Does
        not intercept Cancellation.
        Can pass any async function/routine, or any future/task."""
        loop = asyncio.get_event_loop()
        assert isinstance(loop, asyncio.AbstractEventLoop)
        f = asyncio.ensure_future(coro)
        ret = loop.run_until_complete(f)
        return ret

    def do_print_plugin_names(self, args):
        """Prints the names of the shell plugins this shell hooks.

        Usage: print_plugin_names
        """
        plugin_names = self.get_plugin_names_v1()
        prepend = self.get_plugin_prepend()
        postpend = self.get_plugin_postpend()

        for plugin_name in plugin_names:
            self.poutput(prepend + plugin_name + postpend)

    @abc.abstractmethod
    def get_plugin_names_v1(self) -> typing.List[str]:
        """
        All shells should override this and call super().getPluginNamesV1() to get
        a list and append to it, before returning it.
        
        Returns a list of names for this shell plugin.  e.g. 'myspecialshell','allmyshells'
        Which will be turned into '[prepend]myspecialshell[postpend]'
        Which will be turned into '[prepend]allmyshells[postpend]'
        Plugins are to be registered in the setup.py file as follows:
        
        entry_points={
            '[prepend]myshell[postpend]' : 'myshellpluginscript = myshellpluginscript:pluginfuncname',
        },

        which will load the module myshellpluginscript and call the funciton pluginfuncname, passing a single parameter
        which will be an instance of this shell before its command loop is run.

        note: To add a command to a shell, one needs to add it to the __class__, not the instance.
        e.g. shell.__class__.do_foo = foocommand
        This is because the base cmd class does all its name searching and mangling by
        listing the attributes of the class rather than the instance.  For whatever reason.

        We have AddCommand and AddSubmenu methods to aid in this.
        
        We return a list so we can implement abstract plugins. e.g. ["all_foo","blue_small_foo"]

        The base super() function begins by returning "all"
        """
        return ["all"]

    @abc.abstractmethod
    def get_plugin_prepend(self) -> str:
        """Prepended to all shell plugins that inherit from this shell."""
        raise NotImplementedError()

    @abc.abstractmethod
    def get_plugin_postpend(self) -> str:
        """Postpend to all shell plugins that inherit from this shell."""
        raise NotImplementedError()

    def __init__(self):
        self.allow_cli_args = False
        super().__init__()
        for pluginname in self.get_plugin_names_v1():
            entrypoints = pkg_resources.iter_entry_points(
                self.get_plugin_prepend() + pluginname + self.get_plugin_postpend())
            for entrypoint in entrypoints:
                print(self.colorize("Loading shell plugin: " + entrypoint.name + ":" + pluginname, 'green'))
                method = entrypoint.load()
                method(self)
        self.prompt = self.get_prompt_text() + self.prompt_ending

    prompt_ending = ">"
    prompt_separator = '/'

    @abc.abstractmethod
    def get_prompt_text(self) -> str:
        raise NotImplementedError()

    def get_fork_args(self) -> typing.List[str]:
        """Return a list of arguments that, if passed to this shell as a __main__ function, would reproduce the
        current shell context. Base implementation automatically adds VarCommands."""
        ret = []
        for name, command in self.get_variable_commands().items():
            ret.append("-" + name)
            ret.append(command.value_to_print_string())
        return ret

    def do_fork(self, arg):
        """Forks a new shell in a new process.
        """
        args = [sys.executable, sys.modules[self.__class__.__module__].__file__]
        args.extend(self.get_fork_args())
        subprocess.Popen(args, creationflags=subprocess.CREATE_NEW_CONSOLE)

    def do_exit(self, arg):
        """Exits this shell."""
        return self.do_quit(arg)

    def add_command(self, name: str, target: types.FunctionType, complete: types.FunctionType = None):
        """Dynamically adds a command to the given shell.
        
        Usually called from a plugin's hooked function so a plugin can add commands to a shell.
        
        @param name: a string name for the command.  "foo" not "do_foo"        
        @param target: A function (callable) of the typical "do" type foo(self,args)
        @param complete A function (callable) of the typical "complete" type.
        
        note: internally we use setattr to add to the __class__ of the instance.  This is neccesary to make
        cmd2 able to dynamically find the methods.
        """
        setattr(self.__class__, "do_" + name, target)
        if complete != None:
            setattr(self.__class__, "complete_" + name, complete)

    def add_submenu(self, shell: cmd2.Cmd, name: str, aliases: list):
        submenu.AddSubmenu(shell, name, aliases,
                           reformat_prompt="{sub_prompt}",
                           shared_attributes={"debug":"debug"},
                           require_predefined_shares=True,
                           create_subclass=False,
                           preserve_shares=False,
                           persistent_history_file=None)(self.__class__)

    def parse_arguments(self, line: str) -> typing.List[str]:
        """Parses aruguments from a string into a list of arguments as per the underlying Cmd implementation."""
        return parse_quoted_string(line, preserve_quotes=False)

    def argument_exists(self, args: typing.List[str], lookingFor: typing.List[str]) -> bool:
        """Returns True or False if any of the given lookingFor arguments are in the given args list."""
        return self.index_of_argument(args, lookingFor) != -1

    def index_of_argument(self, args: typing.List[str], lookingFor: typing.List[str]) -> int:
        """Returns the index of an arugment in the args list, if it is one of the argumetns in lookingFor list.
        """
        if len(args) == 0:
            return -1
        for i in range(0, len(args)):
            for a in lookingFor:
                if args[i] == a:
                    return i
        return -1

    def get_argument_value(self, args: typing.List[str], lookingFor: typing.List[str]) -> str:
        """Returns the string value of the argument following any instance of any found argument in lookingFor, or None if
        there is no such argument found in the given args list.
        Simply put:  command-line 'commmand -t foo' would yield 'foo' if the lookingFor list was ['-t','--type']
        """

        i = self.index_of_argument(args, lookingFor)
        if i == -1:
            return None
        if i > (len(args) - 2):
            return None
        return args[i + 1]


T = typing.TypeVar("T")


class VarCommand(Shell, typing.Generic[T]):

    def get_plugin_names_v1(self) -> typing.List[str]:
        ret = super(VarCommand, self).get_plugin_names_v1()
        ret.append("var.command")
        return ret

    def get_plugin_prepend(self) -> str:
        return ""

    def get_plugin_postpend(self) -> str:
        return ""

    def get_prompt_text(self) -> str:
        return "var"

    _ui: InputModalShellUI[T] = None
    _value: T = None

    def get_value(self) -> T:
        return self._value

    def set_value(self, value: T):
        self._value = value

    def __init__(self, input_ui: InputModalShellUI[T], initial_value: T):
        super().__init__()
        self._ui = input_ui
        self._value = initial_value

    def value_to_print_string(self):
        return str(self._value)

    def do_print(self, arg):
        """Prints the value of this variable.
        Usage: print
        """
        self.poutput(self.value_to_print_string())

    def do_set(self, arg):
        """
        Sets the value of this variable.
        Usage: set
        """
        new_val = self.do_coroutine(self._ui.execute("New value"))
        self._value = new_val

    def set_from_args(self, name: str, args: typing.List[str], default: T) -> bool:
        """Returns true if found.  False if not."""
        for i in range(len(args) - 1):
            if args[i] == ("-" + name):
                valid, value = self._ui.validate(args[i + 1])
                if valid:
                    self.set_value(value)
                    return
        self.set_value(default)
