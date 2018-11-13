import abc
import os
import typing

import git

import fiepipelib.shells
from fiepipelib.gitstorage.routines.gitrepo import GitRepoRoutines
from fiepipelib.shells.AbstractShell import AbstractShell

class GitRepoShell(AbstractShell, abc.ABC):


    @abc.abstractmethod
    def get_routines(self) -> GitRepoRoutines:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_plugin_names_v1(self) -> typing.List[str]:
        ret = super().get_plugin_names_v1()
        ret.append('gitrepo')
        return ret

    def do_status(self, args):
        """Prints git status of the asset.

        Usage: status
        """
        routines = self.get_routines()
        routines.load()

        rep = routines.get_repo()
        assert isinstance(rep, git.Repo)
        self.poutput(rep.git.status())

    def do_list_untracked(self, args):
        """Lists the untracked files in this asset

        Usage list_untracked"""
        routines = self.get_routines()
        routines.load()


        for untracked in routines.get_untracked():
            text = untracked
            self.poutput(text)

    def do_list_modified(self, args):
        """Lists the changed files in this asset

        Usage list_changed"""
        routines = self.get_routines()
        routines.load()

        for changed in routines.get_modified():
            text = changed
            self.poutput(text)

    def untracked_complete(self, text, line, begidx, endidx):
        routines = self.get_routines()
        routines.load()

        ret = []

        all_untracked = routines.get_untracked()
        for untracked in all_untracked:
            if untracked.startswith(text):
                ret.append(untracked)
        return ret

    def modified_complete(self, text, line, begidx, endidx):
        routines = self.get_routines()
        routines.load()

        ret = []

        all_modified = routines.get_modified()
        for modified in all_modified:
            if modified.startswith(text):
                ret.append(modified)
        return ret

    def untracked_and_modified_complete(self, text, line,begidx,endidx):
        untracked = self.untracked_complete(text,line,begidx,endidx)
        modified = self.modified_complete(text,line,begidx,endidx)
        ret = []
        ret.extend(untracked)
        ret.extend(modified)
        return ret


    def do_add_interactive(self, args):
        """Enters the git interactive add mode for this asset.

        Usage: add_interactive"""
        routines = self.get_routines()
        routines.load()
        old_dir = os.curdir
        routines.check_create_change_dir()
        self.do_shell('git add -i')
        os.chdir(old_dir)

    complete_add = untracked_and_modified_complete

    def do_add(self, args):
        """Adds the given paths to git index(tracking)

        Usage: add [path] [...]"""
        args = self.parse_arguments(args)
        routines = self.get_routines()
        routines.load()
        repo = routines.get_repo()
        for arg in args:
            output_text = repo.git.add(arg)
            self.poutput(output_text)

    def do_add_all_untracked(self, args):
        """Adds all untracked files to the index(tracking)

        Usage: add_all_untracked
        """
        args = self.parse_arguments(args)
        routines = self.get_routines()
        routines.load()
        repo = routines.get_repo()
        for untracked in routines.get_untracked():
            output_text = repo.git.add(untracked)
            self.poutput(output_text)

    def do_add_all_modified(self, args):
        """Adds all untracked files to the index(tracking)

        Usage: add_all_untracked
        """
        args = self.parse_arguments(args)
        routines = self.get_routines()
        routines.load()
        repo = routines.get_repo()
        for modified in routines.get_modified():
            output_text = repo.git.add(modified)
            self.poutput(output_text)

    def do_add_all(self, args):
        self.do_add_all_untracked(args)
        self.do_add_all_modified(args)

    def do_can_commit(self, args):
        """Checks if this GIT Storage Repo can commit."""
        routines = self.get_routines()
        routines.load()
        can, reason = routines.can_commit()
        if can:
            self.poutput(self.colorize("Yes",'green'))
            self.poutput(self.colorize(reason,'green'))
        else:
            self.poutput(self.colorize("No",'red'))
            self.poutput(self.colorize(reason,'yellow'))