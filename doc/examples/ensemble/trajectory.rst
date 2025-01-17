.. currentmodule:: prody.ensemble

.. _trajectory:

*******************************************************************************
Trajectory analysis
*******************************************************************************

Synopsis
=============================================================================

This example shows how to analyze a trajectory in DCD format. There are 
a number of different ways that coordinate data in DCD files can be analyzed.
 

Input
-------------------------------------------------------------------------------

Currently, ProDy supports only DCD format files. Two DCD trajectory files and 
corresponding PDB structure file is needed for this example.

Example input:
 
* :download:`MDM2 files </doctest/mdm2.tar.gz>` 

Output
-------------------------------------------------------------------------------

RMSD, RMSF, radius of gyration, and distance calculated from the 
trajectory.

ProDy Code
===============================================================================

We start by importing everything from the ProDy package:

>>> from prody import *

Parse reference structure
-------------------------------------------------------------------------------

The PDB file provided with this example contains and X-ray structure which will 
be useful in a number of places, so let's start with parsing this file first:

>>> structure = parsePDB('mdm2.pdb')
>>> structure
<AtomGroup: mdm2 (1449 atoms)>

This function returned a :class:`~prody.atomic.AtomGroup` instance that
stores all atomic data parsed from the PDB file.

Parse data all-at-once
-------------------------------------------------------------------------------

Using :func:`parseDCD` function all coordinate data in the DCD file can
be parsed at once. This function returns an :class:`Ensemble` instance:

>>> ensemble = parseDCD('mdm2.dcd')
>>> ensemble
<Ensemble: mdm2 (0:500:1) (500 conformations, 1449 atoms, 1449 selected)>

.. note:: When parsing large DCD files at once memory may become an issue.
   If the size of the DCD file is larger than half of the RAM in your machine,
   consider parsing DCD files frame-by-frame. See the following subsection for 
   details. 

Let's associate this ensemble with the *structure* we parsed from the PDB file:

>>> ensemble.setAtoms(structure)

This operation set the coordinates of the *structure* as the reference
coordinates of the *ensemble*. Now we can :meth:`~Ensemble.superpose` 
the *ensemble* onto the coordinates of the *structure*.  

>>> ensemble.superpose()

Now, we can get calculate RMSDs and RMSFs as follows: 

>>> print ensemble.getRMSDs().round(2) # doctest: +ELLIPSIS
[ 0.96  1.38  1.86  1.67  1.82  2.    1.84  1.85  1.72  2.    1.91  1.89
  ...
  2.49  2.25  2.35  2.32  2.23  2.36  2.38  2.42]
>>> print ensemble.getRMSFs().round(2) # doctest: +ELLIPSIS
[ 2.17  2.51  2.55 ...,  2.4   2.36  2.36]

Preceding calculations used all atoms in the structure. When we are interested
in a subset of atoms, let's say Cα atoms, we can make a selection before
performing calculations:

>>> ensemble.select('calpha')
<Selection: "calpha" from mdm2 (85 atoms)>
>>> ensemble
<Ensemble: mdm2 (0:500:1) (500 conformations, 1449 atoms, 85 selected)>
>>> ensemble.superpose()

In this case, superposition was based on Cα atom coordinates. 

>>> print ensemble.getRMSDs().round(2) # doctest: +ELLIPSIS
[ 0.57  0.66  1.08  0.87  1.01  1.08  0.97  0.97  0.71  0.99  0.84  0.76
  ...
  1.26  1.1   1.26  1.22  1.09  1.28  1.16  1.17]
>>> print ensemble.getRMSFs().round(2) # doctest: +ELLIPSIS
[ 1.63  1.23  0.8   0.6   0.51  0.46  0.45  0.56  0.55  0.44  0.5   0.56
  ...
  1.55]


The :class:`Ensemble` instance can also be used in :class:`~prody.dynamics.PCA`
calculations. See the examples in :ref:`pca` for more information.

Parse data frame-by-frame
-------------------------------------------------------------------------------

>>> dcd = DCDFile('mdm2.dcd')
>>> dcd
<DCDFile: mdm2 (next 0 of 500 frames, selected 1449 of 1449 atoms)>

>>> dcd.setAtoms(structure)

>>> dcd.getNextIndex()
0
>>> frame = dcd.next()
>>> frame
<Frame: 0 from mdm2 (1449 atoms)>
>>> dcd.getNextIndex()
1

>>> print frame.getRMSD().round(2)
1.1
>>> frame.superpose()
>>> print frame.getRMSD().round(2)
0.96

>>> print calcGyradius(frame).round(2)
12.95

We can perform these calculations for all frames in a for loop. Let's reset
*dcd* to return the the 0th frame:

>>> dcd.reset()
>>> import numpy as np
>>> rgyr = np.zeros(len(dcd))
>>> rmsd = np.zeros(len(dcd))
>>> for i, frame in enumerate(dcd):
...     rgyr[i] = calcGyradius( frame )
...     frame.superpose()
...     rmsd[i] = frame.getRMSD()
>>> print rmsd.round(2) # doctest: +ELLIPSIS
[ 0.96  1.38  1.86  1.67  1.82  2.    1.84  1.85  1.72  2.    1.91  1.89
  ...
  2.49  2.25  2.35  2.32  2.23  2.36  2.38  2.42]
>>> print rgyr.round(2) # doctest: +ELLIPSIS
[ 12.95  13.08  12.93  13.03  12.96  13.02  12.87  12.93  12.9   12.86
  ...
  13.05  13.05  13.16  13.1   13.15  13.18  13.1 ]

Handling multiple files
-------------------------------------------------------------------------------

:class:`Trajectory` is designed for handling multiple trajectory files:

>>> traj = Trajectory('mdm2.dcd')
>>> traj
<Trajectory: mdm2 (1 files, next 0 of 500 frames, selected 1449 of 1449 atoms)>
>>> traj.addFile('mdm2sim2.dcd')
>>> traj 
<Trajectory: mdm2 (2 files, next 0 of 1000 frames, selected 1449 of 1449 atoms)>

Instances of this class are also suitable for previous calculations:

>>> traj.setAtoms( structure )
>>> rgyr = np.zeros(len(traj))
>>> rmsd = np.zeros(len(traj))
>>> for i, frame in enumerate(traj):
...     rgyr[i] = calcGyradius( frame )
...     frame.superpose()
...     rmsd[i] = frame.getRMSD()
>>> print rmsd.round(2) # doctest: +ELLIPSIS
[ 0.96  1.38  1.86  1.67  1.82  2.    1.84  1.85  1.72  2.    1.91  1.89
  ...
  2.34  2.3   2.37  2.36]
>>> print rgyr.round(2) # doctest: +ELLIPSIS
[ 12.95  13.08  12.93  13.03  12.96  13.02  12.87  12.93  12.9   12.86
  ...
  12.95  12.98  12.96  13.    13.08  12.9   12.94  12.98  12.96]
  
  
Writing DCD files
-------------------------------------------------------------------------------

Finally, you can write :class:`Ensemble`, :class:`Trajectory`, and 
:class:`DCDFile` instances in DCD format using :func:`writeDCD` function.
Let's select non-hydrogen protein atoms and write a merged trajectory for
MDM2:

>>> traj.select('noh')
<Selection: "noh" from mdm2 (706 atoms)>
>>> writeDCD('mdm2_merged_noh.dcd', traj)
'mdm2_merged_noh.dcd'

Parsing this file returns:

>>> DCDFile('mdm2_merged_noh.dcd')
<DCDFile: mdm2_merged_noh (next 0 of 1000 frames, selected 706 of 706 atoms)>

See Also
===============================================================================

See :ref:`eda` for essential dynamics analysis example. 

|questions|

|suggestions|
