import typing

import git


def InstallLFSGlobal():
    if not LFSIsInstalledGlobal():
        return git.Git().lfs("install")


def InstallLFSRepo(repo: git.Repo):
    if not LFSIsInstalledRepo(repo):
        return repo.git.lfs("install", "--local")

def LFSIsInstalledRepo(repo: git.Repo):
    configs = repo.git.config("--list --local")
    assert isinstance(configs,str)
    config_lines = configs.splitlines()
    has_clean = False
    has_smudge = False
    has_process = False

    for line in config_lines:
        if line.startswith("filter.lfs.clean"):
            has_clean = True
        if line.startswith("filter.lfs.smudge"):
            has_smudge = True
        if line.startswith("filter.lfs.process"):
            has_process = True

    return has_clean and has_process and has_smudge

def LFSIsInstalledGlobal():
    configs = git.Git().config("--list --global")
    assert isinstance(configs,str)
    config_lines = configs.splitlines()
    has_clean = False
    has_smudge = False
    has_process = False

    for line in config_lines:
        if line.startswith("filter.lfs.clean"):
            has_clean = True
        if line.startswith("filter.lfs.smudge"):
            has_smudge = True
        if line.startswith("filter.lfs.process"):
            has_process = True

    return has_clean and has_process and has_smudge



def Track(repo: git.Repo, patterns:typing.List[str]):
    """@param patterns:  A list of patterns e.g. ["*.foo","bar/*.psd"]
    """
    if len(patterns) == 0:
        return
    quoted = []
    for pattern in patterns:
        quoted.append("\"" + pattern + "\"")
    patterns_string = " ".join(quoted)
    track_args = ["track"]
    track_args.extend(quoted)
    ret = repo.git.lfs(track_args)

    #rm_args = ["--cached", "--ignore-unmatch"]
    #rm_args.extend(quoted)
    #ret = ret + repo.git.rm(rm_args)
    # for pattern in patterns:
    # we always do this just incase.
    #    ret = ret + repo.git.rm("--cached", "--ignore-unmatch", pattern)
    #        if readd:
    # fails when there are not such files becausee there is no --ignore-unmatched for the add command.
    #            ret  = ret + repo.git.add(pattern)
    AddGitAttributes(repo)
    return ret


def Untrack(repo: git.Repo, patterns: typing.List[str]):
    quoted = []
    for pattern in patterns:
        quoted.append("'" + pattern + "'")
    patterns_string = " ".join(quoted)
    track_args = ["untrack"]
    track_args.extend(quoted)
    ret = repo.git.lfs(track_args)
    AddGitAttributes(repo)
    return ret


def GetTrackedPatterns(repo):
    return repo.git.lfs("track")


def GetTrackedFiles(repo):
    return repo.git.lfs("tracked", "paths")


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
    ret = repo.git.config("-f", ".lfsconfig", "lfs.url = " + url)
    ret = ret + repo.git.add(".lfsconfig")
    return ret
