import asyncio

from fiepipelib.shells.AbstractShell import AbstractShell


class ComponentManagerPipeServerCommand(AbstractShell):

    def ParseConnectionStringArgument(self, arg:str) -> (str,str):
        """Returns the hostname,username from a conenction string argument"""
        args = arg.split('@',1)
        if len(args == 2):
            return args[0], args[1]
        else:
            return args[0], None


    def do_pull_all(self, args):
        """Pulls containers from the given server for the current FQDN.
        All local containers in conflict will be overwritten.
        Therefore, the remote server had better be authoritative.

        Usage: pull_all {[user]@}[host]

        param user: the username to use to log into the host.

        param host: the hostname or ipaddress of a server from which to pull

        e.g. pull_all me@computer.machine.org
        e.g. pull_all server.mycompany.com
        """
        args = self.parse_arguments(args)

        if len(args == 0):
            self.get_feedback_ui().error("No connection string given.")
            return

        hostname, username = self.ParseConnectionStringArgument(args[0])
        try:
            self.do_coroutine(self.get_container_managment_routines().PullAllRoutine(hostname, username))
        except asyncio.CancelledError as ce:
            self.get_feedback_ui().feedback("User canceled.")



    def do_push_all(self,args):
        """Pushes all containers for this FQDN to the given server.
        Will overwrite all conflicting containers on the server.
        Therefore, this machine had better be authoritative.

        Usage: push_all {[user]@}[host]

        param user: the username to use to log into the host.

        param host: the hostname or ipaddress of a server to push up to.

        e.g. push_all me@computer.machine.org
        e.g. push_all server.mycompany.com
        """
        args = self.parse_arguments(args)

        if len(args == 0):
            self.get_feedback_ui().error("No connection string given.")
            return

        hostname, username = self.ParseConnectionStringArgument(args[0])
        try:
            self.do_coroutine(self.get_container_managment_routines().PushAllRoutine(hostname, username))
        except asyncio.CancelledError as ce:
            self.get_feedback_ui().feedback("User canceled.")


    def complete_pull(self, text, line, begidx, endidx):
        return self.index_based_complete(text, line, begidx, endidx,
                                         {{1:[]}}, all_else=self.type_complete)

    def do_pull(self, args):
        """Pulls containers from the given server.
        Only named containers are pulled, but those in conflict will be overwritten.
        Therefore, the remote server had better be authoritative for those named containers.

        Usage: pull {[user]@}[host] [name|id] [...]

        param user: the username to use to log into the host.

        param host: the hostname or ipaddress of a server from which to pull.

        param name|id: either the name or id of the containers to pull.
        those that fail to match on name will fail over to matching on ID.
        You can speficy multiple containers separated by spaces here.

        e.g. pull me@computer.machine.org bigcontainer
        e.g. pull server.mycompany.com bigcontainer mediumcontainer
        """

        args = self.parse_arguments(args)

        if len(args == 0):
            self.get_feedback_ui().error("No connection string given.")
            return

        names = args[1,-1]

        hostname, username = self.ParseConnectionStringArgument(args[0])

        try:
            self.do_coroutine(self.get_container_managment_routines().PullRoutine(hostname, names, username))
        except asyncio.CancelledError as ce:
            self.get_feedback_ui().feedback("User canceled.")

    def complete_push(self, text, line, begidx, endidx):
        return self.index_based_complete(text, line, begidx, endidx,
                                         {{1:[]}}, all_else=self.type_complete)

    def do_push(self, args):
        """Pushes containers to the given server.
        Only named containers are pushed, but those in conflict will be overwritten.
        Therefore, this machine had better be authoritative for those named containers.

        Usage: push {[user]@}[host] [name|id] [...]

        param user: the username to use to log into the host.

        param host: the hostname or ipaddress of a server to push to.

        param name|id: either the name or id of the containers to push.
        those that fail to match on name will fail over to matching on ID.
        You can speficy multiple containers separated by spaces here.

        e.g. push me@computer.machine.org bigcontainer
        e.g. push server.mycompany.com bigcontainer mediumcontainer
        """
        args = self.parse_arguments(args)

        if len(args == 0):
            self.get_feedback_ui().error("No connection string given.")
            return

        names = args[1,-1]

        hostname, username = self.ParseConnectionStringArgument(arg[0])

        try:
            self.do_coroutine(self.get_container_managment_routines().PushRoutine(hostname, names, username))
        except asyncio.CancelledError as ce:
            self.get_feedback_ui().feedback("User canceled.")