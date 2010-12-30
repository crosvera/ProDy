#!/usr/bin/python
# ProDy: A Python Package for Protein Dynamics Analysis
# 
# Copyright (C) 2010  Ahmet Bakan
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

__author__ = 'Lidio Meireles'
__copyright__ = 'Copyright (C) 2010 Lidio Meireles, Ahmet Bakan'

import sys
from prody import *
    
def main():
    if len(sys.argv) != 4:
        usage = "ProDy v{0:s} - PDBSelect\nusage: {1:s} <input> <output> <selection>".format(prody.__version__, sys.argv[0])
        print usage
        sys.exit(-1)
        
    pdbfn, out, selection = sys.argv[1:4]
    
    pdb = parsePDB(pdbfn)
    pdbselect = pdb.select(selection)
    writePDB(out,pdbselect)
    
if __name__ == '__main__':
    main()