import sqlite3
import fiepipelib.assetdata.data.assetdatabasemanager
import fiepipelib.assetdata.data.connection
import fiepipelib.gitstorage.data.git_working_asset
import os.path
import pathlib
import abc
import fiepipelib.assetdata.data.items
import json


class AbstractItemsRelation(object):
    """An abstract class with which to make managers of related static asset data.  Currently backed by sqllite.
    Currently, you need to override the following:
    
    GetMultiManagedName
    
    Also, you should override the __init__ method.
    
    You will want to instantiate the actual dataManagers as fields and pass a list of them to super().__init__()
    """
    
    _dataManagers = None    
    _workingAsset = None

    def __init__(self, workingAsset: fiepipelib.gitstorage.data.git_working_asset.GitWorkingAsset, dataManagers = []):
        self._dataManagers = dataManagers.copy()
        for dm in dataManagers:
            assert isinstance(dm, AbstractItemManager)
            dm._multiManager = self
        self._workingAsset = workingAsset

        #we don't check if we're up to date here because that would require a connection(transaction).
        
    def GetWorkingAsset(self):
        return self._workingAsset

    def GetDBDir(self):
        """Directory for the local sqlite DB.  Which is the local cached of db data and not shared."""
        return os.path.join(self._workingAsset.GetSubmodule().abspath,".assetlocal","multi_dbs")

    def GetDumpDir(self):
        """Directory for the asset db dumps.  Which are the actual shared representation of the DB."""
        return os.path.join(self._workingAsset.GetSubmodule().abspath,".assetdb","multi_db_dumps")

    @abc.abstractmethod
    def GetMultiManagedName(self) -> str:
        """Override this: Returns the name of the name of the database for multi managed items.
        e.g. The FooMultiManager probably returns 'Foo'"""
        raise NotImplementedError()

    def _GetDBFilename(self):
        """Returns the full path to the DB file to load."""
        dir = os.path.join(self.GetDBDir(),"dbv1")
        if not os.path.exists(dir):
            os.makedirs(dir)
        return os.path.join(dir,self.GetMultiManagedName() + ".db")
    
    def _GetDBDumpFilename(self):
        """Returns the full path to the DB dump file to use."""
        dir = os.path.join(self.GetDumpDir(),"dbv1")
        if not os.path.exists(dir):
            os.makedirs(dir)
        return os.path.join(dir,self.GetMultiManagedName() + ".dump")

    def _DBExists(self):
        fname = self._GetDBFilename()
        path = pathlib.Path(fname)
        return path.exists() & path.is_file()
        

    def _DumpExists(self):
        fname = self._GetDBDumpFilename()
        path = pathlib.Path(fname)
        return path.exists() & path.is_file()
                    

    def _GetHashOfDump(self):
        fname = self._GetDBDumpFilename()
        path = pathlib.Path(fname)
        dumphash = fiepipelib.assetdata.data.assetdatabasemanager.md5file(str(path.absolute()))
        return dumphash
    
    def _WriteHashToDB(self, hash, conn:sqlite3.Connection):
        h = fiepipelib.assetdata.data.assetdatabasemanager.FromParams(self._GetDBFilename(), hash)
        man = fiepipelib.assetdata.data.assetdatabasemanager.AssetDatabaseManager(self._workingAsset)
        man.Set([h],conn)
    
    def _UpToDateAttach(self, connection:sqlite3.Connection = None):
        """Given a connection to the asset's dbhahses DB, we make sure
        the local database is up to date and attach to it.
        """
        #TODO: Big question.
        #Is it even worth doing all these checks?  Shouldn't we just read each time we connect
        #and dump when we commit?  Let GIT handle the merging?
        #if we do that, we get best of both worlds.  SQLite file-locks for us to guarontee consistency.
        #And the database is modified atomically.  We might want to use a transaction system just to
        #make sure GIT doesn't commit during the milisecond that the db dump is delted before the new one is merged in.
        #and similarly put rollback behavior in the attach to just pick it up if that's how it gets commited.

        #first just based on missing files
        
        if (not self._DumpExists()) & (not self._DBExists()):
            #nothing exists.  So, it's technically fine.
            #we create an empty one then attach.
            self._Connect().close()
            self._Attach(connection)
            return
        
        if (self._DumpExists()) & (not self._DBExists()):
            #dump exists but no db.  So we read it and enter it.
            self._readFrom(self._GetDBDumpFilename())
            hashofdump = self._GetHashOfDump()
            self._WriteHashToDB(hashofdump,connection)
            self._Attach(connection)
            return
        
        if (not self._DumpExists()) & (self._DBExists()):
            #we have a db but no dump.  shouldn't happen.  But if it does, we dump and enter it.
            self._dumpTo(self._GetDBDumpFilename())
            hash = self._GetHashOfDump()
            self._WriteHashToDB(hash,connection)
            self._Attach(connection)
            return

        #done with easy fast cases.

        #both files exist exist

        #before calculating a hash (slow), we check for an existing entry.
        
        dbhashmanager = fiepipelib.assetdata.data.assetdatabasemanager.AssetDatabaseManager(self._workingAsset)
        dbhashes = dbhashmanager.GetByName(self._GetDBFilename(),connection)
        
        if len(dbhashes) == 0:
            #no existing record but there is a file.  No way to know if its okay.  Abundance of caution.  We delete and read.
            #probably this should never happen.  But it is at least easy fast logic.
            self._deleteDB()
            hashofdump = self._GetHashOfDump()
            self._readFrom(self._GetDBDumpFilename())
            self._WriteHashToDB(hashofdump,connection)
            self._Attach(connection)
            return

        #we have a single hash for this local db.

        dbhash = dbhashes[0]
        assert isinstance(dbhash, fiepipelib.assetdata.data.assetdatabasemanager.databasehash)

        #finally, we md5 the dump file (slow) and check equality with the dbhash.
        hashofdump = self._GetHashOfDump()
        
        if dbhash.GetMD5() == hashofdump:
            #it's up to date.  We're fine.
            self._Attach(connection)
            return
        else:
            #they're mismatched.  We delete and read from dump.
            #TODO: POSSIBLE BIG PROBLEM!
            #if we've made local changes but no commits, and then done an update/pull,
            #git will try and merge the sql dumps.  And it may even succeed.  But that doesn't
            #guarontee a valid dump file was made from the merge.  Or does it?
            #need to test this.  Need to create a path toward resolution here.  A re-merge capability maybe?
            self._deleteDB()
            self._readFrom(self._GetDBDumpFilename())
            self._WriteHashToDB(hashofdump,connection)
            self._Attach(connection)
            return

    
    def _Connect(self):
        """Retruns a connection to the db.  No checks."""
        ret = sqlite3.connect(self._GetDBFilename())
        return ret
        
    def _Attach(self, conn:sqlite3.Connection):
        """Attaches the db to the given connection using the GetMultiManagedName as the DB name."""
        statement = "ATTACH DATABASE '" + self._GetDBFilename() + "' as " + self.GetMultiManagedName()
        conn.execute(statement)
        return conn
    
    def AttachToConnection(self, connection: fiepipelib.assetdata.data.connection.Connection):
        """Makes sure the local DB is up to date and attaches it to the connection.
        """
        conn = connection.GetDBConnection()
        self._UpToDateAttach(conn)
        self._CreateTables(conn.cursor())
        connection._attachedmultidbs.append(self)
    
    def _CreateTables(self, cur):
        for m in self._dataManagers:
            assert isinstance(m, AbstractItemManager)
            m._CreateTable(cur)

    def _dumpTo(self, path):
        #TODO implement this as a transaction which can be rolled back or forward (resolved).
        p = pathlib.Path(path)
        conn = self._Connect()
        
        with open(str(p.absolute()), 'w') as f:
            for line in conn.iterdump():
                f.write('%s\n' % line)        
        conn.close()
        #cur = conn.cursor()
        #assert isinstance(cur, sqlite3.Cursor)
        #statement = ".output " + str(p.absolute())
        #cur.execute(statement)
        #statement = ".dump"
        #cur.execute(statement)
        #cur.close()
        #conn.close()

    def _readFrom(self, path):
        #TODO implment resolution (rollback or forward here.)
        conn = self._Connect()
        assert  isinstance(conn, sqlite3.Connection)
        p = pathlib.Path(path)
        
        with open(str(p.absolute()), 'r') as f:
            for line in f:
                conn.execute(line)        
        conn.close()
        
        #cur = conn.cursor()
        #assert isinstance(cur, sqlite3.Cursor)
        #statement = ".read " + str(p.absolute())
        #cur.execute(statement)
        #cur.close()
        #conn.close()
        
    def _deleteDB(self):
        path = pathlib.Path(self._GetDBFilename())
        if path.exists() & path.is_file():
            path.unlink()

class AbstractItemManager(object):
    
    _multiManager = None
    
    def GetMultiManager(self):
        assert isinstance(self._multiManager, AbstractItemsRelation)
        return self._multiManager

    @abc.abstractmethod
    def GetManagedTypeName(self) -> str:
        """Override this: Returns the name of the type of managed item this manager manages.
        e.g. The FooManager probably returns 'Foo'"""
        raise NotImplementedError()
    
    def GetColumns(self) -> list:
        """Override this and call super: Returns a list of two element tupples of sqlite names and types
        for the desired searchable columns in the table.  The baseclass makes sure
        there is a 'json' column of type 'text' to hold the item's serialized json form.
      
        Additional columns will end up being the columns on which searches and deletions are based.

        Use the same names as the JSON field names to automatically promote those
        fields to searchable columns.

        When overriding, make sure to call super().GetColumns() first, which will populate the list with
        required 'json' column.  Then append to it or otherwise modify it before returning it.
        
        Keep in mind.  If you don't add any useful columns, you won't be able to search or delete particularly
        effectively."""

        ret = []
        ret.append( ('json','text') )
        return ret

    @abc.abstractmethod
    def GetPrimaryKeyColumns(self) -> list:
        """Returns a list of column names that make up the primary key"""
        raise NotImplementedError()

    def _CreateTable(self, cur):
        """Checks for and automatically creates the neccesaary table.
        """
        statement = "CREATE TABLE IF NOT EXISTS " + self.GetMultiManager().GetMultiManagedName() + "." + self.GetManagedTypeName() + "( "
        cols = self.GetColumns()
        colstrings = []
        for col in cols:
            colname = col[0]
            coltype = col[1]
            colstring = colname + " " + coltype
            colstrings.append(colstring)
        colstring = ", ".join(colstrings)

        primstring = ", ".join(self.GetPrimaryKeyColumns())

        statement = statement + colstring + ", PRIMARY KEY (" + primstring + ") )"

        cur.execute( statement )
        #TODO: add indexes here

    def _CreateUpdateRows(self, data, conn:sqlite3.Connection):
        """Uses the REPLACE statement to insert or update a row regardless of if it exsits or not.
        @param data: A list of dictionaries of names and data to insert
        """
        statement = "REPLACE INTO " + self.GetMultiManager().GetMultiManagedName() + "." + self.GetManagedTypeName() + " ("
        names = []
        qmarks = []
        values = []
        if (len(data) > 0):
            for k in data[0].keys():
                names.append(k)
                qmarks.append("?")
            for row in data:
                valrow = []
                for k in data[0].keys():
                    valrow.append(row[k])
                values.append(valrow)
            statement = statement + ", ".join(names) + ") VALUES (" + " ,".join(qmarks) + ")"
            cur = conn.cursor()
            cur.executemany(statement,values)

    def _DeleteRowsByMultipleAND(self, conn:sqlite3.Connection, colNamesAndValues = []):
        """Runs a delete statement to search for and delete rows matching all passed column and value tupples with AND logic.
        @param colNamesAndValues: A list of tupples.  e.g. [("firstname","John"),("lastname","Doe")]
        """
        statement = "DELETE FROM " + self.GetMultiManager().GetMultiManagedName() + "." + self.GetManagedTypeName()
        cur = conn.cursor()
        clauses = []
        values = []
        if len(colNamesAndValues) > 0:
            statement = statement + " WHERE "
            for i in colNamesAndValues:
                clauses.append(i[0] + " = ?")
                values.append(str(i[1]))
            statement = statement + " AND ".join(clauses) 
        cur.execute(statement,values)

    def _GetRowsByMultipleAND(self, cur:sqlite3.Cursor, colNamesAndValues = []):
        """Selects and returns rows based on the given search criteria.
        @param cur: the cursor to use.
        @param colNamesAndValues: A list of tupples where the first entry is the column name and the second, the value
        to search for.  These are all strung together with 'AND' methodology.
        Ideally values are already strings.  But we run an str internally just incase.
        """
        statement = "SELECT * FROM " + self.GetMultiManager().GetMultiManagedName() + "." + self.GetManagedTypeName()
        clauses = []
        values = []
        if len(colNamesAndValues) > 0:
            statement = statement + " WHERE "
            for i in colNamesAndValues:
                clauses.append(i[0] + " = ?")
                values.append(str(i[1]))
            statement = statement + " AND ".join(clauses) 
        cur.execute(statement,values)

    @abc.abstractmethod
    def ToJSONData(self, item):
        """Override this: Converts the given item into JSON data, which is a dictionary object, and returns it."""
        raise NotImplementedError()

    @abc.abstractmethod
    def FromJSONData(self, data):
        """Override this: Converts the givne JSON data, which is a dictionary, into an item and returns it."""
        raise NotImplementedError()

    def _ItemFromRow(self, row):
        """Converts row data into an item and returns it."""
        return self.FromJSONData(json.loads(row['json']))

    def _ItemsToInsertData(self, items):
        """Converts the given list of items into data suitable for insertion into the databse."""
        data = []
        for item in items:
            jsondata = self.ToJSONData(item)
            row = {}
            row['json'] = json.dumps(jsondata)
            for col in self.GetColumns():
                if col[0] != 'json':
                    row[col[0]] = str(jsondata[col[0]])
            data.append(row)
        return data

    def _Get(self, conn:sqlite3.Connection, colNamesAndValues = []):
        """Gets items that match an AND based column and value filter.

        Typically a manager will have a series of more type specific Get methods to call.

        If you pass an empty list (default) it gets all of them.  Which is probably faster than listing them.

        @param colNamesAndValues: a list of tupples of column name and value pairs
        e.g. [(foo,1),(bar,100)] means: WHERE foo = 1 AND bar = 100
        @return: A list of items.  Empty list if none meet the criteria.

        """
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        self._GetRowsByMultipleAND(cur, colNamesAndValues)
        rows = cur.fetchall()
        ret = []
        for row in rows:
            ret.append(self._ItemFromRow(row))
        return ret

    def GetAll(self, connection: fiepipelib.assetdata.data.connection.Connection):
        return self._Get(colNamesAndValues=[],conn=connection.GetDBConnection())

    def Set(self, items, connection: fiepipelib.assetdata.data.connection.Connection):
        """Sets (create/update) items.
        @param items: A list of items to set.
        """
        insertData = self._ItemsToInsertData(items)
        self._CreateUpdateRows(insertData,connection.GetDBConnection())

    def _Delete(self, colName, colValue, conn:sqlite3.Connection):
        """Deletes items by the colName and colValue.

        As in: DELETE from TABLE WHERE [colName] = [colValue]

        Typically a manager will have a series of more type specific Delete methods to call.

        @param colName: The column name to match for deletion
        @param colValue: The column value to match for deletion
        """
        self._DeleteRowsByMultipleAND(colNamesAndValues=[(colName,colValue)],conn=conn)

    def _DeleteByMultipleAND(self,conn:sqlite3.Connection, colNamesAndValues = []):
        """Deletes items by multiple AND conditions.

        Typically a manager will have a series of more type specific Delete methods to call.

        @param colNamesAndValus: A list of tupples of names and values to use as conditions.  e.g. [("fqdn","them.com"),("sitename","home")]
        """
        self._DeleteRowsByMultipleAND(colNamesAndValues=colNamesAndValues,conn=conn)
        

    
            
            
