import sys
import typing

import fiepipelib.gitstorage.data.git_asset
import fiepipelib.gitstorage.data.git_root
import fiepipelib.gitstorage.data.git_working_asset
import fiepipelib.gitstorage.data.local_root_configuration
import fiepipelib.gitstorage.shells.roots_component
import fiepipelib.legalentity.registry.data.registered_entity
import fiepipelib.locallymanagedtypes.shells.AbstractLocalManagedTypeCommand
import fiepipelib.shells.AbstractShell
import fiepipelib.gitstorage.shells.gitroot
from fiepipelib.container.shared.routines.container import ContainerRoutines
from fiepipelib.container.shells.container_id_var_command import ContainerIDVariableCommand
from fiepipelib.components.shells.component import AbstractComponentContainerShell


class ContainerShell(fiepipelib.shells.AbstractShell.AbstractShell, AbstractComponentContainerShell):
    """A shell for working in a local container"""

    def get_plugin_names_v1(self) -> typing.List[str]:
        ret = super(ContainerShell, self).get_plugin_names_v1()
        ret.append('container')
        return ret

    def get_prompt_text(self) -> str:
        routines = self.get_container_routines()
        routines.load()
        container = routines.get_container()
        name = container.GetShortName()
        return self.prompt_separator.join(['fiepipe', container.GetFQDN(), container.GetShortName()])

    _container_id_var: ContainerIDVariableCommand = None

    def get_container_id_var(self) -> ContainerIDVariableCommand:
        return self._container_id_var

    def __init__(self, container_id_var: ContainerIDVariableCommand):
        self._container_id_var = container_id_var
        super().__init__()
        self.add_variable_command(container_id_var, "container", [], False)
        roots_submenu = fiepipelib.gitstorage.shells.roots_component.RootsComponentCommand(self._container_id_var)
        self.add_submenu(roots_submenu, "roots", [])

    def get_container_routines(self) -> ContainerRoutines:
        return ContainerRoutines(self._container_id_var.get_value())


def main():
    container_var = ContainerIDVariableCommand("")
    if not container_var.set_from_args("container", sys.argv[1:], ""):
        print("No container id given. e.g. -container 89347589372589")
        exit(-1)
    shell = ContainerShell(container_var)
    shell.cmdloop()


if __file__ == "__main__":
    main()
