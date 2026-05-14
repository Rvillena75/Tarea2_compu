# Tarea 2: Path Tracing con OpenMP y Numba

Repositorio del grupo para la Tarea 2 de IIC3533, Computacion de Alto
Rendimiento. El objetivo es implementar y medir versiones seriales y paralelas
de ray tracing/path tracing, comparar OpenMP contra Numba, calcular speedup y
eficiencia, y repetir los experimentos en mas de un computador.

El repositorio ya contiene corridas finales en `results/final/`:

- `results/final/local/`: corrida completa en el computador local.
- `results/final/cluster/`: corrida completa en el cluster IALab.
- `results/final/informe_entrega_grupo.pdf`: informe de entrega con Local +
  Cluster y espacio para agregar otro computador del grupo.

## Que se esta comparando

La tarea usa dos escenas:

- `src/scene.txt`: escena base con 4 esferas.
- `src/scene_many.txt`: escena mas pesada con 40 esferas.

Y tres configuraciones:

| Config. | Resolucion | S ray tracing | N path tracing |
| --- | --- | ---: | ---: |
| `small` | 400 x 300 | 2 | 32 |
| `medium` | 800 x 600 | 4 | 128 |
| `large` | 1600 x 1200 | 4 | 256 |

La referencia principal para speedup es `serial_pt.cpp`, porque es la version
serial del path tracer. Para cada implementacion paralela se calcula:

```text
S(p) = Ts / T(p)
E(p) = S(p) / p
```

donde `Ts` es el tiempo de `serial_pt` para la misma escena y configuracion, y
`p` es el numero de threads.

## Estructura del repositorio

```text
.
|-- README.md
|-- requirements.txt
|-- tarea02.pdf
|-- CONTINUAR_ENTREGA.md
|-- docs/
|   |-- USO_CLUSTER.md
|   `-- CHECKLIST_ENTREGA.md
|-- results/
|   |-- README.md
|   `-- final/
|       |-- local/
|       |-- cluster/
|       |-- informe_entrega_grupo.md
|       `-- informe_entrega_grupo.pdf
|-- src/
|   |-- Makefile
|   |-- scene.txt
|   |-- scene_many.txt
|   |-- scene.hpp
|   |-- pt.hpp
|   |-- serial.cpp
|   |-- serial_pt.cpp
|   |-- omp_pt.cpp
|   |-- omp_pt_sched.cpp
|   |-- numba_pt.py
|   |-- run_experiments.py
|   |-- run_tarea2_quick.sbatch
|   `-- run_tarea2_full.sbatch
`-- Clases/
```

### Archivos principales

- `tarea02.pdf`: enunciado oficial de la tarea.
- `Clases/`: material del curso usado como referencia conceptual.
- `src/serial.cpp`: ray tracing serial original.
- `src/serial_pt.cpp`: path tracing serial. Es la referencia `Ts`.
- `src/omp_pt.cpp`: path tracing con OpenMP usando `parallel for`.
- `src/omp_pt_sched.cpp`: version OpenMP configurable con
  `schedule(runtime)` para probar `static`, `dynamic` y `guided`.
- `src/numba_pt.py`: version Python acelerada con Numba usando
  `@njit(parallel=True)` y `prange`.
- `src/run_experiments.py`: script principal. Compila, ejecuta experimentos,
  guarda `results.csv`, genera graficos y escribe un informe base.
- `src/run_tarea2_quick.sbatch`: job corto para validar el cluster.
- `src/run_tarea2_full.sbatch`: job completo para medir en el cluster.
- `docs/USO_CLUSTER.md`: guia detallada para subir, correr y descargar desde
  IALab.
- `docs/CHECKLIST_ENTREGA.md`: lista de verificacion antes de entregar.
- `results/final/informe_entrega_grupo.pdf`: informe recomendado para entregar
  despues de revisar/agregar lo que falte del grupo.

## Requisitos

### Sistema

Se recomienda Linux o WSL2 con:

- Python 3.12.
- `g++` con soporte OpenMP.
- `make`.
- `pandoc` y LaTeX (`pdflatex`) para generar PDF.

En Ubuntu/WSL, si falta algo de compilacion o PDF:

```bash
sudo apt update
sudo apt install build-essential pandoc texlive-latex-base texlive-latex-recommended texlive-fonts-recommended
```

### Entorno Python

Desde la raiz del repositorio:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Verificar Numba:

```bash
python3 -c "import numpy, numba, matplotlib; print(numpy.__version__, numba.__version__, matplotlib.__version__)"
```

Si `import numba` falla, el script puede correr OpenMP/serial, pero no medira
Numba. Para una entrega completa conviene instalar Numba y repetir o agregar
solo esa parte con `--only-numba`.

## Compilar

Desde la raiz:

```bash
make -C src -B
```

O desde `src/`:

```bash
cd src
make -B
```

Esto genera estos binarios:

- `src/serial`
- `src/serial_pt`
- `src/omp_pt`
- `src/omp_pt_sched`

Los binarios estan ignorados por Git.

Para limpiar binarios e imagenes de prueba:

```bash
make -C src clean
```

## Ejecutar una prueba rapida

La prueba rapida sirve para verificar que compila, que Python funciona y que el
pipeline genera CSV/graficos/informe. No reemplaza la corrida completa.

```bash
python3 src/run_experiments.py --quick --reps 1 --pdf
```

Por defecto, el resultado queda en una carpeta tipo:

```text
src/results/quick_<timestamp>/
```

## Ejecutar la corrida completa local

Para generar resultados locales finales:

```bash
python3 src/run_experiments.py --full --reps 1 --pdf --outdir "results/full_local_$(date +%Y%m%d_%H%M%S)"
```

`--reps 1` es suficiente para cubrir la pauta. `--reps 3` entrega mediciones
mas robustas porque repite cada punto y conserva el minimo, pero puede tomar
muchas horas.

Si se usa `--reps 3`:

```bash
python3 src/run_experiments.py --full --reps 3 --pdf --outdir "results/full_local_$(date +%Y%m%d_%H%M%S)"
```

## Que genera `run_experiments.py`

Cada corrida genera:

- `results.csv`: tabla completa de tiempos medidos.
- `hardware.json`: informacion del computador.
- `plots/*.png`: graficos de scheduling, tiempo, speedup y eficiencia.
- `report.md`: informe base generado automaticamente.
- `report.pdf`: solo si `pandoc` y LaTeX estan disponibles.

El CSV tiene columnas:

```text
phase, impl, scene, config, width, height, depth, samples,
threads, schedule, chunk, seconds
```

Valores importantes:

- `phase=serial`: corridas `serial_rt` y `serial_pt`.
- `phase=schedule`: barrido de `static`, `dynamic` y `guided` en OpenMP.
- `phase=compare`: comparacion entre `openmp_best` y `numba_pt`.
- `impl=serial_pt`: referencia serial para speedup.
- `impl=openmp_best`: OpenMP usando la mejor estrategia elegida.
- `impl=numba_pt`: version Numba con `prange`.

## Opciones utiles del runner

Ver todas las opciones:

```bash
python3 src/run_experiments.py --help
```

Opciones principales:

- `--quick`: corrida corta de validacion.
- `--full`: matriz completa de la pauta.
- `--reps N`: repeticiones por punto; se reporta el minimo.
- `--outdir DIR`: carpeta de salida.
- `--pdf`: intenta convertir `report.md` a PDF.
- `--save-images`: guarda `.ppm` de cada render. Por defecto solo mide tiempos.

Opciones para saltar fases:

- `--skip-serial`: omite referencias seriales.
- `--skip-openmp`: omite barrido y comparacion OpenMP.
- `--skip-numba`: omite experimentos Numba.
- `--only-numba`: atajo para `--skip-serial --skip-openmp`.
- `--merge-existing`: mezcla los nuevos resultados con un `results.csv`
  existente en el mismo `--outdir`.

### Caso comun: la primera corrida salio sin Numba

Si una corrida completa termino sin Numba, no hace falta repetir todo. Primero
instalar/activar Numba:

```bash
source .venv/bin/activate
python3 -c "import numba; print(numba.__version__)"
```

Luego correr solo Numba y mezclar con el CSV existente:

```bash
OUTDIR="results/full_local_<timestamp>"
cp "$OUTDIR/results.csv" "$OUTDIR/results_before_numba.csv"
python3 src/run_experiments.py --full --reps 1 --only-numba --merge-existing --pdf --outdir "$OUTDIR"
```

Verificar que ahora hay filas Numba:

```bash
grep numba_pt "$OUTDIR/results.csv" | head
```

## Resultados finales del repositorio

Los resultados curados estan en `results/final/` porque esa ruta esta permitida
por `.gitignore`.

```text
results/final/local/
results/final/cluster/
results/final/informe_entrega_grupo.md
results/final/informe_entrega_grupo.pdf
```

### Local

`results/final/local/` contiene:

- `results.csv`
- `hardware.json`
- `report.md`
- `report.pdf`
- `informe_final_local.md`
- `informe_final_local.pdf`
- `plots/*.png`

Hardware medido:

- CPU: Intel Core i7-9750H @ 2.60 GHz.
- 6 cores fisicos.
- 12 threads logicos.

### Cluster

`results/final/cluster/` contiene:

- `results.csv`
- `hardware.json`
- `report.md`
- `report.pdf`
- `slurm_2289.out`
- `slurm_2289.err`
- `plots/*.png`

Hardware medido:

- CPU: Intel Xeon Silver 4210R @ 2.40 GHz.
- 20 cores fisicos.
- 40 threads logicos.

El cluster no tenia `pandoc`, por eso el PDF se genero localmente despues de
descargar los resultados.

## Informe de entrega

El informe mas completo es:

```text
results/final/informe_entrega_grupo.pdf
```

Tambien esta su fuente Markdown:

```text
results/final/informe_entrega_grupo.md
```

Ese informe incluye:

- declaracion de uso de IA;
- hardware local y cluster;
- espacio para un computador adicional del grupo;
- cobertura de resultados;
- resultados seriales;
- crecimiento por resolucion y por `N`;
- barrido de scheduling OpenMP;
- comparacion OpenMP vs Numba;
- speedup y eficiencia;
- comparacion Local vs Cluster;
- graficos de Local y Cluster;
- tablas en blanco para pegar resultados de otro integrante.

Para regenerar el PDF desde Markdown:

```bash
cd results/final
pandoc informe_entrega_grupo.md -o informe_entrega_grupo.pdf --pdf-engine=pdflatex
```

## Agregar resultados de otro computador del grupo

En el computador del integrante:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 src/run_experiments.py --full --reps 1 --pdf --outdir "results/full_grupo_<nombre>"
```

Debe enviar o copiar:

- `results/full_grupo_<nombre>/results.csv`
- `results/full_grupo_<nombre>/hardware.json`
- `results/full_grupo_<nombre>/plots/*.png`
- `results/full_grupo_<nombre>/report.md` o `report.pdf`

Luego copiarlo dentro del repo:

```bash
mkdir -p results/final/grupo_<nombre>
rsync -av results/full_grupo_<nombre>/ results/final/grupo_<nombre>/
```

Despues completar en `results/final/informe_entrega_grupo.md` la seccion:

```text
Espacio para computador adicional del grupo
```

No inventar mediciones. Los valores deben salir de `hardware.json` y
`results.csv`.

## Uso del cluster IALab

La guia completa esta en:

```text
docs/USO_CLUSTER.md
```

Resumen del flujo:

1. Subir el repo al cluster:

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

2. Entrar al cluster:

```bash
ssh grupo40-iic3533@kraken.ing.puc.cl
```

3. Preparar entorno:

```bash
cd ~/Tarea2_compu
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip wheel setuptools
pip install numpy numba matplotlib
```

4. Lanzar corrida completa con Slurm:

```bash
cd ~/Tarea2_compu/src
sbatch run_tarea2_full.sbatch
```

No correr `--full` directamente en el nodo login.

5. Monitorear:

```bash
squeue -u grupo40-iic3533
tail -f ~/Tarea2_compu/src/results/slurm_<JOBID>.out
tail -f ~/Tarea2_compu/src/results/slurm_<JOBID>.err
```

6. Descargar resultados:

```bash
mkdir -p results/final/cluster
rsync -av \
  grupo40-iic3533@kraken.ing.puc.cl:~/Tarea2_compu/src/results/full_cluster_<JOBID>/ \
  results/final/cluster/

rsync -av \
  grupo40-iic3533@kraken.ing.puc.cl:~/Tarea2_compu/src/results/slurm_<JOBID>.* \
  results/final/cluster/
```

## Verificaciones recomendadas

Antes de entregar:

```bash
python3 -m py_compile src/run_experiments.py src/numba_pt.py
make -C src -B
```

Verificar cobertura de resultados:

```bash
python3 - <<'PY'
import csv
from collections import Counter
for base in ["results/final/local", "results/final/cluster"]:
    rows = list(csv.DictReader(open(base + "/results.csv", newline="", encoding="utf-8")))
    print(base, len(rows), Counter(r["phase"] for r in rows), Counter(r["impl"] for r in rows))
PY
```

Una corrida completa debe tener:

- 148 filas totales.
- 12 filas `serial`.
- 88 filas `schedule`.
- 48 filas `compare`.
- 24 filas `openmp_best`.
- 24 filas `numba_pt`.

Verificar que el PDF abre o al menos que se puede extraer texto:

```bash
pdftotext results/final/informe_entrega_grupo.pdf - | head
```

## Que archivos subir

Para que el repo sea entendible en GitHub, subir:

- codigo fuente en `src/`;
- `README.md`;
- `requirements.txt`;
- `docs/`;
- `results/README.md`;
- resultados curados en `results/final/`;
- informe final en `results/final/informe_entrega_grupo.pdf`.

No subir:

- binarios compilados (`src/serial`, `src/serial_pt`, `src/omp_pt`,
  `src/omp_pt_sched`);
- caches (`__pycache__`, `.pytest_cache`, `.matplotlib_cache`, `.venv`);
- dependencias locales (`src/python_deps`);
- corridas temporales fuera de `results/final/`;
- imagenes `.ppm` salvo que alguien las necesite explicitamente.

La regla actual de `.gitignore` ignora `results/*` pero permite
`results/final/**`, para que solo queden versionados los resultados finales.

## Problemas comunes

### `numba no esta instalado`

Instalar dependencias:

```bash
source .venv/bin/activate
pip install -r requirements.txt
python3 -c "import numba; print(numba.__version__)"
```

Si ya existe una corrida sin Numba, usar `--only-numba --merge-existing`.

### No se genero `report.pdf`

Falta `pandoc` o LaTeX. El `report.md`, CSV y graficos siguen siendo validos.
Para generar PDF localmente:

```bash
cd results/final/cluster
pandoc report.md -o report.pdf --pdf-engine=pdflatex
```

### La corrida completa demora demasiado

Usar primero:

```bash
python3 src/run_experiments.py --quick --reps 1 --pdf
```

Para entrega, usar `--full --reps 1`. `--reps 3` es mas robusto, pero no es
necesario si el informe declara que se midio una vez por punto.

### El cluster muestra el job en cola

Revisar:

```bash
squeue -u grupo40-iic3533
sinfo
```

Si el nodo configurado no esta disponible, revisar `docs/USO_CLUSTER.md` y
ajustar `#SBATCH --nodelist=...` en `src/run_tarea2_full.sbatch`.

## Checklist rapido de entrega

Antes de subir a Canvas:

- [ ] `results/final/local/results.csv` existe y tiene Numba.
- [ ] `results/final/cluster/results.csv` existe y tiene Numba.
- [ ] `results/final/informe_entrega_grupo.pdf` abre correctamente.
- [ ] El informe declara uso de IA.
- [ ] El informe declara hardware de cada computador usado.
- [ ] El informe compara OpenMP vs Numba.
- [ ] El informe incluye speedup y eficiencia.
- [ ] El informe compara Local vs Cluster.
- [ ] Si se agrego otro computador del grupo, sus valores son reales y vienen
      de `results.csv`/`hardware.json`.
