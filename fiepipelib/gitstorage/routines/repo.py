import git
import pathlib

class NoSuchRepoError(git.GitError):
    pass

def RepoExists(path):
    if not pathlib.Path(path).exists:
        return False
    try:
        repo = git.Repo(path)
    except:
        return False
    #try:
    #   repo.rev_parse("")
    #except:
    #    return False
    return True

def InitWorkingTreeRoot(path):
    """Returns the Repo object"""
    assert isinstance(path, str)
    pathlib.Path(path).parent.mkdir(parents=True,exist_ok=True)
    return git.Repo.init(path)

def InitBareRepository(path):
    """Returns the Repo object"""
    assert isinstance(path, str)
    pathlib.Path(path).parent.mkdir(parents=True,exist_ok=True)
    return git.Repo.init(path,bare=True)

def CloneToBareRepository(src, dst):
    """Returns a Repo object for the newly created bare clone."""
    srcrep = git.Repo(src)
    InitBareRepository(dst)
    srcrep.git.clone('--bare', dst)
    dstrep = git.Repo(dst)
    return dstrep

def PushToRepo(src, dst, norecursive = True):
    srcrep = git.Repo(src)
    if norecursive:
        srcrep.git.push('--no-recurse-submodules',dst)
    else:
        srcrep.git.push(dst)



    