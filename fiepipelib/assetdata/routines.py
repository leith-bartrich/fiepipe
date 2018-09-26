import copy
import os
import os.path
import pathlib
import shutil
import typing

from fiepipelib.assetdata.data.connection import Connection
from fiepipelib.filerepresentation.data.filerepresentation import AbstractRepresentation, AbstractRepresentationManager
from fiepipelib.fileversion.data.fileversion import AbstractFileVersionManager, AbstractFileVersion
from fieui.FeedbackUI import AbstractFeedbackUI


class RepresentationNotFoundError(Exception):
    pass


async def GetRepresentationsByNameRoutine(name: str, version: AbstractFileVersion, man: AbstractRepresentationManager,
                                          conn: Connection) -> typing.List[AbstractRepresentation]:
    return man.GetByName(name, version, conn)


async def GetRepresentationDirectoryRoutine(name: str, version: AbstractFileVersion, man: AbstractRepresentationManager,
                                            conn: Connection, fb: AbstractFeedbackUI):
    reps = await GetRepresentationsByNameRoutine(name, version, man, conn)

    if len(reps) == 0:
        await fb.error("No such representation: " + name)
        raise RepresentationNotFoundError(name)

    rep = reps[0]

    assert isinstance(rep, AbstractRepresentation)

    repDirPath = pathlib.Path(rep.GetAbsolutePath(version))

    return repDirPath


async def DeployeTemplateRoutine(version: AbstractFileVersion, templatePath: str, fb: AbstractFeedbackUI):
    versionPath = pathlib.Path(version.GetAbsolutePath())

    if versionPath.exists():
        fb.error("File already exists for this version.")
        raise FileExistsError(str(versionPath))

    if not templatePath.exists():
        fb.error("Template file does not exist.")
        raise FileNotFoundError(str(templatePath))

    parentDir = pathlib.Path(versionPath.parent)
    if not parentDir.exists():
        os.makedirs(str(parentDir))

    fb.output("Copying file...")
    shutil.copyfile(str(templatePath), str(versionPath))
    fb.output("Done.")
    return


async def VersionUpViaFileCopy(oldver: AbstractFileVersion, newVersionName: str, man: AbstractFileVersionManager,
                               conn: Connection, fb: AbstractFeedbackUI) -> AbstractFileVersion:
    newver = copy.copy(oldver)
    newver._version = newVersionName

    man.Set([newver], conn)

    if oldver.FileExists():
        if not newver.FileExists():
            fb.feedback("Copying file...")
            shutil.copyfile(oldver.GetAbsolutePath(),
                            newver.GetAbsolutePath())
            fb.feedback("Done.")
        else:
            raise FileExistsError("new version file already exists.")
    else:
        raise FileNotFoundError("old version file doesn't exist.")
    return newver


INGEST_MODE_MOVE = 'm'
INGEST_MODE_COPY = 'c'


async def IngestFileToVersion(filePath: str, ver: AbstractFileVersion, ingestMode: str, fb: AbstractFeedbackUI):
    """Ingests the given file to the given version.  Will rename and move the file appropriately.
    
    Usage: file_ingest [version] [path] [mode]
    
    arg version: the version to ingest to

    arg path:  Path to the file.
    
    arg mode: 'c' or 'm' for copy or move modes.
    
    Will error if the file is of the wrong type or if there is already a file in-place.
    """

    target = pathlib.Path(ver.GetAbsolutePath())

    if target.exists():
        # TODO: logic to interactively correct this.
        fb.error("File already exists. " + str(target))
        raise FileExistsError(str(target))

    source = pathlib.Path(filePath).absolute()

    if not source.is_file():
        fb.error("Not a file:" + str(source))
        raise IOError("Not a file." + str(source))

    pardir = pathlib.Path(target.parent)
    if not pardir.exists():
        fb.feedback("Creating directories...")
        os.makedirs(str(pardir))
        fb.feedback("Done.")

    if mode == INGEST_MODE_MOVE:
        fb.feedback("Moving file...")
        source.rename(target)
        fb.feedback("Done.")
        return
    elif mode == INGEST_MODE_COPY:
        fb.feedback("Copying file...")
        shutil.copyfile(str(source), str(target))
        fb.feedback("Done.")
        return
    else:
        fb.error("Unknown mode: " + mode)
        raise ValueError()


async def EnsureDeleteFile(ver: AbstractFileVersion, fb: AbstractFeedbackUI):
    path = pathlib.Path(version.GetAbsolutePath())
    if path.exists():
        fb.feedback("Deleting file...")
        path.unlink()
        fb.feedback("Done.")
