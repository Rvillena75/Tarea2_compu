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

Procesador: Intel(R) Core(TM) i5-10600K CPU @ 4.10GHz

Cores fisicos reportados: 6

Threads logicos reportados: 12

Threads por core: 2

## Resultados seriales

Las mediciones usan wall-clock time. Si se piden varias repeticiones con
`--reps`, el informe conserva el minimo, siguiendo la recomendacion de clase para
reducir ruido experimental.

| Fase | Impl. | Escena | Config. | p | Schedule | Chunk | Tiempo (s) |
|---|---|---|---:|---:|---|---:|---:|
| serial | serial_rt | scene.txt | small | 1 | serial | 0 | 0.089613 |
| serial | serial_pt | scene.txt | small | 1 | serial | 0 | 5.024520 |
| serial | serial_rt | scene.txt | medium | 1 | serial | 0 | 1.774630 |
| serial | serial_pt | scene.txt | medium | 1 | serial | 0 | 73.509500 |
| serial | serial_rt | scene.txt | large | 1 | serial | 0 | 6.485540 |
| serial | serial_pt | scene.txt | large | 1 | serial | 0 | 621.377000 |
| serial | serial_rt | scene_many.txt | small | 1 | serial | 0 | 0.357465 |
| serial | serial_pt | scene_many.txt | small | 1 | serial | 0 | 7.215990 |
| serial | serial_rt | scene_many.txt | medium | 1 | serial | 0 | 4.203940 |
| serial | serial_pt | scene_many.txt | medium | 1 | serial | 0 | 121.263000 |
| serial | serial_rt | scene_many.txt | large | 1 | serial | 0 | 17.733700 |
| serial | serial_pt | scene_many.txt | large | 1 | serial | 0 | 926.600000 |


## Barrido de scheduling OpenMP

| Fase | Impl. | Escena | Config. | p | Schedule | Chunk | Tiempo (s) |
|---|---|---|---:|---:|---|---:|---:|
| schedule | omp_pt_sched | scene.txt | medium | 1 | static | 1 | 74.565200 |
| schedule | omp_pt_sched | scene.txt | medium | 1 | static | 8 | 73.233300 |
| schedule | omp_pt_sched | scene.txt | medium | 1 | static | 32 | 74.283700 |
| schedule | omp_pt_sched | scene.txt | medium | 1 | static | 128 | 77.353300 |
| schedule | omp_pt_sched | scene.txt | medium | 1 | dynamic | 1 | 75.667300 |
| schedule | omp_pt_sched | scene.txt | medium | 1 | dynamic | 8 | 72.172800 |
| schedule | omp_pt_sched | scene.txt | medium | 1 | dynamic | 32 | 77.670900 |
| schedule | omp_pt_sched | scene.txt | medium | 1 | dynamic | 128 | 78.816600 |
| schedule | omp_pt_sched | scene.txt | medium | 1 | guided | 1 | 75.869100 |
| schedule | omp_pt_sched | scene.txt | medium | 1 | guided | 8 | 75.923800 |
| schedule | omp_pt_sched | scene.txt | medium | 1 | guided | 32 | 74.673200 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | static | 1 | 43.149900 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | static | 8 | 43.653200 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | static | 32 | 43.861600 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | static | 128 | 39.526100 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | dynamic | 1 | 38.706400 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | dynamic | 8 | 40.114100 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | dynamic | 32 | 42.290400 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | dynamic | 128 | 39.666700 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | guided | 1 | 38.469000 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | guided | 8 | 42.307800 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | guided | 32 | 38.511500 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | static | 1 | 22.585300 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | static | 8 | 22.920000 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | static | 32 | 23.325800 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | static | 128 | 21.545700 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | dynamic | 1 | 20.939500 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | dynamic | 8 | 21.707800 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | dynamic | 32 | 21.339100 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | dynamic | 128 | 21.848000 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | guided | 1 | 21.571500 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | guided | 8 | 23.331500 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | guided | 32 | 23.496800 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | static | 1 | 15.433000 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | static | 8 | 15.578500 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | static | 32 | 14.021400 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | static | 128 | 14.566400 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | dynamic | 1 | 14.474000 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | dynamic | 8 | 15.379600 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | dynamic | 32 | 16.460500 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | dynamic | 128 | 18.509900 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | guided | 1 | 16.060500 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | guided | 8 | 16.704600 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | guided | 32 | 15.645500 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | static | 1 | 125.255000 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | static | 8 | 122.036000 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | static | 32 | 113.911000 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | static | 128 | 123.949000 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | dynamic | 1 | 117.751000 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | dynamic | 8 | 115.059000 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | dynamic | 32 | 109.891000 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | dynamic | 128 | 116.666000 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | guided | 1 | 118.725000 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | guided | 8 | 123.038000 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | guided | 32 | 118.826000 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | static | 1 | 63.805400 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | static | 8 | 62.750900 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | static | 32 | 63.083100 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | static | 128 | 62.630600 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | dynamic | 1 | 63.431200 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | dynamic | 8 | 60.843000 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | dynamic | 32 | 62.774500 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | dynamic | 128 | 62.772300 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | guided | 1 | 61.838100 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | guided | 8 | 69.515600 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | guided | 32 | 63.060700 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | static | 1 | 33.704900 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | static | 8 | 34.959500 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | static | 32 | 34.753400 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | static | 128 | 34.899600 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | dynamic | 1 | 36.131900 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | dynamic | 8 | 33.588600 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | dynamic | 32 | 34.186600 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | dynamic | 128 | 34.786600 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | guided | 1 | 38.162900 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | guided | 8 | 36.543800 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | guided | 32 | 33.481200 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | static | 1 | 22.649300 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | static | 8 | 22.660300 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | static | 32 | 23.966300 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | static | 128 | 22.472500 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | dynamic | 1 | 21.056500 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | dynamic | 8 | 20.370900 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | dynamic | 32 | 20.850600 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | dynamic | 128 | 21.351500 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | guided | 1 | 22.101000 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | guided | 8 | 20.649200 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | guided | 32 | 21.014100 |


## Comparacion OpenMP vs Numba

Para cada punto paralelo se calcula contra la referencia `serial_pt` de la misma
escena y configuracion: `S(p) = Ts / T(p)` y `E(p) = S(p) / p`. Los graficos de
tiempo incluyen ademas la curva ideal `Ts / p`.

| Fase | Impl. | Escena | Config. | p | Schedule | Chunk | Tiempo (s) |
|---|---|---|---:|---:|---|---:|---:|
| compare | openmp_best | scene.txt | small | 1 | dynamic | 8 | 4.471490 |
| compare | numba_pt | scene.txt | small | 1 | prange | 0 | 3.437824 |
| compare | openmp_best | scene.txt | small | 2 | dynamic | 8 | 2.123740 |
| compare | numba_pt | scene.txt | small | 2 | prange | 0 | 2.385778 |
| compare | openmp_best | scene.txt | small | 4 | dynamic | 8 | 1.626770 |
| compare | numba_pt | scene.txt | small | 4 | prange | 0 | 1.038126 |
| compare | openmp_best | scene.txt | small | 8 | dynamic | 8 | 0.720105 |
| compare | numba_pt | scene.txt | small | 8 | prange | 0 | 0.866910 |
| compare | openmp_best | scene.txt | medium | 1 | dynamic | 8 | 67.701900 |
| compare | numba_pt | scene.txt | medium | 1 | prange | 0 | 55.828807 |
| compare | openmp_best | scene.txt | medium | 2 | dynamic | 8 | 40.053000 |
| compare | numba_pt | scene.txt | medium | 2 | prange | 0 | 36.115949 |
| compare | openmp_best | scene.txt | medium | 4 | dynamic | 8 | 21.655800 |
| compare | numba_pt | scene.txt | medium | 4 | prange | 0 | 19.582525 |
| compare | openmp_best | scene.txt | medium | 8 | dynamic | 8 | 13.317400 |
| compare | numba_pt | scene.txt | medium | 8 | prange | 0 | 11.934378 |
| compare | openmp_best | scene.txt | large | 1 | dynamic | 8 | 572.255000 |
| compare | numba_pt | scene.txt | large | 1 | prange | 0 | 473.989943 |
| compare | openmp_best | scene.txt | large | 2 | dynamic | 8 | 309.690000 |
| compare | numba_pt | scene.txt | large | 2 | prange | 0 | 282.348699 |
| compare | openmp_best | scene.txt | large | 4 | dynamic | 8 | 165.777000 |
| compare | numba_pt | scene.txt | large | 4 | prange | 0 | 172.013300 |
| compare | openmp_best | scene.txt | large | 8 | dynamic | 8 | 158.678000 |
| compare | numba_pt | scene.txt | large | 8 | prange | 0 | 169.868194 |
| compare | openmp_best | scene_many.txt | small | 1 | dynamic | 32 | 18.069700 |
| compare | numba_pt | scene_many.txt | small | 1 | prange | 0 | 15.366541 |
| compare | openmp_best | scene_many.txt | small | 2 | dynamic | 32 | 9.085690 |
| compare | numba_pt | scene_many.txt | small | 2 | prange | 0 | 9.591352 |
| compare | openmp_best | scene_many.txt | small | 4 | dynamic | 32 | 5.639630 |
| compare | numba_pt | scene_many.txt | small | 4 | prange | 0 | 5.416906 |
| compare | openmp_best | scene_many.txt | small | 8 | dynamic | 32 | 3.341330 |
| compare | numba_pt | scene_many.txt | small | 8 | prange | 0 | 3.201872 |
| compare | openmp_best | scene_many.txt | medium | 1 | dynamic | 32 | 217.096000 |
| compare | numba_pt | scene_many.txt | medium | 1 | prange | 0 | 108.220837 |
| compare | openmp_best | scene_many.txt | medium | 2 | dynamic | 32 | 69.440900 |
| compare | numba_pt | scene_many.txt | medium | 2 | prange | 0 | 64.288973 |
| compare | openmp_best | scene_many.txt | medium | 4 | dynamic | 32 | 37.269500 |
| compare | numba_pt | scene_many.txt | medium | 4 | prange | 0 | 37.618835 |
| compare | openmp_best | scene_many.txt | medium | 8 | dynamic | 32 | 25.485300 |
| compare | numba_pt | scene_many.txt | medium | 8 | prange | 0 | 25.597702 |
| compare | openmp_best | scene_many.txt | large | 1 | dynamic | 32 | 966.554000 |
| compare | numba_pt | scene_many.txt | large | 1 | prange | 0 | 877.889786 |
| compare | openmp_best | scene_many.txt | large | 2 | dynamic | 32 | 516.116000 |
| compare | numba_pt | scene_many.txt | large | 2 | prange | 0 | 513.052025 |
| compare | openmp_best | scene_many.txt | large | 4 | dynamic | 32 | 329.924000 |
| compare | numba_pt | scene_many.txt | large | 4 | prange | 0 | 343.350592 |
| compare | openmp_best | scene_many.txt | large | 8 | dynamic | 32 | 215.079000 |
| compare | numba_pt | scene_many.txt | large | 8 | prange | 0 | 183.131697 |




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
