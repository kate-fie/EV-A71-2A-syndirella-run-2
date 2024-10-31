#!/bin/bash

#SBATCH --job-name=dirs
#SBATCH --chdir=/opt/xchem-fragalysis-2/kfieseler
#SBATCH --output=/opt/xchem-fragalysis-2/kfieseler/logs/slurm-log_%x_%j.log
#SBATCH --error=/opt/xchem-fragalysis-2/kfieseler/logs/slurm-error_%x_%j.log
# gpu partition is `gpu`
#SBATCH --partition=main
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
##SBATCH --time=01:00:00

# extras
##SBATCH --nodes=1
##SBATCH --exclusive
##SBATCH --mem-per-cpu=<memory>
##SBATCH --gres=gpu:1
##SBATCH --constraint=<constraint>
# this does nothing
#SBATCH --mail-type=END
#SBATCH --mail-user=kate.fieseler@stats.ox.ac.uk

# -------------------------------------------------------

export SUBMITTER_HOST=$HOST
export HOST=$( hostname )
export USER=${USER:-$(users)}
export HOME=$HOME
source /etc/os-release;

echo "Running $SLURM_JOB_NAME ($SLURM_JOB_ID) as $USER in $HOST which runs $PRETTY_NAME submitted from $SUBMITTER_HOST"
echo "Request had cpus=$SLURM_JOB_CPUS_PER_NODE mem=$SLURM_MEM_PER_NODE tasks=$SLURM_NTASKS jobID=$SLURM_JOB_ID partition=$SLURM_JOB_PARTITION jobName=$SLURM_JOB_NAME"
echo "Started at $SLURM_JOB_START_TIME"
echo "job_pid=$SLURM_TASK_PID job_gid=$SLURM_JOB_GID topology_addr=$SLURM_TOPOLOGY_ADDR home=$HOME cwd=$PWD"

# -------------------------------------------------------
# CONDA
source /opt/xchem-fragalysis-2/kfieseler/.bashrc
# debug
echo '$CONDA_PREFIX = ' $CONDA_PREFIX
echo '$LD_LIBRARY_PATH = ' $LD_LIBRARY_PATH
echo "which python = " `which python`
# test conda
echo -e "\nconda info: "
conda activate syndirella
conda info
# -------------------------------------------------------

cd $HOME2/EV-A71-2A-syndirella-run-2/clean_up_A71EV2A_run5
pwd;

# Specify the file that contains the list of directories
DIR_LIST="dirs_to_delete.txt"

# Check if the file exists
if [[ ! -f $DIR_LIST ]]; then
    echo "Directory list file $DIR_LIST does not exist."
    exit 1
fi

# Loop through each line in the file and delete the directory
while IFS= read -r dir; do
    # Check if the directory exists before attempting to delete
    if [[ -d $dir ]]; then
        echo "Deleting directory: $dir"
        rm -rf "$dir"
    else
        echo "Directory $dir does not exist, skipping."
    fi
done < "$DIR_LIST"

echo "Directory deletion completed."