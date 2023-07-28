#! /usr/bin/env python
import os
import numpy as np


def merge_xdat(files: list):
    xdatcar = None
    conf_entries = None
    poscar_header = None
    natom = None

    for file in files:
        with open(file, "r") as xdatcar_file:
            this_xdatcar = xdatcar_file.readlines()

            # extract the entries of each configuration
            this_conf = [i for i in range(len(this_xdatcar))
                         if this_xdatcar[i].find("configuration") != -1]
            this_header = this_xdatcar[:this_conf[0]]
            this_natom = this_conf[1] - this_conf[0]
    
            if natom is not None:
                assert this_natom == natom, 'two XDATCAR return different natom'
    
            poscar_header = this_header
            natom = this_natom
            if conf_entries is None:
                conf_entries = this_conf
                xdatcar = this_xdatcar
            else:
                # The last geometry in last XDATCAR should equal to the first
                # geometry in current XDATCAR file, therefore do not use the 1st
                last_conf = len(xdatcar)
                conf_entries.extend([ii + last_conf for ii in this_conf[1:]])
                xdatcar.extend(this_xdatcar)

    return {'xdatcar': xdatcar, 'conf_entries': conf_entries,
            'poscar_header': poscar_header, 'natom': natom}


# read XDATCAR
def split_xdat(geometries: dict = None, start: int = 0, end: int = -1):
    if geometries is None:
        with open("XDATCAR", "r") as xdatcar_file:
            xdatcar = xdatcar_file.readlines()
    
        # extract the entries of each configuration
        conf_entries = [i for i in range(len(xdatcar)) 
                        if xdatcar[i].find("configuration") != -1]

        # extract shared header of POSCAR and number of atoms
        poscar_header = xdatcar[:conf_entries[0]]
        natom = conf_entries[1] - conf_entries[0]
    else:
        xdatcar = geometries['xdatcar']
        conf_entries = geometries['conf_entries']
        poscar_header = geometries['poscar_header']
        natom = geometries['natom']

    # extract atomic positions of each configuration and write to POSCAR_$n
    os.system('rm POSCAR_*')
    num_list = np.arange(len(conf_entries)).tolist()[start - 1: end]
    for inum, entry in zip(num_list, conf_entries[start - 1: end]):
        nl0 = entry
        nl1 = nl0 + natom

        with open("POSCAR_" + str('%04d' % (inum + 1)), "w") as poscar_file:
            for line in poscar_header:
                poscar_file.write(line)
            for line in xdatcar[nl0:nl1]:
                poscar_file.write(line)
