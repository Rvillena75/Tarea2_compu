# Tarea 2: Path Tracing con OpenMP y Numba

> Falta ejecutar este mismo script en un segundo computador fisico y copiar sus resultados a la seccion de comparacion. No se inventan mediciones de hardware no disponible.


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

Procesador: Intel(R) Xeon(R) Silver 4210R CPU @ 2.40GHz

Cores fisicos reportados: 10

Threads logicos reportados: 40

Threads por core: 2

## Resultados seriales

Las mediciones usan wall-clock time. Si se piden varias repeticiones con
`--reps`, el informe conserva el minimo, siguiendo la recomendacion de clase para
reducir ruido experimental.

| Fase | Impl. | Escena | Config. | p | Schedule | Chunk | Tiempo (s) |
|---|---|---|---:|---:|---|---:|---:|
| serial | serial_rt | scene.txt | small | 1 | serial | 0 | 0.129249 |
| serial | serial_pt | scene.txt | small | 1 | serial | 0 | 6.442810 |
| serial | serial_rt | scene.txt | medium | 1 | serial | 0 | 1.791990 |
| serial | serial_pt | scene.txt | medium | 1 | serial | 0 | 100.985000 |
| serial | serial_rt | scene.txt | large | 1 | serial | 0 | 7.550420 |
| serial | serial_pt | scene.txt | large | 1 | serial | 0 | 811.762000 |
| serial | serial_rt | scene_many.txt | small | 1 | serial | 0 | 0.375928 |
| serial | serial_pt | scene_many.txt | small | 1 | serial | 0 | 11.424400 |
| serial | serial_rt | scene_many.txt | medium | 1 | serial | 0 | 6.261570 |
| serial | serial_pt | scene_many.txt | medium | 1 | serial | 0 | 175.809000 |
| serial | serial_rt | scene_many.txt | large | 1 | serial | 0 | 25.112500 |
| serial | serial_pt | scene_many.txt | large | 1 | serial | 0 | 1406.140000 |


## Barrido de scheduling OpenMP

| Fase | Impl. | Escena | Config. | p | Schedule | Chunk | Tiempo (s) |
|---|---|---|---:|---:|---|---:|---:|
| schedule | omp_pt_sched | scene.txt | medium | 1 | static | 1 | 103.586000 |
| schedule | omp_pt_sched | scene.txt | medium | 1 | static | 8 | 103.152000 |
| schedule | omp_pt_sched | scene.txt | medium | 1 | static | 32 | 103.362000 |
| schedule | omp_pt_sched | scene.txt | medium | 1 | static | 128 | 102.943000 |
| schedule | omp_pt_sched | scene.txt | medium | 1 | dynamic | 1 | 103.230000 |
| schedule | omp_pt_sched | scene.txt | medium | 1 | dynamic | 8 | 103.170000 |
| schedule | omp_pt_sched | scene.txt | medium | 1 | dynamic | 32 | 102.952000 |
| schedule | omp_pt_sched | scene.txt | medium | 1 | dynamic | 128 | 101.612000 |
| schedule | omp_pt_sched | scene.txt | medium | 1 | guided | 1 | 101.302000 |
| schedule | omp_pt_sched | scene.txt | medium | 1 | guided | 8 | 103.465000 |
| schedule | omp_pt_sched | scene.txt | medium | 1 | guided | 32 | 101.425000 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | static | 1 | 52.939900 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | static | 8 | 53.001600 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | static | 32 | 52.823800 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | static | 128 | 52.976400 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | dynamic | 1 | 52.506300 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | dynamic | 8 | 52.714600 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | dynamic | 32 | 53.045900 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | dynamic | 128 | 52.347000 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | guided | 1 | 52.964000 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | guided | 8 | 53.064500 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | guided | 32 | 53.109400 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | static | 1 | 27.621600 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | static | 8 | 27.661900 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | static | 32 | 27.814500 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | static | 128 | 27.606900 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | dynamic | 1 | 27.586800 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | dynamic | 8 | 27.686500 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | dynamic | 32 | 27.571800 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | dynamic | 128 | 27.575600 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | guided | 1 | 27.565500 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | guided | 8 | 27.569600 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | guided | 32 | 27.533400 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | static | 1 | 19.619500 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | static | 8 | 19.653300 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | static | 32 | 19.737900 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | static | 128 | 19.770600 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | dynamic | 1 | 19.555900 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | dynamic | 8 | 19.706700 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | dynamic | 32 | 19.628900 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | dynamic | 128 | 19.710800 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | guided | 1 | 19.694600 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | guided | 8 | 19.686500 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | guided | 32 | 19.705800 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | static | 1 | 179.688000 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | static | 8 | 179.374000 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | static | 32 | 179.383000 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | static | 128 | 179.556000 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | dynamic | 1 | 169.603000 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | dynamic | 8 | 179.371000 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | dynamic | 32 | 179.575000 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | dynamic | 128 | 179.048000 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | guided | 1 | 178.066000 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | guided | 8 | 169.697000 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | guided | 32 | 179.484000 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | static | 1 | 92.056800 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | static | 8 | 92.156100 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | static | 32 | 92.271200 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | static | 128 | 90.649500 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | dynamic | 1 | 92.099500 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | dynamic | 8 | 90.131500 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | dynamic | 32 | 90.580800 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | dynamic | 128 | 91.458700 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | guided | 1 | 89.833400 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | guided | 8 | 92.173200 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | guided | 32 | 91.337200 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | static | 1 | 47.938000 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | static | 8 | 47.861200 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | static | 32 | 47.982600 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | static | 128 | 47.920800 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | dynamic | 1 | 48.197700 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | dynamic | 8 | 47.831900 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | dynamic | 32 | 48.666500 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | dynamic | 128 | 47.880000 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | guided | 1 | 47.867400 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | guided | 8 | 47.791000 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | guided | 32 | 47.803700 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | static | 1 | 37.591200 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | static | 8 | 37.542700 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | static | 32 | 37.606000 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | static | 128 | 37.629900 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | dynamic | 1 | 37.343100 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | dynamic | 8 | 37.396000 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | dynamic | 32 | 37.458000 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | dynamic | 128 | 37.625500 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | guided | 1 | 37.500700 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | guided | 8 | 37.655700 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | guided | 32 | 37.567600 |


## Comparacion OpenMP vs Numba

Para cada punto paralelo se calcula contra la referencia `serial_pt` de la misma
escena y configuracion: `S(p) = Ts / T(p)` y `E(p) = S(p) / p`. Los graficos de
tiempo incluyen ademas la curva ideal `Ts / p`.

| Fase | Impl. | Escena | Config. | p | Schedule | Chunk | Tiempo (s) |
|---|---|---|---:|---:|---|---:|---:|
| compare | openmp_best | scene.txt | small | 1 | dynamic | 128 | 6.616900 |
| compare | numba_pt | scene.txt | small | 1 | prange | 0 | 4.885835 |
| compare | openmp_best | scene.txt | small | 2 | dynamic | 128 | 3.415820 |
| compare | numba_pt | scene.txt | small | 2 | prange | 0 | 2.744184 |
| compare | openmp_best | scene.txt | small | 4 | dynamic | 128 | 1.777660 |
| compare | numba_pt | scene.txt | small | 4 | prange | 0 | 1.484349 |
| compare | openmp_best | scene.txt | small | 8 | dynamic | 128 | 1.269230 |
| compare | numba_pt | scene.txt | small | 8 | prange | 0 | 1.084230 |
| compare | openmp_best | scene.txt | medium | 1 | dynamic | 128 | 103.303000 |
| compare | numba_pt | scene.txt | medium | 1 | prange | 0 | 73.706042 |
| compare | openmp_best | scene.txt | medium | 2 | dynamic | 128 | 52.478700 |
| compare | numba_pt | scene.txt | medium | 2 | prange | 0 | 44.085470 |
| compare | openmp_best | scene.txt | medium | 4 | dynamic | 128 | 27.836600 |
| compare | numba_pt | scene.txt | medium | 4 | prange | 0 | 23.238844 |
| compare | openmp_best | scene.txt | medium | 8 | dynamic | 128 | 19.699100 |
| compare | numba_pt | scene.txt | medium | 8 | prange | 0 | 16.977437 |
| compare | openmp_best | scene.txt | large | 1 | dynamic | 128 | 822.579000 |
| compare | numba_pt | scene.txt | large | 1 | prange | 0 | 581.332042 |
| compare | openmp_best | scene.txt | large | 2 | dynamic | 128 | 421.544000 |
| compare | numba_pt | scene.txt | large | 2 | prange | 0 | 352.311262 |
| compare | openmp_best | scene.txt | large | 4 | dynamic | 128 | 219.374000 |
| compare | numba_pt | scene.txt | large | 4 | prange | 0 | 185.739256 |
| compare | openmp_best | scene.txt | large | 8 | dynamic | 128 | 157.145000 |
| compare | numba_pt | scene.txt | large | 8 | prange | 0 | 135.203175 |
| compare | openmp_best | scene_many.txt | small | 1 | dynamic | 1 | 11.420600 |
| compare | numba_pt | scene_many.txt | small | 1 | prange | 0 | 8.165558 |
| compare | openmp_best | scene_many.txt | small | 2 | dynamic | 1 | 5.731960 |
| compare | numba_pt | scene_many.txt | small | 2 | prange | 0 | 4.710695 |
| compare | openmp_best | scene_many.txt | small | 4 | dynamic | 1 | 3.061580 |
| compare | numba_pt | scene_many.txt | small | 4 | prange | 0 | 2.595941 |
| compare | openmp_best | scene_many.txt | small | 8 | dynamic | 1 | 2.379510 |
| compare | numba_pt | scene_many.txt | small | 8 | prange | 0 | 2.012933 |
| compare | openmp_best | scene_many.txt | medium | 1 | dynamic | 1 | 177.196000 |
| compare | numba_pt | scene_many.txt | medium | 1 | prange | 0 | 128.414949 |
| compare | openmp_best | scene_many.txt | medium | 2 | dynamic | 1 | 91.865300 |
| compare | numba_pt | scene_many.txt | medium | 2 | prange | 0 | 75.439223 |
| compare | openmp_best | scene_many.txt | medium | 4 | dynamic | 1 | 47.580000 |
| compare | numba_pt | scene_many.txt | medium | 4 | prange | 0 | 41.411138 |
| compare | openmp_best | scene_many.txt | medium | 8 | dynamic | 1 | 37.521100 |
| compare | numba_pt | scene_many.txt | medium | 8 | prange | 0 | 31.522765 |
| compare | openmp_best | scene_many.txt | large | 1 | dynamic | 1 | 1434.800000 |
| compare | numba_pt | scene_many.txt | large | 1 | prange | 0 | 1043.958627 |
| compare | openmp_best | scene_many.txt | large | 2 | dynamic | 1 | 732.822000 |
| compare | numba_pt | scene_many.txt | large | 2 | prange | 0 | 613.288810 |
| compare | openmp_best | scene_many.txt | large | 4 | dynamic | 1 | 381.005000 |
| compare | numba_pt | scene_many.txt | large | 4 | prange | 0 | 332.148715 |
| compare | openmp_best | scene_many.txt | large | 8 | dynamic | 1 | 298.016000 |
| compare | numba_pt | scene_many.txt | large | 8 | prange | 0 | 252.487236 |




## Graficos

![schedule_scene](plots/schedule_scene.png)
![schedule_scene_many](plots/schedule_scene_many.png)
![time_scene_large](plots/time_scene_large.png)
![speedup_scene_large](plots/speedup_scene_large.png)
![efficiency_scene_large](plots/efficiency_scene_large.png)
![time_scene_medium](plots/time_scene_medium.png)
![speedup_scene_medium](plots/speedup_scene_medium.png)
![efficiency_scene_medium](plots/efficiency_scene_medium.png)
![time_scene_small](plots/time_scene_small.png)
![speedup_scene_small](plots/speedup_scene_small.png)
![efficiency_scene_small](plots/efficiency_scene_small.png)
![time_scene_many_large](plots/time_scene_many_large.png)
![speedup_scene_many_large](plots/speedup_scene_many_large.png)
![efficiency_scene_many_large](plots/efficiency_scene_many_large.png)
![time_scene_many_medium](plots/time_scene_many_medium.png)
![speedup_scene_many_medium](plots/speedup_scene_many_medium.png)
![efficiency_scene_many_medium](plots/efficiency_scene_many_medium.png)
![time_scene_many_small](plots/time_scene_many_small.png)
![speedup_scene_many_small](plots/speedup_scene_many_small.png)
![efficiency_scene_many_small](plots/efficiency_scene_many_small.png)

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
