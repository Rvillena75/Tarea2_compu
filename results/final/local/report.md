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

Procesador: Intel(R) Core(TM) i7-9750H CPU @ 2.60GHz

Cores fisicos reportados: 6

Threads logicos reportados: 12

Threads por core: 2

## Resultados seriales

Las mediciones usan wall-clock time. Si se piden varias repeticiones con
`--reps`, el informe conserva el minimo, siguiendo la recomendacion de clase para
reducir ruido experimental.

| Fase | Impl. | Escena | Config. | p | Schedule | Chunk | Tiempo (s) |
|---|---|---|---:|---:|---|---:|---:|
| serial | serial_rt | scene.txt | small | 1 | serial | 0 | 0.083447 |
| serial | serial_pt | scene.txt | small | 1 | serial | 0 | 4.075030 |
| serial | serial_rt | scene.txt | medium | 1 | serial | 0 | 1.378930 |
| serial | serial_pt | scene.txt | medium | 1 | serial | 0 | 64.689800 |
| serial | serial_rt | scene.txt | large | 1 | serial | 0 | 5.657600 |
| serial | serial_pt | scene.txt | large | 1 | serial | 0 | 533.884000 |
| serial | serial_rt | scene_many.txt | small | 1 | serial | 0 | 0.220340 |
| serial | serial_pt | scene_many.txt | small | 1 | serial | 0 | 6.176730 |
| serial | serial_rt | scene_many.txt | medium | 1 | serial | 0 | 3.484430 |
| serial | serial_pt | scene_many.txt | medium | 1 | serial | 0 | 98.009700 |
| serial | serial_rt | scene_many.txt | large | 1 | serial | 0 | 13.774700 |
| serial | serial_pt | scene_many.txt | large | 1 | serial | 0 | 782.014000 |


## Barrido de scheduling OpenMP

| Fase | Impl. | Escena | Config. | p | Schedule | Chunk | Tiempo (s) |
|---|---|---|---:|---:|---|---:|---:|
| schedule | omp_pt_sched | scene.txt | medium | 1 | static | 1 | 64.443800 |
| schedule | omp_pt_sched | scene.txt | medium | 1 | static | 8 | 65.133800 |
| schedule | omp_pt_sched | scene.txt | medium | 1 | static | 32 | 64.336100 |
| schedule | omp_pt_sched | scene.txt | medium | 1 | static | 128 | 64.795100 |
| schedule | omp_pt_sched | scene.txt | medium | 1 | dynamic | 1 | 64.453600 |
| schedule | omp_pt_sched | scene.txt | medium | 1 | dynamic | 8 | 64.673600 |
| schedule | omp_pt_sched | scene.txt | medium | 1 | dynamic | 32 | 64.586500 |
| schedule | omp_pt_sched | scene.txt | medium | 1 | dynamic | 128 | 64.583800 |
| schedule | omp_pt_sched | scene.txt | medium | 1 | guided | 1 | 64.648200 |
| schedule | omp_pt_sched | scene.txt | medium | 1 | guided | 8 | 64.460700 |
| schedule | omp_pt_sched | scene.txt | medium | 1 | guided | 32 | 64.414900 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | static | 1 | 38.203700 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | static | 8 | 38.156000 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | static | 32 | 38.031300 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | static | 128 | 37.833600 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | dynamic | 1 | 37.810500 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | dynamic | 8 | 37.481700 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | dynamic | 32 | 37.379500 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | dynamic | 128 | 37.637400 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | guided | 1 | 37.459300 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | guided | 8 | 37.322800 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | guided | 32 | 37.382200 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | static | 1 | 21.527300 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | static | 8 | 22.044500 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | static | 32 | 22.337600 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | static | 128 | 22.103300 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | dynamic | 1 | 21.980000 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | dynamic | 8 | 22.071200 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | dynamic | 32 | 22.139400 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | dynamic | 128 | 22.119800 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | guided | 1 | 22.068800 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | guided | 8 | 22.064400 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | guided | 32 | 22.097700 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | static | 1 | 14.257600 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | static | 8 | 14.280900 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | static | 32 | 14.330900 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | static | 128 | 14.337100 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | dynamic | 1 | 14.067100 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | dynamic | 8 | 14.121400 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | dynamic | 32 | 14.137700 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | dynamic | 128 | 14.129000 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | guided | 1 | 14.206500 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | guided | 8 | 14.195200 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | guided | 32 | 14.156600 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | static | 1 | 99.549200 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | static | 8 | 99.342300 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | static | 32 | 99.531600 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | static | 128 | 99.874400 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | dynamic | 1 | 99.214900 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | dynamic | 8 | 99.397000 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | dynamic | 32 | 100.454000 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | dynamic | 128 | 99.199800 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | guided | 1 | 100.031000 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | guided | 8 | 99.319900 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | guided | 32 | 99.332400 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | static | 1 | 59.445000 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | static | 8 | 58.518200 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | static | 32 | 58.719800 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | static | 128 | 58.971500 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | dynamic | 1 | 58.627200 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | dynamic | 8 | 58.187600 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | dynamic | 32 | 58.370500 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | dynamic | 128 | 58.240100 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | guided | 1 | 58.552300 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | guided | 8 | 59.205600 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | guided | 32 | 57.949200 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | static | 1 | 34.195400 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | static | 8 | 35.180600 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | static | 32 | 35.624200 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | static | 128 | 35.205100 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | dynamic | 1 | 35.051100 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | dynamic | 8 | 35.141900 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | dynamic | 32 | 34.933700 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | dynamic | 128 | 34.955900 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | guided | 1 | 35.035800 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | guided | 8 | 34.922600 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | guided | 32 | 35.029800 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | static | 1 | 23.118700 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | static | 8 | 23.007300 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | static | 32 | 23.228800 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | static | 128 | 23.197100 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | dynamic | 1 | 22.729500 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | dynamic | 8 | 22.672800 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | dynamic | 32 | 22.885100 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | dynamic | 128 | 22.725000 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | guided | 1 | 23.687500 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | guided | 8 | 23.223600 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | guided | 32 | 23.011500 |


## Comparacion OpenMP vs Numba

Para cada punto paralelo se calcula contra la referencia `serial_pt` de la misma
escena y configuracion: `S(p) = Ts / T(p)` y `E(p) = S(p) / p`. Los graficos de
tiempo incluyen ademas la curva ideal `Ts / p`.

| Fase | Impl. | Escena | Config. | p | Schedule | Chunk | Tiempo (s) |
|---|---|---|---:|---:|---|---:|---:|
| compare | openmp_best | scene.txt | small | 1 | guided | 8 | 4.181170 |
| compare | openmp_best | scene.txt | small | 2 | guided | 8 | 2.405550 |
| compare | openmp_best | scene.txt | small | 4 | guided | 8 | 1.346190 |
| compare | openmp_best | scene.txt | small | 8 | guided | 8 | 0.765462 |
| compare | openmp_best | scene.txt | medium | 1 | guided | 8 | 70.217400 |
| compare | openmp_best | scene.txt | medium | 2 | guided | 8 | 39.677700 |
| compare | openmp_best | scene.txt | medium | 4 | guided | 8 | 23.280200 |
| compare | openmp_best | scene.txt | medium | 8 | guided | 8 | 15.464000 |
| compare | openmp_best | scene.txt | large | 1 | guided | 8 | 581.278000 |
| compare | openmp_best | scene.txt | large | 2 | guided | 8 | 302.865000 |
| compare | openmp_best | scene.txt | large | 4 | guided | 8 | 175.561000 |
| compare | openmp_best | scene.txt | large | 8 | guided | 8 | 112.857000 |
| compare | openmp_best | scene_many.txt | small | 1 | dynamic | 128 | 6.307610 |
| compare | openmp_best | scene_many.txt | small | 2 | dynamic | 128 | 3.659360 |
| compare | openmp_best | scene_many.txt | small | 4 | dynamic | 128 | 2.227480 |
| compare | openmp_best | scene_many.txt | small | 8 | dynamic | 128 | 1.251090 |
| compare | openmp_best | scene_many.txt | medium | 1 | dynamic | 128 | 101.456000 |
| compare | openmp_best | scene_many.txt | medium | 2 | dynamic | 128 | 58.990300 |
| compare | openmp_best | scene_many.txt | medium | 4 | dynamic | 128 | 34.330200 |
| compare | openmp_best | scene_many.txt | medium | 8 | dynamic | 128 | 22.855100 |
| compare | openmp_best | scene_many.txt | large | 1 | dynamic | 128 | 796.495000 |
| compare | openmp_best | scene_many.txt | large | 2 | dynamic | 128 | 468.221000 |
| compare | openmp_best | scene_many.txt | large | 4 | dynamic | 128 | 279.796000 |
| compare | openmp_best | scene_many.txt | large | 8 | dynamic | 128 | 182.725000 |
| compare | numba_pt | scene.txt | small | 1 | prange | 0 | 3.578515 |
| compare | numba_pt | scene.txt | small | 2 | prange | 0 | 1.994008 |
| compare | numba_pt | scene.txt | small | 4 | prange | 0 | 1.142180 |
| compare | numba_pt | scene.txt | small | 8 | prange | 0 | 0.658976 |
| compare | numba_pt | scene.txt | medium | 1 | prange | 0 | 51.965004 |
| compare | numba_pt | scene.txt | medium | 2 | prange | 0 | 32.415745 |
| compare | numba_pt | scene.txt | medium | 4 | prange | 0 | 18.847139 |
| compare | numba_pt | scene.txt | medium | 8 | prange | 0 | 12.601827 |
| compare | numba_pt | scene.txt | large | 1 | prange | 0 | 399.574343 |
| compare | numba_pt | scene.txt | large | 2 | prange | 0 | 261.005850 |
| compare | numba_pt | scene.txt | large | 4 | prange | 0 | 159.329554 |
| compare | numba_pt | scene.txt | large | 8 | prange | 0 | 102.853527 |
| compare | numba_pt | scene_many.txt | small | 1 | prange | 0 | 5.487715 |
| compare | numba_pt | scene_many.txt | small | 2 | prange | 0 | 3.481544 |
| compare | numba_pt | scene_many.txt | small | 4 | prange | 0 | 2.048548 |
| compare | numba_pt | scene_many.txt | small | 8 | prange | 0 | 1.298125 |
| compare | numba_pt | scene_many.txt | medium | 1 | prange | 0 | 87.361184 |
| compare | numba_pt | scene_many.txt | medium | 2 | prange | 0 | 56.068161 |
| compare | numba_pt | scene_many.txt | medium | 4 | prange | 0 | 34.581465 |
| compare | numba_pt | scene_many.txt | medium | 8 | prange | 0 | 23.217140 |
| compare | numba_pt | scene_many.txt | large | 1 | prange | 0 | 696.564260 |
| compare | numba_pt | scene_many.txt | large | 2 | prange | 0 | 452.235132 |
| compare | numba_pt | scene_many.txt | large | 4 | prange | 0 | 284.197160 |
| compare | numba_pt | scene_many.txt | large | 8 | prange | 0 | 185.490495 |




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
