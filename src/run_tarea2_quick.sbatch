#!/bin/bash
#SBATCH --job-name=tarea2_g40_q
#SBATCH --partition=ialab
#SBATCH --nodelist=ventress
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=0-00:20:00
#SBATCH --output=results/slurm_quick_%j.out
#SBATCH --error=results/slurm_quick_%j.err

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

hostname
lscpu
python3 --version
python3 -c "import numpy, numba, matplotlib; print('numpy', numpy.__version__); print('numba', numba.__version__); print('matplotlib', matplotlib.__version__)"

make -B
export OMP_DYNAMIC=FALSE

python3 run_experiments.py --quick --reps 1 --pdf --outdir "results/quick_cluster_${SLURM_JOB_ID}"
