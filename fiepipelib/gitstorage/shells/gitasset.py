import os
import os.path
import typing

import git

import fiepipelib.shells.AbstractShell
from fiepipelib.container.shells.container_id_var_command import ContainerIDVariableCommand
from fiepipelib.gitstorage.routines.gitasset import GitAssetRoutines
from fiepipelib.gitstorage.shells.vars.asset_id import AssetIDVarCommand
from fiepipelib.gitstorage.shells.vars.root_id import RootIDVarCommand


class Shell(fiepipelib.shells.AbstractShell.AbstractShell):
    _container_id_var: ContainerIDVariableCommand
    _root_id_var: RootIDVarCommand
    _asset_id_var: AssetIDVarCommand

    def __init__(self, container_id: str, root_id: str, asset_id: str):
        self._container_id_var = ContainerIDVariableCommand(container_id)
        self.add_variable_command(self._container_id_var, 'container', [], False)
        self._root_id_var = RootIDVarCommand(root_id)
        self.add_variable_command(self._root_id_var, 'root', [], False)
        self._asset_id_var = AssetIDVarCommand(asset_id)
        self.add_variable_command(self._asset_id_var, "asset", [], False)
        super(Shell, self).__init__()
        routines = self.get_routines()
        routines.load()
        os.chdir(routines._working_asset.GetSubmodule().abspath)
        self.do_coroutine(routines.update_lfs_track_patterns())

    def get_routines(self) -> GitAssetRoutines:
        return GitAssetRoutines(self._container_id_var.get_value(), self._root_id_var.get_value(),
                                self._asset_id_var.get_value(), feedback_ui=self.get_feedback_ui())

    def get_plugin_names_v1(self) -> typing.List[str]:
        ret = super().get_plugin_names_v1()
        ret.append('gitasset')
        return ret

    def get_prompt_text(self) -> str:
        routines = self.get_routines()
        routines.load()
        fqdn = routines.container.GetFQDN()
        container_name = routines.container.GetShortName()
        subpath = routines._working_asset.GetSubmodule().path
        root_name = routines._root.GetName()
        return self.prompt_separator.join(['fiepipe', fqdn, container_name, root_name, subpath])

    def do_status(self, args):
        """Prints git status of the asset.
        
        Usage: status
        """
        routines = self.get_routines()
        routines.load()
        submod = routines._working_asset.GetSubmodule()
        if not routines._working_asset.IsCheckedOut():
            self.poutput(self.colorize("not checked out.", "yellow"))
            return
        rep = submod.module()
        assert isinstance(rep, git.Repo)
        self.poutput(rep.git.status())

    def do_list_untracked(self, args):
        """Lists the untracked files in this asset

        Usage list_untracked"""
        routines = self.get_routines()
        routines.load()

        if not routines._working_asset.IsCheckedOut():
            raise git.GitError("Not checked out.")

        all_untracked = routines.get_untracked()
        for untracked in routines.get_untracked():
            text = self.colorize(untracked, 'yellow')
            self.poutput(text)

    def untracked_complete(self, text, line, begidx, endidx):
        routines = self.get_routines()
        routines.load()

        if not routines._working_asset.IsCheckedOut():
            return []

        ret = []

        all_untracked = routines.get_untracked()
        for untracked in all_untracked:
            if untracked.startswith(text):
                ret.append(untracked)
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

    complete_add = untracked_complete

    def do_add(self, args):
        """Adds the given paths to git index(tracking)

        Usage: add [path] [...]"""
        args = self.parse_arguments(args)
        routines = self.get_routines()
        routines.load()
        repo = routines._working_asset.GetRepo()
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
        repo = routines._working_asset.GetRepo()
        for untracked in routines.get_untracked():
            output_text = repo.git.add(untracked)
            self.poutput(output_text)

    def do_update_lfs_tracked_files(self, args):
        """Updated lfs tracked files for this asset.
        Usage: update_lfs_tracked_files
        """
        routines = self.get_routines()
        routines.load()
        self.do_coroutine(routines.update_lfs_track_patterns())
