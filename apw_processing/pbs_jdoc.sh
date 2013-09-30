#!/bin/zsh
#PBS -l ncpus=32
#PBS -l walltime=30:00:00
#PBS -q batch
#PBS -j oe
source ~/fake_pbs.env
cd $PBS_O_WORKDIR
source $HOME/profile
ja
set -eux

#################################################

make -j30 jdoc 2>&1 | tee -a make_jdoc.log

#################################################
ja -chlst
