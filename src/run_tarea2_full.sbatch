#!/bin/bash
#SBATCH --job-name=tarea2_g40
#SBATCH --partition=ialab
#SBATCH --nodelist=yodaxico
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=8G
#SBATCH --time=0-23:00:00
#SBATCH --output=results/slurm_%j.out
#SBATCH --error=results/slurm_%j.err

set -euo pipefail

cd "$SLURM_SUBMIT_DIR"
mkdir -p results

if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
  source "$HOME/miniconda3/etc/profile.d/conda.sh"
  conda activate tarea2-hpc
elif [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
  source "$HOME/anaconda3/etc/profile.d/conda.sh"
  conda activate tarea2-hpc
elif [ -f "../.venv/bin/activate" ]; then
  source "../.venv/bin/activate"
fi

echo "Fecha inicio:"
date

echo "Nodo:"
hostname

echo "Hardware:"
lscpu

echo "Python:"
python3 --version
python3 -c "import numpy, numba, matplotlib; print('numpy', numpy.__version__); print('numba', numba.__version__); print('matplotlib', matplotlib.__version__)"

echo "Compilando:"
make -B

export OMP_DYNAMIC=FALSE

echo "Ejecutando experimentos completos:"
python3 run_experiments.py --full --reps 1 --pdf --outdir "results/full_cluster_${SLURM_JOB_ID}"

echo "Fecha termino:"
date
echo "Terminado job $SLURM_JOB_ID"
