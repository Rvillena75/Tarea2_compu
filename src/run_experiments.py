#!/usr/bin/env python3
"""Ejecuta experimentos, genera CSV, graficos e informe Markdown.

Uso rapido para verificar:
    python3 run_experiments.py --quick

Uso completo sugerido para la entrega:
    python3 run_experiments.py --full --reps 3 --pdf

Solo Numba sobre un directorio existente:
    python3 run_experiments.py --full --only-numba --merge-existing --pdf --outdir results/full_local_...
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
RESULT_RE = re.compile(
    r"RESULT,([^,]+),([^,]+),(\d+),(\d+),(\d+),(\d+),(\d+),([^,]+),(\d+),([0-9.eE+-]+)"
)
TIME_RE = re.compile(r"Tiempo\s*:\s*([0-9.eE+-]+)\s*s")


@dataclass(frozen=True)
class Config:
    name: str
    width: int
    height: int
    spp: int
    samples: int
    depth: int = 8


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Experimentos Tarea 2")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--quick", action="store_true", help="corrida corta de prueba")
    mode.add_argument("--full", action="store_true", help="corrida completa de la pauta")
    parser.add_argument("--reps", type=int, default=1,
                        help="repeticiones por punto; se reporta el minimo")
    parser.add_argument("--outdir", type=Path, default=None,
                        help="directorio de resultados")
    parser.add_argument("--skip-serial", action="store_true",
                        help="omite referencias seriales")
    parser.add_argument("--skip-openmp", action="store_true",
                        help="omite barrido y comparacion OpenMP")
    parser.add_argument("--skip-numba", action="store_true",
                        help="omite experimentos Numba")
    parser.add_argument("--only-numba", action="store_true",
                        help="atajo para --skip-serial --skip-openmp")
    parser.add_argument("--merge-existing", action="store_true",
                        help="mezcla con results.csv existente en --outdir")
    parser.add_argument("--save-images", action="store_true",
                        help="guarda PPM de cada corrida; por defecto solo mide tiempos")
    parser.add_argument("--pdf", action="store_true",
                        help="intenta convertir report.md a PDF con pandoc")
    args = parser.parse_args()
    if args.only_numba:
        if args.skip_numba:
            parser.error("--only-numba no se puede combinar con --skip-numba")
        args.skip_serial = True
        args.skip_openmp = True
    if args.skip_serial and args.skip_openmp and args.skip_numba:
        parser.error("no queda ninguna fase para ejecutar")
    return args


def command_text(cmd: list[str]) -> str:
    return " ".join(str(c) for c in cmd)


def run(cmd: list[str], *, env: dict[str, str] | None = None, check: bool = True) -> subprocess.CompletedProcess:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    merged_env.setdefault("MPLCONFIGDIR", str(SRC / ".matplotlib_cache"))
    local_deps = SRC / "python_deps"
    if local_deps.exists():
        old_path = merged_env.get("PYTHONPATH", "")
        merged_env["PYTHONPATH"] = str(local_deps) + (os.pathsep + old_path if old_path else "")
    return subprocess.run(
        cmd,
        cwd=SRC,
        env=merged_env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def have_numba() -> bool:
    env = os.environ.copy()
    local_deps = SRC / "python_deps"
    if local_deps.exists():
        old_path = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = str(local_deps) + (os.pathsep + old_path if old_path else "")
    proc = subprocess.run(
        [sys.executable, "-c", "import numba"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    return proc.returncode == 0


def build() -> None:
    proc = run(["make"])
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)


def hardware_info() -> dict[str, str]:
    info: dict[str, str] = {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "processor": platform.processor(),
        "logical_cpus": str(os.cpu_count() or "unknown"),
    }
    lscpu = shutil.which("lscpu")
    if lscpu:
        proc = subprocess.run([lscpu], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        info["lscpu"] = proc.stdout
        for line in proc.stdout.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if key in {
                "Model name", "CPU(s)", "Thread(s) per core",
                "Core(s) per socket", "Socket(s)", "CPU max MHz", "CPU min MHz",
            }:
                info[key] = value
    return info


def parse_result(text: str) -> tuple[str, int, int, int, int, int, str, int, float] | None:
    match = RESULT_RE.search(text)
    if not match:
        return None
    impl, _scene, w, h, d, samples, threads, sched, chunk, seconds = match.groups()
    return impl, int(w), int(h), int(d), int(samples), int(threads), sched, int(chunk), float(seconds)


def parse_time(text: str) -> float:
    match = TIME_RE.search(text)
    if not match:
        raise RuntimeError(f"No se pudo parsear tiempo desde salida:\n{text[-1000:]}")
    return float(match.group(1))


def add_record(records: list[dict[str, object]], **kwargs: object) -> None:
    records.append(kwargs)
    print(
        f"{kwargs['phase']:>9} {kwargs['impl']:<12} {kwargs['scene']:<14} "
        f"{kwargs['config']:<8} p={kwargs['threads']:<2} "
        f"{kwargs['schedule']}:{kwargs['chunk']} {kwargs['seconds']:.6f}s"
    )


def run_best_of(cmd: list[str], reps: int, *, env: dict[str, str] | None = None) -> tuple[float, str]:
    outputs: list[str] = []
    times: list[float] = []
    for _ in range(reps):
        proc = run(cmd, env=env)
        text = proc.stdout + proc.stderr
        outputs.append(text)
        parsed = parse_result(text)
        if parsed:
            times.append(parsed[-1])
        else:
            times.append(parse_time(text))
    best_index = min(range(len(times)), key=times.__getitem__)
    return times[best_index], outputs[best_index]


def configs(quick: bool) -> list[Config]:
    if quick:
        return [
            Config("quick", 120, 90, 1, 4, 4),
            Config("quick2", 180, 135, 1, 8, 4),
        ]
    return [
        Config("small", 400, 300, 2, 32),
        Config("medium", 800, 600, 4, 128),
        Config("large", 1600, 1200, 4, 256),
    ]


def scenes(quick: bool) -> list[str]:
    return ["scene.txt"] if quick else ["scene.txt", "scene_many.txt"]


def thread_values(quick: bool) -> list[int]:
    return [1, 2] if quick else [1, 2, 4, 8]


def schedule_values(quick: bool) -> list[tuple[str, int]]:
    if quick:
        return [("static", 1), ("dynamic", 1), ("guided", 1)]
    return [
        ("static", 1), ("static", 8), ("static", 32), ("static", 128),
        ("dynamic", 1), ("dynamic", 8), ("dynamic", 32), ("dynamic", 128),
        ("guided", 1), ("guided", 8), ("guided", 32),
    ]


def output_path(outdir: Path, impl: str, scene: str, config: str, threads: int = 1,
                schedule: str = "serial", chunk: int = 0, save_images: bool = False) -> Path:
    if not save_images:
        return Path("-")
    stem = f"{impl}_{Path(scene).stem}_{config}_p{threads}_{schedule}{chunk}.ppm"
    return outdir / "images" / stem


def run_serials(records: list[dict[str, object]], outdir: Path, cfgs: list[Config],
                scene_names: list[str], reps: int, save_images: bool) -> None:
    for scene in scene_names:
        for cfg in cfgs:
            out = output_path(outdir, "serial_rt", scene, cfg.name, save_images=save_images)
            seconds, _text = run_best_of(
                ["./serial", scene, str(out), str(cfg.width), str(cfg.height),
                 str(cfg.depth), str(cfg.spp)],
                reps,
            )
            add_record(
                records, phase="serial", impl="serial_rt", scene=scene, config=cfg.name,
                width=cfg.width, height=cfg.height, depth=cfg.depth, samples=cfg.spp,
                threads=1, schedule="serial", chunk=0, seconds=seconds,
            )

            out = output_path(outdir, "serial_pt", scene, cfg.name, save_images=save_images)
            seconds, _text = run_best_of(
                ["./serial_pt", scene, str(out), str(cfg.width), str(cfg.height),
                 str(cfg.depth), str(cfg.samples)],
                reps,
            )
            add_record(
                records, phase="serial", impl="serial_pt", scene=scene, config=cfg.name,
                width=cfg.width, height=cfg.height, depth=cfg.depth, samples=cfg.samples,
                threads=1, schedule="serial", chunk=0, seconds=seconds,
            )


def run_schedule_sweep(records: list[dict[str, object]], outdir: Path, cfg: Config,
                       scene_names: list[str], threads: list[int],
                       schedules: list[tuple[str, int]], reps: int, save_images: bool) -> None:
    for scene in scene_names:
        for p in threads:
            for schedule, chunk in schedules:
                out = output_path(outdir, "omp_sched", scene, cfg.name, p, schedule, chunk, save_images)
                seconds, text = run_best_of(
                    ["./omp_pt_sched", scene, str(out), str(cfg.width), str(cfg.height),
                     str(cfg.depth), str(cfg.samples), str(p), schedule, str(chunk)],
                    reps,
                    env={"OMP_NUM_THREADS": str(p), "OMP_DYNAMIC": "FALSE"},
                )
                parsed = parse_result(text)
                active_schedule = schedule
                active_chunk = chunk
                if parsed:
                    active_schedule = parsed[6]
                    active_chunk = parsed[7]
                add_record(
                    records, phase="schedule", impl="omp_pt_sched", scene=scene,
                    config=cfg.name, width=cfg.width, height=cfg.height,
                    depth=cfg.depth, samples=cfg.samples, threads=p,
                    schedule=active_schedule, chunk=active_chunk, seconds=seconds,
                )


def choose_best_schedule(records: list[dict[str, object]], scene: str,
                         medium_name: str) -> tuple[str, int]:
    candidates: dict[tuple[str, int], list[float]] = {}
    for row in records:
        if row["phase"] != "schedule":
            continue
        if row["scene"] != scene or row["config"] != medium_name:
            continue
        key = (str(row["schedule"]), int(row["chunk"]))
        candidates.setdefault(key, []).append(float(row["seconds"]))
    if not candidates:
        return "static", 1
    return min(candidates, key=lambda key: mean(candidates[key]))


def run_compare(records: list[dict[str, object]], outdir: Path, cfgs: list[Config],
                scene_names: list[str], threads: list[int], reps: int,
                skip_openmp: bool, skip_numba: bool, save_images: bool) -> None:
    best_by_scene: dict[str, tuple[str, int]] = {}
    if not skip_openmp:
        best_by_scene = {
            scene: choose_best_schedule(records, scene, "medium" if cfgs[-1].name != "quick2" else "quick")
            for scene in scene_names
        }
    numba_ok = (not skip_numba) and have_numba()
    if not numba_ok and not skip_numba:
        print("Aviso: numba no esta instalado; se omiten corridas numba.", file=sys.stderr)
        if skip_openmp:
            raise RuntimeError("Se pidio correr solo Numba, pero numba no esta instalado.")

    for scene in scene_names:
        schedule, chunk = best_by_scene.get(scene, ("static", 1))
        for cfg in cfgs:
            for p in threads:
                if not skip_openmp:
                    out = output_path(outdir, "omp_best", scene, cfg.name, p, schedule, chunk, save_images)
                    seconds, text = run_best_of(
                        ["./omp_pt_sched", scene, str(out), str(cfg.width), str(cfg.height),
                         str(cfg.depth), str(cfg.samples), str(p), schedule, str(chunk)],
                        reps,
                        env={"OMP_NUM_THREADS": str(p), "OMP_DYNAMIC": "FALSE"},
                    )
                    parsed = parse_result(text)
                    active_schedule = parsed[6] if parsed else schedule
                    active_chunk = parsed[7] if parsed else chunk
                    add_record(
                        records, phase="compare", impl="openmp_best", scene=scene,
                        config=cfg.name, width=cfg.width, height=cfg.height,
                        depth=cfg.depth, samples=cfg.samples, threads=p,
                        schedule=active_schedule, chunk=active_chunk, seconds=seconds,
                    )

                if numba_ok:
                    out = output_path(outdir, "numba", scene, cfg.name, p, "prange", 0, save_images)
                    numba_cmd = [
                        sys.executable, "numba_pt.py", scene, str(out),
                        str(cfg.width), str(cfg.height), str(cfg.depth),
                        str(cfg.samples), str(p),
                    ]
                    if not save_images:
                        numba_cmd.append("--no-image")
                    seconds, text = run_best_of(
                        numba_cmd,
                        reps,
                    )
                    parsed = parse_result(text)
                    add_record(
                        records, phase="compare", impl="numba_pt", scene=scene,
                        config=cfg.name, width=cfg.width, height=cfg.height,
                        depth=cfg.depth, samples=cfg.samples, threads=p,
                        schedule="prange", chunk=0, seconds=seconds,
                    )


def write_csv(path: Path, records: list[dict[str, object]]) -> None:
    fields = [
        "phase", "impl", "scene", "config", "width", "height", "depth",
        "samples", "threads", "schedule", "chunk", "seconds",
    ]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in records:
            writer.writerow({field: row[field] for field in fields})


def row_key(row: dict[str, object]) -> tuple[str, ...]:
    fields = (
        "phase", "impl", "scene", "config", "width", "height", "depth",
        "samples", "threads", "schedule", "chunk",
    )
    return tuple(str(row[field]) for field in fields)


def merge_existing_records(csv_path: Path, records: list[dict[str, object]]) -> list[dict[str, object]]:
    if not csv_path.exists():
        return records
    existing: list[dict[str, object]] = load_csv(csv_path)
    new_keys = {row_key(row) for row in records}
    merged = [row for row in existing if row_key(row) not in new_keys]
    merged.extend(records)
    return merged


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def maybe_plots(outdir: Path, csv_path: Path) -> list[str]:
    os.environ.setdefault("MPLCONFIGDIR", str(SRC / ".matplotlib_cache"))
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:  # pragma: no cover
        print(f"Aviso: no se pudieron generar graficos: {exc}", file=sys.stderr)
        return []

    rows = load_csv(csv_path)
    plots: list[str] = []
    plot_dir = outdir / "plots"
    plot_dir.mkdir(parents=True, exist_ok=True)

    def seconds(row: dict[str, str]) -> float:
        return float(row["seconds"])

    scenes_seen = sorted({row["scene"] for row in rows})
    configs_seen = sorted({row["config"] for row in rows})

    for scene in scenes_seen:
        sched_rows = [r for r in rows if r["phase"] == "schedule" and r["scene"] == scene]
        if sched_rows:
            plt.figure(figsize=(8, 5))
            for key in sorted({(r["schedule"], r["chunk"]) for r in sched_rows}):
                subset = [r for r in sched_rows if (r["schedule"], r["chunk"]) == key]
                xs = sorted({int(r["threads"]) for r in subset})
                ys = []
                for x in xs:
                    vals = [seconds(r) for r in subset if int(r["threads"]) == x]
                    ys.append(min(vals))
                plt.plot(xs, ys, marker="o", label=f"{key[0]}({key[1]})")
            plt.title(f"OpenMP scheduling - {scene}")
            plt.xlabel("Threads")
            plt.ylabel("Tiempo (s)")
            plt.grid(True, alpha=0.3)
            plt.legend(fontsize=8)
            path = plot_dir / f"schedule_{Path(scene).stem}.png"
            plt.tight_layout()
            plt.savefig(path, dpi=160)
            plt.close()
            plots.append(str(path.relative_to(outdir)))

    for scene in scenes_seen:
        for config in configs_seen:
            comp = [
                r for r in rows
                if r["phase"] == "compare" and r["scene"] == scene and r["config"] == config
            ]
            serial = [
                r for r in rows
                if r["impl"] == "serial_pt" and r["scene"] == scene and r["config"] == config
            ]
            if not comp or not serial:
                continue
            ts = min(seconds(r) for r in serial)
            plt.figure(figsize=(8, 5))
            max_p = max(int(r["threads"]) for r in comp)
            xs_all = sorted({int(r["threads"]) for r in comp})
            plt.axhline(ts, color="black", linestyle="--", label="Serial PT")
            plt.plot(xs_all, [ts/x for x in xs_all], color="gray", linestyle=":", label="Ideal")
            for impl in sorted({r["impl"] for r in comp}):
                subset = [r for r in comp if r["impl"] == impl]
                xs = sorted({int(r["threads"]) for r in subset})
                ys = [min(seconds(r) for r in subset if int(r["threads"]) == x) for x in xs]
                plt.plot(xs, ys, marker="o", label=impl)
            plt.title(f"T(p) - {scene} - {config}")
            plt.xlabel("Threads")
            plt.ylabel("Tiempo (s)")
            plt.xticks(xs_all)
            plt.xlim(1, max_p)
            plt.grid(True, alpha=0.3)
            plt.legend()
            path = plot_dir / f"time_{Path(scene).stem}_{config}.png"
            plt.tight_layout()
            plt.savefig(path, dpi=160)
            plt.close()
            plots.append(str(path.relative_to(outdir)))

            plt.figure(figsize=(8, 5))
            for impl in sorted({r["impl"] for r in comp}):
                subset = [r for r in comp if r["impl"] == impl]
                xs = sorted({int(r["threads"]) for r in subset})
                sp = [ts / min(seconds(r) for r in subset if int(r["threads"]) == x) for x in xs]
                plt.plot(xs, sp, marker="o", label=f"{impl} speedup")
            plt.plot(xs_all, xs_all, color="gray", linestyle=":", label="Ideal")
            plt.title(f"Speedup - {scene} - {config}")
            plt.xlabel("Threads")
            plt.ylabel("Speedup")
            plt.xticks(xs_all)
            plt.grid(True, alpha=0.3)
            plt.legend()
            path = plot_dir / f"speedup_{Path(scene).stem}_{config}.png"
            plt.tight_layout()
            plt.savefig(path, dpi=160)
            plt.close()
            plots.append(str(path.relative_to(outdir)))

            plt.figure(figsize=(8, 5))
            for impl in sorted({r["impl"] for r in comp}):
                subset = [r for r in comp if r["impl"] == impl]
                xs = sorted({int(r["threads"]) for r in subset})
                eff = [
                    ts / min(seconds(r) for r in subset if int(r["threads"]) == x) / x
                    for x in xs
                ]
                plt.plot(xs, eff, marker="o", label=impl)
            plt.axhline(1.0, color="gray", linestyle=":", label="Ideal")
            plt.title(f"Eficiencia - {scene} - {config}")
            plt.xlabel("Threads")
            plt.ylabel("Eficiencia")
            plt.xticks(xs_all)
            plt.ylim(bottom=0.0)
            plt.grid(True, alpha=0.3)
            plt.legend()
            path = plot_dir / f"efficiency_{Path(scene).stem}_{config}.png"
            plt.tight_layout()
            plt.savefig(path, dpi=160)
            plt.close()
            plots.append(str(path.relative_to(outdir)))

    return plots


def table_for(rows: list[dict[str, str]], phase: str | None = None) -> str:
    subset = [r for r in rows if phase is None or r["phase"] == phase]
    if not subset:
        return "_Sin datos en esta corrida._\n"
    header = "| Fase | Impl. | Escena | Config. | p | Schedule | Chunk | Tiempo (s) |\n"
    sep = "|---|---|---|---:|---:|---|---:|---:|\n"
    body = ""
    for r in subset:
        body += (
            f"| {r['phase']} | {r['impl']} | {r['scene']} | {r['config']} | "
            f"{r['threads']} | {r['schedule']} | {r['chunk']} | "
            f"{float(r['seconds']):.6f} |\n"
        )
    return header + sep + body


def write_report(outdir: Path, csv_path: Path, plots: list[str], info: dict[str, str],
                 numba_requested: bool, quick: bool) -> Path:
    rows = load_csv(csv_path)
    report = outdir / "report.md"
    numba_rows = [r for r in rows if r["impl"] == "numba_pt"]
    second_machine_note = (
        "> Falta ejecutar este mismo script en un segundo computador fisico y copiar "
        "sus resultados a la seccion de comparacion. No se inventan mediciones de "
        "hardware no disponible.\n"
    )
    if quick:
        scope_note = (
            "> Esta es una corrida `--quick` para validar codigo y flujo. Para la entrega "
            "use `python3 run_experiments.py --full --reps 3 --pdf`.\n"
        )
    else:
        scope_note = ""

    plot_lines = "\n".join(f"![{Path(p).stem}]({p})" for p in plots)
    if not plot_lines:
        plot_lines = "_No se generaron graficos en esta corrida._"

    model = info.get("Model name", info.get("processor", "No informado"))
    cores = info.get("Core(s) per socket", "No informado")
    threads = info.get("CPU(s)", info.get("logical_cpus", "No informado"))
    tpc = info.get("Thread(s) per core", "No informado")

    text = f"""# Tarea 2: Path Tracing con OpenMP y Numba

{scope_note}{second_machine_note}

## Declaracion de uso de IA

Se uso un asistente de IA para revisar la pauta y las clases, implementar las
versiones OpenMP/Numba, crear scripts de experimentacion y redactar este informe.
Los resultados numericos provienen de ejecuciones locales registradas en
`results.csv`.

## Resumen del problema

El ray tracing serial calcula iluminacion directa con modelo de Phong, sombras y
rebotes especulares. El path tracing agrega rebotes difusos aleatorios en el
hemisferio y promedia N caminos por pixel, por lo que el costo crece como
O(W*H*N*D*K), donde K es el numero de objetos. Cada pixel es independiente:
corresponde a un patron map, trivialmente paralelizable en memoria compartida.

La carga por pixel es irregular porque algunos rayos escapan al fondo rapidamente,
mientras otros generan cadenas de rebotes, rayos de sombra e intersecciones contra
mas objetos. Por eso `schedule(static)` puede dejar threads esperando en la barrera
final, mientras `dynamic` o `guided` mejoran el balance a cambio de overhead de
planificacion.

## Implementacion

`omp_pt.cpp` paraleliza el loop de pixeles con `#pragma omp parallel for`.
`omp_pt_sched.cpp` usa `schedule(runtime)` y selecciona `static`, `dynamic` o
`guided` con `omp_set_schedule`, lo que permite barrer chunksize sin recompilar.
El espacio 2D de pixeles se aplano a un indice `idx`; asi el chunksize representa
pixeles y no filas completas. Cada iteracion escribe una posicion unica de
`pixels[idx]` y usa un RNG local sembrado con `idx + 1`, por lo que no hay
condiciones de carrera.

`numba_pt.py` implementa la misma logica con `@njit(parallel=True)` y `prange`.
Numba compila las funciones a codigo nativo con LLVM durante la primera llamada;
por eso el script hace un warm-up minimo antes de medir. A diferencia de OpenMP,
donde el paralelismo se expresa mediante directivas al compilador C++, Numba
traduce una subparte compatible de Python/NumPy y administra sus propios threads.
El RNG de Numba es un LCG local por pixel para evitar estado global compartido.

## Computador 1

Procesador: {model}

Cores fisicos reportados: {cores}

Threads logicos reportados: {threads}

Threads por core: {tpc}

## Resultados seriales

Las mediciones usan wall-clock time. Si se piden varias repeticiones con
`--reps`, el informe conserva el minimo, siguiendo la recomendacion de clase para
reducir ruido experimental.

{table_for(rows, "serial")}

## Barrido de scheduling OpenMP

{table_for(rows, "schedule")}

## Comparacion OpenMP vs Numba

Para cada punto paralelo se calcula contra la referencia `serial_pt` de la misma
escena y configuracion: `S(p) = Ts / T(p)` y `E(p) = S(p) / p`. Los graficos de
tiempo incluyen ademas la curva ideal `Ts / p`.

{table_for(rows, "compare")}

{"_Numba no se ejecuto porque no estaba instalado o fue omitido._" if not numba_rows else ""}

## Graficos

{plot_lines}

## Comentarios

El crecimiento esperado al duplicar la resolucion es cercano a 4x, porque se
cuadruplica el numero de pixeles. En path tracing, duplicar N duplica
aproximadamente el trabajo por pixel, salvo variaciones por terminacion anticipada
y efectos de cache/runtime. La escena con 40 esferas aumenta K y por tanto el
costo de cada interseccion, lo que vuelve mas visible el desbalance de carga.

La eficiencia decae al aumentar p por overhead fork-join, barreras implicitas,
planificacion dinamica, contencion de recursos compartidos y saturacion de partes
del procesador. En esta tarea no hay reducciones ni escrituras compartidas sobre
una misma variable; el principal riesgo de rendimiento es el desbalance y el costo
de scheduling con chunks demasiado finos.

## Segundo computador

Ejecute el mismo comando completo en otro computador y agregue aqui la tabla y
graficos generados. Deben declararse cores fisicos, threads logicos y frecuencia
del procesador de ese equipo.
"""
    report.write_text(text, encoding="utf-8")
    return report


def maybe_pdf(report: Path) -> None:
    if not shutil.which("pandoc"):
        print("Aviso: pandoc no esta disponible; se omite PDF.", file=sys.stderr)
        return
    pdf = report.with_suffix(".pdf")
    try:
        subprocess.run(
            ["pandoc", report.name, "-o", pdf.name, "--pdf-engine=pdflatex"],
            cwd=report.parent,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        print(f"Aviso: no se pudo generar PDF con pandoc/pdflatex: {exc}", file=sys.stderr)


def main() -> int:
    args = parse_args()
    quick = not args.full
    reps = max(1, args.reps)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    outdir = args.outdir or (SRC / "results" / ("quick_" + stamp if quick else "full_" + stamp))
    if args.save_images:
        (outdir / "images").mkdir(parents=True, exist_ok=True)
    else:
        outdir.mkdir(parents=True, exist_ok=True)

    print(f"Directorio de resultados: {outdir}")
    print(f"Modo: {'quick' if quick else 'full'}, reps={reps}")

    if not args.skip_serial or not args.skip_openmp:
        build()
    info = hardware_info()
    (outdir / "hardware.json").write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding="utf-8")

    cfgs = configs(quick)
    scene_names = scenes(quick)
    threads = thread_values(quick)
    schedules = schedule_values(quick)
    records: list[dict[str, object]] = []

    csv_path = outdir / "results.csv"
    if not args.skip_serial:
        run_serials(records, outdir, cfgs, scene_names, reps, args.save_images)
    if not args.skip_openmp:
        medium_cfg = cfgs[0] if quick else next(c for c in cfgs if c.name == "medium")
        run_schedule_sweep(records, outdir, medium_cfg, scene_names, threads, schedules, reps, args.save_images)
    run_compare(
        records, outdir, cfgs, scene_names, threads, reps,
        args.skip_openmp, args.skip_numba, args.save_images,
    )
    if args.merge_existing:
        records = merge_existing_records(csv_path, records)
    write_csv(csv_path, records)
    plots = maybe_plots(outdir, csv_path)
    report = write_report(outdir, csv_path, plots, info, not args.skip_numba, quick)
    if args.pdf:
        maybe_pdf(report)

    print(f"CSV: {csv_path}")
    print(f"Informe: {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
