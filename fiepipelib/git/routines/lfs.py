import git

def InstallLFSGlobal():
    git.Repo.git.lfs("install")

def InstallLFSRepo(repo:git.Repo):
    repo.git.lfs("install","--local")

def Track(repo:git.Repo, patterns, readd = False):
    """@param patterns:  A list of patterns e.g. ["*.foo","bar/*.psd"]
    @param readd: If true, existing git tracked files that meet the pattern are removed from normal
    git tracking and re-added as lfs tracked.  Note this doesn't affect history.  Only current status
    and subsequent commits.
    """
    ret = ""
    for pattern in patterns:
        ret = ret + repo.git.lfs("track", "'" + pattern + "'")
        if readd:
            ret  = ret + repo.git.rm("--cached", pattern)
            ret  = ret + repo.git.add(pattern)
    AddGitAttributes(repo)
    return ret

def GetTrackedPatterns(repo):
    return repo.git.lfs("track")

def GetTrackedFiles(repo):
    return repo.git.lfs("tracked","paths")

def AddGitAttributes(repo):
    return repo.git.add(".gitattributes")

def GetGitEnv(repo):
    return repo.git.lfs("env")

def SetConfigLFSServerLocal(gitcmd, url):
    """Sets a configuration for the lfs server local to the machine
    @param gitcmd: a git command object.  not a repo, as this modifies the git configuration, not the repo.
    """
    return gitcmd.config("lfs.url = " + url)

def SetConfigLFSServerRepo(repo, url):
    """Sets a configuration for the lfs server for the given repository
    """
    ret = repo.git.config("-f", ".lfsconfig","lfs.url = " + url)
    ret = ret + repo.git.add(".lfsconfig")
    return ret



