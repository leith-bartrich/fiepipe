import git
import os
import os.path
import pathlib

def CheckCreateIgnore(repo):
    assert isinstance(repo, git.Repo)
    workTreeDir = repo.working_dir
    ignorePath = pathlib.Path(os.path.join(workTreeDir,".gitignore"))
    if not ignorePath.exists():
        ignorePath.touch()
    elif not ignorePath.is_file():
        print(".gitignore exists but is not a file.")
        raise FileNotFoundError(str(ignorePath.absolute()))
    repo.index.add([str(ignorePath.absolute())])
    
    return ignorePath

def AddIgnore(repo, pattern):
    assert isinstance(repo, git.Repo)
    ignorePath = CheckCreateIgnore(repo)
    with ignorePath.open() as f:
        lines = f.readlines()
    for line in lines:
        if line.strip() == pattern.strip():
            print("Pattern already ignored: " + pattern)
            return
    lines.append(pattern)
    with ignorePath.open('w') as f:
        f.writelines(lines)

def RemoveIgnore(repo, pattern):
    assert isinstance(repo, git.Repo)
    ignorePath = CheckCreateIgnore(repo)
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
    ignorePath = CheckCreateIgnore(repo)
    with ignorePath.open() as f:
        lines = f.readlines()
    return lines


