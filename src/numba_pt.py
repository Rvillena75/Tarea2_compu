#!/usr/bin/env python3
"""Path tracer equivalente acelerado con Numba.

Uso:
    python3 numba_pt.py <scene.txt> <output.ppm> [W H D N threads]

La medicion excluye el tiempo de compilacion JIT: antes del render real se
ejecuta un render minimo para compilar las funciones @njit.
"""

from __future__ import annotations

import argparse
import math
import sys
import time
from pathlib import Path

LOCAL_DEPS = Path(__file__).resolve().parent / "python_deps"
if LOCAL_DEPS.exists():
    sys.path.insert(0, str(LOCAL_DEPS))

import numpy as np

try:
    from numba import njit, prange, set_num_threads, get_num_threads
except ModuleNotFoundError as exc:  # pragma: no cover - mensaje para entorno local
    raise SystemExit(
        "Error: falta instalar numba. Use, por ejemplo:\n"
        "  conda install numpy numba matplotlib -y\n"
        "o active el entorno del curso antes de ejecutar este script."
    ) from exc


@njit(cache=True)
def clampd(x: float) -> float:
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return x


@njit(cache=True)
def rng_uniform(state: np.uint64):
    # LCG de 64 bits. El estado es local a cada pixel, por lo que no hay
    # contencion ni carreras entre threads.
    state = state * np.uint64(6364136223846793005) + np.uint64(1442695040888963407)
    value = (state >> np.uint64(11)) * (1.0 / 9007199254740992.0)
    return state, value


@njit(cache=True)
def random_unit_sphere(state: np.uint64):
    while True:
        state, rx = rng_uniform(state)
        state, ry = rng_uniform(state)
        state, rz = rng_uniform(state)
        x = rx * 2.0 - 1.0
        y = ry * 2.0 - 1.0
        z = rz * 2.0 - 1.0
        l2 = x*x + y*y + z*z
        if l2 <= 1.0 and l2 > 1e-10:
            inv = 1.0 / math.sqrt(l2)
            return state, x*inv, y*inv, z*inv


@njit(cache=True)
def random_hemisphere(nx: float, ny: float, nz: float, state: np.uint64):
    state, x, y, z = random_unit_sphere(state)
    x += nx
    y += ny
    z += nz
    l2 = x*x + y*y + z*z
    if l2 < 1e-10:
        return state, nx, ny, nz
    inv = 1.0 / math.sqrt(l2)
    return state, x*inv, y*inv, z*inv


@njit(cache=True)
def closest_hit(ox: float, oy: float, oz: float,
                dx: float, dy: float, dz: float,
                spheres: np.ndarray, planes: np.ndarray):
    best_t = 1.0e300
    valid = False
    hit_px = hit_py = hit_pz = 0.0
    hit_nx = hit_ny = hit_nz = 0.0
    mat_r = mat_g = mat_b = 0.0
    mat_refl = mat_shiny = 0.0

    for si in range(spheres.shape[0]):
        cx = spheres[si, 0]
        cy = spheres[si, 1]
        cz = spheres[si, 2]
        radius = spheres[si, 3]

        ocx = ox - cx
        ocy = oy - cy
        ocz = oz - cz
        a = dx*dx + dy*dy + dz*dz
        hb = ocx*dx + ocy*dy + ocz*dz
        c = ocx*ocx + ocy*ocy + ocz*ocz - radius*radius
        disc = hb*hb - a*c
        if disc < 0.0:
            continue

        sq = math.sqrt(disc)
        t = (-hb - sq) / a
        if t < 1e-4:
            t = (-hb + sq) / a
        if t < 1e-4 or t >= best_t:
            continue

        px = ox + t*dx
        py = oy + t*dy
        pz = oz + t*dz
        inv_r = 1.0 / radius
        best_t = t
        valid = True
        hit_px = px
        hit_py = py
        hit_pz = pz
        hit_nx = (px - cx) * inv_r
        hit_ny = (py - cy) * inv_r
        hit_nz = (pz - cz) * inv_r
        mat_r = spheres[si, 4]
        mat_g = spheres[si, 5]
        mat_b = spheres[si, 6]
        mat_refl = spheres[si, 7]
        mat_shiny = spheres[si, 8]

    for pi in range(planes.shape[0]):
        nx = planes[pi, 0]
        ny = planes[pi, 1]
        nz = planes[pi, 2]
        d = planes[pi, 3]
        denom = nx*dx + ny*dy + nz*dz
        if abs(denom) < 1e-8:
            continue

        t = (d - (nx*ox + ny*oy + nz*oz)) / denom
        if t < 1e-4 or t >= best_t:
            continue

        best_t = t
        valid = True
        hit_px = ox + t*dx
        hit_py = oy + t*dy
        hit_pz = oz + t*dz
        if denom < 0.0:
            hit_nx = nx
            hit_ny = ny
            hit_nz = nz
        else:
            hit_nx = -nx
            hit_ny = -ny
            hit_nz = -nz
        mat_r = planes[pi, 4]
        mat_g = planes[pi, 5]
        mat_b = planes[pi, 6]
        mat_refl = planes[pi, 7]
        mat_shiny = planes[pi, 8]

    return (valid, best_t, hit_px, hit_py, hit_pz, hit_nx, hit_ny, hit_nz,
            mat_r, mat_g, mat_b, mat_refl, mat_shiny)


@njit(cache=True)
def trace_path(ox: float, oy: float, oz: float,
               dx: float, dy: float, dz: float,
               spheres: np.ndarray, planes: np.ndarray, lights: np.ndarray,
               max_depth: int, state: np.uint64):
    color_r = color_g = color_b = 0.0
    thr_r = thr_g = thr_b = 1.0
    ambient_r = ambient_g = ambient_b = 0.02

    for _depth in range(max_depth):
        (valid, _t, px, py, pz, nx, ny, nz, mat_r, mat_g, mat_b,
         mat_refl, mat_shiny) = closest_hit(ox, oy, oz, dx, dy, dz, spheres, planes)

        if not valid:
            tsky = 0.5 * (dy + 1.0)
            sky_r = (1.0 - tsky) * 1.0 + tsky * 0.5
            sky_g = (1.0 - tsky) * 1.0 + tsky * 0.7
            sky_b = 1.0
            color_r += thr_r * sky_r * 0.6
            color_g += thr_g * sky_g * 0.6
            color_b += thr_b * sky_b * 0.6
            break

        direct_r = ambient_r * mat_r
        direct_g = ambient_g * mat_g
        direct_b = ambient_b * mat_b

        for li in range(lights.shape[0]):
            lx = lights[li, 0] - px
            ly = lights[li, 1] - py
            lz = lights[li, 2] - pz
            ldist = math.sqrt(lx*lx + ly*ly + lz*lz)
            inv_l = 1.0 / ldist
            lx *= inv_l
            ly *= inv_l
            lz *= inv_l

            sh_ox = px + nx*1e-4
            sh_oy = py + ny*1e-4
            sh_oz = pz + nz*1e-4
            (sh_valid, sh_t, _spx, _spy, _spz, _snx, _sny, _snz, _sr, _sg,
             _sb, _srefl, _sshiny) = closest_hit(
                 sh_ox, sh_oy, sh_oz, lx, ly, lz, spheres, planes
             )
            if sh_valid and sh_t < ldist:
                continue

            intensity = lights[li, 3]
            ndotl = nx*lx + ny*ly + nz*lz
            if ndotl < 0.0:
                ndotl = 0.0
            diff = ndotl * intensity
            direct_r += mat_r * diff
            direct_g += mat_g * diff
            direct_b += mat_b * diff

            scale = 2.0 * (nx*lx + ny*ly + nz*lz)
            rlx = scale*nx - lx
            rly = scale*ny - ly
            rlz = scale*nz - lz
            spec_dot = rlx*(-dx) + rly*(-dy) + rlz*(-dz)
            if spec_dot < 0.0:
                spec_dot = 0.0
            spec = (spec_dot ** mat_shiny) * intensity
            direct_r += spec * 0.5
            direct_g += spec * 0.5
            direct_b += spec * 0.5

        local_scale = 1.0 - mat_refl
        color_r += thr_r * local_scale * direct_r
        color_g += thr_g * local_scale * direct_g
        color_b += thr_b * local_scale * direct_b

        ox = px + nx*1e-4
        oy = py + ny*1e-4
        oz = pz + nz*1e-4

        if mat_refl > 1e-4:
            scale = 2.0 * (nx*dx + ny*dy + nz*dz)
            rdx = dx - scale*nx
            rdy = dy - scale*ny
            rdz = dz - scale*nz
            inv_r = 1.0 / math.sqrt(rdx*rdx + rdy*rdy + rdz*rdz)
            dx = rdx * inv_r
            dy = rdy * inv_r
            dz = rdz * inv_r
            thr_r *= mat_refl
            thr_g *= mat_refl
            thr_b *= mat_refl
        else:
            state, dx, dy, dz = random_hemisphere(nx, ny, nz, state)
            thr_r *= mat_r
            thr_g *= mat_g
            thr_b *= mat_b

        max_thr = thr_r
        if thr_g > max_thr:
            max_thr = thr_g
        if thr_b > max_thr:
            max_thr = thr_b
        if max_thr < 0.01:
            break

    return state, clampd(color_r), clampd(color_g), clampd(color_b)


@njit(parallel=True, cache=True)
def render_kernel(spheres: np.ndarray, planes: np.ndarray, lights: np.ndarray,
                  origin: np.ndarray, lower_left: np.ndarray,
                  horiz: np.ndarray, vert: np.ndarray,
                  width: int, height: int, max_depth: int, samples: int,
                  pixels: np.ndarray):
    total_pixels = width * height
    seed_mul = np.uint64(11400714819323198485)

    for idx in prange(total_pixels):
        j = idx // width
        i = idx - j * width
        state = (np.uint64(idx + 1) * seed_mul) ^ np.uint64(0xD1B54A32D192ED03)
        color_r = color_g = color_b = 0.0

        for _sample in range(samples):
            state, ru = rng_uniform(state)
            state, rv = rng_uniform(state)
            u = (i + ru) / width
            v = (j + rv) / height

            dx = lower_left[0] + u*horiz[0] + v*vert[0] - origin[0]
            dy = lower_left[1] + u*horiz[1] + v*vert[1] - origin[1]
            dz = lower_left[2] + u*horiz[2] + v*vert[2] - origin[2]
            inv = 1.0 / math.sqrt(dx*dx + dy*dy + dz*dz)
            dx *= inv
            dy *= inv
            dz *= inv

            state, r, g, b = trace_path(
                origin[0], origin[1], origin[2], dx, dy, dz,
                spheres, planes, lights, max_depth, state
            )
            color_r += r
            color_g += g
            color_b += b

        inv_samples = 1.0 / samples
        pixels[idx, 0] = color_r * inv_samples
        pixels[idx, 1] = color_g * inv_samples
        pixels[idx, 2] = color_b * inv_samples


def normalize(v: np.ndarray) -> np.ndarray:
    return v / np.linalg.norm(v)


def make_camera(width: int, height: int):
    origin = np.array([0.0, 0.5, 3.8], dtype=np.float64)
    lookat = np.array([0.0, 0.0, 0.0], dtype=np.float64)
    up = np.array([0.0, 1.0, 0.0], dtype=np.float64)
    theta = math.radians(55.0)
    half_h = math.tan(theta / 2.0)
    half_w = half_h * float(width) / float(height)
    ww = normalize(origin - lookat)
    uu = normalize(np.cross(up, ww))
    vv = np.cross(ww, uu)
    lower_left = origin - uu*half_w - vv*half_h - ww
    horiz = uu * (2.0 * half_w)
    vert = vv * (2.0 * half_h)
    return origin, lower_left, horiz, vert


def fixed_planes() -> np.ndarray:
    return np.array([
        [ 0.0, 1.0, 0.0, -1.5, 0.75, 0.75, 0.75, 0.05, 8.0],
        [ 0.0, 1.0, 0.0,  2.5, 0.90, 0.90, 0.90, 0.00, 1.0],
        [ 0.0, 0.0, 1.0, -4.0, 0.80, 0.80, 0.80, 0.00, 1.0],
        [ 1.0, 0.0, 0.0, -3.0, 0.75, 0.15, 0.15, 0.00, 1.0],
        [-1.0, 0.0, 0.0, -3.0, 0.15, 0.75, 0.15, 0.00, 1.0],
    ], dtype=np.float64)


def fixed_lights() -> np.ndarray:
    return np.array([[0.5, 2.2, 0.5, 1.0]], dtype=np.float64)


def load_scene(path: Path) -> np.ndarray:
    spheres: list[list[float]] = []
    with path.open("r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if parts[0] != "sphere":
                continue
            values = [float(x) for x in parts[1:]]
            if len(values) != 9:
                raise ValueError(f"Linea de esfera invalida en {path}: {line}")
            spheres.append(values)
    return np.array(spheres, dtype=np.float64)


def save_ppm(path: Path, pixels: np.ndarray, width: int, height: int) -> None:
    with path.open("w", encoding="ascii") as fh:
        fh.write(f"P3\n{width} {height}\n255\n")
        for j in range(height - 1, -1, -1):
            row = pixels[j*width:(j+1)*width]
            for rgb in row:
                r = int(255.99 * min(1.0, max(0.0, float(rgb[0]))))
                g = int(255.99 * min(1.0, max(0.0, float(rgb[1]))))
                b = int(255.99 * min(1.0, max(0.0, float(rgb[2]))))
                fh.write(f"{r} {g} {b}\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Path tracer con Numba")
    parser.add_argument("scene", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("width", type=int, nargs="?", default=800)
    parser.add_argument("height", type=int, nargs="?", default=600)
    parser.add_argument("depth", type=int, nargs="?", default=8)
    parser.add_argument("samples", type=int, nargs="?", default=64)
    parser.add_argument("threads", type=int, nargs="?", default=0)
    parser.add_argument("--no-image", action="store_true",
                        help="mide el render pero no escribe el PPM")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.threads > 0:
        set_num_threads(args.threads)

    spheres = load_scene(args.scene)
    planes = fixed_planes()
    lights = fixed_lights()
    origin, lower_left, horiz, vert = make_camera(args.width, args.height)

    # Warm-up de compilacion JIT con las mismas signaturas.
    warm_pixels = np.empty((1, 3), dtype=np.float64)
    render_kernel(spheres, planes, lights, origin, lower_left, horiz, vert,
                  1, 1, 1, 1, warm_pixels)

    pixels = np.empty((args.width * args.height, 3), dtype=np.float64)
    t0 = time.perf_counter()
    render_kernel(spheres, planes, lights, origin, lower_left, horiz, vert,
                  args.width, args.height, args.depth, args.samples, pixels)
    elapsed = time.perf_counter() - t0

    if not args.no_image:
        save_ppm(args.output, pixels, args.width, args.height)

    threads = get_num_threads()
    print(f"Resolucion  : {args.width}x{args.height}")
    print(f"Prof. maxima: {args.depth} rebotes")
    print(f"Muestras/px : {args.samples}")
    print(f"Rayos total : {args.width * args.height * args.samples}")
    print(f"Esferas     : {spheres.shape[0]}")
    print(f"Threads     : {threads}")
    print(f"Tiempo      : {elapsed} s")
    print(f"Imagen      : {args.output if not args.no_image else '(omitida)'}")
    print(
        "RESULT,numba_pt,"
        f"{args.scene},{args.width},{args.height},{args.depth},{args.samples},"
        f"{threads},prange,0,{elapsed}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
