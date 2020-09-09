# -*- coding: utf-8 -*-
#
# All ensembl-based object models
# 
# @author <bprinty@gmail.com>
# ------------------------------------------------


# imports
# -------
import os
from cached_property import cached_property
import pymongo
from gems import composite, DocRequire, keywords

from coda.objects import File, Collection


# config
# ------
__base__ = os.path.dirname(os.path.realpath(__file__))
__default_config__ = os.path.join(__base__, '.coda')
__user_config__ = os.path.join(os.path.expanduser("~"), '.coda')


# database config
# ---------------
class Session(object):
    """
    Object for managing connection to internal database.

    Args:
        host (str): Host with database to connect to.
        port (int): Port to connect to database with.
        write (bool): Whether or not to allow writing to the database.
        dbname (str): Name of database to use.
    """

    def __init__(self, host='localhost', port=27017, write=True, dbname='coda'):
        self.host = host
        self.port = port
        self.write = write
        self.dbname = dbname
        self._db = None
        return

    @property
    def options(self):
        """
        Return JSON with options on the session.
        """
        return {
            'host': self.host,
            'port': self.port,
            'write': self.write,
            'dbname': self.dbname
        }

    @property
    def db(self):
        """
        Internal property for managing connection to mongodb database.
        """
        if self._db is None:
            try:
                client = pymongo.MongoClient(self.host, self.port)
                self._db = client[self.dbname]
            except pymongo.errors.ServerSelectionTimeoutError:
                self._db = None
                raise AssertionError('Could not connect to database! Try using `mongod` to start mongo server.')
        return self._db


@keywords
def options(*args, **kwargs):
    """
    Set options for the current session.

    Args:
        kwargs (dict): List of arbitrary config items to set.

    Examples:
        >>> # set options to defaults
        >>> coda.options()
        >>> coda.find_one({'name': 'test'}).path
        '/file/on/localhost/server'
        >>>
        >>> # connect to a database for a different host
        >>> coda.options({'host': 'remote'})
        >>> coda.find_one({'name': 'test'}).path
        '/file/on/remote/server'
    """
    global session, __default_config__, __user_config__
    with open(__default_config__, 'r') as cfig:
        config = composite(cfig)
    if os.path.exists(__user_config__):
        with open(__user_config__, 'r') as cfig:
            config = config + composite(cfig)
    if len(kwargs) != 0:
        config = config + composite(kwargs)
    try:
        session = Session(**config._dict)
    except TypeError:
        raise AssertionError('Something is wrong with your coda configuration'
                             ' -- check your config file for valid parameters.')
    return config.json()


session = Session()
options()


# extensions
# ----------
def _metadata(self):
    """
    Proxy for returning metadata -- if the file exists in the database,
    then pull metadata for it if none already exists. If metadata exists
    for the object, then return that.
    """
    if len(self._metadata) == 0:
        obj = find_one({'path': self.path})
        if obj is not None:
            self._metadata = obj._metadata
    return self._metadata


File.metadata = property(_metadata)
Collection.__file_base__ = File


# searching
# ---------
def find(query):
    """
    Search database for files with specified metadata.

    Args:
        query (dict): Dictionary with query parameters.

    Returns:
        Collection: Collection object with results.

    Examples:
        >>> # assuming the database has already been populated
        >>> print coda.find({'type': 'test'})
        '/my/testing/file/one.txt'
        '/my/testing/file/two.txt'
        >>>
        >>> # assuming 'count' represents line count in the file
        >>> print coda.find({'type': 'test', 'count': {'$lt': 30}})
        '/my/testing/file/two.txt'
        >>>
        >>> # using the filter() method on collections instead
        >>> print coda.find({'type': 'test'}).filter(lambda x: x.count < 30)
        '/my/testing/file/two.txt'
    """
    files = []
    for item in session.db.files.find(query):
        path = item.get('path')
        if path is None:
            raise AssertionError('Path information for file not available -- '
                                 'your database is in a weird state. Please '
                                 'ensure that each record in the database has '
                                 'an associated path.')
        item.pop('path', None)
        files.append(File(path=path, metadata=item))
    if len(files) == 0:
        return None
    return Collection(files=files)


def find_one(query):
    """
    Search database for one file with specified metadata.

    Args:
        query (dict): Dictionary with query parameters.

    Returns:
        File: File object with results.

    Examples:
        >>> # assuming the database has already been populated
        >>> print coda.find_one({'type': 'test'})
        '/my/testing/file/one.txt'
        >>>
        >>> # assuming 'count' represents line count in the file
        >>> print coda.find({'type': 'test', 'count': {'$lt': 30}})
        '/my/testing/file/two.txt'
    """
    item = session.db.files.find_one(query)
    if item is None:
        return None
    path = item.get('path')
    if path is None:
        raise AssertionError('Path information for file not available -- '
                             'your database is in a weird state. Please '
                             'ensure that each record in the database has '
                             'an associated path.')
    item.pop('path', None)
    return File(path=path, metadata=item)


# database update methods
# -----------------------
def add(obj):
    """
    Add file object or collection object to database.

    Args:
        obj (File, Collection): File or collection of files to add.

    Examples:
        >>> # instantiate File object and add metadata
        >>> fi = coda.File('/path/to/test/file.txt')
        >>> fi.type = 'test'
        >>> 
        >>> # add file to database
        >>> coda.add(fi)
        >>>
        >>> # instantiate directory as Collection with common metadata
        >>> cl = coda.Collection('/path/to/test/dir/')
        >>> cl.type = 'test'
        >>> coda.add(cl)
    """
    global session
    if isinstance(obj, (Collection, list, tuple)):
        return list(map(add, obj))
    if not isinstance(obj, File):
        raise TypeError('unsupported type for add {}'.format(type(obj)))
    ret = session.db.files.find_one({'path': obj.path})
    dat = obj.metadata.json()
    dat['path'] = obj.path
    if ret is None:
        return session.db.files.insert_one(dat)
    else:
        return session.db.files.update({'path': dat['path']}, dat)


def delete(obj):
    """
    Delete file or collection of files from database.

    Args:
        obj (File, Collection): File or collection of files to delete.

    Examples:
        >>> # instantiate File object and delete
        >>> fi = coda.File('/path/to/test/file.txt')
        >>> coda.delete(fi)
        >>>
        >>> # instantiate directory and delete
        >>> cl = coda.Collection('/path/to/test/dir/')
        >>> coda.delete(cl)
        >>>
        >>> # query by metadata and delete entries
        >>> cl = coda.find({'type': 'testing'})
        >>> coda.delete(cl)
    """
    global session
    if isinstance(obj, (Collection, list, tuple)):
        return list(map(delete, obj.files))
    if not isinstance(obj, File):
        raise TypeError('unsupported type for delete {}'.format(type(obj)))
    return session.db.files.delete_many({'path': obj.path})

