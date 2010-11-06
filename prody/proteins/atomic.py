# ProDy: A Python Package for Protein Structural Dynamics Analysis
# 
# Copyright (C) 2010  Ahmet Bakan <ahb12@pitt.edu>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#  
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

""":mod:`atomgroup` module defines classes for handling atomic data.

Classes:

    * :class:`AtomGroup`
    * :class:`AtomMap`
    * :class:`AtomSubset`
    * :class:`Chain`
    * :class:`Residue`
    * :class:`Selection`
    * :class:`AtomMap`
    * :class:`HierView`
"""

__author__ = 'Ahmet Bakan'
__copyright__ = 'Copyright (C) 2010  Ahmet Bakan'

from collections import defaultdict

import numpy as np

import prody
from prody import ProDyLogger as LOGGER
from .select import ProDyAtomSelect as SELECT
from . import ATOMIC_DATA_FIELDS

__all__ = ['AtomGroup', 'Atom', 'AtomSubset', 'Selection', 'Chain', 'Residue', 'HierView', 'AtomMap']


class AtomGroupMeta(type):
    
    def __init__(cls, name, bases, dict):

        def wrapGetMethod(fn):
            def wrapped(self):
                return fn(self)
            return wrapped

        def wrapSetMethod(fn):
            def wrapped(self, array):
                return fn(self, array)
            return wrapped

        for field in ATOMIC_DATA_FIELDS.values():
            def getData(self, var=field.var):
                array = self.__dict__['_'+var]
                if array is None:
                    return None
                return array.copy() 
            getData = wrapGetMethod(getData)
            getData.__name__ = field.meth_pl
            getData.__doc__ = 'Return a copy of {0:s}.'.format(field.doc_pl)
            setattr(cls, 'get'+field.meth_pl, getData)
            
            def setData(self, array, var=field.var, dtype=field.dtype):
                if self._n_atoms == 0:
                    self._n_atoms = len(array)
                elif len(array) != self._n_atoms:
                    raise ValueError('length of array must match n_atoms')
                    
                if isinstance(array, list):
                    array = np.array(array, dtype)
                elif not isinstance(array, np.ndarray):
                    raise TypeError('array must be a NumPy array or a list')
                elif array.dtype != dtype:
                    try:
                        array.astype(dtype)
                    except ValueError:
                        raise ValueError('array cannot be assigned type '
                                         '{0:s}'.format(dtype))
                self.__dict__['_'+var] = array
            setData = wrapSetMethod(setData)
            setData.__name__ = field.meth_pl 
            setData.__doc__ = 'Set {0:s}.'.format(field.doc_pl)  
            setattr(cls, 'set'+field.meth_pl, setData)


class AtomGroup(object):
    
    """A class for storing and accessing atomic data.
    
    
    The number of atoms of the atom group is inferred at the first set method
    call from the size of the data array. 

    **Atomic Data**
    
    All atomic data is stored in :class:`numpy.ndarray` instances.

    **Get and Set Methods** 
    
    *getAttribute()* methods return copies of the data arrays. 
    
    *setAttribute()* methods accepts data contained in :class:`list` or 
    :class:`numpy.ndarray` instances. The length of the list or array must 
    match the number of atoms in the atom group. Set method sets attributes of 
    all atoms at once.
    
    Atom groups with multiple coordinate sets may have one of these sets as 
    the active coordinate set. The active coordinate set may be changed using
    :meth:`setActiveCoordsetIndex()` method. :meth:`getCoordinates` returns
    coordinates from the active set.
    
    To access and modify data associated with a subset of atoms in an atom group, 
    :class:`Selection` instances may be used. A selection from an atom 
    group has initially the same coordinate set as the active coordinate set.
    
    User can iterate over atoms and coordinate sets in an atom group. To 
    iterate over residues and chains, get a hierarchical view of the atom 
    group by calling :meth:`getHierView()`. 

    """
    __metaclass__ = AtomGroupMeta
    
    
    def __init__(self, name):
        """Instantiate an AtomGroup with a *name*."""
        self._name = str(name)
        self._n_atoms = 0
        self._coordinates = None
        self._acsi = 0                  # Active Coordinate Set Index
        self._n_coordsets = 0
        
        for field in ATOMIC_DATA_FIELDS.values():
            self.__dict__['_'+field.var] = None

    def __repr__(self):
        return ('<AtomGroup: {0:s} ({1:d} atoms; {2:d} coordinate sets, active '
               'set index: {3:d})>').format(self._name, 
              self._n_atoms, self._n_coordsets, self._acsi)
        return ('<AtomGroup: {0:s}>').format(str(self))
        
    def __str__(self):
        return ('AtomGroup {0:s}').format(self._name)
        return ('{0:s} ({1:d} atoms; {2:d} coordinate sets, active '
               'set index: {3:d})').format(self._name, 
              self._n_atoms, self._n_coordsets, self._acsi)

    def __getitem__(self, indices):
        if isinstance(indices, int):
            if indices < 0:
                indices = self._n_atoms + indices
            return Atom(self, indices, self._acsi)
        elif isinstance(indices, slice):
            start, stop, step = indices.indices(self._n_atoms)
            if start is None:
                start = 0
            if step is None:
                step = 1
            selstr = 'index {0:d}:{1:d}:{2:d}'.format(start, stop, step)
            return Selection(self, 
                             np.arange(start, stop, step), 
                             selstr,
                             self._acsi)
        elif isinstance(indices, (list, np.ndarray)):
            return Selection(self, 
                             np.array(indices), 
                             'Some atoms', 
                             'index {0:s}'.format(
                                            ' '.join(np.array(indices, '|S'))),
                             self._acsi)
        else:
            raise IndexError('invalid index') 
    
    def __iter__(self):
        """Iterate over atoms in the atom group."""
        acsi = self._acsi
        for index in xrange(self._n_atoms):
            yield Atom(self, index, acsi)

    def __len__(self):
        return self._n_atoms
    
    def __add__(self, other):
        if not isinstance(other, AtomGroup):
            raise TypeError('type mismatch')
        if self == other:
            raise ValueError('an atom group cannot be added to itself')
        
        new = AtomGroup(self._name + ' + ' + other._name)
        n_coordsets = self._n_coordsets
        if n_coordsets != other._n_coordsets:
            LOGGER.warning('AtomGroups {0:s} and {1:s} do not have same number '
                'of coordinate sets. First from both AtomGroups will be merged.'
                .format(str(self._name), str(other._name), n_coordsets))
            n_coordsets = 1
        coordset_range = range(n_coordsets)
        new.setCoordinates(np.concatenate((self._coordinates[coordset_range],
                                        other._coordinates[coordset_range]), 1))
        
        for field in ATOMIC_DATA_FIELDS:
            var = '_' + field.var
            this = self.__dict__[var]
            that = other.__dict__[var]
            if this is not None and that is not None:
                new.__dict__[var] = np.concatenate((this, that))

        return new

    def getName(self):
        """Return name of the atom group instance."""
        return self._name
    
    def setName(self, name):
        """Set name of the atom group instance."""
        self._name = str(name)
    
    def getNumOfAtoms(self):
        """Return number of atoms."""
        return self._n_atoms
    
    def getCoordinates(self): 
        """Return coordinates from active coordinate set."""
        if self._coordinates is None:
            return None
        return self._coordinates[self._acsi].copy()
    
    def setCoordinates(self, coordinates):
        """Set coordinates.
        
        Coordinates must be a NumPy ndarray instance.
        
        If the shape of the coordinates array is (n_coordsets,n_atoms,3),
        the given array will replace all coordinate sets. To avoid it,
        :meth:`addCoordset` may be used.
        
        If the shape of the coordinates array is (n_atoms,3) or (1,n_atoms,3),
        the coordinate set will replace the coordinates of the currently active 
        coordinate set.
        
        """
        if not isinstance(coordinates, np.ndarray):
            raise TypeError('coordinates must be an ndarray instance')

        if not coordinates.ndim in (2, 3):
            raise ValueError('coordinates must be a 2d or a 3d array')
            
        if coordinates.shape[-1] != 3:
            raise ValueError('shape of coordinates must be (n_atoms,3) or '
                             '(n_coordsets,n_atoms,3)')
        float64 = np.float64
        if coordinates.dtype != float64:
            try:
                coordinates.astype(float64)
            except ValueError:
                raise ValueError('coordinate array cannot be assigned type '
                                 '{0:s}'.format(np.float64))

        if self._n_atoms == 0:
            self._n_atoms = coordinates.shape[-2] 
        elif coordinates.shape[-2] != self._n_atoms:
            raise ValueError('length of coordinate array must match n_atoms')
        
        if self._coordinates is None:
            if coordinates.ndim == 2:
                coordinates = coordinates.reshape(
                                (1, coordinates.shape[0], coordinates.shape[1]))
            self._coordinates = coordinates
            self._n_coordsets = self._coordinates.shape[0]
            self._acsi = 0
        else:
            if coordinates.ndim == 2:
                self._coordinates[self._acsi] = coordinates
            elif coordinates.shape[0] == 1:
                self._coordinates[self._acsi] = coordinates[0]
            else:
                self._coordinates = coordinates
                self._n_coordsets = self._coordinates.shape[0]
                self._acsi = min(self._n_coordsets-1,
                                                    self._acsi)
    
    def addCoordset(self, coords):
        """Add a coordinate set to the atom group."""
        if self._coordinates is None:
            self.setCoordinates(coords)
        if not isinstance(coords, np.ndarray):
            raise TypeError('coords must be an ndarray instance')
        elif not coords.ndim in (2, 3):
            raise ValueError('coords must be a 2d or a 3d array')
        elif coords.shape[-2:] != self._coordinates.shape[1:]:
            raise ValueError('shape of coords must be ([n_coordsets,] n_atoms, 3)')
        elif coords.dtype != np.float64:
            try:
                coords.astype(np.float64)
            except ValueError:
                raise ValueError('coords array cannot be assigned type '
                                 '{0:s}'.format(np.float64))
        if coords.ndim == 2:
            coords = coords.reshape((1, coords.shape[0], coords.shape[1]))
        
        self._coordinates = np.concatenate((self._coordinates, coords), axis=0)
        self._n_coordsets = self._coordinates.shape[0]

    def delCoordset(self, index):
        """Delete a coordinate set from the atom group."""
        which = np.ones(self._n_coordsets, np.bool)
        which[index] = False
        if which.sum() == self._n_coordsets:
            self._coordinates = None
            self._n_coordsets = 0
        else:
            self._coordinates = self._coordinates[which]
            self._n_coordsets = self._coordinates.shape[0]
        self._acsi = 0

    def getCoordsets(self, indices=None):
        """Return a copy of coordinate sets at given indices.
        
        *indices* may be an integer, a list of integers or ``None``. ``None``
        returns all coordinate sets. 
        
        """
        if indices is None:
            indices = slice(None)
        if self._coordinates is None:
            return None
        try: 
            return self._coordinates[indices].copy()
        except IndexError:
            raise IndexError('indices must be an integer, a list of integers, or None')

    def getNumOfCoordsets(self):
        """Return number of coordinate sets."""
        return self._n_coordsets
    
    def iterCoordsets(self):
        """Iterate over coordinate sets by returning a copy of each 
        coordinate set."""
        for i in range(self._n_coordsets):
            yield self._coordinates[i].copy()
    
    def getActiveCoordsetIndex(self):
        """Return index of the active coordinate set."""
        return self._acsi
    
    def setActiveCoordsetIndex(self, index):
        """Set the index of the active coordinate set."""
        if self._n_coordsets == 0:
            self._acsi = 0
        if not isinstance(index, int):
            raise TypeError('index must be an integer')
        if self._n_coordsets <= index or self._n_coordsets < abs(index):
            raise IndexError('coordinate set index is out of range')
        if index < 0:
            index += self._n_coordsets 
        #self._kdtree = None
        self._acsi = index
    


    def select(self, selstr):
        """Return a selection matching the criteria given by *selstr*."""
        return SELECT.select(self, selstr)
    
    
    def copy(self, which=None):
        """Return a copy of atoms indicated *which* as a new AtomGroup instance.
        
        *which* may be:
            
            * a Selection, Residue, Chain, or Atom instance
            * a list or an array of indices
            * a selection string
        
        """
        
        if which is None:
            indices = None
            newmol = AtomGroup('Copy of {0:s}'.format(self._name))
        elif isinstance(which, int):
            indices = [which]
            newmol = AtomGroup('Copy of {0:s} index {1:d}'.format(
                                 self._name, which))
        elif isinstance(which, str):
            indices = SELECT.select(self, which).getIndices()
            newmol = AtomGroup('Copy of {0:s} selection "{1:s}"'
                              .format(self._name, which))
        elif isinstance(which, (list, np.ndarray)):
            if isinstance(which, list):
                indices = np.array(which)
            else:
                indices = which
            newmol = AtomGroup('Copy of a {0:s} subset'
                              .format(self._name))
        elif isinstance(which, prody.Selection):
            indices = which.getIndices()
            newmol = AtomGroup('Copy of {0:s} selection "{1:s}"'
                              .format(self._name, which.getSelectionString()))
        elif isinstance(which, prody.Chain):
            indices = which.getIndices()
            newmol = AtomGroup('Copy of {0:s} chain {1:s}'
                              .format(self._name, which.getIdentifier()))
        elif isinstance(which, prody.Residue):
            indices = which.getIndices()
            newmol = AtomGroup('Copy of {0:s} residue {1:s}{2:d}'
                              .format(self._name, which.getName(), which.getNumber()))
        elif isinstance(which, prody.Atom):
            indices = [which.getIndex()]
            newmol = AtomGroup('Copy of {0:s} index {1:d}'.format(
                                 self._name, which.getIndex()))
        elif isinstance(which, prody.AtomMap):
            indices = which.getIndices()
            newmol = AtomGroup('Copy of {0:s} atom map {1:s}'.format(
                                 self._name, str(which)))
            

        if indices is None:
            newmol.setCoordinates(self._coordinates.copy())
            for field in ATOMIC_DATA_FIELDS:
                var = '_' + field.var
            array = self.__dict__[var]
            if array is not None:
                newmol.__dict__[var] = array.copy()
        else:
            newmol.setCoordinates(
                    self._coordinates[:, indices].copy(
                        ).reshape((self._n_coordsets, len(indices), 3)))
            for field in ATOMIC_DATA_FIELDS:
                var = '_' + field.var
            array = self.__dict__[var]
            if array is not None:
                newmol.__dict__[var] = array[indices].copy()

        return newmol
    
    def getHierView(self):
        """Return a hierarchical view of the atom group."""
        return HierView(self)
    
class AtomMeta(type):
    
    def __init__(cls, name, bases, dict):

        def wrapGetMethod(fn):
            def wrapped(self):
                return fn(self)
            return wrapped
        def wrapSetMethod(fn):
            def wrapped(self, value):
                return fn(self, value)
            return wrapped

        for field in ATOMIC_DATA_FIELDS.values():
            def getData(self, var=field.var):
                array = self._ag.__dict__['_'+var]
                if array is None:
                    return None
                return array[self._index] 
            getData = wrapGetMethod(getData)
            getData.__name__ = field.meth
            getData.__doc__ = 'Return {0:s} of the atom.'.format(field.doc)
              
            setattr(cls, 'get'+field.meth, getData)
            
            def setData(self, value, var=field.var):
                array = self._ag.__dict__['_'+var]
                if array is None:
                    raise AttributeError('attribute of the AtomGroup is not set')
                array[self._index] = value
            setData = wrapSetMethod(setData)
            setData.__name__ = field.meth 
            setData.__doc__ = 'Set {0:s} of the atom.'.format(field.doc)  
            setattr(cls, 'set'+field.meth, setData)
        setattr(cls, 'getName', getattr(cls, 'getAtomName'))
        setattr(cls, 'setName', getattr(cls, 'setAtomName'))

class Atom(object):
    """A class for accessing and manipulating attributes of an atom 
    in a :class:`AtomGroup` instance."""
    
    __metaclass__ = AtomMeta
    
    __slots__ = ('_ag', '_index', '_acsi')
    
    def __init__(self, atomgroup, index, acsi=None):
        if not isinstance(atomgroup, prody.AtomGroup):
            raise TypeError('atomgroup must be AtomGroup, not {0:s}'
                            .format(type(atomgroup)))
        self._ag = atomgroup
        self._index = int(index)
        if acsi is None:
            self._acsi = atomgroup.getActiveCoordsetIndex()
        else: 
            self._acsi = int(acsi)
        
    def __repr__(self):
        return ('<Atom: {0:s} from {1:s} (index {2:d}; {3:d} '
                'coordinate sets, active set index: {4:d})>').format(
                self.getAtomName(), self._ag._name, self._index,  
                self._ag._n_coordsets, self._acsi)

    def __str__(self):
        return ('Atom {0:s} from {1:s} (index {2:d})').format(
                self.getAtomName(), self._ag.getName(), self._index)
        return ('{0:s} from {2:s} (index {1:d}; {3:d} '
                'coordinate sets, active set index: {4:d})').format(
                self.getAtomName(), self._index, self._ag._name, 
                self._ag._n_coordsets, self._acsi)

    def __len__(self):
        return 1
    
    def getAtomGroup(self):
        """Return associated atom group."""
        return self._ag
    
    def getIndex(self):
        """Return index of the atom."""
        return self._index
    
    def getNumOfCoordsets(self):
        """Return number of coordinate sets."""
        return self._ag._n_coordsets
    
    def getActiveCoordsetIndex(self):
        """Return the index of the active coordinate set for the atom."""
        return self._acsi
    
    def setActiveCoordsetIndex(self, index):
        """Set the index of the active coordinate set for the atom."""
        if self._ag._coordinates is None:
            raise AttributeError('coordinates are not set')
        if not isinstance(index, int):
            raise TypeError('index must be an integer')
        if self._ag._n_coordsets <= index or \
           self._ag._n_coordsets < abs(index):
            raise IndexError('coordinate set index is out of range')
        if index < 0:
            index += self._ag._n_coordsets
        self._acsi = index
    
    def getCoordinates(self):
        """Return a copy of coordinates of the atom from the active coordinate set."""
        return self._ag._coordinates[self._acsi, self._index].copy()
    
    def setCoordinates(self, coordinates):
        """Set coordinates of the atom in the active coordinate set."""
        self._ag._coordinates[self._acsi, self._index] = coordinates
        
    def getCoordsets(self, indices):
        """Return a copy of coordinate sets at given indices.
        
        *indices* may be an integer or a list of integers.
        
        """
        if self._ag._coordinates is None:
            raise AttributeError('coordinates are not set')
        try: 
            return self._ag._coordinates[indices, self._index].copy()
        except IndexError:
            raise IndexError('indices may be an integer or a list of integers')

    def iterCoordsets(self):
        """Iterate over coordinate sets."""
        for i in range(self._ag._n_coordsets):
            yield self._ag._coordinates[i, self._index].copy()

    def getSelectionString(self):
        """Return selection string that will select this atom."""
        return 'index {0:d}'.format(self._index)
    
class AtomSubsetMeta(type):
    
    def __init__(cls, name, bases, dict):
        def wrapGetMethod(fn):
            def wrapped(self):
                return fn(self)
            return wrapped
        def wrapSetMethod(fn):
            def wrapped(self, value):
                return fn(self, value)
            return wrapped

        for field in ATOMIC_DATA_FIELDS.values():
            def getData(self, var=field.var):
                array = self._ag.__dict__['_'+var]
                if array is None:
                    return None
                return array[self._indices] 
            getData = wrapGetMethod(getData)
            getData.__name__ = field.meth_pl
            getData.__doc__ = 'Return {0:s} of the atoms.'.format(field.doc_pl)
              
            setattr(cls, 'get'+field.meth_pl, getData)
            
            def setData(self, value, var=field.var):
                array = self._ag.__dict__['_'+var]
                if array is None:
                    raise AttributeError('attribute of the AtomGroup is not set')
                array[self._indices] = value
            setData = wrapSetMethod(setData)
            setData.__name__ = field.meth_pl 
            setData.__doc__ = 'Set {0:s} of the atoms.'.format(field.doc_pl)  
            setattr(cls, 'set'+field.meth_pl, setData)
        
class AtomSubset(object):
    """A class for manipulating subset of atomic data in an :class:`AtomGroup`.
    
    This class stores a reference to an :class:`AtomGroup` instance, a set of 
    atom indices, and active coordinate set index for the atom group.
    
    """
    __metaclass__ = AtomSubsetMeta    
    __slots__ = ['_ag', '_indices', '_acsi']
    
    def __init__(self, atomgroup, indices, acsi=None):
        """Instantiate atom group base class. 
        
        :arg atomgroup: an atom group
        :type atomgroup: :class:`AtomGroup`
        
        :arg indices: list of indices of atoms in the subset
        :type indices: list of integers
        
        :arg acsi: active coordinate set index
        :type acsi: integer
        
        """
        
        if not isinstance(atomgroup, prody.AtomGroup):
            raise TypeError('atomgroup must be AtomGroup, not {0:s}'
                            .format(type(atomgroup)))
        self._ag = atomgroup

        if not isinstance(indices, np.ndarray):
            indices = np.array(indices, np.int64)
        elif not indices.dtype == np.int64:
            indices = indices.astype(np.int64)
        else:
            indices = indices
        self._indices = np.unique(indices)

        if acsi is None:
            self._acsi = atomgroup.getActiveCoordsetIndex()
        else:
            self._acsi = int(acsi)

    
    def __iter__(self):
        """Iterate over atoms."""
        acsi = self._acsi
        ag = self._ag 
        for index in self._indices:
            yield Atom(ag, index, acsi)
    
    def __len__(self):
        return len(self._indices)
    
    def __invert__(self):
        
        arange = range(self._ag.getNumOfAtoms())
        indices = list(self._indices)
        while indices:
            arange.pop(indices.pop())
        sel = Selection(self._ag, arange, "not ({0:s}) ".format(
                                                self.getSelectionString()),
                        self._acsi)        
        return sel
    
    def __or__(self, other):
        if not isinstance(other, AtomSubset):
            raise TypeError('other must be an AtomSubset')
        if self._ag != other._ag:
            raise ValueError('both selections must be from the same AtomGroup')
        if self is other:
            return self
        acsi = self._acsi
        if acsi != other._acsi:
            LOGGER.warning('active coordinate set indices do not match, '
                           'so it will be set to zero in the union.')
            acsi = 0
        if isinstance(other, Atom):
            other_indices = np.array([other._index])
        else:
            other_indices = other._indices
        indices = np.unique(np.concatenate((self._indices, other_indices)))
        return Selection(self._ag, indices, 
                         '({0:s}) or ({1:s})'.format(self.getSelectionString(), 
                                                    other.getSelectionString()),
                          acsi)

    def __and__(self, other):
        if not isinstance(other, AtomSubset):
            raise TypeError('other must be an AtomSubset')
        if self._ag != other._ag:
            raise ValueError('both selections must be from the same AtomGroup')
        if self is other:
            return self
        acsi = self._acsi
        if acsi != other._acsi:
            LOGGER.warning('active coordinate set indices do not match, '
                           'so it will be set to zero in the union.')
            acsi = 0
        indices = set(self._indices)
        if isinstance(other, Atom):
            other_indices = set([other._index])
        else:
            other_indices = set(other._indices)
        indices = indices.intersection(other_indices)
        indices = np.unique(indices)
        return Selection(self._ag, indices, 
                         '({0:s}) and ({1:s})'.format(self.getSelectionString(), 
                                                    other.getSelectionString()),
                         acsi)    
    
    def getAtomGroup(self):
        """Return associated atom group."""
        return self._ag

    def getIndices(self):
        """Return the indices of atoms."""
        return self._indices.copy()
    
    def getNumOfAtoms(self):
        """Return number of atoms."""
        return self._indices.__len__()

    def getCoordinates(self):
        """Return coordinates from the active coordinate set."""
        if self._ag._coordinates is None:
            return None
        return self._ag._coordinates[self._acsi, self._indices].copy()
    
    def setCoordinates(self, coordinates):
        """Set coordinates in the active coordinate set."""
        self._ag._coordinates[self._acsi, self._indices] = coordinates
        
    def getCoordsets(self, indices):
        """Return coordinate sets at given *indices*.
        
        *indices* may be an integer or a list of integers.
        
        """
        if self._ag._coordinates is None:
            return None
        if indices is None:
            indices = slice(None)
        try: 
            return self._ag._coordinates[indices, self._indices].copy()
        except IndexError:
            raise IndexError('indices may be an integer or a list of integers')

    def getNumOfCoordsets(self):
        """Return number of coordinate sets."""
        return self._ag._n_coordsets
    
    def iterCoordsets(self):
        """Iterate over coordinate sets by returning a copy of each coordinate set."""
        for i in range(self._ag._n_coordsets):
            yield self._ag._coordinates[i, self._indices].copy()

    def getActiveCoordsetIndex(self):
        """Return the index of the active coordinate set."""
        return self._acsi
    
    def setActiveCoordsetIndex(self, index):
        """Set the index of the active coordinate set."""
        if self._ag._coordinates is None:
            return None
        if not isinstance(index, int):
            raise TypeError('index must be an integer')
        if self._ag._n_coordsets <= index or \
           self._ag._n_coordsets < abs(index):
            raise IndexError('coordinate set index is out of range')
        if index < 0:
            index += self._ag._n_coordsets
        self._acsi = index

    def select(self, selstr):
        """Return a selection matching the given selection criteria."""
        return SELECT.select(self, selstr)

class Chain(AtomSubset):
    
    __slots__ = AtomSubset.__slots__ + ['_seq', '_dict']
    
    def __init__(self, atomgroup, indices, acsi=None):
        AtomSubset.__init__(self, atomgroup, indices, acsi)
        self._seq = None
        self._dict = dict()
        
    def __repr__(self):
        return ('<Chain: {0:s} from {1:s} ({2:d} atoms; '
                '{3:d} coordinate sets, active set index: {4:d})>').format(
                self.getIdentifier(), self._ag.getName(), len(self), 
                self._ag.getNumOfCoordsets(), self._acsi)

    def __str__(self):
        return ('Chain {0:s} from {1:s}').format(self.getIdentifier(), self._ag.getName())
        return ('Chain {0:s} from {1:s} ({2:d} atoms; '
                '{3:d} coordinate sets, active set index: {4:d})').format(
                self.getIdentifier(), self._ag.getName(), len(self), 
                self._ag.getNumOfCoordsets(), self._acsi)

    def __getitem__(self, number):
        """Returns the residue with given number, if it exists. Assumes
        the insertion code is an empty string."""
        return self.getResidue(number)
    
    def getResidue(self, number, insertcode=''):
        """Return residue with given number."""
        return self._dict.get((number, insertcode), None)

    def iterResidues(self):
        """Iterate residues in the chain."""
        keys = self._dict.keys()
        keys.sort()
        for key in keys:
            yield self._dict[key]
    
    def getNumOfResidues(self):
        """Return number of residues."""
        return len(self._dict)

    def getIdentifier(self):
        """Return chain identifier."""
        return self._ag._chids[self._indices[0]]
    
    def setIdentifier(self, identifier):
        """Set chain identifier."""
        self.setChainIdentifiers(identifier)
    
    def getSequence(self):
        """Return sequence, if chain is a polypeptide."""
        if self._seq:
            return self._seq
        CAs = self.select('name CA').select('protein')
        if len(CAs) > 0:
            self._seq = prody.proteins.compare._getSequence(CAs.residue_names)
        else:
            self._seq = ''
        return self._seq

    def getSelectionString(self):
        """Return selection string that selects this atom group."""
        return 'chain {0:s}'.format(self.getIdentifier())


class Residue(AtomSubset):
    
    __slots__ = AtomSubset.__slots__ + ['_icode', '_chain']
    
    def __init__(self, atomgroup, indices, chain, acsi=None):
        AtomSubset.__init__(self, atomgroup, indices, acsi)
        self._chain = chain

    def __repr__(self):
        return '<Residue: {0:s}>'.format(str(self))
        
    def __str__(self):
        return ('{0:s} {1:d}{2:s} from Chain {3:s} from {4:s} '
                '({5:d} atoms; {6:d} coordinate sets, '
                'active set index: {7:d})').format(self.getName(), 
                self.getNumber(), self.getInsertionCode(), 
                self.getChain().getIdentifier(), self._ag.getName(), 
                len(self), self._ag.getNumOfCoordsets(), self._acsi)

    def __getitem__(self, name):
        return self.getAtom(name)
    
    def getAtom(self, name):
        """Return atom with given *name*, ``None`` if not found.
        
        Assumes that atom names in a residue are unique. If more than one atoms 
        with the given *name* exists, the one with the smaller index will be 
        returned.
        
        """
        nz = (self.getAtomNames() == name).nonzero()[0]
        if len(nz) > 0:
            return Atom(self._ag, self._indices[nz[0]], self._acsi)
    
    def getChain(self):
        """Return the chain that the residue belongs to."""
        return self._chain
    
    def getNumber(self):
        """Return residue number."""
        return self._ag._resnums[self._indices[0]]
    
    def setNumber(self, number):
        """Set residue number."""
        self.setResidueNumbers(number)
    
    def getName(self):
        """Return residue name."""
        return self._ag._resnames[self._indices[0]]
    
    def setName(self, name):
        """Set residue name."""
        self.setResidueNames(name)

    def getInsertionCode(self):
        """Return residue insertion code."""
        return self._ag._icodes[self._indices[0]]
        
    def setInsertionCode(self, icode):
        """Set residue insertion code."""
        self.setInsertionCodes(icode)
    
    def getChainIdentifier(self):
        return self._chain.getIdentifier()
    
    def getSelectionString(self):
        """Return selection string that will select this residue."""
        return 'chain {0:s} and resnum {1:d}{2:s}'.format(
                self.getChainIdentifier(), self.getNumber(), 
                self.getInsertionCode())

class Selection(AtomSubset):
    """A class for accessing and manipulating attributes of select of atoms 
    in an :class:`AtomGroup` instance."""
    
    __slots__ = AtomSubset.__slots__ + ['_selstr']
    
    def __init__(self, atomgroup, indices, selstr, acsi=None):
        AtomSubset.__init__(self, atomgroup, indices, acsi)
        self._selstr = str(selstr)
        
    def __repr__(self):
        selstr = self._selstr
        if len(selstr) > 33:
            selstr = selstr[:15] + '...' + selstr[-15:]  
        return ('<Selection: "{0:s}" from {1:s} ({2:d} atoms; '
                '{3:d} coordinate sets, active set index: {4:d})>').format(
                selstr, self._ag.getName(), len(self), 
                         self._ag._n_coordsets, self._acsi)
        return '<Selection: {0:s}>'.format(str(self))
                   
    def __str__(self):
        selstr = self._selstr
        if len(selstr) > 33:
            selstr = selstr[:15] + '...' + selstr[-15:]  
        return 'Selection "{0:s}" from {1:s}'.format(selstr, self._ag.getName())
        
    
    def getSelectionString(self):
        """Return selection string that selects this atom subset."""
        return self._selstr

    def getHierView(self):
        """Return a hierarchical view of the atom subset."""
        LOGGER.warning('HierView will be disabled for selections.')
        return prody.proteins.HierView(self)

class HierView(object):
    
    
    __slots__ = ['_atoms', '_chains']
    
    def __init__(self, atoms):
        """Instantiate a hierarchical view for atoms in an :class:`AtomGroup` 
        or :class:`Selection`."""
        self._atoms = atoms
        self._chains = dict()
        self.build()
        
    def build(self):
        """Build hierarchical view of the atom group.
        
        This method is called at instantiation, but can be used to rebuild
        the hierarchical view when attributes of atoms change.
        
        """
        
        acsi = self._atoms.getActiveCoordsetIndex()
        atoms = self._atoms
        if isinstance(atoms, AtomGroup):
            atomgroup = atoms
            _indices = np.arange(atomgroup._n_atoms)
            chainids = atomgroup.getChainIdentifiers() 
            if chainids is None:
                chainids = np.zeros(atomgroup._n_atoms, 
                                    dtype=ATOMIC_DATA_FIELDS['chain'].dtype)
                atomgroup.setChainIdentifiers(chainids)
        else:
            atomgroup = atoms._ag
            _indices = atoms._indices
            if atomgroup.getChainIdentifiers() is None:
                chainids = np.zeros(atomgroup._n_atoms, 
                                    dtype=ATOMIC_DATA_FIELDS['chain'].dtype)
                atomgroup.setChainIdentifiers(chainids)
            chainids = chainids[_indices]


        for chid in np.unique(chainids):
            ch = Chain(atomgroup, _indices[chainids == chid], acsi)
            self._chains[chid] = ch
        
        if atomgroup.getResidueNumbers() is None:
            atomgroup.setResidueNumbers(np.zeros(atomgroup._n_atoms, dtype=ATOMIC_DATA_FIELDS['resnum'].dtype))
        if atomgroup.getResidueNames() is None:
            atomgroup.setResidueNames(np.zeros(atomgroup._n_atoms, dtype=ATOMIC_DATA_FIELDS['resname'].dtype))
        if atomgroup.getInsertionCodes() is None:
            atomgroup.setInsertionCodes(np.zeros(atomgroup._n_atoms, dtype=ATOMIC_DATA_FIELDS['icode'].dtype))

        icodes = atomgroup.getInsertionCodes()
        

        for chain in self.iterChains():
            chid = chain.getIdentifier()
            rd = defaultdict(list)
            indices = chain.getIndices()
            resnums = chain.getResidueNumbers()
            for i in xrange(len(resnums)):
                rd[resnums[i]].append(indices[i])
            
            resnums = rd.keys()
            resnums.sort()
            for resnum in resnums:
                resindices = np.array(rd[resnum])
                res_icodes = icodes[resindices]
                
                for ic in np.unique(res_icodes): 
                    subindices = resindices[res_icodes == ic]
                    temp = subindices[0]
                    res = Residue(atomgroup, subindices, chain, acsi)   
                    chain._dict[(resnum, ic)] = res
        
    def __repr__(self):
        return '<HierView: {0:s}>'.format(str(self._atoms))
    
    def __str__(self):
        return 'HierView of {0:s}'.format(str(self._atoms))
    
    def __iter__(self):
        """Iterate over chains."""
        return self.iterChains()
    
    def iterResidues(self):
        """Iterate over residues."""
        chids = self._chains.keys()
        chids.sort()
        for chid in chids:
            chain = self._chains[chid]
            for res in chain.iterResidues():
                yield res

                
    def getResidue(self, chainid, resnum, icode=''):
        """Return residue with number *resnum* and insertion code *icode* from 
        the chain with identifier *chainid*, if it exists."""
        ch = self._chains.get(chainid, None)
        if ch is not None:
            return ch.getResidue(resnum, icode)
        return None

    def getNumOfResidues(self):
        """Returns number of residues."""
        return sum([ch.getNumOfResidues() for ch in self._chains.itervalues()])    

    def iterChains(self):
        """Iterate over chains."""
        chids = self._chains.keys()
        chids.sort()
        for chid in chids:
            yield self._chains[chid]
    
    def getChain(self, chainid):
        """Return chain with identifier *chainid*, if it exists."""
        return self._chains.get(chainid, None)

    def getNumOfChains(self):
        """Return number of chains."""
        return len(self._chains)
    
class AtomMapMeta(type):
    
    def __init__(cls, name, bases, dict):
        def wrapSetMethod(fn):
            def wrapped(self, value):
                return fn(self, value)
            return wrapped

        for field in ATOMIC_DATA_FIELDS.values():
            def getData(self, name=field.name, var=field.var):
                var = '_'+var
                array = self._ag.__dict__[var]
                if array is None:
                    return None
                result = np.zeros(self._len, ATOMIC_DATA_FIELDS[name].dtype)
                result[self._mapping] = self._ag.__dict__[var][self._indices]
                return result 
            getData = wrapGetMethod(getData)
            getData.__name__ = field.meth_pl
            getData.__doc__ = 'Return {0:s} of the atoms. Unmapped atoms will have 0 or empty entries.'.format(field.doc_pl)
              
            setattr(cls, 'get'+field.meth_pl, getData)


class AtomMap(object):
    """A class for mapping atomic data.
    
    This class stores a reference to an :class:`AtomGroup` instance, a set of 
    atom indices, active coordinate set index, mapping for indices, and
    indices of unmapped atoms.
    
    """
    
    __slots__ = ['_ag', '_indices', '_acsi', '_name', '_mapping', '_unmapped',
                 '_len']
    
    def __init__(self, atomgroup, indices, mapping, unmapped, name='Unnamed', acsi=None):
        """Instantiate with an AtomMap with following arguments:        
        
        :arg atomgroup: the atomgroup instance from which atoms are mapped
        :arg indices: indices of mapped atoms
        :arg mapping: mapping of the atoms as a list of indices
        :arg unmapped: list of indices for unmapped atoms
        :arg name: name of the AtomMap instance
        :arg acsi: active coordinate set index, if ``None`` defaults to that of *atomgrup*
        
        Length of *mapping* must be equal to length of *indices*. Number of 
        atoms (including unmapped dummy atoms) are determined from the 
        sum of lengths of *mapping* and *unmapped* arrays.         
        
        """
        if not isinstance(atomgroup, AtomGroup):
            raise TypeError('atomgroup must be AtomGroup, not {0:s}'
                            .format(type(atomgroup)))
            
        self._ag = atomgroup

        if not isinstance(indices, np.ndarray):
            self._indices = np.array(indices, np.int64)
        elif not indices.dtype == np.int64:
            self._indices = indices.astype(np.int64)
        else:
            self._indices = indices

        if not isinstance(mapping, np.ndarray):
            self._mapping = np.array(mapping, np.int64)
        elif not mapping.dtype == np.int64:
            self._mapping = mapping.astype(np.int64)
        else:
            self._mapping = mapping

        if not isinstance(unmapped, np.ndarray):
            self._unmapped = np.array(unmapped, np.int64)
        elif not unmapped.dtype == np.int64:
            self._unmapped = unmapped.astype(np.int64)
        else:
            self._unmapped = unmapped
        
        self._name = str(name)
        
        if acsi is None:
            self._acsi = atomgroup.getActiveCoordsetIndex()
        else:
            self._acsi = int(acsi)

        self._len = len(self._unmapped) + len(self._mapping)

        
    def __repr__(self):
        return ('<AtomMap: {0:s} (from {1:s}; {2:d} atoms; '
                '{3:d} mapped; {4:d} unmapped; {5:d} coordinate sets, '
                'active set index: {6:d})>').format(self._name,
                self._ag.getName(), self._len, len(self._mapping), 
                len(self._unmapped), self.getNumOfCoordsets(), self._acsi)
    
    def __str__(self):
        return 'AtomMap {0:s}'.format(self._name)
    
    def __iter__(self):
        indices = np.zeros(self._len, np.int64)
        indices[self._unmapped] = -1
        indices[self._mapping] = self._indices
        ag = self._ag
        acsi = self._acsi
        for index in indices:
            if index > -1:
                yield Atom(ag, index, acsi)
            else:
                yield None
    
    def __len__(self):
        return self._len
    
    def __add__(self, other):
        if not isinstance(other, AtomMap):
            raise TypeError('other must be an AtomMap instance')
        if self._ag != other._ag:
            raise ValueError('both AtomMaps must be from the same AtomGroup')
        acsi = self._acsi
        if acsi != other._acsi:
            LOGGER.warning('active coordinate set indices do not match, '
                           'so it will be set to zero')
            acsi = 0
        indices = np.concatenate((self._indices, other._indices))
        #if isinstance(other, AtomMap): 
        name = '({0:s}) + ({1:s})'.format(self._name, other._name)
        mapping = np.concatenate((self._mapping, other._mapping + self._len))
        unmapped = np.concatenate((self._unmapped, other._unmapped + self._len))
        #else:
        #    name = '({0:s}) + ({1:s})'.format(self._name, other.getSelectionString())
        #    mapping = np.concatenate((self._mapping, np.arange(len(other)) + self._len))
        #    unmapped = self._unmapped.copy()
            
        return AtomMap(self._ag, indices, mapping, unmapped, name, acsi)
    
    def getName(self):
        return self._name
    
    def setName(self, name):
        self._name = name


    def getAtomGroup(self):
        """Return the atom group from which the atoms are mapped."""
        return self._ag
    
    def getNumOfAtoms(self):
        """Return number of mapped atoms."""
        return self._len

    def getNumOfUnmapped(self):
        """Return number of unmapped atoms."""
        return len(self._unmapped)

    def getNumOfMapped(self):
        """Return number of mapped atoms."""
        return len(self._mapping)

    def getIndices(self):
        """Return indices of mapped atoms."""
        return self._indices.copy()

    def getMapping(self):
        """Return mapping of indices."""
        return self._mapping.copy()


    def iterCoordsets(self):
        """Iterate over coordinate sets by returning a copy of each coordinate set."""
        for i in range(self._ag._n_coordsets):
            coordinates = np.zeros((self._len, 3), np.float64)
            coordinates[self._mapping] = self._ag._coordinates[i, self._indices] 
            yield coordinates

    def getNumOfCoordsets(self):
        """Return number of coordinate sets."""
        return self._ag._n_coordsets
    
    def getActiveCoordsetIndex(self):
        """Return the index of the active coordinate set."""
        return self._acsi
    
    def setActiveCoordsetIndex(self, index):
        """Set the index of the active coordinate set."""
        if self._ag._coordinates is None:
            return
        if not isinstance(index, int):
            raise TypeError('index must be an integer')
        if self._ag._n_coordsets <= index or \
           self._ag._n_coordsets < abs(index):
            raise IndexError('coordinate set index is out of range')
        if index < 0:
            index += self._ag._n_coordsets
        self._acsi = index
    
    def getCoordinates(self):
        """Return coordinates from the active coordinate set."""
        coordinates = np.zeros((self._len, 3), np.float64)
        coordinates[self._mapping] = self._ag._coordinates[self._acsi, self._indices] 
        return coordinates
    
    def setCoordinates(self, coordinates):
        """Set coordinates in the active coordinate set."""
        self._ag._coordinates[self._acsi, self._indices] = coordinates
    
    def getCoordsets(self, indices):
        """Return coordinate sets at given indices.
        
        *indices* may be an integer or a list of integers.
        
        """
        if self._ag._coordinates is None:
            return None
        try: 
            return self._ag._coordinates[indices, self._indices].copy()
        except IndexError:
            raise IndexError('indices may be an integer or a list of integers')

    def getUnmappedFlags(self):
        """Return an array with 1s for unmapped atoms."""
        flags = np.zeros(self._len)
        if len(self._unmapped):
            flags[self._unmapped] = 1
        return flags
    
    def getMappedFlags(self):
        """Return an array with 1s for mapped atoms."""
        flags = np.ones(self._len)
        if len(self._unmapped):
            flags[self._unmapped] = 0
        return flags

    def select(self, selstr):
        """Return a atom map matching the criteria given by *selstr*.
        
        Note that this is a special case for making atom selections. Unmapped
        atoms will not be included in the returned :class:`AtomMap` instance.
        The order of atoms will be preserved.
        
        """
        return SELECT.select(self, selstr)