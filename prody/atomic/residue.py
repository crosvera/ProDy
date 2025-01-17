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

"""This module defines classes for handling residues."""

__author__ = 'Ahmet Bakan'
__copyright__ = 'Copyright (C) 2010-2012 Ahmet Bakan'

from subset import AtomSubset
from atom import Atom

__all__ = ['Residue']

class Residue(AtomSubset):
    
    """Instances are generated by :class:`HierView` class.
    
    Indexing a :class:`Residue` by atom name returns :class:`Atom` instances.
    
    >>> from prody import *
    >>> pdb = parsePDB('1p38')
    >>> hv = pdb.getHierView()
    >>> chA = hv['A']
    >>> res = chA[4]
    >>> res['CA']
    <Atom: CA from 1p38 (index 1)>
    >>> res['CB']
    <Atom: CB from 1p38 (index 4)>
    >>> print res['H'] # X-ray structure 1p38 does not contain H atoms
    None"""
     
    __slots__ = ['_ag', '_indices', '_acsi', '_selstr', '_chain']        
        
    def __init__(self, ag, indices, acsi=None, **kwargs):
        
        AtomSubset.__init__(self, ag, indices, acsi, **kwargs)
        self._chain = kwargs.get('chain')

    def __repr__(self):

        n_csets = self._ag.numCoordsets()
        chain = self._chain
        if chain is None:
            chain = ''
        else:
            chain = ' from Chain {0:s}'.format(self.getChid())
        
        if n_csets == 1:
            return ('<Residue: {0:s} {1:d}{2:s}{3:s} from {4:s} ({5:d} atoms)>'
                    ).format(self.getResname(), self.getResnum(), 
                     self.getIcode() or '', chain, self._ag.getTitle(), 
                     len(self))
        elif n_csets > 1:
            return ('<Residue: {0:s} {1:d}{2:s}{3:s} from {4:s} '
                    '({5:d} atoms; active #{6:d} of {7:d} coordsets)>').format(
                    self.getResname(), self.getResnum(), self.getIcode() or '', 
                    chain, self._ag.getTitle(), len(self), self.getACSIndex(), 
                    n_csets)
        else:                        
            return ('<Residue: {0:s} {1:d}{2:s}{3:s} from {4:s} ({5:d} atoms; '
                    'no coordinates)>').format(self.getResname(), 
                    self.getResnum(), self.getIcode() or '', chain, 
                    self._ag.getTitle(), len(self))

    def __str__(self):
        
        return '{0:s} {1:d}{2:s}'.format(self.getResname(), self.getResnum(), 
                                         self.getIcode() or '')

    def getAtom(self, name):
        """Return atom with given *name*, ``None`` if not found.  Assumes that 
        atom names in the residue are unique.  If more than one atoms with the 
        given *name* exists, the one with the smaller index will be returned.
        """
        
        acsi = self.getACSIndex()
        if isinstance(name, str):
            nz = (self.getNames() == name).nonzero()[0]
            if len(nz) > 0:
                return Atom(self._ag, self._indices[nz[0]], acsi)
    
    __getitem__ = getAtom

    def getChain(self):
        """Return the chain that the residue belongs to."""
        
        return self._chain
    
    def getResnum(self):
        """Return residue number."""
        
        return int(self._ag._data['resnums'][self._indices[0]])
    
    def setResnum(self, number):
        """Set residue number."""
        
        self.setResnums(number)
    
    def getResname(self):
        """Return residue name."""
        
        data = self._ag._data['resnames']
        if data is not None:
            return data[self._indices[0]]
    
    def setResname(self, name):
        """Set residue name."""
        
        self.setResnames(name)

    def getIcode(self):
        """Return residue insertion code."""
        
        data = self._ag._data['icodes']
        if data is not None:
            return data[self._indices[0]]
        
    def setIcode(self, icode):
        """Set residue insertion code."""
        
        self.setIcodes(icode)
    
    def getChid(self):
        """Return chain identifier."""
        
        if self._chain:
            return self._chain.getChid()
    
    def getSelstr(self):
        """Return selection string that will select this residue."""
        
        icode = self.getIcode() or ''
        if self._chain is None:        
            if self._selstr:
                return 'resnum {0:s}{1:s} and ({1:s})'.format(
                            self.getResnum(), icode, self._selstr)
            else:
                return 'resnum {0:s}{1:s}'.format(self.getResnum(), icode)
        else:
            selstr = self._chain.getSelstr()
            return 'resnum {0:d}{1:s} and ({2:s})'.format(
                                self.getResnum(), icode, selstr)

    def getPrev(self):
        """Return preceding residue in the chain."""
        
        i = self._chain._dict.get((self.getResnum(), self.getIcode() or None))
        if i is not None and i > 0:
            return self._chain._list[i-1]
        
    def getNext(self):
        """Return following residue in the chain."""

        i = self._chain._dict.get((self.getResnum(), self.getIcode() or None))
        if i is not None and i + 1 < len(self._chain):
            return self._chain._list[i+1]
