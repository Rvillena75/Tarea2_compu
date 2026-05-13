# Tarea 2: Path Tracing con OpenMP y Numba

Repositorio del grupo para la Tarea 2 de IIC3533, Computacion de Alto
Rendimiento. El proyecto compara una referencia serial de ray/path tracing con
versiones paralelas en OpenMP y Numba.

## Estructura

- `tarea02.pdf`: enunciado.
- `src/serial.cpp`: ray tracing serial.
- `src/serial_pt.cpp`: path tracing serial.
- `src/omp_pt.cpp`: path tracing OpenMP con `schedule(static)`.
- `src/omp_pt_sched.cpp`: path tracing OpenMP con `static`, `dynamic` y `guided`.
- `src/numba_pt.py`: version Python acelerada con Numba y `prange`.
- `src/run_experiments.py`: automatiza compilacion, experimentos, CSV, graficos e informe Markdown.
- `src/run_tarea2_quick.sbatch`: prueba corta en cluster.
- `src/run_tarea2_full.sbatch`: corrida completa en cluster.
- `docs/USO_CLUSTER.md`: guia para usar el cluster IALab.
- `docs/CHECKLIST_ENTREGA.md`: lista de cierre antes de Canvas.

`Clases/` contiene material de referencia del curso. No es necesario para
compilar ni ejecutar la tarea.

## Requisitos

Localmente se recomienda Python 3.12, `g++` con OpenMP, `make`, `pandoc` y un
entorno Python con:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

En Linux, OpenMP se compila con `g++ -fopenmp`.

## Compilar

```bash
cd src
make -B
```

Esto genera los binarios `serial`, `serial_pt`, `omp_pt` y `omp_pt_sched`.
Estos binarios estan ignorados por Git.

## Corrida rapida

Usar para validar que todo funciona:

```bash
python3 src/run_experiments.py --quick --reps 1 --pdf
```

## Corrida completa local

Para resultados locales finales:

```bash
python3 src/run_experiments.py --full --reps 1 --pdf --outdir "results/full_local_$(date +%Y%m%d_%H%M%S)"
```

`--reps 3` entrega mediciones mas robustas, pero puede tomar muchas horas.

## Salidas

Cada corrida genera:

- `results.csv`: tiempos medidos.
- `hardware.json`: datos del computador.
- `plots/*.png`: graficos de scheduling, tiempo, speedup y eficiencia.
- `report.md`: informe base generado.
- `report.pdf`: solo si `pandoc` y LaTeX estan disponibles.

Los resultados generados no se suben al repo.
Para compartir resultados finales con el grupo, copiar solo las corridas finales
a `results/final/local/` y `results/final/cluster/`. Esa ruta si queda permitida
por `.gitignore`. Ver [`results/README.md`](results/README.md).

## Cluster

El cluster IALab se usa como segundo computador de medicion. Ver
[`docs/USO_CLUSTER.md`](docs/USO_CLUSTER.md).

Resumen:

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

Luego, en el cluster:

```bash
cd ~/Tarea2_compu/src
sbatch run_tarea2_quick.sbatch
sbatch run_tarea2_full.sbatch
```

## Informe final

El `report.md` generado es una base. Antes de entregar hay que completar el
analisis con interpretacion concreta de los datos, especialmente:

- crecimiento por resolucion y por `N`;
- mejor schedule OpenMP por escena;
- comparacion OpenMP vs Numba;
- speedup y eficiencia;
- comparacion entre computador local y cluster;
- declaracion de uso de IA.
