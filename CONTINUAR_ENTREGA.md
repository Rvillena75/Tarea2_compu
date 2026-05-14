# Continuidad de entrega

Este archivo resume el estado actual del repositorio y que hacer si otro
integrante del grupo quiere agregar una tercera medicion antes de entregar.

## Estado actual

El repositorio ya tiene resultados finales completos para dos computadores:

- Local: `results/final/local/`
- Cluster IALab: `results/final/cluster/`

Ambas corridas tienen:

- `results.csv`
- `hardware.json`
- `report.md`
- `report.pdf`
- `plots/*.png`

La cobertura verificada en cada `results.csv` es:

- 148 filas totales.
- 12 filas `serial`.
- 88 filas `schedule`.
- 48 filas `compare`.
- 24 filas `openmp_best`.
- 24 filas `numba_pt`.

El informe principal para revisar/entregar es:

```text
results/final/informe_entrega_grupo.pdf
```

Su fuente editable esta en:

```text
results/final/informe_entrega_grupo.md
```

Ese informe ya incluye Local + Cluster y deja un espacio para completar con un
computador adicional de otro integrante del grupo.

## Si se quiere agregar otro computador

En el computador del integrante, desde la raiz del repo:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 src/run_experiments.py --full --reps 1 --pdf --outdir "results/full_grupo_<nombre>"
```

Copiar la carpeta generada a este repo:

```bash
mkdir -p results/final/grupo_<nombre>
rsync -av results/full_grupo_<nombre>/ results/final/grupo_<nombre>/
```

Luego completar en `results/final/informe_entrega_grupo.md` la seccion:

```text
Espacio para computador adicional del grupo
```

No inventar valores. Usar solo `results.csv` y `hardware.json` de esa corrida.

Regenerar el PDF:

```bash
cd results/final
pandoc informe_entrega_grupo.md -o informe_entrega_grupo.pdf --pdf-engine=pdflatex
```

## Verificaciones antes de subir

Desde la raiz del repo:

```bash
python3 -m py_compile src/run_experiments.py src/numba_pt.py
make -C src -B
python3 src/run_experiments.py --quick --reps 1 --outdir /tmp/tarea2_push_quick
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

Verificar PDF:

```bash
pdftotext results/final/informe_entrega_grupo.pdf - | head
```

## Archivos que deben quedar en Git

Incluir:

- `README.md`
- `CONTINUAR_ENTREGA.md`
- `requirements.txt`
- `docs/`
- `src/`
- `results/README.md`
- `results/final/`

No incluir:

- binarios compilados en `src/`
- `.venv/`
- `src/python_deps/`
- caches de Python/Numba/Matplotlib
- corridas temporales `results/full_*`
