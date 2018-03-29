import json
import sqlite3
import fiepipelib.localuser
import os.path
import abc
import pathlib

class abstractmanager(object):
    """An abstract class with which to make managers of static data.  Currently backed by sqllite.
    Currently, you need to override the following:
    
    GetConfigDir
    GetManagedTypeName
    GetColumns
    ToJSONData
    FromJSONData

    In addition, you will likely want to implement various versions of:

    Get
    Delete
    """

    def __init__(self):
        #we create/update the table
        conn = self._GetDBConnection()
        assert isinstance(conn, sqlite3.Connection)
        cur = conn.cursor()
        self._CreateTable(cur)
        conn.commit()
        conn.close()

    @abc.abstractmethod
    def GetConfigDir(self):
        """Override this: Returns the path to the configuration directory for this manager."""
        raise NotImplementedError()

    @abc.abstractmethod
    def GetManagedTypeName(self) -> str:
        """Override this: Returns the name of the type of managed item this manager manages.
        e.g. The FooManager probably returns 'Foo'"""
        raise NotImplementedError()

    def _GetDBFilename(self):
        """Returns the full path to the DB file to load."""
        dir = os.path.join(self.GetConfigDir(),"dbv1")
        if not os.path.exists(dir):
            os.makedirs(dir)
        return os.path.join(dir,self.GetManagedTypeName() + ".db")


    def _GetDBConnection(self):
        """Returns an open sqlite3 connection for the mananger's data.  Keep in mind, the database is usually
        locked based on the transaction this connection represents.  So grab it, use it, and dump it quickly
        to avoid blocking processes.  Or, hold on to it if you really need to."""
        #TODO: when we move to v2, we'll need to detect the missing v2
        #and run an upgrade from v1 to v2 here.  And upon failure, raise
        #an exception.
        ret = sqlite3.connect(self._GetDBFilename())
        assert isinstance(ret, sqlite3.Connection)
        return ret

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
        statement = "CREATE TABLE IF NOT EXISTS " + self.GetManagedTypeName() + "( "
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

    def _CreateUpdateRows(self, data):
        """Uses the REPLACE statement to insert or update a row regardless of if it exsits or not.
        @param data: A list of dictionaries of names and data to insert
        """
        statement = "REPLACE INTO " + self.GetManagedTypeName() + " ("
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
            conn = self._GetDBConnection()
            cur = conn.cursor()
            cur.executemany(statement,values)
            conn.commit()
            conn.close()

    def _DeleteRowsByMultipleAND(self, colNamesAndValues = []):
        """Runs a delete statement to search for and delete rows matching all passed column and value tupples with AND logic.
        @param colNamesAndValues: A list of tupples.  e.g. [("firstname","John"),("lastname","Doe")]
        """
        statement = "DELETE FROM " + self.GetManagedTypeName()
        conn = self._GetDBConnection()
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
        conn.commit()
        conn.close()

    def _GetRowsByMultipleAND(self, cur, colNamesAndValues = []):
        """Selects and returns rows based on the given search criteria.
        @param cur: the cursor to use.
        @param colNamesAndValues: A list of tupples where the first entry is the column name and the second, the value
        to search for.  These are all strung together with 'AND' methodology.
        Ideally values are already strings.  But we run an str internally just incase.
        """
        statement = "SELECT * FROM " + self.GetManagedTypeName()
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

    def _Get(self, colNamesAndValues = []):
        """Gets items that match an AND based column and value filter.

        Typically a manager will have a series of more type specific Get methods to call.

        If you pass an empty list (default) it gets all of them.  Which is probably faster than listing them.

        @param colNamesAndValues: a list of tupples of column name and value pairs
        e.g. [(foo,1),(bar,100)] means: WHERE foo = 1 AND bar = 100
        @return: A list of items.  Empty list if none meet the criteria.

        """
        conn = self._GetDBConnection()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        self._GetRowsByMultipleAND(cur, colNamesAndValues)
        rows = cur.fetchall()
        ret = []
        for row in rows:
            ret.append(self._ItemFromRow(row))
        conn.close()
        return ret

    def GetAll(self):
        return self._Get()

    def Set(self, items):
        """Sets (create/update) items.
        @param items: A list of items to set.
        """
        insertData = self._ItemsToInsertData(items)
        self._CreateUpdateRows(insertData)

    def _Delete(self, colName, colValue):
        """Deletes items by the colName and colValue.

        As in: DELETE from TABLE WHERE [colName] = [colValue]

        Typically a manager will have a series of more type specific Delete methods to call.

        @param colName: The column name to match for deletion
        @param colValue: The column value to match for deletion
        """
        self._DeleteRowsByMultipleAND([(colName,colValue)])

    def _DeleteByMultipleAND(self, colNamesAndValues = []):
        """Deletes items by multiple AND conditions.

        Typically a manager will have a series of more type specific Delete methods to call.

        @param colNamesAndValus: A list of tupples of names and values to use as conditions.  e.g. [("fqdn","them.com"),("sitename","home")]
        """
        self._DeleteRowsByMultipleAND(colNamesAndValues)

    def _dumpTo(self, path):
        p = pathlib.Path(path)
        conn = self._GetDBConnection()
        cur = conn.cursor()
        assert isinstance(cur, sqlite3.Cursor)
        statement = ".output " + str(p.absolute())
        cur.execute(statement)
        statement = ".dump"
        cur.execute(statement)
        cur.close()
        conn.close()

    def _readFrom(self, path):
        p = pathlib.Path(path)
        conn = self._GetDBConnection()
        cur = conn.cursor()
        assert isinstance(cur, sqlite3.Cursor)
        statement = ".read " + str(p.absolute())
        cur.execute(statement)

class abstractlocalmanager(abstractmanager):
    """Subclass this.
    
    A local manager than knows how to save its data to sqlite databases in the user's fiepipe configuration directory.

    Implements the GetConfigDir abstract method.

    All others must still be overidden from the superclass.
    """

    _localUser = None
    

    def __init__(self, localUser):
        assert isinstance(localUser, fiepipelib.localuser.localuser)
        self._localUser = localUser
        super().__init__()

    def GetConfigDir(self):
        return os.path.join(self._localUser.GetPipeConfigurationDir(),"local_managers")

