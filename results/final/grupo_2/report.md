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

Procesador: Intel(R) Core(TM) Ultra 5 225U

Cores fisicos reportados: 7

Threads logicos reportados: 14

Threads por core: 2

## Resultados seriales

Las mediciones usan wall-clock time. Si se piden varias repeticiones con
`--reps`, el informe conserva el minimo, siguiendo la recomendacion de clase para
reducir ruido experimental.

| Fase | Impl. | Escena | Config. | p | Schedule | Chunk | Tiempo (s) |
|---|---|---|---:|---:|---|---:|---:|
| serial | serial_rt | scene.txt | small | 1 | serial | 0 | 0.079102 |
| serial | serial_pt | scene.txt | small | 1 | serial | 0 | 4.043810 |
| serial | serial_rt | scene.txt | medium | 1 | serial | 0 | 1.227410 |
| serial | serial_pt | scene.txt | medium | 1 | serial | 0 | 63.416700 |
| serial | serial_rt | scene.txt | large | 1 | serial | 0 | 4.575870 |
| serial | serial_pt | scene.txt | large | 1 | serial | 0 | 489.973000 |
| serial | serial_rt | scene_many.txt | small | 1 | serial | 0 | 0.212520 |
| serial | serial_pt | scene_many.txt | small | 1 | serial | 0 | 7.041240 |
| serial | serial_rt | scene_many.txt | medium | 1 | serial | 0 | 3.343980 |
| serial | serial_pt | scene_many.txt | medium | 1 | serial | 0 | 92.552300 |
| serial | serial_rt | scene_many.txt | large | 1 | serial | 0 | 14.655200 |
| serial | serial_pt | scene_many.txt | large | 1 | serial | 0 | 750.842000 |


## Barrido de scheduling OpenMP

| Fase | Impl. | Escena | Config. | p | Schedule | Chunk | Tiempo (s) |
|---|---|---|---:|---:|---|---:|---:|
| schedule | omp_pt_sched | scene.txt | medium | 1 | static | 1 | 62.225400 |
| schedule | omp_pt_sched | scene.txt | medium | 1 | static | 8 | 62.530200 |
| schedule | omp_pt_sched | scene.txt | medium | 1 | static | 32 | 62.239800 |
| schedule | omp_pt_sched | scene.txt | medium | 1 | static | 128 | 62.429100 |
| schedule | omp_pt_sched | scene.txt | medium | 1 | dynamic | 1 | 62.709000 |
| schedule | omp_pt_sched | scene.txt | medium | 1 | dynamic | 8 | 62.409000 |
| schedule | omp_pt_sched | scene.txt | medium | 1 | dynamic | 32 | 62.571500 |
| schedule | omp_pt_sched | scene.txt | medium | 1 | dynamic | 128 | 62.302200 |
| schedule | omp_pt_sched | scene.txt | medium | 1 | guided | 1 | 62.349600 |
| schedule | omp_pt_sched | scene.txt | medium | 1 | guided | 8 | 66.716100 |
| schedule | omp_pt_sched | scene.txt | medium | 1 | guided | 32 | 64.208000 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | static | 1 | 33.457300 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | static | 8 | 32.533200 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | static | 32 | 32.390900 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | static | 128 | 33.658500 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | dynamic | 1 | 33.423800 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | dynamic | 8 | 31.706000 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | dynamic | 32 | 32.371200 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | dynamic | 128 | 34.172500 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | guided | 1 | 31.751900 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | guided | 8 | 33.540100 |
| schedule | omp_pt_sched | scene.txt | medium | 2 | guided | 32 | 32.031900 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | static | 1 | 19.373200 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | static | 8 | 19.542800 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | static | 32 | 19.766900 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | static | 128 | 19.657200 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | dynamic | 1 | 19.122000 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | dynamic | 8 | 18.654000 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | dynamic | 32 | 18.861800 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | dynamic | 128 | 19.598500 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | guided | 1 | 19.162100 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | guided | 8 | 18.841100 |
| schedule | omp_pt_sched | scene.txt | medium | 4 | guided | 32 | 18.801600 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | static | 1 | 11.034500 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | static | 8 | 10.957600 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | static | 32 | 11.031800 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | static | 128 | 11.028500 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | dynamic | 1 | 10.802900 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | dynamic | 8 | 10.878700 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | dynamic | 32 | 10.779400 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | dynamic | 128 | 10.828300 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | guided | 1 | 11.480600 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | guided | 8 | 11.757100 |
| schedule | omp_pt_sched | scene.txt | medium | 8 | guided | 32 | 11.379600 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | static | 1 | 93.078500 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | static | 8 | 92.575100 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | static | 32 | 93.007000 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | static | 128 | 92.975600 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | dynamic | 1 | 93.163700 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | dynamic | 8 | 92.871700 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | dynamic | 32 | 93.168100 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | dynamic | 128 | 93.991700 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | guided | 1 | 93.938100 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | guided | 8 | 94.882200 |
| schedule | omp_pt_sched | scene_many.txt | medium | 1 | guided | 32 | 95.587900 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | static | 1 | 47.790400 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | static | 8 | 47.600000 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | static | 32 | 47.361100 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | static | 128 | 47.527600 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | dynamic | 1 | 46.227500 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | dynamic | 8 | 46.597200 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | dynamic | 32 | 46.952000 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | dynamic | 128 | 48.735600 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | guided | 1 | 47.932800 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | guided | 8 | 46.510200 |
| schedule | omp_pt_sched | scene_many.txt | medium | 2 | guided | 32 | 46.466200 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | static | 1 | 28.523700 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | static | 8 | 28.497900 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | static | 32 | 29.394900 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | static | 128 | 28.744900 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | dynamic | 1 | 28.856700 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | dynamic | 8 | 28.491800 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | dynamic | 32 | 28.084900 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | dynamic | 128 | 27.931000 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | guided | 1 | 28.103100 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | guided | 8 | 28.331300 |
| schedule | omp_pt_sched | scene_many.txt | medium | 4 | guided | 32 | 28.151200 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | static | 1 | 16.929900 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | static | 8 | 17.078900 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | static | 32 | 17.297500 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | static | 128 | 17.283800 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | dynamic | 1 | 16.861900 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | dynamic | 8 | 17.293700 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | dynamic | 32 | 17.105600 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | dynamic | 128 | 17.139600 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | guided | 1 | 17.720200 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | guided | 8 | 17.424600 |
| schedule | omp_pt_sched | scene_many.txt | medium | 8 | guided | 32 | 17.191300 |


## Comparacion OpenMP vs Numba

Para cada punto paralelo se calcula contra la referencia `serial_pt` de la misma
escena y configuracion: `S(p) = Ts / T(p)` y `E(p) = S(p) / p`. Los graficos de
tiempo incluyen ademas la curva ideal `Ts / p`.

| Fase | Impl. | Escena | Config. | p | Schedule | Chunk | Tiempo (s) |
|---|---|---|---:|---:|---|---:|---:|
| compare | openmp_best | scene.txt | small | 1 | dynamic | 8 | 4.076970 |
| compare | numba_pt | scene.txt | small | 1 | prange | 0 | 2.945458 |
| compare | openmp_best | scene.txt | small | 2 | dynamic | 8 | 2.007260 |
| compare | numba_pt | scene.txt | small | 2 | prange | 0 | 1.707752 |
| compare | openmp_best | scene.txt | small | 4 | dynamic | 8 | 1.185760 |
| compare | numba_pt | scene.txt | small | 4 | prange | 0 | 0.968892 |
| compare | openmp_best | scene.txt | small | 8 | dynamic | 8 | 0.687313 |
| compare | numba_pt | scene.txt | small | 8 | prange | 0 | 0.581626 |
| compare | openmp_best | scene.txt | medium | 1 | dynamic | 8 | 62.765300 |
| compare | numba_pt | scene.txt | medium | 1 | prange | 0 | 46.178714 |
| compare | openmp_best | scene.txt | medium | 2 | dynamic | 8 | 31.589400 |
| compare | numba_pt | scene.txt | medium | 2 | prange | 0 | 26.555474 |
| compare | openmp_best | scene.txt | medium | 4 | dynamic | 8 | 19.050800 |
| compare | numba_pt | scene.txt | medium | 4 | prange | 0 | 15.786484 |
| compare | openmp_best | scene.txt | medium | 8 | dynamic | 8 | 10.618100 |
| compare | numba_pt | scene.txt | medium | 8 | prange | 0 | 9.295209 |
| compare | openmp_best | scene.txt | large | 1 | dynamic | 8 | 502.154000 |
| compare | numba_pt | scene.txt | large | 1 | prange | 0 | 370.223332 |
| compare | openmp_best | scene.txt | large | 2 | dynamic | 8 | 254.722000 |
| compare | numba_pt | scene.txt | large | 2 | prange | 0 | 218.234487 |
| compare | openmp_best | scene.txt | large | 4 | dynamic | 8 | 150.099000 |
| compare | numba_pt | scene.txt | large | 4 | prange | 0 | 124.897278 |
| compare | openmp_best | scene.txt | large | 8 | dynamic | 8 | 84.750300 |
| compare | numba_pt | scene.txt | large | 8 | prange | 0 | 77.406287 |
| compare | openmp_best | scene_many.txt | small | 1 | dynamic | 1 | 5.893770 |
| compare | numba_pt | scene_many.txt | small | 1 | prange | 0 | 4.975243 |
| compare | openmp_best | scene_many.txt | small | 2 | dynamic | 1 | 2.949720 |
| compare | numba_pt | scene_many.txt | small | 2 | prange | 0 | 2.863989 |
| compare | openmp_best | scene_many.txt | small | 4 | dynamic | 1 | 1.789700 |
| compare | numba_pt | scene_many.txt | small | 4 | prange | 0 | 1.646302 |
| compare | openmp_best | scene_many.txt | small | 8 | dynamic | 1 | 1.089680 |
| compare | numba_pt | scene_many.txt | small | 8 | prange | 0 | 1.041764 |
| compare | openmp_best | scene_many.txt | medium | 1 | dynamic | 1 | 92.873700 |
| compare | numba_pt | scene_many.txt | medium | 1 | prange | 0 | 79.644092 |
| compare | openmp_best | scene_many.txt | medium | 2 | dynamic | 1 | 39.662500 |
| compare | numba_pt | scene_many.txt | medium | 2 | prange | 0 | 38.264951 |
| compare | openmp_best | scene_many.txt | medium | 4 | dynamic | 1 | 25.772500 |
| compare | numba_pt | scene_many.txt | medium | 4 | prange | 0 | 25.193997 |
| compare | openmp_best | scene_many.txt | medium | 8 | dynamic | 1 | 18.191900 |
| compare | numba_pt | scene_many.txt | medium | 8 | prange | 0 | 18.451115 |
| compare | openmp_best | scene_many.txt | large | 1 | dynamic | 1 | 504.395000 |
| compare | numba_pt | scene_many.txt | large | 1 | prange | 0 | 424.150763 |
| compare | openmp_best | scene_many.txt | large | 2 | dynamic | 1 | 315.299000 |
| compare | numba_pt | scene_many.txt | large | 2 | prange | 0 | 296.247382 |
| compare | openmp_best | scene_many.txt | large | 4 | dynamic | 1 | 221.034000 |
| compare | numba_pt | scene_many.txt | large | 4 | prange | 0 | 209.612273 |
| compare | openmp_best | scene_many.txt | large | 8 | dynamic | 1 | 150.229000 |
| compare | numba_pt | scene_many.txt | large | 8 | prange | 0 | 143.607296 |




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
