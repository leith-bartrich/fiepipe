import typing

import git


def create_update_remote(repo: git.Repo, name: str, url: str):
    found_remote = None
    for existing_remote in repo.remotes:
        assert isinstance(existing_remote, git.Remote)
        if existing_remote.name == name:
            found_remote = existing_remote
    if found_remote is not None:
        found_remote.set_url(url)
        return found_remote
    else:
        new_remote = repo.create_remote(name, url)
        return new_remote


def get_commits_behind(repo: git.Repo, branch: str, remote: str) -> typing.List[git.Commit]:
    ret = []
    iter = repo.iter_commits(branch + ".." + remote + "/" + branch)
    for commit in iter:
        ret.append(commit)
    return ret


def get_commits_ahead(repo: git.Repo, branch: str, remote: str) -> typing.List[git.Commit]:
    ret = []
    iter = repo.iter_commits(remote + "/" + branch + ".." + branch)
    for commit in iter:
        ret.append(commit)
    return ret


def exists(repo: git.Repo, remote: str) -> bool:
    try:
        repo.git.ls_remote(remote, " --exit-code", "--quiet")
        return True
    except git.GitCommandError as err:
        return False
