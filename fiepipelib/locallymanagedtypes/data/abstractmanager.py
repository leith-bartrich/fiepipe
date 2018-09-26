import abc
import json
import os.path
import pathlib
import sqlite3
import typing

import fiepipelib.localuser.routines.localuser

T = typing.TypeVar("T", bound=object)


class AbstractLocalTypeManager(typing.Generic[T]):
    """An abstract class with which to make managers of static data.  Currently backed by sqlite.
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
        # we create/update the table
        conn = self._GetDBConnection()
        assert isinstance(conn, sqlite3.Connection)
        cur = conn.cursor()
        self._CreateTable(cur)
        conn.commit()
        conn.close()

    @abc.abstractmethod
    def GetConfigDir(self) -> str:
        """Override this: Returns the path to the configuration directory for this manager."""
        raise NotImplementedError()

    @abc.abstractmethod
    def GetManagedTypeName(self) -> str:
        """Override this: Returns the name of the type of managed item this manager manages.
        e.g. The FooManager probably returns 'Foo'"""
        raise NotImplementedError()

    def _GetDBFilename(self) -> str:
        """Returns the full path to the DB file to load."""
        dir = os.path.join(self.GetConfigDir(), "dbv1")
        if not os.path.exists(dir):
            os.makedirs(dir)
        return os.path.join(dir, self.GetManagedTypeName() + ".db")

    def _GetDBConnection(self) -> sqlite3.Connection:
        """Returns an open sqlite3 connection for the mananger's data.  Keep in mind, the database is usually
        locked based on the transaction this connection represents.  So grab it, use it, and dump it quickly
        to avoid blocking processes.  Or, hold on to it if you really need to."""
        # TODO: when we move to v2, we'll need to detect the missing v2
        # and run an upgrade from v1 to v2 here.  And upon failure, raise
        # an exception.
        ret = sqlite3.connect(self._GetDBFilename())
        assert isinstance(ret, sqlite3.Connection)
        return ret

    def GetDBConnection(self) -> sqlite3.Connection:
        """Returns an open sqlite3 connection with the mananger's data as the "main" DB.  Keep in mind, the
        database is usually
        locked based on the transaction this connection represents.  So grab it, use it, and dump it quickly
        to avoid blocking processes.  Or, hold on to it if you really need to.
        
        Most manager methods that take a connection argument will open and close one automatically.  If you
        instead intend to use a connection's transation capabilities, you'll want to get one here
        and pass it around, using it's commit, rollback methods at appropriate times.
        """
        return self._GetDBConnection()

    @abc.abstractmethod
    def GetColumns(self) -> typing.List[typing.Tuple[str, str]]:
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
        ret.append(('json', 'text'))
        return ret

    @abc.abstractmethod
    def GetPrimaryKeyColumns(self) -> typing.List[str]:
        """Returns a list of column names that make up the primary key"""
        raise NotImplementedError()

    def _CreateTable(self, conn: sqlite3.Connection = None):
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

        if conn == None:
            conn = self._GetDBConnection()

        conn.execute(statement)
        # TODO: add indexes here

    def _CreateUpdateRows(self, data: typing.List[dict], conn: sqlite3.Connection = None, commit=True):
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
            if conn == None:
                conn = self._GetDBConnection()
            cur = conn.cursor()
            cur.executemany(statement, values)
            if commit:
                conn.commit()

    def _DeleteRowsByMultipleAND(self, colNamesAndValues: typing.List[typing.Tuple[str, typing.Any]] = [],
                                 conn: sqlite3.Connection = None, commit=True):
        """Runs a delete statement to search for and delete rows matching all passed column and value tupples with AND logic.
        @param colNamesAndValues: A list of tupples.  e.g. [("firstname","John"),("lastname","Doe")]
        """
        statement = "DELETE FROM " + self.GetManagedTypeName()
        if conn == None:
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
        cur.execute(statement, values)
        if commit:
            conn.commit()

    def _GetRowsByMultipleAND(self, cur: sqlite3.Cursor,
                              colNamesAndValues: typing.List[typing.Tuple[str, typing.Any]] = []):
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
        cur.execute(statement, values)

    @abc.abstractmethod
    def ToJSONData(self, item: T) -> dict:
        """Override this: Converts the given item into JSON data, which is a dictionary object, and returns it."""
        raise NotImplementedError()

    @abc.abstractmethod
    def FromJSONData(self, data: dict) -> T:
        """Override this: Converts the givne JSON data, which is a dictionary, into an item and returns it."""
        raise NotImplementedError()

    def _ItemFromRow(self, row: sqlite3.Row) -> T:
        """Converts row data into an item and returns it."""
        return self.FromJSONData(json.loads(row['json']))

    def _ItemsToInsertData(self, items: typing.List[T]) -> typing.List[typing.Tuple[str, typing.Any]]:
        """Converts the given list of items into data suitable for insertion into the databse."""
        data = []
        for item in items:
            jsondata = self.ToJSONData(item)
            row = {}
            row['json'] = json.dumps(jsondata,indent=4,sort_keys=True)
            for col in self.GetColumns():
                if col[0] != 'json':
                    row[col[0]] = str(jsondata[col[0]])
            data.append(row)
        return data

    def _Get(self, colNamesAndValues: typing.List[typing.Tuple[str, typing.Any]] = [],
             conn: sqlite3.Connection = None) -> typing.List[T]:
        """Gets items that match an AND based column and value filter.

        Typically a manager will have a series of more type specific Get methods to call.

        If you pass an empty list (default) it gets all of them.  Which is probably faster than listing them.

        @param colNamesAndValues: a list of tupples of column name and value pairs
        e.g. [(foo,1),(bar,100)] means: WHERE foo = 1 AND bar = 100
        @return: A list of items.  Empty list if none meet the criteria.

        """
        if conn == None:
            conn = self._GetDBConnection()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        self._GetRowsByMultipleAND(cur, colNamesAndValues)
        rows = cur.fetchall()
        ret = []
        for row in rows:
            ret.append(self._ItemFromRow(row))
        return ret

    def GetAll(self, conn: sqlite3.Connection = None) -> typing.List[T]:
        return self._Get(conn=conn)

    def Set(self, items: typing.List[T], conn: sqlite3.Connection = None, commit=True):
        """Sets (create/update) items.
        @param items: A list of items to set.
        """
        insertData = self._ItemsToInsertData(items)
        self._CreateUpdateRows(insertData, conn, commit)

    def _Delete(self, colName: str, colValue: typing.Any, conn: sqlite3.Connection = None, commit=True):
        """Deletes items by the colName and colValue.

        As in: DELETE from TABLE WHERE [colName] = [colValue]

        Typically a manager will have a series of more type specific Delete methods to call.

        @param colName: The column name to match for deletion
        @param colValue: The column value to match for deletion
        """
        self._DeleteRowsByMultipleAND([(colName, colValue)], conn, commit)

    def _DeleteByMultipleAND(self, colNamesAndValues: typing.List[typing.Tuple[str, typing.Any]] = [],
                             conn: sqlite3.Connection = None, commit=True):
        """Deletes items by multiple AND conditions.

        Typically a manager will have a series of more type specific Delete methods to call.

        @param colNamesAndValus: A list of tupples of names and values to use as conditions.  e.g. [("fqdn","them.com"),("sitename","home")]
        """
        self._DeleteRowsByMultipleAND(colNamesAndValues, conn, commit)

    def _dumpTo(self, path: str):
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

    def _readFrom(self, path: str, conn: sqlite3.Connection = None):
        p = pathlib.Path(path)
        if conn == None:
            conn = self._GetDBConnection()
        cur = conn.cursor()
        assert isinstance(cur, sqlite3.Cursor)
        statement = ".read " + str(p.absolute())
        cur.execute(statement)
        conn.commit()

class AbstractUserLocalTypeManager(AbstractLocalTypeManager[T]):
    """Subclass this.
    
    A local manager than knows how to save its data to sqlite databases in the user's fiepipe configuration directory.

    Implements the GetConfigDir abstract method.

    All others must still be overridden from the superclass.
    """

    _localUser = None

    def __init__(self, localUser: fiepipelib.localuser.routines.localuser.LocalUserRoutines):
        assert isinstance(localUser, fiepipelib.localuser.routines.localuser.LocalUserRoutines)
        self._localUser = localUser
        super().__init__()

    def GetConfigDir(self) -> str:
        return os.path.join(self._localUser.get_pipe_configuration_dir(), "local_managers")
