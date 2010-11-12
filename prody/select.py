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

"""
*******************************************************************************
:mod:`select` - Select atoms
*******************************************************************************

This module defines a class for selecting subsets of atoms based on a 
string, and functions to learn and change definitions of selection keywords.

Classes
=======

  * :class:`Select`
  
Functions
=========

Below functions can be used to learn the definitions of :ref:`selkeys`
and to change the behavior of the default atom selector object.

  * Learn keyword definitions:
    
    * :func:`getAromaticResidueNames`
    * :func:`getNucleicResidueNames`
    * :func:`getBackboneAtomNames`
    * :func:`getProteinResidueNames`
    * :func:`getHydrogenRegex`
    * :func:`getBasicResidueNames`
    * :func:`getAliphaticResidueNames`
    * :func:`getCyclicResidueNames`
    * :func:`getSmallResidueNames`
    * :func:`getWaterResidueNames`
    * :func:`getMediumResidueNames`
    * :func:`getAcidicResidueNames`
    
  * Change keyword definitions:
    
    * :func:`setAromaticResidueNames`
    * :func:`setNucleicResidueNames`
    * :func:`setBackboneAtomNames`
    * :func:`setProteinResidueNames`
    * :func:`setHydrogenRegex`
    * :func:`setBasicResidueNames`
    * :func:`setAliphaticResidueNames`
    * :func:`setCyclicResidueNames`
    * :func:`setSmallResidueNames`
    * :func:`setWaterResidueNames`
    * :func:`setMediumResidueNames`
    * :func:`setAcidicResidueNames`

"""

__author__ = 'Ahmet Bakan'
__copyright__ = 'Copyright (C) 2010  Ahmet Bakan'

import time

import numpy as np
from . import pyparsing as pp
pp.ParserElement.enablePackrat()

import prody
from prody import ProDyLogger as LOGGER
from prody.atomic import *
DEBUG = False

__all__ = ['Select',
           'getAromaticResidueNames', 'setAromaticResidueNames',
           'getNucleicResidueNames', 'setNucleicResidueNames',
           'getBackboneAtomNames', 'setBackboneAtomNames',
           'getProteinResidueNames', 'setProteinResidueNames',
           'getHydrogenRegex', 'setHydrogenRegex',
           'getBasicResidueNames', 'setBasicResidueNames',
           'getAliphaticResidueNames', 'setAliphaticResidueNames',
           'getCyclicResidueNames', 'setCyclicResidueNames',
           'getSmallResidueNames', 'setSmallResidueNames',
           'getWaterResidueNames', 'setWaterResidueNames',
           'getMediumResidueNames', 'setMediumResidueNames',
           'getAcidicResidueNames', 'setAcidicResidueNames',
           ]


""" TODO
- make classmethods from methods not related to instances
- evalonly in within and sameas 
"""

BACKBONE_ATOM_NAMES = ('CA', 'N', 'C', 'O') 
PROTEIN_RESIDUE_NAMES = ('ALA', 'ARG', 'ASN', 'ASP', 'CYS', 'GLN', 
        'GLU', 'GLY', 'HIS', 'ILE', 'LEU', 'LYS', 'MET', 'PHE', 'PRO', 
        'SER', 'THR', 'TRP', 'TYR', 'VAL', 'HSD', 'HSE', 'HSP')
WATER_RESIDUE_NAMES = ('HOH', 'WAT', 'TIP3', 'H2O')#, 'HH0', 'OHH', 'OH2', 'SOL', 'TIP', 'TIP2', 'TIP4')
NUCLEIC_RESIDUE_NAMES = ('GUA', 'ADE', 'CYT', 'THY', 'URA', 
                           'DA', 'DC', 'DG', 'DT')
HYDROGEN_REGEX = '[0-9]?H.*'
ACIDIC_RESIDUE_NAMES = ('ASP', 'GLU')
BASIC_RESIDUE_NAMES = ('LYS', 'ARG', 'HIS', 'HSP')
ALIPHATIC_RESIDUE_NAMES = ('ALA', 'GLY', 'ILE', 'LEU', 'VAL')
AROMATIC_RESIDUE_NAMES = ('HIS', 'PHE', 'TRP', 'TYR')
SMALL_RESIDUE_NAMES = ('ALA', 'GLY', 'SER')
MEDIUM_RESIDUE_NAMES = ('VAL', 'THR', 'ASP', 'ASN', 'PRO', 'CYS')
HYDROPHOBIC_RESIDUE_NAMES = ()
CYCLIC_RESIDUE_NAMES = ('HIS', 'PHE', 'PRO', 'TRP', 'TYR')

def getBackboneAtomNames():
    """Return protein :term:`backbone` atom names."""
    return list(BACKBONE_ATOM_NAMES)

def setBackboneAtomNames(backbone_atom_names):
    """Set protein :term:`backbone` atom names."""
    if not isinstance(backbone_atom_names, (list, tuple)):
        raise TypeError('backbone_atom_names must be a list or a tuple')
    BACKBONE_ATOM_NAMES = tuple(backbone_atom_names)

def getProteinResidueNames():
    """Return :term:`protein` residue names."""
    return list(PROTEIN_RESIDUE_NAMES)

def setProteinResidueNames(protein_residue_names):
    """Set :term:`protein` residue names."""
    if not isinstance(protein_residue_names, (list, tuple)):
        raise TypeError('protein_residue_names must be a list or a tuple')
    PROTEIN_RESIDUE_NAMES = tuple(protein_residue_names)

def getAcidicResidueNames():
    """Return :term:`acidic` residue names."""
    return list(ACIDIC_RESIDUE_NAMES)

def setAcidicResidueNames(acidic_residue_names):
    """Set :term:`acidic` residue names."""
    if not isinstance(acidic_residue_names, (list, tuple)):
        raise TypeError('acidic_residue_names must be a list or a tuple')
    ACIDIC_RESIDUE_NAMES = tuple(acidic_residue_names)
    
def getBasicResidueNames():
    """Return :term:`basic` residue names."""
    return list(BASIC_RESIDUE_NAMES)

def setBasicResidueNames(basic_residue_names):
    """Set :term:`basic` residue names."""
    if not isinstance(basic_residue_names, (list, tuple)):
        raise TypeError('basic_residue_names must be a list or a tuple')
    BASIC_RESIDUE_NAMES = tuple(basic_residue_names)

def getAliphaticResidueNames():
    """Return :term:`aliphatic` residue names."""
    return list(ALIPHATIC_RESIDUE_NAMES)

def setAliphaticResidueNames(aliphatic_residue_names):
    """Set :term:`aliphatic` residue names."""
    if not isinstance(aliphatic_residue_names, (list, tuple)):
        raise TypeError('aliphatic_residue_names must be a list or a tuple')
    ALIPHATIC_RESIDUE_NAMES = tuple(aliphatic_residue_names)

def getAromaticResidueNames():
    """Return :term:`aromatic` residue names."""
    return list(AROMATIC_RESIDUE_NAMES)

def setAromaticResidueNames(aromatic_residue_names):
    """Set :term:`aromatic` residue names."""
    if not isinstance(aromatic_residue_names, (list, tuple)):
        raise TypeError('aromatic_residue_names must be a list or a tuple')
    AROMATIC_RESIDUE_NAMES = tuple(aromatic_residue_names)

def getSmallResidueNames():
    """Return :term:`small` residue names."""
    return list(SMALL_RESIDUE_NAMES)

def setSmallResidueNames(small_residue_names):
    """Set :term:`small` residue names."""
    if not isinstance(small_residue_names, (list, tuple)):
        raise TypeError('small_residue_names must be a list or a tuple')
    SMALL_RESIDUE_NAMES = tuple(small_residue_names)

def getMediumResidueNames():
    """Return :term:`medium` residue names."""
    return list(MEDIUM_RESIDUE_NAMES)

def setMediumResidueNames(medium_residue_names):
    """Set :term:`medium` residue names."""
    if not isinstance(medium_residue_names, (list, tuple)):
        raise TypeError('medium_residue_names must be a list or a tuple')
    MEDIUM_RESIDUE_NAMES = tuple(medium_residue_names)

def getCyclicResidueNames():
    """Return :term:`cyclic` residue names."""
    return list(CYCLIC_RESIDUE_NAMES)

def setCyclicResidueNames(cyclic_residue_names):
    """Set :term:`cyclic` residue names."""
    if not isinstance(cyclic_residue_names, (list, tuple)):
        raise TypeError('cyclic_residue_names must be a list or a tuple')
    CYCLIC_RESIDUE_NAMES = tuple(cyclic_residue_names)

def getWaterResidueNames():
    """Return :term:`water` residue names."""
    return list(WATER_RESIDUE_NAMES)

def setWaterResidueNames(water_residue_names):
    """Set :term:`water` residue names."""
    if not isinstance(water_residue_names, (list, tuple)):
        raise TypeError('water_residue_names must be a list or a tuple')
    WATER_RESIDUE_NAMES = tuple(water_residue_names)

def getNucleicResidueNames():
    """Return :term:`nucleic` residue names."""
    return list(NUCLEIC_RESIDUE_NAMES)

def setNucleicResidueNames(nucleic_residue_names):
    """Set :term:`nucleic` residue names."""
    if not isinstance(water_residue_names, (list, tuple)):
        raise TypeError('nucleic_residue_names must be a list or a tuple')
    NUCLEIC_RESIDUE_NAMES = tuple(nucleic_residue_names)

def getHydrogenRegex():
    """Return regular expression to match :term:`hydrogen` atom names."""
    return list(HYDROGEN_REGEX)

def setHydrogenRegex(hydrogen_regex):
    """Set regular expression to match :term:`hydrogen` atom names."""
    if not isinstance(hydrogen_regex, (str)):
        raise TypeError('hydrogen_regex must be a string')
    HYDROGEN_REGEX = hydrogen_regex

class SelectionError(Exception):    
    pass
    
class Select(object):

    """Select subsets of atoms based on a selection string.
    
    Definitions of single word keywords, such as :term:`protein`, 
    :term:`backbone`, :term:`polar`, etc., may be altered using functions in 
    :mod:`select`. 

    """
    # Numbers and ranges
    PLUSORMINUS = pp.Literal('+') | pp.Literal('-')
    NUMBER = pp.Word(pp.nums) 
    INTEGER = pp.Combine( pp.Optional(PLUSORMINUS) + NUMBER )
    E = pp.CaselessLiteral('E')
    FLOAT = pp.Combine(INTEGER + 
                       pp.Optional(pp.Literal('.') + pp.Optional(NUMBER)) +
                       pp.Optional( E + INTEGER )
                       )
    
    NOT_READY = ('helix', 'alpha_helix', 'helix_3_10', 'pi_helix',
                'sheet', 'extended_beta', 'bridge_beta', 'turn', 'coil', 'purine', 'pyrimidine')
    KEYWORDS_BOOLEAN = ('all', 'none', 'protein', 'nucleic', 'hetero', 'water',
                        'backbone', 'sidechain', 'calpha', 'acidic', 'basic', 'polar', 'charged',
                        'neutral', 'aliphatic', 'hydrophobic', 'aromatic', 'cyclic', 'acyclic', 
                        'noh', 'hydrogen', 'large', 'medium', 'small')
    KEYWORDS_FLOAT = ('x', 'y', 'z', 'beta', 'mass', 'occupancy', 'mass', 'radius', 'charge')
    KEYWORDS_INTEGER = ('serial', 'index', 'resnum', 'resid')
    KEYWORDS_STRING = ('name', 'type', 'resname', 'chain', 'element', 'segment')
    KEYWORDS_NUMERIC = KEYWORDS_FLOAT + KEYWORDS_INTEGER    
    KEYWORDS_VALUE_PAIRED = KEYWORDS_NUMERIC + KEYWORDS_STRING 

    def isFloatKeyword(keyword):
        return keyword in Select.KEYWORDS_FLOAT
    isFloatKeyword = staticmethod(isFloatKeyword)

    def isNumericKeyword(keyword):
        return keyword in Select.KEYWORDS_NUMERIC
    isNumericKeyword = staticmethod(isNumericKeyword)

    def isAlnumKeyword(keyword):
        return keyword in Select.KEYWORDS_STRING
    isAlnumKeyword = staticmethod(isAlnumKeyword)

    def isValuePairedKeyword(keyword):
        return keyword in Select.KEYWORDS_VALUE_PAIRED
    isValuePairedKeyword = staticmethod(isValuePairedKeyword)

    def isBooleanKeyword(keyword):
        return keyword in Select.KEYWORDS_BOOLEAN
    isBooleanKeyword = staticmethod(isBooleanKeyword)
        
    def isKeyword(keyword):
        return (Select.isBooleanKeyword(keyword) or 
                Select.isValuePairedKeyword(keyword) or
                Select.isNumericKeyword(keyword))
    isKeyword = staticmethod(isKeyword)
    
    def __init__(self):
        self._ag = None
        self._atoms = None
        self._indices = None
        self._n_atoms = None
        self._selstr = None
        self._evalonly = None
        
        self._coordinates = None
        self._kdtree = None
        self._kwargs  = None
        for field in ATOMIC_DATA_FIELDS.values():
            self.__dict__['_'+field.var] = None        
        
        self._tokenizer = pp.operatorPrecedence(
             pp.OneOrMore(pp.Word(pp.alphanums+'.:_') | 
             pp.Group(pp.oneOf('" \'') + pp.Word(pp.alphanums+'~!@#$%^&*_+`=:;,.<>?|') + pp.oneOf('" \' "r \'r'))),
             [(pp.oneOf('+ -'), 1, pp.opAssoc.RIGHT, self._sign),
              (pp.oneOf('sqrt pow sq abs floor ceil sin cos tan atan asin acos sinh cosh tanh exp log log10'), 1, pp.opAssoc.RIGHT, self._func),
              (pp.oneOf('** ^'), 2, pp.opAssoc.LEFT, self._pow),
              (pp.oneOf('* / %'), 2, pp.opAssoc.LEFT, self._mul),
              (pp.oneOf('+ -'), 2, pp.opAssoc.LEFT, self._add),
              (pp.oneOf('< > <= >= == = !='), 2, pp.opAssoc.LEFT, self._comp),
              (pp.Regex('same [a-z]+ as') | pp.Regex('(ex)?within [0-9]+\.?[0-9]* of'), 1, pp.opAssoc.RIGHT, self._special),
              (pp.Keyword('!!!'), 1, pp.opAssoc.RIGHT, self._not),
              (pp.Keyword('&&&'), 2, pp.opAssoc.LEFT, self._and),
              (pp.Keyword('||'), 2, pp.opAssoc.LEFT, self._or),]
            )
        self._tokenizer.setParseAction(self._action)
        
    def _reset(self):
        self._ag = None
        self._atoms = None
        self._indices = None
        self._n_atoms = None
        self._selstr = None
        self._evalonly = None

        self._coordinates = None
        self._kdtree = None
        self._kwargs  = None
        for field in ATOMIC_DATA_FIELDS.values():
            self.__dict__['_'+field.var] = None        
                    
    def _getAtomicData(self, keyword):
        field = ATOMIC_DATA_FIELDS.get(keyword, None)
        if field is None:
            raise SelectionError('"{0:s}" is not a valid keyword.'.format(keyword))
        __dict__ = self.__dict__
        var = '_'+field.var
        data = __dict__[var]
        if data is None:
            data = self._ag.__dict__[var] 
            if data is None:
                raise SelectionError('{0:s} are not set.'.format(field.doc_pl))
            if self._indices is not None:
                data = data[self._indices]
            __dict__[var] = data 
        return data
    
    def _getCoordinates(self):
        if self._coordinates is None:
            if self._indices is None:
                self._coordinates = self._ag._coordinates[self._ag._acsi]
            else:
                self._coordinates = self._atoms.getCoordinates()
        return self._coordinates
   
    def _getKDTree(self):
        if prody.KDTree is None:
            prody.importBioKDTree()
        if self._kdtree is None:
            kdtree = prody.KDTree(3)
            kdtree.set_coords(self._getCoordinates())
            self._kdtree = kdtree
            return kdtree
        return self._kdtree

    def _evalBoolean(self, keyword):
        if DEBUG: print '_evalBoolean', keyword
        
        if self._evalonly is None:
            n_atoms = self._n_atoms
        else:        
            n_atoms = len(self._evalonly)
        
        if keyword == 'calpha':
            return self._and([['name', 'CA', '&&&', 'protein']])
        elif keyword == 'noh':
            return self._not([['!!!', 'name', (['"', HYDROGEN_REGEX,'"r'])]])
        elif keyword == 'all':
            return np.ones(n_atoms, np.bool)
        elif keyword == 'none':
            return np.zeros(n_atoms, np.bool)
        elif keyword == 'hydrogen':
            return self._evaluate(['name', (['"', HYDROGEN_REGEX,'"r'])])
            
        
        atom_names = None
        atom_names_not = False
        residue_names = None
        invert = False
        
        if keyword == 'protein':
            residue_names = PROTEIN_RESIDUE_NAMES
        elif keyword == 'backbone':
            atom_names = BACKBONE_ATOM_NAMES
            residue_names = PROTEIN_RESIDUE_NAMES
        elif keyword == 'acidic':
            residue_names = ACIDIC_RESIDUE_NAMES
        elif keyword == 'basic':
            residue_names = BASIC_RESIDUE_NAMES 
        elif keyword == 'charged':
            residue_names = ACIDIC_RESIDUE_NAMES + BASIC_RESIDUE_NAMES
        elif keyword == 'aliphatic':
            residue_names = ALIPHATIC_RESIDUE_NAMES
        elif keyword == 'aromatic':
            residue_names = AROMATIC_RESIDUE_NAMES
        elif keyword == 'small':
            residue_names = SMALL_RESIDUE_NAMES
        elif keyword == 'medium':
            residue_names = MEDIUM_RESIDUE_NAMES
        elif keyword == 'cyclic':
            residue_names = CYCLIC_RESIDUE_NAMES  
        elif keyword == 'large':
            residue_names = tuple(set(PROTEIN_RESIDUE_NAMES).difference( 
                    set(SMALL_RESIDUE_NAMES + MEDIUM_RESIDUE_NAMES)))
        elif keyword == 'neutral':
            residue_names = ACIDIC_RESIDUE_NAMES + BASIC_RESIDUE_NAMES
            invert = True
        elif keyword == 'acyclic':
            residue_names = CYCLIC_RESIDUE_NAMES
            invert = True
        elif keyword in ('water', 'waters'):
            residue_names = WATER_RESIDUE_NAMES
        elif keyword == 'nucleic':
            residue_names = NUCLEIC_RESIDUE_NAMES
        elif keyword == 'hetero':
            residue_names = NUCLEIC_RESIDUE_NAMES + PROTEIN_RESIDUE_NAMES
            invert = True
        elif keyword == 'sidechain':
            atom_names = BACKBONE_ATOM_NAMES
            residue_names = PROTEIN_RESIDUE_NAMES
            atom_names_not = True
        else:
            raise SelectionError('"{0:s}" is not a valid keyword.'.format(keyword))
            
        resnames = self._getAtomicData('resname')
        #print len(resnames), resnames
        if self._evalonly is not None:
            resnames = resnames[self._evalonly]
        #print len(resnames), resnames
        torf = np.zeros(n_atoms, np.bool)

        if atom_names is None:
            for i in xrange(n_atoms):
                torf[i] = (resnames[i] in residue_names)
        else:
            atomnames = self._getAtomicData('name')
            if self._evalonly is not None:
                atomnames = atomnames[self._evalonly]
            if atom_names_not:
                for i in xrange(n_atoms):
                    torf[i] = (not atomnames[i] in atom_names and
                               resnames[i] in residue_names)                
            else:
                for i in xrange(n_atoms):
                    torf[i] = (atomnames[i] in atom_names and
                               resnames[i] in residue_names)
            
        if invert:
            torf = np.invert(torf, torf)
        #print torf, torf.sum()
        return torf
    
    def _numrange(self, token):
        tknstr = ' '.join(token)
        while '  ' in tknstr:
            tknstr = tknstr.replace('  ', ' ')
        tknstr = tknstr.replace(' to ', 'to').replace('to ', 'to').replace(' to', 'to')
        tknstr = tknstr.replace(' : ', ':').replace(': ', ':').replace(' :', ':')
        token = []
        for item in tknstr.split():
            if 'to' in item:
                items = item.split('to')
                if len(items) != 2:
                    raise SelectionError('"{0:s}" is not understood.'.format(' to '.join(items)))
                try:
                    token.append( [float(items[0]), float(items[1])] )
                except:
                    raise SelectionError('"{0:s}" is not understood, "to" must be surrounded by numbers.'.format(' to '.join(items)))
            elif ':' in item:
                items = item.split(':')
                if not len(items) in (2, 3):
                    raise SelectionError('"{0:s}" is not understood.'.format(':'.join(items)))
                try:
                    if len(items) == 2:
                        token.append( (int(items[0]), int(items[1])) )
                    else:
                        token.append( (int(items[0]), int(items[1]), int(items[2])) )
                except:
                    raise SelectionError('"{0:s}" is not understood, ":" must be surrounded by integers.'.format(':'.join(items)))
            elif '.' in item:
                try:
                    token.append( float(item) )
                except:
                    raise SelectionError('"{0:s}" is not understood.'.format(item))
            elif item.isdigit():
                try:
                    token.append( int(item) )
                except:
                    raise SelectionError('"{0:s}" is not understood.'.format(item))
            else:
                token.append( item )
        if DEBUG: print '_numrange', token            
        return token
    
    def _resnum(self, token=None):
        if DEBUG: print '_resnum', token
        if token is None:
            return self._getAtomicData('resnum') 
        icodes = None
        if self._evalonly is None:
            resids = self._getAtomicData('resnum')
            n_atoms = self._n_atoms
        else:
            evalonly = self._evalonly
            resids = self._getAtomicData('resnum')[evalonly]
            n_atoms = len(evalonly)
        torf = np.zeros(n_atoms, np.bool)
        
        for item in self._numrange(token):
            if isinstance(item, str):
                if icodes is None:
                    if self._evalonly is None:
                        icodes = self._getAtomicData('icode')
                    else:
                        icodes = self._getAtomicData('icode')[evalonly]
                icode = str(item[-1])
                if icode == '_':
                    icode = ''
                torf[(resids == int(item[:-1])) * (icodes == icode)] = True
            elif isinstance(item, list):
                fr = item[0] 
                to = item[1]
                for i in xrange(n_atoms):
                    if fr <= resids[i] <= to:
                        torf[i] = True            
            elif isinstance(item, tuple):
                if len(item) == 2:
                    fr = item[0] 
                    to = item[1]
                    for i in xrange(n_atoms):
                        if fr <= resids[i] < to:
                            torf[i] = True
                else:
                    arange = range(item[0], item[1], item[2])
                    for i in xrange(n_atoms):
                            torf[i] = resids[i] in arange
            else:
                torf[resids == item] = True
        return torf
    
    def _index(self, token=None, add=0):
        if token is None:
            if self._indices is not None:
                return self._indices + add
            else:
                return np.arange(add, self._ag._n_atoms + add)
        torf = np.zeros(self._ag._n_atoms, np.bool)
        
        for item in self._numrange(token):
            if isinstance(item, str):
                raise SelectionError('"index/serial {0:s}" is not understood.'.format(item))
            elif isinstance(item, tuple):
                if len(item) == 2:
                    torf[item[0]-add:item[1]-add] = True
                else:
                    torf[item[0]-add:item[1]-add:item[2]-add] = True
            elif isinstance(item, list):
                torf[int(np.ceil(item[0]-add)):int(np.floor(item[1]-add))+1] = True
            else:
                try:
                    torf[int(item)-add] = True
                except IndexError:
                    pass

        if self._indices is not None:
            return torf[self._indices]
        return torf

    def _evalAlnum(self, keyword, values):
        data = self._getAtomicData(keyword)
        if keyword == 'chain':
            for i, value in enumerate(values):
                if value == '_':
                    values[i] = ' '
            
        if self._evalonly is not None:
            data = data[self._evalonly]
        n_atoms = len(data)
        torf = np.zeros(n_atoms, np.bool)
        
        for value in values:
            if not isinstance(value, str):
                if len(value[2]) == 1:
                    value = value[1]
                else:
                    if prody.re is None: prody.importRE()
                    value = prody.re.compile(value[1])
                    for i in xrange(n_atoms):
                        torf[i] = (value.match(data[i]) is not None)
                    continue
            torf[ data == value ] = True
        return torf
    
    def _evalFloat(self, keyword, values=None):
        if keyword == 'x':
            data = self._getCoordinates()[:,0]
        elif keyword == 'y':
            data = self._getCoordinates()[:,1]
        elif keyword == 'z':
            data = self._getCoordinates()[:,2]
        else:
            data = self._getAtomicData(keyword)
        
        if values is None:
            return data
    
        if self._evalonly is not None:
            data = data[self._evalonly]
        n_atoms = len(data)
        torf = np.zeros(n_atoms, np.bool)

        for item in self._numrange(values):
            if isinstance(item, str):
                pass
            elif isinstance(item, list):
                fr = item[0] 
                to = item[1]
                for i in xrange(n_atoms):
                    if fr <= data[i] <= to:
                        torf[i] = True            
            elif isinstance(item, tuple):
                if len(item) == 2:
                    fr = item[0] 
                    to = item[1]
                    for i in xrange(n_atoms):
                        if fr <= data[i] < to:
                            torf[i] = True
                else:
                    raise SelectionError('"{0:s}" is not valid for keywords expecting floating values.'.format(':'.join(item)))
            else:
                torf[data == item] = True
        return torf
    
    def select(self, atoms, selstr, **kwargs):
        """Return a Selection (or an AtomMap) of atoms matching *selstr*.
        
        If type of atoms is :class:`prody.atomic.AtomMap`, an 
        :class:`prody.atomic.AtomMap` instance is returned.
        
        .. versionchanged:: 0.2.0
            If selection string does not match any atoms, ``None`` is returned.
        
        """
        
        if not isinstance(atoms, (prody.AtomGroup, prody.AtomSubset, prody.AtomMap)):
            raise TypeError('atoms must be an atom container, not {0:s}'.format(type(atoms)))
        elif not isinstance(selstr, str):
            raise TypeError('selstr must be a string, not a {0:s}'.format(type(selstr)))
        self._reset()
        self._selstr = selstr
        if isinstance(atoms, prody.AtomGroup): 
            self._ag = atoms
            self._atoms = atoms
            self._indices = None
            self._n_atoms = atoms._n_atoms
        else:
            self._ag = atoms.getAtomGroup()
            self._indices = atoms.getIndices()
            if isinstance(atoms, prody.AtomMap):
                self._atoms = prody.Selection(self._ag, self._indices, '')
                self._atoms._indices = self._indices
            else: 
                self._atoms = atoms
            self._n_atoms = len(self._indices)
        self._kwargs = kwargs
        if DEBUG:
            print '_select', selstr
        torf = self._parseSelStr()[0]
        if not isinstance(torf, np.ndarray):
            raise SelectionError('{0:s} is not a valid selection string.'.format(selstr))
        elif torf.dtype != np.bool:
            if DEBUG:
                print '_select torf.dtype', torf.dtype, isinstance(torf.dtype, np.bool)
            raise SelectionError('{0:s} is not a valid selection string.'.format(selstr))
        if DEBUG:
            print '_select', torf
        if isinstance(atoms, prody.AtomGroup):
            indices = torf.nonzero()[0]
        else:
            indices = self._indices[torf]
        if len(indices) == 0:
            return None
        
        ag = self._ag
        self._reset()
        if isinstance(atoms, prody.AtomMap):
            return prody.AtomMap(ag, indices, np.arange(len(indices)), 
                                 np.array([]),
                                 'Selection "{0:s}" from AtomMap {1:s}'.format(
                                 selstr, atoms.getName()),
                                 atoms.getActiveCoordsetIndex())
        else:
            if isinstance(atoms, prody.AtomSubset):
                selstr = '({0:s}) and ({1:s})'.format(selstr, atoms.getSelectionString())
            return prody.Selection(ag, indices, selstr, 
                                   atoms.getActiveCoordsetIndex())

    def _getStdSelStr(self):
        selstr = self._selstr
        selstr = ' ' + selstr + ' '
        #selstr = selstr.replace('(', ' ( ').replace(')', ' ) ')
        while ' and ' in selstr:
            selstr = selstr.replace(' and ', ' &&& ')
        while ' or ' in selstr:
            selstr = selstr.replace(' or ', ' || ')
        while ' not ' in selstr:
            selstr = selstr.replace(' not ', ' !!! ')
        while '  ' in selstr:
            selstr = selstr.replace('  ', ' ')
        selstr = selstr.strip()
        return selstr

    def _parseSelStr(self):
        selstr = self._getStdSelStr()
        if DEBUG: print '_parseSelStr', selstr
        start = time.time()
        try: 
            tokens = self._tokenizer.parseString(selstr, parseAll=True).asList()
            if DEBUG: print '_parseSelStr', tokens
            return tokens
        except pp.ParseException, err:
            print 'Parse Failure'
            print self._selstr #err.line
            print " "*(err.column-1) + "^"
            raise pp.ParseException(str(err))

    def _special(self, token):
        token = token[0]
        if token[0].startswith('same'):
            return self._sameas(token)
        else:
            return self._within(token, token[0].startswith('exwithin'))
    
    def _within(self, token, exclude):
        terms = token
        if DEBUG: print '_within', terms
        within = float(terms[0].split()[1])
        which = terms[1]
        if not isinstance(which, np.ndarray):
            which = self._evaluate(terms[1:])
        result = []
        append = result.append
        kdtree = self._getKDTree()
        get_indices = kdtree.get_indices
        search = kdtree.search
        if isinstance(which, np.ndarray):
            coordinates = self._getCoordinates()
            which = which.nonzero()[0]
            for index in which:
                search(coordinates[index], within)
                append(get_indices())
        elif which in self._kwargs:
            kw = which
            which = self._kwargs[which]
            if isinstance(which, np.ndarray):
                if which.ndim == 1 and len(which) == 3:
                    which = [which]
                elif not (which.ndim == 2 and which.shape[1] == 3):
                    raise SelectionError('{0:s} must be a coordinate array, shape (N, 3) or (3,)'.format(kw))
                for xyz in which:
                    search(xyz, within)
                    append(get_indices())
            else:
                try:
                    coordinates = which.getCoordinates()
                except:
                    raise SelectionError('{0:s} must have a getCoordinates() method'.format(kw))
                if not isinstance(coordinates, np.ndarray):
                    raise SelectionError('{0:s}.getCoordinates() method must return a numpy.ndarray instance'.format(kw))
                for xyz in coordinates:
                    search(xyz, within)
                    append(get_indices())
        else:
            raise SelectionError('unknown error when using within keyword')
                
        unique = np.unique(np.concatenate(result))
        
        if self._indices is None:
            torf = np.zeros(self._n_atoms, np.bool)
            torf[unique] = True
        else:
            torf = np.zeros(self._ag._n_atoms, np.bool)
            torf[unique] = True
            torf = torf[self._indices]
        if exclude:
            torf[which] = False
        return torf

    def _sameas(self, token):
        terms = token
        if DEBUG: print '_sameas', terms
        what = token[0].split()[1]
        which = token[1]
        if not isinstance(which, np.ndarray):
            which = self._evaluate(token[1:])
        
        if what == 'residue':
            chainids = self._getAtomicData('chain')
            resids =  self._getAtomicData('resnum')
            resnum = list(np.unique(resids[which]).astype(np.str))
            torf = np.all(
                [self._evalAlnum('chain', list(np.unique(chainids[which]))),
                 self._resnum(resnum)], 0)
        elif what == 'chain':
            chainids = self._getAtomicData('chain')
            torf = self._evalAlnum('chain', list(np.unique(chainids[which])))        
        elif what == 'segment':
            segnames = self._getAtomicData('segment')
            torf = self._evalAlnum('segment', list(np.unique(segnames[which]))) 
        return torf

    def _not(self, token):
        if DEBUG: print '_not', token
        torf = self._evaluate(token[0][1:])
        np.invert(torf, torf)
        return torf
    
    def _and(self, tokens):
        if DEBUG: print '_and', tokens
        temp = tokens[0]
        tokenlist = []
        token = []
        while temp:
            tkn = temp.pop(0)
            if tkn == '&&&':
                tokenlist.append(token)
                token = []
            else:
                if Select.isBooleanKeyword(tkn) and not token and temp and temp[0] != '&&&':
                    if DEBUG: print '_and inserting &&&'
                    token.append(tkn)
                    tokenlist.append(token)
                    token = []
                else:
                    token.append(tkn)
        tokenlist.append(token)
        
        if DEBUG: print '_and tokenlist', tokenlist

        for token in tokenlist:
            zero = token[0]
            if isinstance(zero, np.ndarray):                    
                if self._evalonly is None: 
                    self._evalonly = zero.nonzero()[0]
                else:        
                    self._evalonly = self._evalonly[zero[self._evalonly].nonzero()[0]]
            else:
                torf = self._evaluate(token)
                if self._evalonly is None:
                    self._evalonly = torf.nonzero()[0]
                else:
                    self._evalonly = self._evalonly[torf]
            if DEBUG: print '_and', self._evalonly
        torf = np.zeros(self._n_atoms, np.bool)
        torf[self._evalonly] = True
        self._evalonly = None
        return torf
    
    def _or(self, tokens):
        if DEBUG: print '_or', tokens
        temp = tokens[0]
        tokenlist = []
        token = []
        while temp:
            tkn = temp.pop(0)
            if tkn == '||':
                tokenlist.append(token)
                token = []
            else:
                token.append(tkn)
        tokenlist.append(token)

        if DEBUG: print '_or tokenlist', tokenlist

        for token in tokenlist:
            zero = token[0]
            if isinstance(zero, np.ndarray):                    
                if self._evalonly is None: 
                    self._evalonly = np.invert(zero).nonzero()[0]
                else:        
                    self._evalonly = self._evalonly[np.invert(zero[self._evalonly]).nonzero()[0]]
            else:
                torf = self._evaluate(token)
                if self._evalonly is None:
                    self._evalonly = np.invert(torf).nonzero()[0]
                else:
                    self._evalonly = self._evalonly[np.invert(torf)]
            if DEBUG: print '_or', self._evalonly
        torf = np.ones(self._n_atoms, np.bool)
        torf[self._evalonly] = False
        self._evalonly = None
        return torf
        
    def _evaluate(self, token):
        if DEBUG: print '_evaluate', token
        keyword = token[0]
        if len(token) == 1:
            if Select.isBooleanKeyword(keyword):
                return self._evalBoolean(keyword)
            elif Select.isNumericKeyword(keyword):
                return self._getnum(keyword)
            elif self._kwargs is not None and keyword in self._kwargs:
                return keyword
            else:
                try:
                    return float(keyword)
                except ValueError:
                    raise SelectionError('"{0:s}" is not a valid keyword or a number.'.format(keyword))
        elif Select.isBooleanKeyword(keyword):
            return self._and([token])
        elif Select.isAlnumKeyword(keyword):
            return self._evalAlnum(keyword, token[1:])
        elif Select.isFloatKeyword(keyword):
            return self._evalFloat(keyword, token[1:])
        elif keyword in ('resnum', 'resid'):
            return self._resnum(token[1:])
        elif keyword == 'index':
            return self._index(token[1:])
        elif keyword == 'serial':
            return self._index(token[1:], 1)
        for item in token[1:]:
            if Select.isKeyword(item):
                raise SelectionError('"{0:s}" in "{1:s}" is not understood, use "" to escape'.format(item, ' '.join(token)))
        raise SelectionError('{0:s} is not yet implemented'.format(' '.join(token)))
    
    def _action(self, token):
        if DEBUG: print '_action', token
        if isinstance(token[0], np.ndarray):
            return token[0]
        else:
            return self._evaluate(token)

    def _comp(self, token):
        if DEBUG: print '_comp', token
        token = token[0]
        if len(token) > 3:
            if Select.isBooleanKeyword(token[0]):
                return self._and([[token[0], '&&&', self._comp([token[1:]])] ])
            elif Select.isBooleanKeyword(token[-1]):
                return self._and([[token[-1], '&&&', self._comp([token[:-1]])] ])
            else:
                raise SelectionError('{0:s} is not a valid selection string.'.format(' '.join(token)))
        comp = token[1]
        left = self._getnum(token[0])
        if DEBUG: print '_comp', left
        right = self._getnum(token[2])
        if DEBUG: print '_comp', right
        
        if comp == '>':
            return left > right
        elif comp == '<':
            return left < right
        elif comp == '<=':
            return left <= right
        elif comp == '>=':
            return left >= right
        elif comp == '==':
            return left == right
        elif comp == '=':
            return left == right
        elif comp == '!=':
            return left != right
        else:
            raise SelectionError('Unknown error in "{0:s}".'.format(' '.join(token)))

    def _pow(self, token):
        if DEBUG: print '_pow', token
        items = token[0]
        return self._getnum(items[0]) ** self._getnum(items[2])

    def _add(self, token):
        if DEBUG: print '_add', token
        items = token[0]
        left = self._getnum(items[0])
        op = items[1]
        right = self._getnum(items[2])
        if op == '+':
            return left + right
        else:
            return left - right
 
    def _mul(self, token):
        if DEBUG: print '_mul', token
        items = token[0]
        left = self._getnum(items[0])
        op = items[1]
        right = self._getnum(items[2])
        if op == '*':
            return left * right
        elif op == '/':
            if right == 0.0:
                raise ZeroDivisionError(' '.join(items))
            return left / right
        else:
            return left % right

    def _getnum(self, token):
        if DEBUG: print '_getnum', token
        if isinstance(token, np.ndarray):
            return token
        elif Select.isFloatKeyword(token):
            return self._evalFloat(token)
        elif token in ('resnum', 'resid'):
            return self._resnum()
        elif token == 'index':
            return self._index()    
        elif token == 'serial':
            return self._index(None, 1)
        else:
            try:
                num = float(token)
            except ValueError:
                raise SelectionError('"{0:s}" must be a number or a valid keyword'.format(token))
            else:
                return num

    def _sign(self, token):
        token = token[0]
        if DEBUG: print '_sign', token
        num = self._getnum(token[1])
        if token[0] == '-':
            return -num
        return num

    def _func(self, token):
        token = token[0]
        if DEBUG: print '_func', token
        fun = token[0]
        num = token[1] 
        if fun == 'sqrt':
            return np.sqrt(num)
        elif fun == 'sq':
            return np.power(num, 2)
        elif fun == 'abs':
            return np.abs(num)
        elif fun == 'floor':
            return np.floor(num)
        elif fun == 'ceil':
            return np.ceil(num)
        elif fun == 'sin':
            return np.sin(num)
        elif fun == 'cos':
            return np.cos(num)
        elif fun == 'tan':
            return np.tan(num)
        elif fun == 'atan':
            return np.arctan(num)
        elif fun == 'asin':
            return np.arcsin(num)
        elif fun == 'acos':
            return np.arccos(num)
        elif fun == 'sinh':
            return np.sinh(num)
        elif fun == 'cosh':
            return np.cosh(num)
        elif fun == 'tanh':
            return np.tanh(num)
        elif fun == 'exp':
            return np.exp(num)
        elif fun == 'log':
            return np.log(num)
        elif fun == 'log10':
            return np.log10(num)