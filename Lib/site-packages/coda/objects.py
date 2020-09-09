# -*- coding: utf-8 -*-
#
# All ensembl-based object models
# 
# @author <bprinty@gmail.com>
# ------------------------------------------------


# imports
# -------
import os
from gems import composite, filetree, DocRequire, keywords


# files
# -----
class File(object):
    """
    Abstract class for file object.

    Args:
        path (list): List of file object to manage.
        metadata (dict): Dictionary with common metadata for collection,
            specified a priori.
    """
    __metaclass__ = DocRequire

    def __init__(self, path, metadata={}):
        assert os.path.exists(path), 'Specified file path does not exist!'
        assert not os.path.isdir(path), 'Specified file is not a file! Use the Collection object for a directory.'
        self.path = os.path.realpath(path)
        self._metadata = composite(metadata)
        return

    @property
    def name(self):
        """
        Return basename for file.
        """
        return os.path.basename(self.path)

    @property
    def location(self):
        """
        Return dirname for file.
        """
        return os.path.dirname(self.path)

    @property
    def extension(self):
        """
        Return extension for file.
        """
        return '.' + self.name.split('.')[-1]

    @property
    def metadata(self):
        """
        Proxy for returning metadata about specified file.
        """
        return self._metadata

    def __repr__(self):
        """
        Return string representation for file (file path).
        """
        return str(self)

    def __str__(self):
        """
        Return string representation for file (file path).
        """
        return self.path

    def __contains__(self, item):
        """
        Check if specified string exists in file name.
        """
        return item in self.name

    def __lt__(self, other):
        """
        Comparison operator. Compares left and right file
        paths alphanumerically.
        """
        if not isinstance(other, File):
            TypeError('unsupported comparison type(s) \'{}\' and \'{}\''.format(type(self), type(other)))
        return self.path < other.path

    def __gt__(self, other):
        """
        Comparison operator. Compares left and right file
        paths alphanumerically.
        """
        if not isinstance(other, File):
            TypeError('unsupported comparison type(s) \'{}\' and \'{}\''.format(type(self), type(other)))
        return self.path > other.path

    def __eq__(self, other):
        """
        Test equality for File objects.
        """
        return self.path == other.path

    def __add__(self, other):
        """
        Addition operator for files or collections. Using this, you can
        add File objects to other File objects to form a Collection, or
        add File objects to Collection objects to form a new Collection.

        Examples:
            >>> # add files to create collection
            >>> one = coda.File('/file/one.txt')
            >>> two = coda.File('/file/two.txt')
            >>> collection = one + two
            >>> print collection
            '/file/one.txt'
            '/file/two.txt'
            >>>
            >>> # add file to collection to create new collection'
            >>> three = coda.File('/file/three.txt')
            >>> collection = three + collection
            >>> print collection
            '/file/three.txt'
            '/file/one.txt'
            '/file/two.txt'
        """
        if isinstance(other, File):
            if self == other:
                return Collection(files=[self])
            else:
                return Collection(files=[self, other])
        elif isinstance(other, Collection):
            if self in other:
                return other
            else:
                return Collection(files=[self] + other.files)
        else:
            raise TypeError('unsupported operand type(s) for +: \'{}\' and \'{}\''.format(type(self), type(other)))
        return

    def __getattr__(self, name):
        """
        Proxy for accessing metadata directly as a property on the class.
        """
        return self.metadata[name]

    def __getitem__(self, name):
        """
        Proxy for accessing metadata directly as a property on the class.
        """
        return self.metadata[name]

    def __setattr__(self, name, value):
        """
        Proxy for setting metadata directly as a property on the class.
        """
        if name not in ['_metadata', 'path']:
            self.metadata[name] = value
        else:
            super(File, self).__setattr__(name, value)
        return


class Collection(object):
    """
    Abstract class for collection of file objects.

    Args:
        files (list): List of file objects to manage, or path to directory
            to generate collection from.
        metadata (dict): Dictionary with common metadata for collection,
            specified a priori.
    """
    __metaclass__ = DocRequire
    __file_base__ = File

    def __init__(self, files, metadata={}):
        if isinstance(files, str):
            ft = filetree(files)
            self.files = [self.__file_base__(x) for x in ft.filelist()]
            if len(self.files) == 0:
                raise AssertionError('Could not find any files for collection!')
        else:
            self.files = files
        self._metadata = composite(metadata)
        return

    @property
    def filelist(self):
        """
        Return list with full paths to files in collection.
        """
        return [x.path for x in self.files]

    @property
    def metadata(self):
        """
        If no metadata is initially specified for a file, query the database
        for metadata about the specified file.
        """
        if len(self._metadata) == 0:
            res = self.files[0].metadata
            for idx in range(1, len(self.files)):
                res = res.intersection(self.files[idx].metadata)
            self._metadata = res
        return self._metadata

    @keywords
    def add_metadata(self, *args, **kwargs):
        """
        Add metadata for all objects in the collection. 
        """
        for idx in range(0, len(self.files)):
            for key in kwargs:
                self.files[idx].metadata[key] = kwargs[key]
        for key in kwargs:
            self._metadata[key] = kwargs[key]
        return

    def filter(self, func=lambda x: True):
        """
        Filter collection using specified function. This function
        allows for filtering files from collection objects by an arbitrary
        operator. This could be used for filtering more specifically by 
        existing metadata tags, or by more complex methods that read in the file
        and perform some operation to it.

        Args:
            func (function): Function to filter with.

        Examples:
            >>> # query collection for tag
            >>> cl = coda.find({'group': 'testing'})
            >>>
            >>> # query file by data_type tag (assuming tags exist)
            >>> cl.filter(lambda x: x.data_type in ['csv', 'txt'])
        """
        return self.__class__(files=list(filter(func, self.files)))

    def __repr__(self):
        """
        Return string representation for collection (list of file paths).
        """
        return str(self)

    def __str__(self):
        """
        Return string representation for collection (list of file paths).
        """
        return '[' + ',\n '.join(map(str, self.files)) + ']'

    def __lt__(self, other):
        """
        Compare collection objects by number of files in the collections.
        """
        return len(self.files) < len(other.files)

    def __gt__(self, other):
        """
        Compare collection objects by number of files in the collections.
        """
        return len(self.files) > len(other.files)

    def __eq__(self, other):
        """
        Compare equality for collections.
        """
        return sorted(self.files) == sorted(other.files)

    def __iter__(self):
        """
        Iterator for collection object. Iterates by returning each file.
        """
        for obj in self.files:
            yield obj

    def __len__(self):
        """
        Return length of collection object (number of files in collection).
        """
        return len(self.files)

    def __contains__(self, item):
        """
        Check if item exists in file set. Input item should be a File object.
        """
        return item in self.files

    def __add__(self, other):
        """
        Addition operator for collections or files. Using this, you can
        add Collection objects to other Colletion objects to form a Collection, or
        add Collection objects to File objects to form a new Collection.

        Examples:
            >>> # add files to create collection
            >>> one = coda.File('/file/one.txt')
            >>> two = coda.File('/file/two.txt')
            >>> onetwo = one + two
            >>> three = coda.File('/file/three.txt')
            >>> four = coda.File('/file/four.txt')
            >>> threefour = three + four
            >>>
            >>> # add collection objects to create new collection
            >>> print onetwo + threefour
            '/file/one.txt'
            '/file/two.txt'
            '/file/three.txt'
            '/file/four.txt'
            >>>
            >>> # add collection to file object to create new collection
            >>> print onetwo + three
            '/file/one.txt'
            '/file/two.txt'
            '/file/three.txt'
        """
        if isinstance(other, self.__file_base__):
            res = [x for x in self.files]
            if other not in self:
                res += [other]
            return self.__class__(files=res, metadata=self._metadata)
        elif isinstance(other, self.__class__):
            res = [x for x in self.files]
            for item in other.files:
                if item not in self:
                    res += [item]
            return self.__class__(files=res, metadata=self._metadata)
        else:
            raise TypeError('unsupported operand type(s) for +: \'{}\' and \'{}\''.format(type(self), type(other)))
        return

    def __sub__(self, other):
        """
        Subtraction operator for collections or files. Using this, you can
        subtract Collection objects from other Colletion objects to form a Collection
        with the difference in files, or subtract File objects from Collection objects
        to return a new Collection without the File object.

        Examples:
            >>> # add files to create collection
            >>> one = coda.File('/file/one.txt')
            >>> two = coda.File('/file/two.txt')
            >>> onetwo = one + two
            >>> three = coda.File('/file/three.txt')
            >>> onetwothree = onetwo + three
            >>>
            >>> # subtract collection objects to create new collection
            >>> print onetwothree - onetwo
            '/file/three.txt'
            >>>
            >>> # subtract file from collection object to create new collection
            >>> print onetwothree - three
            '/file/one.txt'
            '/file/two.txt'
        """
        if isinstance(other, self.__file_base__):
            return self.__class__(files=[x for x in self.files if x != other])
        elif isinstance(other, Collection):
            return self.__class__(files=[x for x in self.files if x not in other])
        else:
            raise TypeError('unsupported operand type(s) for +: \'{}\' and \'{}\''.format(type(self), type(other)))
        return

    def __getattr__(self, name):
        """
        Proxy for accessing metadata directly as a property on the class.
        """
        return self.metadata[name]

    def __getitem__(self, item):
        """
        Proxy for accessing metadata directly as a property on the class.
        """
        if isinstance(item, str):
            return self.metadata[item]
        else:
            return self.files[item]

    def __setattr__(self, name, value):
        """
        Proxy for setting metadata directly as a property on the class.
        """
        if name not in ['_metadata', 'files']:
            self.add_metadata({name: value})
        else:
            super(self.__class__, self).__setattr__(name, value)
        return

