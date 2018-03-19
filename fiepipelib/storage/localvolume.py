import fiepipelib.abstractmanager
import fiepipelib.localuser
import os
import os.path
import textwrap
import pathlib

def FromJSONData(data):
    ret = localvolume()
    ret._name = data['name']
    ret._path = data['path']
    ret._adjectives = data['adjectives']
    return ret

def ToJSONData(volume):
    ret = {}
    ret['version'] = 1
    ret['name'] = volume._name
    ret['path'] = volume._path
    ret['adjectives'] = volume._adjectives
    return ret

def FromParameters(name, path, adjectives = []):
    ret = localvolume()
    ret._name = name
    ret._path = path
    ret._adjectives = adjectives
    return ret

def GetHomeVolume(localUser):
    assert isinstance(localUser, fiepipelib.localuser.localuser)
    return FromParameters("home",localUser.GetHomeDir(),[CommonAdjectives.containerrole.WORKING_VOLUME])


def GetAllRegisteredLocalVolumes(localUser):
    ret = []
    registry = localvolumeregistry(localUser)
    ret.extend(registry.GetAll())
    return ret

def GetAllMountedVolumes(localUser,removableAdjectives = []):
    all = []
    all.append(GetHomeVolume(localUser))
    all.extend(GetAllRegisteredLocalVolumes(localUser))
    all.extend(GetUnregisteredRemovableVolumes(localUser,removableAdjectives))
    ret = []
    for a in all:
        assert isinstance(a, localvolume)
        if a.IsMounted():
            ret.append(a)
    return ret

def GetUnregisteredRemovableVolumes(localUser, adjectives = []):
    """Does platform specific scanning for unregistered removable volumes and returns them.

    The passed adjectives list is neccesary since removable volumes don't inherently have adjectives.

    You instead, tell the system what adjectives you want applied to all found volumes when you do the scanning.

    As removable volumes can migrate from system to system, it's not reasonable to assume the same sets of adjectives
    mean the same things from system to system.
    """

    ret = []

    #useful
    registry = localvolumeregistry(localUser)

    assert isinstance(localUser, fiepipelib.localuser.localuser)
    platform = localUser.GetPlatform()

    #windows logic for drive letter scanning
    if isinstance(platform, fiepipelib.localplatform.localplatformwindows):
        #we walk drive letters for mounted drives
        driveLetters = platform.getLogicalDriveLetters()
        for driveLetter in driveLetters:

            #check for a volume.name file
            volumeNamePath = pathlib.Path(os.path.join(driveLetter + ":\\","volume.name"))

            #UGLY.  But empty optical drives throw.  And who knows what else.
            try:
                if volumeNamePath.exists():
                   if volumeNamePath.is_file():
                        with volumeNamePath.open('r') as f:
                            lines = f.readlines()
                        for l in lines:
                            name = l.strip()
                            if len(name) > 0:
                                if name.startswith("#"):
                                    #skip comments
                                    continue
                                #if we get here, we found a drive with a name
                                #we just need to make sure it's not registered first
                                if len(registry.GetByName(name)) == 0:
                                    ret.append(FromParameters(name,driveLetter + ":\\",adjectives))
            except:
                pass
    return ret
                            
def SetupUnregisteredRemovableVolume(path, name):
    """Sets up a removable volume to be recognized during scanning for removable volumes.
    Usually this just sets up a 'volume.name' file in the root with the name.

    Warning.  This just works on the given path.  It doesn't do any checking to make sure
    the given path is actually a removable media of any kind.
    
    """
    path = pathlib.Path(os.path.join(path, "volume.name"))
    with path.open('w') as f:
        f.writelines(['#Volume name for fiepipe local volume\n',name])



def FilterVolumesByAdjectives(volumes, filters):
    """
    @param volumes: A list of volumes to filter.  Perhaps from GetAllMountedVolumes or GetAllLocalVolumes?
    @param filters: A list of adjectives to filter by.  To pass, a volume must contain all adjectives in the list.
    @return: A list of passing volumes.
    """
    assert isinstance(volumes, list)
    assert isinstance(filters, list)

    passed = []

    for volume in volumes:
        assert isinstance(volume, localvolume)
        filtered = False
        for filter in filters:
            if not volume.HasAdjective(filter):
                filtered = True
        if not filtered:
            passed.append(volume)
    return passed



def CommonAdjectivesDict():
    ret = {}
    ret['latency'] = {
        CommonAdjectives.latency.LATENCY_HIGH:'e.g. optical drives or network drives with high network latency',
        }
    ret['speed'] = {
        CommonAdjectives.speed.SPEED_HIGH:'e.g. a RAID 0 or high performance network volume.',
        CommonAdjectives.speed.SPEED_LOW:'e.g. an optical drive or higly redundant drive like a raid 5 or 6 in some cases.',
        CommonAdjectives.speed.DEDICATED_STREAM:'Storage which has physically dedicated spindles, busses and fiber exclusively dedicated to guaronteeing a "stream" of a particular bandwidth.',
        }
    ret['redundancy'] = {
        
        CommonAdjectives.redundnacy.HIGH_RISK:"e.g. A RAID 0 e.g. Portable drive that travels a lot.",
        CommonAdjectives.redundnacy.HIGH_REDUNDANCY:"A drive that is engineered to fail far less easily than normal.  Such as a RAID 1, RAID 5 or RAID 6.",
        CommonAdjectives.redundnacy.RECOVERABLE:"A drive that is recoverable from failure.  Usually because it's backed-up regularly. RAID levels are probably not enough here because the whole chasis or controller can take a power hit.",
        CommonAdjectives.redundnacy.GEO_REDUNDANT:"Storage that can survive a physical disaster of large proportions such as a fire, becasue it is backed-up off-site.",
        }
    ret['container role'] = {
        
        CommonAdjectives.containerrole.WORKING_VOLUME:"Storage that's meant to be worked on by applications.",
        CommonAdjectives.containerrole.BACKING_VOLUME:"Storage that provides robust online 'backing' to working volumes.  A place to frequently push and pull publishes and versions.  The data need not be workable here.",
        CommonAdjectives.containerrole.ARCHIVE_VOLUME:"Storage that's meant to keep in a long-term, near-line or even off-line sense.  The data need not be workable here.",
        }
    return ret

class CommonAdjectives:

    class latency:
        """Absense of a latency adjective suggests latency comparable to a contemporary local drive."""

        LATENCY_HIGH = "high_latency"

    class speed:
        """Absense of a speed adjective suggets speed (bandwidth) comparable to a contemporary local drive."""

        SPEED_HIGH = "high_speed"
        SPEED_LOW = "low_speed"
        DEDICATED_STREAM = "dedicated_stream"

    class redundnacy:
        """Absense of a redundancy adjective suggests a drive that can reasonably fail and is not
        known to be backed up.  e.g. A removable drive e.g. A scratch drive e.g. A system drive that's not being backed up."""

        HIGH_RISK = "high_risk_fail"
        HIGH_REDUNDANCY = "low_risk_fail"
        RECOVERABLE = "recoverable"
        GEO_REDUNDANT = "geo_redundant"

    class containerrole:
        """Used to mark certain volumes for roles in a the container system"""

        WORKING_VOLUME = "working_volume"
        BACKING_VOLUME = "backing_volume"
        ARCHIVE_VOLUME = "archive_volume"


class localvolume(object):
    """Represents a local storage volume as it currently exists on the system.  Unlike traditional low-level computer systems, a volume in this case is just a directory.  It's found via a path.
    Most modern computer systems have virtualized volumes to this degree via virtual file systems (VFS).
    
    Technically speaking, we're okay with some network file systems here.  The requirement is that the storage "effectively" be local.  Which means POSIX compliant.  So, a clustered SAN file system mounted
    on this system might work fine.  A well tested NFS mount might work fine.
  
    However, keep in mind that many network file-systems that appear to be local file-systems are not actually POSIX compliant.
    Most often, they don't properly handle file-locks.  So, if a particualr NFS mount lies about file-locks and doesn't actually execute a reliable network based file lock, it's dangerous to configure it
    as a local volume.

    I (the author) have personally run into enterprise level NFS storage appliances that claimed to properly execute network based lock managment over NFS, and actually did not get it right.  BE VERY CAREFUL ABOUT THIS!
    """

    _name = None
    _path = None
    _adjectives = None

    def GetName(self):
        """Typically, a volume mapping system will reference the volume by this name. 'home' is reserved for a volume that points to the user's home (~) directory."""
        return self._name

    def GetPath(self):
        """The path to the volume.  Essentially, a path to a directory.  This is platform specific, as local volumes don't migrate from machine to machine."""
        return self._path

    def IsMounted(self):
        """Checks if the volume is mounted.  We check if the path exists, if it's a directory, and if there isn't an entry in it named 'volume.notmounted'

        In some OSes you might have a removable volume that mounts into an existing subdirectory as a mountpoint.  That can make it difficult
        to detect if the removable media is not mounted, without knowing quite a bit about the mount table of the system.  If that's the case,
        try putting an empty text file named 'volume.notmounted' in the empty mount point.  The sytem will find it and return false here.

        In some OSes, you might mount all removable volumes in the same place, making it difficult to differentiate between them.  In this case,
        we also look for a file named 'volume.name' and check the first line of text for a match to this volume's name.

        We stick to platform independent logic here because it's likley that a removable drive will migrate from system to system.
        """
        #must exist
        if os.path.exists(self.GetPath()):
            #must be a directory
            if os.path.isdir(self.GetPath()):
                #must be no entry named volume.notmounted
                if not os.path.exists(os.path.join(self.GetPath(),"volume.notmounted")):
                    #logic for checking a explicitly named volume
                    if os.path.exists(os.path.join(self.GetPath(),"volume.name")):
                        #it's explicitly named, we need to make sure it's the right one for this volume.
                        with open(os.path.join(self.GetPath(),"volume.name")) as f:
                            lines = f.readlines()
                        for line in lines:
                            #skip comments
                            if line.startswith("#"):
                                continue
                            #skip empty
                            if len (line.strip()) != 0:
                                #it's not empty or a comment.  it's the name
                                return line.strip() == self._name
                    else:
                        #it's not explicitly named, so we've verified enough.
                        return True
        return False

    def GetAdjectives(self):
        return self._adjectives.copy()

    def AddAdjective(self, adjective):
        assert isinstance(adjective, str)
        if adjective not in self._adjectives:
            self._adjectives.append(adjective)

    def RemoveAdjective(self, adjective):
        assert isinstance(adjective, str)
        if adjective in self._adjectives:
           self._adjectives.remove(adjective)
    
    def HasAdjective(self, adjective):
        return adjective in self._adjectives



class localvolumeregistry(fiepipelib.abstractmanager.abstractlocalmanager):

    def FromJSONData(self, data):
        return FromJSONData(data)

    def ToJSONData(self, item):
        return ToJSONData(item)

    def GetColumns(self):
        ret = super().GetColumns()
        ret.append(("name","text"))
        return ret

    def GetPrimaryKeyColumns(self):
        return ["name"]

    def GetManagedTypeName(self):
        return "localvolume"

    def GetByName(self, name):
        return self._Get([("name",name)])

    def DeleteByName(self, name):
        self._Delete("name",name)

class VolumeNotFoundException(Exception):
    pass