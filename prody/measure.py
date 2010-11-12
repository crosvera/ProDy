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
:mod:`measure` - Measure quantities 
*******************************************************************************

This module defines class and methods and for calculating comparing coordinate 
data and measuring quantities.

Classes
=======
  
  * :class:`Transformation`
    
Functions
=========
    
  * :func:`applyTransformation`
  * :func:`getDeformVector`
  * :func:`getDistance`
  * :func:`getRadiusOfGyration`
  * :func:`getRMSD`
  * :func:`getTransformation`
  * :func:`superimpose` 

"""

__author__ = 'Ahmet Bakan'
__copyright__ = 'Copyright (C) 2010  Ahmet Bakan'

import prody as pd
import numpy as np

__all__ = ['Transformation', 'applyTransformation', 'getDeformVector',
           'getDistance', 'getRadiusOfGyration', 'getRMSD', 'getTransformation',
           'superimpose']
           
class Transformation(object):
    
    __slots__ = ['_rotation', '_translation']
    
    def __init__(self, rotation, translation):
        self._rotation = rotation
        self._translation = translation
    
    #def __repr__(self):
    #    if self._name is not None: 
    #        return '<Transformation: {0:s}>'.format(self._name)
    #    else:
    #        return object.__repr__(self)

    #def __str__(self):
    #    if self._name is not None: 
    #        return 'Transformation {0:s}'.format(self._name)
    #    else:    
    #        return ''

    #def getName(self): 
    #    """Return name of the translation"""
    #    return self._name
    #def setName(self, name):
    #    """Set name of the translation"""
    #    self._name = name
    
    def getRotation(self): 
        """Returns rotation matrix."""
        return self._rotation.copy()

    def setRotation(self, rotation):
        """Set rotation matrix."""
        if not isinstance(rotation, np.ndarray):
            raise TypeError('rotation must be an ndarray')
        elif rotation.shape != (3,3):
            raise TypeError('rotation must be a 3x3 array')
        self._rotation = rotation

    def getTranslation(self): 
        """Returns translation vector."""
        return self._translation.copy()
    
    def setTranslation(self): 
        """Set translation vector."""
        if not isinstance(translation, np.ndarray):
            raise TypeError('translation must be an ndarray')
        elif translation.shape != (3,):
            raise TypeError('translation must be an ndarray of length 3')
        self._translation = translation
    
    def ge4x4Matrix(self):
        """Returns 4x4 transformation matrix whose top left is rotation matrix
        and last column is translation vector."""
        
        fourby4 = np.eye(4)
        fourby4[:3, :3] = self._rotation
        fourby4[:3, 3] = self._translation
        return fourby4
    
    def apply(self, atoms):
        """Applies transformation to given atoms or coordinate set.
        
        :class:`AtomGroup`, :class:`Chain`, :class:`Residue`, :class:`Atom`, 
        and :class:`Selection` instances are accepted.
        If an instance of one of these is provided, it is returned after
        its active coordinate set is transformed.
        
        If a NumPy array is provided, transformed array is returned.
        
        """
        return applyTransformation(self, atoms)
    

def getTransformation(mobile, target, weights=None):
    """Returns a :class:`Transformation` instance which, when applied to the 
    atoms in *mobile*, minimizes the weighted RMSD between *mobile* and 
    *target*.
    
    *mobile* and *target* may be NumPy coordinate arrays, or istances of 
    Molecule, AtomGroup, Chain, or Residue.
    
    """
    name = ''
    if not isinstance(mobile, np.ndarray): 
        try:
            mob = mobile.getCoordinates()
        except AttributeError:
            raise TypeError('mobile is not a coordinate array '
                            'and do not contain a coordinate set')
    else:
        mob = mobile
    if not isinstance(target, np.ndarray): 
        try:
            tar = target.getCoordinates()
        except AttributeError:
            raise TypeError('target is not a coordinate array '
                            'and do not contain a coordinate set')
    else:
        tar = target
    
    if mob.shape != tar.shape:
        raise ValueError('reference and target coordinate arrays must have same shape')
    

    if mob.shape[1] != 3:
        raise ValueError('reference and target must be 3-d coordinate arrays')
        
    t = _getTransformation(mob, tar, weights)
    return t

def _getTransformation(mob, tar, weights=None):
    if pd.la is None: pd.importScipyLinalg()
    n_atoms = mob.shape[0]
    
    if weights is None:
        weights = 1
        weights_sum = n_atoms
        weights_dot = 1
    else:
        if not isinstance(weights, np.ndarray): 
            raise TypeError('weights must be an ndarray instance')
        elif weights.shape[0] != n_atoms:
            raise ValueError('lenth of weights array and coordinate arrays must be the same')
        
        weights_sum = weights.sum()
        weights_dot = np.dot(weights.T, weights)
    
    mob_com = (mob * weights).sum(axis=0) / weights_sum
    tar_com = (tar * weights).sum(axis=0) / weights_sum
    mob = mob - mob_com
    tar = tar - tar_com
    

    matrix = np.dot((tar * weights).T, (mob * weights)) / weights_dot
    U, s, Vh = pd.la.svd(matrix)
    
    U, s, Vh = pd.la.svd(matrix)
    Id = np.array([ [1, 0, 0], 
                    [0, 1, 0], 
                    [0, 0, np.sign(pd.la.det(matrix))] ])
    rotation = np.dot(Vh.T, np.dot(Id, U.T))
    
    # optalign
    # http://www.pymolwiki.org/index.php/Kabsch
    #E0 = np.sum( np.sum(ref_centered * ref_centered,axis=0),axis=0) + np.sum( np.sum(tar_centered * tar_centered,axis=0),axis=0)
    #reflect = float(str(float(pd.la.det(U) * pd.la.det(Vh))))
    #if reflect == -1.0:
    #    s[-1] = -s[-1]
    #    U[:,-1] = -U[:,-1]
    #RMSD = E0 - (2.0 * sum(s))
    #RMSD = np.sqrt(abs(RMSD / n_atoms))
    #print RMSD
    #transformation._rotation = np.dot(U, Vh)
    t = Transformation(rotation, tar_com - np.dot(mob_com, rotation))
    return t

def applyTransformation(transformation, coordinates):
    """Applies a transformation to a given coordinate set."""
    if not isinstance(coordinates, np.ndarray): 
        molecule = coordinates
        try:
            coordinates = molecule.getCoordinates()
        except AttributeError:
            raise TypeError('coordinates is not an array of coordinates '
                            'and do not contain a coordinate set')
    else:
        molecule = None
    
    if coordinates.shape[1] != 3:
        raise ValueError('coordinates must be a 3-d coordinate array')
    
    transformed = transformation._translation + np.dot(coordinates, 
                                                       transformation._rotation)
                                      
                                    
    if molecule is not None:
        molecule.setCoordinates(transformed) 
        return molecule
    else:
        return transformed

def getDeformVector(atoms_from, atoms_to):
    """Returns deformation :class:`prody.dynamics.Vector` from *atoms_from* 
    to *atoms_to*."""
    
    name = '"{0:s}" => "{1:s}"'.format(str(atoms_from), str(atoms_to))
    if len(name) > 30: 
        name = 'Deformation'
    array = (atoms_to.getCoordinates() - atoms_from.getCoordinates()).flatten()
    return pd.Vector(name,array)

def getRMSD(reference, target, weights=None):
    """Returns Root-Mean-Square-Deviations between reference and target coordinates."""
    if not isinstance(reference, np.ndarray): 
        try:
            ref = reference.getCoordinates()
        except AttributeError:
            raise TypeError('reference is not an array of coordinates '
                            'and do not contain a coordinate set')
    else:
        ref = reference
    if not isinstance(target, np.ndarray): 
        try:
            tar = target.getCoordinates()
        except AttributeError:
            raise TypeError('target is not an array of coordinates '
                            'and do not contain a coordinate set')
    else:
        tar = target
    
    if ref.shape != tar.shape:
        raise ValueError('reference and target coordinate arrays must have same shape')
    return _getRMSD(ref, tar, weights)
    
def _getRMSD(ref, tar, weights=None):
    n_atoms = ref.shape[0]
    if weights is None:
        weights = 1
        weights_sum = n_atoms
    else:
        if not isinstance(weights, np.ndarray): 
            raise TypeError('weights must be an ndarray instance')
        elif weights.shape[0] != n_atoms:
            raise ValueError('lenth of weights array and coordinate arrays must be the same')
        weights_sum = weights.sum()
    
    return np.sqrt(((ref-tar) ** 2).sum() / weights_sum)
    
def superimpose(mobile, target, weights=None):
    """Superimpose *mobile* onto *target* to minimize the RMSD distance."""
    t = getTransformation(mobile, target, weights)
    result = applyTransformation(t, mobile)
    return (result, t) 

def getDistance(one, two):
    """Return the Euclidean distance between *one* and *two*.
    
    Arguments may be :class:`Atom` instances or NumPy arrays. Shape 
    of numpy arrays must be ([M,]N,3), where M is number of coordinate sets
    and N is the number of atoms.
    
    """
    if not isinstance(one, np.ndarray):
        one = one.getCoordinates()
    if not isinstance(two, np.ndarray):
        two = two.getCoordinates()
    if one.shape != two.shape:
        raise ValueError('shape of coordinates must be the same')
    #if one.shape[-2:] != (1,3):
    #    raise ValueError('shape of coordinates must be ([M,]1,3)')
    
    return np.sqrt(np.power(one - two, 2).sum(axis=-1))
    
def getAngle():
    pass

def getDihedral():
    pass

def getRadiusOfGyration(coords, weights=None):
    """Calculate radius of gyration for a set of coordinates or atoms."""
    if isinstance(coords, (pd.AtomGroup, pd.AtomSubset, pd.AtomMap)):
        coords = coords.getCoordinates()
    if not isinstance(coords, np.ndarray):
        raise TypeError('coords must be a array or atomic')
    elif not coords.ndim in (2, 3):
        raise ValueError('coords may be a 2 or 3 dimentional array')
    elif coords.shape[-1] != 3:
        raise ValueError('coords must have shape ([n_coordsets,]n_atoms,3)')
    if weights is not None:
        weights = weights.flatten()
        if len(weights) != coords.shape[-2]:
            raise ValueError('length of weights must match number of atoms')
        wsum = weights.sum()
    else:
        wsum = coords.shape[-2]
        
    if coords.ndim == 2:
        if weights is None:
            com = coords.mean(0)
            d2sum = ((coords - com)**2).sum()
        else:
            
            com = (coords * weights).mean(0) / wsum
            d2sum = (((coords - com)**2).sum(1) * weights).sum()
    else:
        rgyr = []
        for coords in coords:        
            if weights is None:
                com = coords.mean(0)
                d2sum = ((coords - com)**2).sum()
                rgyr.append(d2sum)
            else:
                
                com = (coords * weights).mean(0) / wsum
                d2sum = (((coords - com)**2).sum(1) * weights).sum()
                rgyr.append(d2sum)
        d2sum = np.array(rgyr)
    return (d2sum / wsum) ** 0.5
            
            
    