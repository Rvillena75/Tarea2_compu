# Uso del cluster IALab

Esta guia explica como ejecutar los experimentos de la tarea en el cluster para
obtener las mediciones del segundo computador.

## Acceso

Host:

```bash
kraken.ing.puc.cl
```

Usuario del grupo:

```bash
grupo40-iic3533
```

Conexion:

```bash
ssh grupo40-iic3533@kraken.ing.puc.cl
```

No guardar contrasenas en archivos del repositorio. Si es el primer ingreso,
cambiar la contrasena inicial con:

```bash
passwd
```

## Subir el repo

Desde la raiz local del repo:

```bash
rsync -av --delete \
  --exclude '.git/' \
  --exclude 'results/' \
  --exclude 'src/results/' \
  --exclude 'src/python_deps/' \
  --exclude 'src/__pycache__/' \
  --exclude 'src/.matplotlib_cache/' \
  --exclude 'src/serial' \
  --exclude 'src/serial_pt' \
  --exclude 'src/omp_pt' \
  --exclude 'src/omp_pt_sched' \
  ./ grupo40-iic3533@kraken.ing.puc.cl:~/Tarea2_compu/
```

## Preparar entorno Python en el cluster

En el cluster:

```bash
cd ~/Tarea2_compu
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip wheel setuptools
pip install numpy numba matplotlib
```

Verificar:

```bash
cd ~/Tarea2_compu/src
../.venv/bin/python -c "import numpy, numba, matplotlib; print(numpy.__version__, numba.__version__, matplotlib.__version__)"
make -B
```

## Slurm

No ejecutar `--full` directamente en el nodo login. Enviar trabajos con Slurm.

Prueba corta:

```bash
cd ~/Tarea2_compu/src
sbatch run_tarea2_quick.sbatch
```

Corrida completa:

```bash
cd ~/Tarea2_compu/src
sbatch run_tarea2_full.sbatch
```

El script completo esta configurado para:

- particion `ialab`;
- nodo `yodaxico`;
- 1 tarea;
- 8 CPU por tarea;
- 8 GB de memoria;
- limite de 23 horas;
- `--full --reps 1`.

Si `yodaxico` no esta disponible, revisar nodos:

```bash
sinfo
squeue -u grupo40-iic3533
```

Y cambiar `#SBATCH --nodelist=...` en `src/run_tarea2_full.sbatch`.

## Monitoreo

Revisar estado:

```bash
squeue -u grupo40-iic3533
```

Revisar logs:

```bash
tail -f ~/Tarea2_compu/src/results/slurm_<JOBID>.out
tail -f ~/Tarea2_compu/src/results/slurm_<JOBID>.err
```

Cancelar un job:

```bash
scancel <JOBID>
```

## Descargar resultados

Cuando termine el job:

```bash
rsync -av \
  grupo40-iic3533@kraken.ing.puc.cl:~/Tarea2_compu/src/results/full_cluster_<JOBID>/ \
  "results/full_cluster_<JOBID>/"
```

Tambien conviene descargar logs:

```bash
rsync -av \
  grupo40-iic3533@kraken.ing.puc.cl:~/Tarea2_compu/src/results/slurm_<JOBID>.* \
  results/
```

## Nota sobre PDF

El cluster puede no tener `pdflatex`. En ese caso el script genera `report.md`,
CSV y graficos, pero no PDF. Descargar los resultados y generar el PDF localmente:

```bash
cd results/full_cluster_<JOBID>
pandoc report.md -o report.pdf --pdf-engine=pdflatex
```
