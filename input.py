#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, math, glob
from CAnac import nac_calc
from split_xdat import split_xdat, merge_xdat


run_scf = True  # If run SCF calculations to get wavefunction data
restart = True
if restart:
    restart_geometry = 20  # equals to the last path with WAVECAR but without NACs
    xda_list = ['XDATCAR0', 'XDATCAR1']
else:
    xda_list = ['XDATCAR']
    
# Before running, please:
# 1. copy XDATCAR from MD calculations
# 2. revise `run_vasp.sh` to make it adpative to current platform
# 3. please prepare vasp input files, including INCAR, KPOINTS, POTCAR in current path

batch = 5  # wavefunction data is huge, how many systems (wavefunction data)
            # calculate and store each time
if not run_scf:  # traditional CA-NAC calculations
    T_start = 1
    T_end = 50
else:
    # split geometric data
    xda_data = merge_xdat(xda_list)
    split_xdat(xda_data)
    path_to_run_vasp = 'run_vasp.sh'

# NAC calculations and Genration of standard input for HFNAMD or PYXAID
# bmin and bmax are actual band index in VASP,
# and should be same with the bmin and bmax in your NAMD simulation.
is_combine = True   # If generate standard input for HFNAMD or PYXAID
# iformat = "PYXAID"
iformat = "HFNAMD"
bmin = 4
bmax = 5
potim = 1  # Nuclear timestep, unit: fs

# Time-overlap
# bmin_stored bmax_stored are actual band index in VASP
# Use a large basis sets here if
# you would like to remove WAVECAR to save disk usage
# Or when you turn on the state reordering
bmin_stored = 3  # bmin - 10
bmax_stored = 6  # bmax + 10

nproc = 4  # Number of cores used in parallelization

is_gamma_version = False  # vasp_std False vasp_gam True
is_reorder = False  # If turn on State Reordering True (use with care) or False
is_alle = True  # If use All-electron wavefunction (require NORMALCAR) True or False
is_real = True  # If rotate wavefunction to ensure NAC is real value.
                # True (Mandatory for HFNAMD and PYXAID) or False.
ikpt = 1  # k-point index, starting from 1 to NKPTS
ispin = 1  # spin index, 1 or 2


# Don't change anything below if you are new to CA-NAC
# ########################################################################
# For Pseudo NAC only. omin and omax are used for post-orthonormalization.
# In principle, you should use entire basis sets in VASP
icor = 1
omin = bmin_stored
omax = bmax_stored

skip_file_verification = False
skip_TDolap_calc = False
skip_NAC_calc = False
onthefly_verification = True

checking_dict = {'skip_file_verification': skip_file_verification,
                 'skip_TDolap_calc': skip_TDolap_calc,
                 'skip_NAC_calc': skip_NAC_calc,
                 'onthefly_verification': onthefly_verification}


if not run_scf:
    # Directories structure.
    # Here, 0001 for 1st ionic step, 0002 for 2nd ionic step, etc.
    # Don't forget the forward slash at the end.
    Dirs = ['./%04d/' % (ii + 1) for ii in range(T_start-1, T_end)]

    nac_calc(Dirs, checking_dict, nproc,
             is_gamma_version, is_reorder, is_alle, is_real, is_combine,
             iformat, bmin, bmax, bmin_stored, bmax_stored, omin, omax,
             ikpt, ispin, icor, potim)
else:
    Dirs = sorted(glob.glob("POSCAR_*"))

    if restart:
        # remove all previous geometric files
        [os.system(f'rm {ii}') for ii in Dirs[: restart_geometry - 1]]
        # check if previous file has WAVECAR
        is_wavecar = os.path.isfile(Dirs[restart_geometry - 1].split("_", 1)[1] + '/WAVECAR')
        if not is_wavecar:
            raise FileExistsError(f'warning: {Dirs[restart_geometry - 1]} do not has WAVECAR')

        # save previous NAC files
        file_list = os.listdir('./')

        # Filter the files that start with the specified prefix
        ca_files = [file for file in file_list if file.startswith('CA')]

        # remove to prevent be covered by new files
        for ii in ca_files:
            os.system(f'mv {ii} {ii}.old')

        # get new Dirs for calculations
        Dirs = sorted(glob.glob("POSCAR_*"))
        dir_last = Dirs[0].split("_", 1)[1] + '/'

    else:
        dir_last = None

    n_batch = math.ceil(len(Dirs) / batch)
    new_nac = True

    for ii in range(0, len(Dirs), batch):
        files = Dirs[ii: min(ii + batch, len(Dirs))]
        dir_list = [file.split("_", 1)[1] + '/' for file in files]
        print(f'\n Calculate geometries list: {dir_list}')

        for ipath_scf in dir_list:
            os.system(f'mkdir {ipath_scf}')
            print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
            print(f'path: {ipath_scf}')
            os.system(f'mv POSCAR_{ipath_scf[:-1]} POSCAR')  # `:-1` is to rm /
            os.system(f'bash {path_to_run_vasp}')
            os.system(f'cp WAVECAR POSCAR POTCAR NormalCAR {ipath_scf}')

        if dir_last is not None:
            dir_list.insert(0, dir_last)
        nac_calc(dir_list, checking_dict, nproc,
                 is_gamma_version, is_reorder, is_alle, is_real, is_combine,
                 iformat, bmin, bmax, bmin_stored, bmax_stored, omin, omax,
                 ikpt, ispin, icor, potim, new_nac=new_nac)
        print(f'finish NAC calculations, the last one is {ipath_scf}')
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')

        # remove WAVECAR
        os.system(f'rm {dir_last}WAVECAR') if dir_last is not None else None
        [os.system(f'rm -rf {idir}WAVECAR') for idir in dir_list[:-1]]

        dir_last = dir_list[-1]
        new_nac = False
