import git
import pathlib
import shutil
import os
import stat

class NoSuchRepoError(git.GitError):
    pass

def RepoExists(path):
    if not pathlib.Path(path).exists:
        return False
    try:
        repo = git.Repo(path)
        del(repo)
    except:
        return False
    #try:
    #   repo.rev_parse("")
    #except:
    #    return False
    return True

def DeleteLocalRepo(path):
    #git makes its object files 'readonly' which freaks out shutil on windows.
    #the onerror implementation detects this and tries to change readonly permission first.
    shutil.rmtree(path,onerror=onerror)

def onerror(func, path, exc_info):
    """
    Error handler for ``shutil.rmtree``.

    If the error is due to an access error (read only file)
    it attempts to add write permission and then retries.

    If the error is for another reason it re-raises the error.

    Usage : ``shutil.rmtree(path, onerror=onerror)``
    """
    if not os.access(path, os.W_OK):
        # Is the error an access error ?
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        func(path)



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



def CloneFrom(src:str, dst:str):
    """
    :param src: the remote url
    :param dst: the local path
    """
    git.Repo().clone_from(src,dst)

def PushToRepo(src, dst, norecursive = True):
    srcrep = git.Repo(src)
    if norecursive:
        srcrep.git.push('--no-recurse-submodules',dst)
    else:
        srcrep.git.push(dst)


    