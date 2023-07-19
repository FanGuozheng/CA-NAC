#!/bin/bash

source ~/intel/oneapi/setvars.sh --force

mpirun -np 4 /home/gz_fan/Downloads/software/vasp/vasp.5.4.4/bin/vasp_std | tee vasp.out


