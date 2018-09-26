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
