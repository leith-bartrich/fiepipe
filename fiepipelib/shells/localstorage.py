import sys
import fiepipelib.localuser
import fiepipelib.privatekey
import fiepipelib.authoredlegalentity
import fiepipelib.storage.localvolume
import os.path
import json
import fiepipelib.shells.abstract
import cmd2
import textwrap
import pathlib
import functools

class Shell(fiepipelib.shells.abstract.Shell):
    _localUser = None

    def __init__(self, localUser):
        assert isinstance(localUser, fiepipelib.localuser.localuser)
        self._availableAdjectives = fiepipelib.storage.localvolume.CommonAdjectivesDict()
        super().__init__()
        self._localUser = localUser

    def getPluginNameV1(self):
        return 'local_storage'

    def GetBreadCrumbsText(self):
        return self.breadcrumbs_separator.join(["pipe","local_storage"])

    def do_list_mounted_volumes(self,arg):
        volumes = fiepipelib.storage.localvolume.GetAllMountedVolumes(self._localUser)
        for vol in volumes:
            assert isinstance(vol, fiepipelib.storage.localvolume.localvolume)
            print ( vol.GetName() + ": " + vol.GetPath() + "  [" + "] [".join(vol.GetAdjectives()) + "]" )

    def do_list_configured_volumes(self,arg):
        manager = fiepipelib.storage.localvolume.localvolumeregistry(self._localUser)
        volumes = manager.GetAll()
        for vol in volumes:
            print ( vol.GetName() + ": " + vol.GetPath() + "  [" + "] [".join(vol.GetAdjectives()) + "]" )

    def do_delete_configured_volume(self,arg):
        """Deletes the named configured storage.
        Usage: DeleteConfiguredVolume [name]
        arg name: the name of the configured storage to delete"""
        if arg == None:
            print("No storage specified.")
            return
        if arg == "":
            print ("No storage specified.")
            return
        manager = fiepipelib.storage.localvolume.localvolumeregistry(self._localUser)
        manager.DeleteByName(arg)

    complete_create_volume = functools.partial(cmd2.Cmd.path_complete)

    def do_create_volume(self,arg):
        """Creates a named configured volume.
        Usage: CreateConfiguredVolume [name] [path]
        arg name: the name of the new volume.  No spaces please.
        arg path: the absolute path of the new storage volume.  Spaces are allowed but always discouraged.
        """
        args = arg.split(maxsplit=1)
        if len(args) != 2:
            print ("Incorrect number of arguments specified.")
            return
        if not os.path.isabs(args[1]):
            print("Path must be absolute: " + args[1])
            return
        vol = fiepipelib.storage.localvolume.FromParameters(args[0],args[1])
        manager = fiepipelib.storage.localvolume.localvolumeregistry(self._localUser)
        manager.Set([vol])
        
    _availableAdjectives = None

    def printAdjectives(self):
        print("Available Adjectives:")
        for catName in self._availableAdjectives.keys():
            print (self.colorize("  " + catName + ":","green"))
            cat = self._availableAdjectives[catName]
            for adj in cat.keys():
                print ("    " + adj + ":")
                print(self.colorize(textwrap.indent(textwrap.fill(cat[adj]),"      "),"blue"))
                

    def do_add_adjective(self,arg):
        if arg == None:
            print("No storage specified.")
            return
        if arg == "":
            print ("No storage specified.")
            return
        manager = fiepipelib.storage.localvolume.localvolumeregistry(self._localUser)
        volumes = manager.GetByName(arg)
        if len (volumes) == 0:
            print ("Volume not found: " + arg)
            return
        volume = volumes[0]
        assert isinstance(volume, fiepipelib.storage.localvolume.localvolume)
        self.printAdjectives()
        toAdd = self.AskStringQuestion("Adjective to add")
        if (toAdd == None):
            print("Empty.  Not adding.")
            return
        if (toAdd.strip() == ""):
            print("Empty.  Not adding.")
            return
        if not volume.HasAdjective(toAdd):
            volume.AddAdjective(toAdd)
        manager.Set([volume])

    def do_delete_adjective(self,arg):
        if arg == None:
            print("No storage specified.")
            return
        if arg == "":
            print ("No storage specified.")
            return
        manager = fiepipelib.storage.localvolume.localvolumeregistry(self._localUser)
        volumes = manager.GetByName(arg)
        if len (volumes) == 0:
            print ("Volume not found: " + arg)
            return
        volume = volumes[0]
        assert isinstance(volume, fiepipelib.storage.localvolume.localvolume)
        print("Adjectives currently on " + volume.GetName() + ":")
        for adj in volume.GetAdjectives():
            print (adj)
        toRemove = self.AskStringQuestion("Adjective to remove")
        if (toRemove == None):
            print("Empty.  Not removing.")
            return
        if (toRemove.strip() == ""):
            print("Empty.  Not removing.")
            return
        if volume.HasAdjective(toRemove):
            volume.RemoveAdjective(toRemove)
        else:
            print("No such adjective: " + toRemove)
        manager.Set([volume])

    def external_volume_paths_complete(self,text,line,begidx,endidx):
        
        ret = []
        platform = self._localUser.GetPlatform()

        if isinstance(platform, fiepipelib.localplatform.localplatformwindows):
            #windows logic.  drive letter paths.
            letters = platform.getLogicalDriveLetters()
            for letter in letters:
                if letter.lower().startswith(text.lower()):
                    ret.append(letter + ":\\")
            return ret
        else:
            #on linux, we default to path completion
            return cmd2.path_complete(text,line,begidx,endidx)

    complete_setup_removable = external_volume_paths_complete

    def do_setup_removable(self, args):
        if args == None:
            print ("No path specified.")
            return
        if args == "":
            print("No path specified.")
            return
        
        pth = pathlib.Path(args)
        if not pth.is_dir():
            print ("Not a valid path to a directory.")
            return

        name = self.AskStringQuestion("Name for removable volume")

        if name == "":
            print("Volume must be given a name.")
            return

        fiepipelib.storage.localvolume.SetupUnregisteredRemovableVolume(str(pth.absolute()),name)


