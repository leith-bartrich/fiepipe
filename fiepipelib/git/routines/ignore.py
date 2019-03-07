import git
import os
import os.path
import pathlib

def CheckCreateIgnore(repo) -> (bool, str):
    """returns true if it already existed"""
    ret = True
    assert isinstance(repo, git.Repo)
    workTreeDir = repo.working_dir
    ignorePath = pathlib.Path(os.path.join(workTreeDir,".gitignore"))
    if not ignorePath.exists():
        ignorePath.touch()
        ret = False
    elif not ignorePath.is_file():
        print(".gitignore exists but is not a file.")
        raise FileNotFoundError(str(ignorePath.absolute()))
    repo.index.add([str(ignorePath.absolute())])
    return ret, ignorePath

def AddIgnore(repo, pattern:str, replace_slashes=True) -> bool:
    """returns true if a change was made."""
    if replace_slashes:
        pattern = pattern.replace('\\','/')
    assert isinstance(repo, git.Repo)
    change_made, ignorePath = CheckCreateIgnore(repo)
    with ignorePath.open() as f:
        lines = f.readlines()
    for line in lines:
        if line.strip() == pattern.strip():
            return False
    lines.append(pattern + '\n')
    with ignorePath.open('w') as f:
        for line in lines:
            stripped = line.strip()
            if stripped != '':
                f.write(line)
    return True

def RemoveIgnore(repo, pattern):
    assert isinstance(repo, git.Repo)
    change_made, ignorePath = CheckCreateIgnore(repo)
    with ignorePath.open() as f:
        lines = f.readlines()
    newlines = []
    for line in lines:
        if line.strip() != pattern.strip():
            newlines.append(line)
    with ignorePath.open('w') as f:
        f.writelines(newlines)

def GetIgnores(repo):
    assert isinstance(repo, git.Repo)
    chage_made, ignorePath = CheckCreateIgnore(repo)
    with ignorePath.open() as f:
        lines = f.readlines()
    return lines


