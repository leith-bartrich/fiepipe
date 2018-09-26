import hashlib
import pathlib
import sqlite3

from fiepipelib.gitstorage.data.locally_managed_types import abstractassetlocalmanager


class databasehash(object):
    _name = None
    _md5hash = None

    def GetName(self):
        return self._name

    def GetMD5(self):
        return self._md5hash


def FromParams(name: str, md5: str):
    """@param name: the name of the db
    @param md5: the hex of the md5 hash e.g. md5.hexdigest()
    """
    ret = databasehash()
    ret._name = name
    ret._md5hash = md5
    return ret


def ToJSON(dbh: databasehash):
    ret = {}
    ret["name"] = dbh.GetName()
    ret["md5hash"] = dbh.GetMD5()
    return ret


def FromJSON(data: dict):
    ret = databasehash()
    ret._name = data['name']
    ret._md5hash = data['md5hash']
    return ret


def md5file(fname: str):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


class AssetDatabaseManager(abstractassetlocalmanager):

    def FromJSONData(self, data):
        return FromJSON(data)

    def ToJSONData(self, item):
        return ToJSON(item)

    def GetManagedTypeName(self):
        return "database_hash"

    def GetColumns(self):
        ret = super().GetColumns()
        ret.append(("name", "text"))
        ret.append(("md5hash", "text"))
        return ret

    def GetPrimaryKeyColumns(self):
        return ["name"]

    def GetByName(self, name, conn: sqlite3.Connection = None):
        return self._Get([("name", name)], conn)

    def Cull(self, conn: sqlite3.Connection = None):
        """Deletes rows that reference db files that currenlty don't exist.
        """
        allhashes = self.GetAll(conn)
        toremove = []
        for h in allhashes:
            assert isinstance(h, databasehash)
            p = pathlib.Path(h.GetName())
            if not p.exists():
                toremove.append(p)
        for r in toremove:
            assert isinstance(r, databasehash)
            self._Delete("name", r.GetName(), conn)
