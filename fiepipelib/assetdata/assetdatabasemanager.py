import fiepipelib.abstractmanager
import hashlib
import pathlib
import fiepipelib.gitstorage.data
import sqlite3

class databasehash(object):
    _name = None
    _md5hash = None

    def GetName(self):
        return self._name
    
    def GetMD5(self):
        return self._md5hash

def FromParams(name:str, md5:str):
    """@param name: the name of the db
    @param md5: the hex of the md5 hash e.g. md5.hexdigest()
    """
    ret = databasehash()
    ret._name = name
    ret._md5hash = md5
    return ret

def ToJSON(dbh:databasehash):
    ret = {}
    ret["name"] = dbh.GetName()
    ret["md5hash"] = dbh.GetMD5()
    return ret

def FromJSON(data:dict):
    ret = databasehash()
    ret._name = data['name']
    ret._md5hash = data['md5hash']
    return ret

def md5file(fname:str):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

class TransactionError(Exception):
    pass

class Connection(object):

    _conn = None
    _attachedmultidbs = None
    
    def __init__(self, *args, **kwargs):
        self._attachedmultidbs = []
    
    def GetDBConnection(self) -> sqlite3.Connection:
        if self._conn == None:
            raise TransactionError("Connection already closed.")
        return self._conn
    
    def Commit(self):
        if self._conn == None:
            raise TransactionError("Connection already closed.")
        #first we commit everything
        self._conn.commit()
        #then we walk through each multi db that has been attached.
        for db in self._attachedmultidbs:
            assert isinstance(db, fiepipelib.assetdata.abstractassetdata.abstractmultimanager)
            #open it and dump it
            db._dumpTo(db._GetDBDumpFilename())
            
        #we do a loop again because the dump is critical and want that to complete first.
        #A failed hash db update will just result in an extraneous read of the dump and hash db update the
        #next time we read.  Which is not optimal. But isn't a failure.
        for db in self._attachedmultidbs:
            assert isinstance(db, fiepipelib.assetdata.abstractassetdata.abstractmultimanager)
            #get the hash
            hash = db._GetHashOfDump()
            #update the dbhashes table
            db._WriteHashToDB(hash, self._conn)
        #commit again to commit the updated hashes.
        self._conn.commit()
        
    def Rollback(self):
        if self._conn == None:
            raise TransactionError("Connection already closed.")
        self._conn.rollback()        
        
    def Close(self):
        if self._conn == None:
            raise TransactionError("Connection already closed.")
        self._conn.close()
        self._conn = None
    
    def __del__(self):
        if self._conn != None:
            self.Close()
        
    
def GetConnection(workingAsset:fiepipelib.gitstorage.workingasset.workingasset) -> Connection:
    man = AssetDatabaseManager(workingAsset)
    ret = Connection()
    ret._conn = man.GetDBConnection()
    return ret

class AssetDatabaseManager(fiepipelib.gitstorage.data.abstractassetlocalmanager):
    
    def FromJSONData(self, data):
        return FromJSON(data)
    
    def ToJSONData(self, item):
        return ToJSON(item)
    
    def GetManagedTypeName(self):
        return "database_hash"
    
    def GetColumns(self):
        ret = super().GetColumns()
        ret.append(("name","text"))
        ret.append(("md5hash","text"))
        return ret
    
    def GetPrimaryKeyColumns(self):
        return ["name"]
    
    def GetByName(self, name, conn:sqlite3.Connection=None):
        return self._Get([("name",name)],conn)
    
    def Cull(self,conn:sqlite3.Connection=None):
        """Deletes rows that reference db files that currenlty don't exist.
        """
        allhashes = self.GetAll(conn)
        toremove = []
        for h in allhashes:
            assert isinstance(h,databasehash)
            p = pathlib.Path(h.GetName())
            if not p.exists():
                toremove.append(p)
        for r in toremove:
            assert isinstance(r,databasehash)
            self._Delete("name", r.GetName(),conn)

