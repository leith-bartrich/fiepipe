import sqlite3
import fiepipelib.assetdata
from fiepipelib.assetdata.data.assetdatabasemanager import AssetDatabaseManager
from fiepipelib.gitstorage.data.git_working_asset import GitWorkingAsset


class Connection(object):
    _conn = None
    _attachedmultidbs = None
    _readonly: bool = False

    def __init__(self, conn: sqlite3.Connection, readonly=False):
        """
        :param conn:
        :param readonly: a readonly connection allows concurrency.  A non-readonly connection gets and exclusive lock
        immediately
        """
        self._attachedmultidbs = []
        self._readonly = readonly
        if not self._readonly:
            # get exclusive lock immediately.
            self._conn = conn
            self._conn.isolation_level = 'EXCLUSIVE'
            self._conn.execute('BEGIN EXCLUSIVE')

    def GetDBConnection(self) -> sqlite3.Connection:
        if self._conn is None:
            raise TransactionError("Connection already closed.")
        return self._conn

    def Commit(self):
        if self._readonly:
            raise TransactionError("This connection is readonly.")
        if self._conn is None:
            raise TransactionError("Connection already closed.")
        # first we commit everything
        self._conn.commit()
        # then we walk through each multi db that has been attached.
        for db in self._attachedmultidbs:
            assert isinstance(db, fiepipelib.assetdata.abstractassetdata.abstractmultimanager)
            # open it and dump it
            db._dumpTo(db._GetDBDumpFilename())

        # we do a loop again because the dump is critical and want that to complete first.
        # A failed hash db update will just result in an extraneous read of the dump and hash db update the
        # next time we read.  Which is not optimal. But isn't a failure.
        for db in self._attachedmultidbs:
            assert isinstance(db, fiepipelib.assetdata.abstractassetdata.abstractmultimanager)
            # get the hash
            hash = db._GetHashOfDump()
            # update the dbhashes table
            db._WriteHashToDB(hash, self._conn)
        # commit again to commit the updated hashes.
        self._conn.commit()

    def Rollback(self):
        if self._readonly:
            raise TransactionError("This connection is readonly.")
        if self._conn is None:
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


class TransactionError(Exception):
    pass


def GetConnection(workingAsset: GitWorkingAsset, readonly: bool = False) -> Connection:
    man = AssetDatabaseManager(workingAsset)
    ret = Connection(man.GetDBConnection(), readonly)
    return ret