import git
import git.util
import os
import os.path
import tempfile
import fiepipelib.git.routines.repo
import fiepipelib.gitstorage.data.git_asset
import fiepipelib.git.routines.ignore
import shutil
import pathlib

def InitializeSystem(repo):
    assert isinstance(repo, git.Repo)
    repo.git.submodule.init()


def Add(repo, name, path, url, branch = None, no_checkout=False):
    """@return: the submodule
    """
    assert isinstance(repo, git.Repo)

    args = ['add']
    if not branch == None:
        args.append('-b')
        args.append(branch)
    args.append('--name')
    args.append(name)
    args.append('--')
    args.append(url)
    args.append(path)
    repo.git.submodule(args)
    
def Remove(repo, name):
    """Fully removes a submodule from the worktree and from the repo configuration.
    Doesn't care if the submodule is dirty.
    """
    assert isinstance(repo, git.Repo)
    submod = repo.submodule(name)
    assert isinstance(submod, git.Submodule)
    submod.remove(module = True, force = True, configuration = True)

def CreateEmpty(repo, subpath, name, url:str=None):
    """Creates an empty submodule by creating a new temporary empty repository
    and then adding it as a submodule.  The temporary repo is then deleted.

    To keep submodule for freaking out, we add a .gitignore and commit that change,
    so that we have at least one commit at the 'HEAD'

    Note that as a result, all the urls for the new submodule are pointing
    to an invalid repoistory on the local system that likely is platform
    dependent.  Meaning, this submodule is somewhat broken in 'purist GIT' terms.
    Specifically, because a checkout of the parent module will not know where
    to go get this submodule by default.  Also, because the local copy has
    invalid urls from which to push or pull this submodule.

    You need to use the other routines in this python module to set reasonable
    urls in the various locations in a reasonable way to bring this submodule
    into some reasonable form over time.

    However, keep in mind, that there is no "right" url for any submoudle, as
    their urls should change based on what 'site' you are using at any given time.

    @return: the submodule"""
    assert isinstance(repo, git.Repo)
    assert isinstance(subpath, str)
    tempdirpath = tempfile.mkdtemp()
    tempRepo = fiepipelib.git.routines.repo.InitWorkingTreeRoot(tempdirpath)
    fiepipelib.git.routines.ignore.CheckCreateIgnore(tempRepo)
    tempRepo.index.commit("Initial commit.  Added empty .gitignore")
    fiepipelib.git.routines.ignore.AddIgnore(tempRepo, ".assetlocal/")
    ret = Add(repo,name,subpath,tempdirpath,None,False)
    tempRepo.close()
    fiepipelib.git.routines.repo.DeleteLocalRepo(tempdirpath)
    #shutil.rmtree(tempdirpath)
    if url is not None:
        SetURL(repo,name,url)
    return ret

def ChangeURL(repo, name, url, revertGitModulesFile = True):
    """Changes the urls in all places. Optionally reverting changes to the .gitmodules file.

    The .gitmodules file is tracked by the repository itself and is only used to populate
    the functional local urls.  Therefore, if you just want to make a local change but leave
    the default for others, set revertGitModulesFile to True (default).  If instead you want
    the change in the url to be pushed up as the default for everyone, set it to False.

    Note the sync sometimes takes a while.  Therefore, you might want to do your own loop for
    multiple changes and call the sync once rather than call this multiple times.
    
    Simple pseudocode for such a loop: FOR name in names { olds[name] = GetURL; SetURL(new); }; Sync; FOR name in names {SetURL(olds[name])}; 

    If branch is not specified, it defaults to "master"

    Note this doesn't actually run an update or fetch.  It just gets you ready to do so.
    """
    assert isinstance(repo, git.Repo)
    old = GetURL(repo,name)
    SetURL(repo,name,url)
    Sync(repo)
    if (revertGitModulesFile):
        SetURL(repo,name,old)

def GetURL(repo, name):
    """Gets the url info from the current .gitmodules file.
    @return: A tuple in the format (url,branch)"""
    assert isinstance(repo, git.Repo)
    oldurl = repo.git.config("--file=.gitmodules","--get", "submodule." + name + ".url")
    #oldbranch = repo.git.config("--file=.gitmodules","--get", "submodule." + name + ".branch")
    #return (oldurl,oldbranch)
    return oldurl

def SetURL(repo, name, url):
    """Sets the url in the .gitmodules file"""
    assert isinstance(repo, git.Repo)
    ret = "setting url\n"
    ret = ret + repo.git.config("--file=.gitmodules","submodule." + name + ".url", url)
    #ret = ret + "setting branch\n"
    #ret = ret + repo.git.config("--file=.gitmodules","submodule."+ name + ".branch " + branch)
    
def Sync(repo):
    """Pushes the url from .gitmodules to the local repository configurations.
    """
    return repo.git.submodule("sync")

def CreateFromSubDirectory(repo, subpath, name, forgedHistory=False, url:str=None):
    """Creates a submodule from an existing subdirectory in the repository.

    If the subdirectory was already comitted, it removes it form tracking before
    creating the submodule.

    Also works if there is nothing there yet.  Meaning you can probably call this
    instead of CreateEmpty in many cases.

    If forgedHistory is True and the given folder has a commit history, the
    history will be preserved in the new submodule via a history filter.

    If forgedHistory is False, the new submodule will have no commits.
    
    forgedHistory=True is not currently implemented and will throw an exception.

    Note this does not commit the submodule.

    Note this usually uses CreateEmpty and all warnings about URLs from that routine apply here.

    Throws NotADirectoryError if the path points to something that exists and is not a directory.

    Throws FileExistsError if a submodule already exists at that path or by that name.

    Throws NotImplementedError currently, if you specify forgedHistory = True

    Throws IOError if the given path is absolute rather than relative.

    @return: The new Submodule
    """

    if forgedHistory:
        raise NotImplementedError()

    assert isinstance(repo, git.Repo)

    if os.path.isabs(subpath):
        raise IOError("Path is absolute. Should be relative.")

    #build paths
    workingDir = repo.working_tree_dir
    submoduleAbsolutePath = os.path.join(workingDir,subpath)

    ###We may need to put this logic back in.
    #check if it's already a submodule
    #for sub in repo.submodules:
    #    assert isinstance(sub, git.Submodule)
    #    if os.path.samefile(sub.abspath,submoduleAbsolutePath):
    #        raise FileExistsError(submoduleAbsolutePath)
    #    if sub.name == name:
    #        raise FileExistsError(name)
        

    #check if it exists and isn't a directory
    if os.path.exists(submoduleAbsolutePath) and not os.path.isdir(submoduleAbsolutePath):
        raise NotADirectoryError(submoduleAbsolutePath)

    #we remove the directory recurisvely from the index.  note this doesn't delete
    #actual files, but instead markes them deleted for the next commit.  Effectively
    #dropping them from tracking for the parent module but keeping them in the
    #history.  We do this before adding the submodule because once the submodule is added
    #this path is ignored.  Git must be told to remove them first when replaying changes.
    print("Removing any existing files from git index.")
    repo.git.rm("--cached", "--ignore-unmatch", "-r", subpath)

    #move out of the way or create an empty temp dir if need be.
    tempPath = tempfile.mktemp(prefix="createsubmod_", dir=workingDir)
    if (os.path.exists(submoduleAbsolutePath)):
        os.rename(submoduleAbsolutePath,tempPath)
    else:
        os.mkdir(tempPath)

    #make a new submodule
    print("Creating new empty submodule.")
    ret = CreateEmpty(repo,subpath,name,url)

    #move contents back in
    for e in os.listdir(tempPath):
        os.rename(os.path.join(tempPath,e),os.path.join(submoduleAbsolutePath,e))

    #delete now empty temp dir
    os.rmdir(tempPath)

    return ret

def Checkout(repo, submodule, recursive=False):
    """Runs an update appropriate for an initial checkout of this submodule.
    """
    assert isinstance(repo, git.Repo)
    assert isinstance(submodule, git.Submodule)
    submodule.update(recursive,True)

def Update(repo, submodule, recursive=False):
    """Runs an update appropriate for updating the checkout to the
    latest available revision.
    """
    assert isinstance(repo, git.Repo)
    assert isinstance(submodule, git.Submodule)
    submodule.update(recursive,True,True)
    
def CanCreateSubmodule(repo, subpath):
    """Returns a tupple of (repo,subpath) for the submodule repository for which
    the given subpath can be created.  This function walks recursively into
    submodules, shortening the subpath as neccesary.
    And if the submodule cannot be created, it returns a tupple of (None,None).
    """
    assert isinstance(repo, git.Repo)
    #by default, if we don't find otherwise, you can create that submodule in this repository.
    ret = (repo,subpath)

    #we walk through the submodules first and check some things.   
    for submod in repo.submodules:
        assert isinstance(submod, git.Submodule)
        #it's inside this path
        isInside = subpath.lower().startswith(submod.path.lower())
        if not isInside:
            #we move on if it's not inside
            continue
        #if it's not checked out on disk, we can't tell if you can create the submodule because we don't know
        #if the subpath is in one of this submodule's submodules.  So we say: NO!
        if not submod.module_exists():
            ret = (None,None)
            return ret
        else:
            #but if it does exist, we recursively return.
            newSubpath = str(pathlib.Path(subpath).relative_to(pathlib.Path(submod.path)))
            return CanCreateSubmodule(submod.module(),newSubpath)

    #if we get here, then the subpath isn't inside a submodule.

    #check if it exists already

    absPath = os.path.join(repo.working_dir,subpath)
    if os.path.exists(absPath):
        if os.path.isfile(absPath):
            #can't create a submod if its already a file.
            return (None,None)
        if os.path.isdir(absPath):
            #we might be okay if it's empty.
            if not len(os.listdir(absPath)) == 0:
                #not empty
                return (None,None)

    #if we get here, we've passed all tests, we can create here.
    return ret

    



