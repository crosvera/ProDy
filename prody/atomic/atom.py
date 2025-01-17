# -*- coding: utf-8 -*-
# ProDy: A Python Package for Protein Dynamics Analysis
# 
# Copyright (C) 2010-2012 Ahmet Bakan
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

"""This module defines classes to handle individual atoms."""

__author__ = 'Ahmet Bakan'
__copyright__ = 'Copyright (C) 2010-2012 Ahmet Bakan'

import numpy as np

from fields import ATOMIC_DATA_FIELDS
from fields import wrapGetMethod, wrapSetMethod
from pointer import AtomPointer
from bond import Bond

__all__ = ['Atom', 'Atom']

class AtomMeta(type):

    def __init__(cls, name, bases, dict):
        
        for field in ATOMIC_DATA_FIELDS.values():
            
            meth = field.meth
            getMeth = 'get' + meth
            setMeth = 'set' + meth
            # Define public method for retrieving a copy of data array
            if field.call:
                def getData(self, var=field.var, call=field.call):
                    for meth in call:
                        getattr(self._ag, meth)()
                    array = self._ag._data[var]
                    return array[self._index] 
            else:
                def getData(self, var=field.var):
                    array = self._ag._data[var]
                    if array is None:
                        return None
                    return array[self._index] 
            getData = wrapGetMethod(getData)
            getData.__name__ = getMeth
            getData.__doc__ = field.getDocstr('set', False)
            setattr(cls, getMeth, getData)
            setattr(cls, '_' + getMeth, getData)
            
            if field.readonly:
                continue
            
            # Define public method for setting values in data array
            def setData(self, value, var=field.var, none=field.none):
                array = self._ag._data[var]
                if array is None:
                    raise AttributeError('attribute of the AtomGroup is '
                                         'not set')
                array[self._index] = value
                if None:
                    self._ag.__setattr__('_' + none,  None)
            setData = wrapSetMethod(setData)
            setData.__name__ = setMeth 
            setData.__doc__ = field.getDocstr('set', False)
            setattr(cls, setMeth, setData)
                            

class Atom(AtomPointer):
    
    """A class for handling individual atoms in an atom group."""
    
    __metaclass__ = AtomMeta
    
    __slots__ = ['_ag', '_acsi', '_index']
    
    def __init__(self, ag, index, acsi):
        AtomPointer.__init__(self, ag, acsi)
        self._index = int(index)
        
    def __repr__(self):

        n_csets = self._ag.numCoordsets()
        if n_csets == 1:
            return '<Atom: {0:s} from {1:s} (index {2:d})>'.format(
                   self.getName(), self._ag.getTitle(), self._index)
        elif n_csets > 1:
            return ('<Atom: {0:s} from {1:s} (index {2:d}; active #{3:d} of '
                    '{4:d} coordsets)>').format(self.getName(), 
                     self._ag.getTitle(), self._index, self.getACSIndex(), 
                     n_csets)
        else:
            return ('<Atom: {0:s} from {1:s} (index {2:d}; no coordinates)>'
                    ).format(self.getName(), self._ag.getTitle(), self._index)

    def __str__(self):

        return 'Atom {0:s} (index {1:d})'.format(self.getName(), self._index)

    def __len__(self):
    
        return 1
    
    def numAtoms(self):
        """Return number of atoms."""
        
        return 1
    
    def getIndex(self):
        """Return index of the atom."""
        
        return self._index
    
    def getIndices(self):
        """Return index of the atom in an :class:`numpy.ndarray`."""
        
        return np.array([self._index])
    
    _getIndices = getIndices
    
    def iterAtoms(self):
        """Yield atoms."""

        yield Atom(ag=self._ag, index=self._index, acsi=self.getACSIndex())

    __iter__ = iterAtoms
    
    def getCoords(self):
        """Return a copy of coordinates of the atom from the active coordinate 
        set."""
        
        if self._ag._coords is not None:
            return self._ag._coords[self.getACSIndex(), self._index].copy()
    
    def _getCoords(self):
        """Return a view of coordinates of the atom from the active coordinate 
        set."""
        
        if self._ag._coords is not None:
            return self._ag._coords[self.getACSIndex(), self._index]
    
    def setCoords(self, coords):
        """Set coordinates of the atom in the active coordinate set."""
        
        acsi = self.getACSIndex()
        self._ag._coords[acsi, self._index] = coords
        self._ag._setTimeStamp(acsi)
        
    def getCoordsets(self, indices=None):
        """Return a copy of coordinate set(s) at given *indices*."""
        
        if self._ag._coords is None:
            return None
        
        if indices is None:
            return self._ag._coords[:, self._index].copy()
        
        if isinstance(indices, (int, slice)):
            return self._ag._coords[indices, self._index].copy()
        
        if isinstance(indices, (list, np.ndarray)):
            return self._ag._coords[indices, self._index]
        
        raise IndexError('indices must be an integer, a list/array of '
                         'integers, a slice, or None')
       
    def _getCoordsets(self, indices=None): 
        """Return a view of coordinate set(s) at given *indices*."""
        
        if self._ag._coords is None:
            return None
    
        if indices is None:
            return self._ag._coords[:, self._index]
    
        if isinstance(indices, (int, slice)):
            return self._ag._coords[indices, self._index]
    
        if isinstance(indices, (list, np.ndarray)):
            return self._ag._coords[indices, self._index]
    
        raise IndexError('indices must be an integer, a list/array of '
                         'integers, a slice, or None')

    def iterCoordsets(self):
        """Yield copies of coordinate sets."""
        
        for i in range(self._ag._n_csets):
            yield self._ag._coords[i, self._index].copy()


    def _iterCoordsets(self):
        """Yield views of coordinate sets."""
        
        for i in range(self._ag._n_csets):
            yield self._ag._coords[i, self._index]
    
    def getData(self, label):
        """Return data *label*, if it exists."""
        
        if self._ag.isData(label):
            return self._ag._data[label][self._index]
    
    _getData = getData
    
    def setData(self, label, data):
        """Update *data* with *label* for the atom."""
        
        if self._ag.isData(label):
            if label in READONLY:
                raise AttributeError("{0:s} is read-only".format(label))
            self._ag._data[label][self._index] = data 
        else:
            raise AttributeError("AtomGroup '{0:s}' has no data associated "
                      "with label '{1:s}'".format(self._ag.getTitle(), label))
    
    def getSelstr(self):
        """Return selection string that will select this atom."""
        
        return 'index {0:d}'.format(self._index)

    def numBonds(self):
        """Return number of bonds formed by this atom.  Bonds must be set first
        using :meth:`~atomgroup.AtomGroup.setBonds`."""
        
        numbonds = self._ag._data.get('numbonds')
        if numbonds is not None:
            return numbonds[self._index]
    
    def iterBonds(self):
        """Yield bonds formed by the atom.  Bonds must be set first."""
        
        ag = self._ag
        if ag._bmap is not None:
            acsi = self.getACSIndex()
            this = self._index
            for other in self._ag._bmap[this]:
                if other == -1:
                    break
                yield Bond(ag, [this, other], acsi) 
                    
    def iterBonded(self):
        """Yield bonded atoms.  Bonds must be set first."""
        
        ag = self._ag
        if ag._bmap is not None:
            acsi = self.getACSIndex()
            this = self._index
            for other in self._ag._bmap[this]:
                if other == -1:
                    break
                yield Atom(ag, other, acsi) 
