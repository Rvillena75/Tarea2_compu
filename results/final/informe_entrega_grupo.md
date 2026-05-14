---
title: "Tarea 2: Path Tracing con OpenMP y Numba"
geometry: margin=1.5cm
fontsize: 10pt
---

## Declaracion de uso de IA

Se uso un asistente de IA para revisar la pauta y clases, implementar las versiones OpenMP y Numba, automatizar experimentos, revisar cobertura de resultados y generar este informe. Los resultados numericos provienen de `results/final/local/results.csv` y `results/final/cluster/results.csv`. Se deja una seccion preparada para incorporar un computador adicional de otro integrante del grupo.

## Entorno de ejecucion

| Maquina          | Procesador                                  | Cores fisicos | Threads logicos | Threads/core | Max MHz      |
| ---------------- | ------------------------------------------- | ------------- | --------------- | ------------ | ------------ |
| Local            | Intel(R) Core(TM) i7-9750H CPU @ 2.60GHz    | 6             | 12              | 2            | No informado |
| Cluster          | Intel(R) Xeon(R) Silver 4210R CPU @ 2.40GHz | 20            | 40              | 2            | 3200.0000    |
| Computador grupo | Pendiente                                   | Pendiente     | Pendiente       | Pendiente    | Pendiente    |

## Cobertura de resultados

Las corridas Local y Cluster corresponden a la matriz completa con `--full --reps 1`: dos escenas, tres configuraciones y p en {1, 2, 4, 8}.

| Maquina          | Filas     | Serial    | Scheduling | OpenMP cmp. | Numba cmp. |
| ---------------- | --------- | --------- | ---------- | ----------- | ---------- |
| Local            | 148       | 12        | 88         | 24          | 24         |
| Cluster          | 148       | 12        | 88         | 24          | 24         |
| Computador grupo | Pendiente | Pendiente | Pendiente  | Pendiente   | Pendiente  |

## Configuraciones

| Config. | Resolucion  | S ray tracing | N path tracing |
| ------- | ----------- | ------------- | -------------- |
| small   | 400 x 300   | 2             | 32             |
| medium  | 800 x 600   | 4             | 128            |
| large   | 1600 x 1200 | 4             | 256            |

## Implementacion

`omp_pt.cpp` paraleliza el loop de pixeles con `#pragma omp parallel for`. `omp_pt_sched.cpp` usa `schedule(runtime)` y `omp_set_schedule` para probar `static`, `dynamic` y `guided` con distintos chunks. Cada pixel es independiente y escribe una posicion unica en la imagen, por lo que la paralelizacion sigue el patron map.

`numba_pt.py` implementa la misma logica con `@njit(parallel=True)` y `prange`. El script realiza un warm-up minimo antes de medir para excluir el costo de compilacion JIT inicial de Numba.

## Resultados seriales

### Comparacion serial_pt entre computadores

El cociente es `Cluster/Local`; valores mayores a 1 indican que el cluster demoro mas que el equipo local.

| Escena         | Config. | Local Ts | Cluster Ts | Cluster/Local | Grupo Ts  |
| -------------- | ------- | -------- | ---------- | ------------- | --------- |
| scene.txt      | small   | 4.075    | 6.443      | 1.58x         | Pendiente |
| scene.txt      | medium  | 64.690   | 100.985    | 1.56x         | Pendiente |
| scene.txt      | large   | 533.884  | 811.762    | 1.52x         | Pendiente |
| scene_many.txt | small   | 6.177    | 11.424     | 1.85x         | Pendiente |
| scene_many.txt | medium  | 98.010   | 175.809    | 1.79x         | Pendiente |
| scene_many.txt | large   | 782.014  | 1406.140   | 1.80x         | Pendiente |

### Local: serial.cpp vs serial_pt.cpp

| Escena         | Config. | serial.cpp | serial_pt.cpp |
| -------------- | ------- | ---------- | ------------- |
| scene.txt      | small   | 0.083      | 4.075         |
| scene.txt      | medium  | 1.379      | 64.690        |
| scene.txt      | large   | 5.658      | 533.884       |
| scene_many.txt | small   | 0.220      | 6.177         |
| scene_many.txt | medium  | 3.484      | 98.010        |
| scene_many.txt | large   | 13.775     | 782.014       |

### Crecimiento Local

| Escena         | small -> medium | medium -> large |
| -------------- | --------------- | --------------- |
| scene.txt      | 15.87x          | 8.25x           |
| scene_many.txt | 15.87x          | 7.98x           |

### Cluster: serial.cpp vs serial_pt.cpp

| Escena         | Config. | serial.cpp | serial_pt.cpp |
| -------------- | ------- | ---------- | ------------- |
| scene.txt      | small   | 0.129      | 6.443         |
| scene.txt      | medium  | 1.792      | 100.985       |
| scene.txt      | large   | 7.550      | 811.762       |
| scene_many.txt | small   | 0.376      | 11.424        |
| scene_many.txt | medium  | 6.262      | 175.809       |
| scene_many.txt | large   | 25.113     | 1406.140      |

### Crecimiento Cluster

| Escena         | small -> medium | medium -> large |
| -------------- | --------------- | --------------- |
| scene.txt      | 15.67x          | 8.04x           |
| scene_many.txt | 15.39x          | 8.00x           |

El crecimiento observado es consistente con el costo esperado O(W*H*N*D*K). De `small` a `medium` se cuadruplica la resolucion y N pasa de 32 a 128, por lo que se espera cerca de 16x. De `medium` a `large` la resolucion vuelve a crecer 4x y N se duplica, por lo que se espera cerca de 8x.

## Barrido de scheduling OpenMP

### Local

| Escena         | Mejor promedio | Tiempo prom. |
| -------------- | -------------- | ------------ |
| scene.txt      | guided(8)      | 34.511       |
| scene_many.txt | dynamic(128)   | 53.780       |

| Escena         | p=1                   | p=2                 | p=4                | p=8                 |
| -------------- | --------------------- | ------------------- | ------------------ | ------------------- |
| scene.txt      | static(32), 64.336s   | guided(8), 37.323s  | static(1), 21.527s | dynamic(1), 14.067s |
| scene_many.txt | dynamic(128), 99.200s | guided(32), 57.949s | static(1), 34.195s | dynamic(8), 22.673s |

### Cluster

| Escena         | Mejor promedio | Tiempo prom. |
| -------------- | -------------- | ------------ |
| scene.txt      | dynamic(128)   | 50.311       |
| scene_many.txt | dynamic(1)     | 86.811       |

| Escena         | p=1                  | p=2                   | p=4                 | p=8                 |
| -------------- | -------------------- | --------------------- | ------------------- | ------------------- |
| scene.txt      | guided(1), 101.302s  | dynamic(128), 52.347s | guided(32), 27.533s | dynamic(1), 19.556s |
| scene_many.txt | dynamic(1), 169.603s | guided(1), 89.833s    | guided(8), 47.791s  | dynamic(1), 37.343s |

No aparece una politica unica para todos los casos. La carga por pixel es irregular porque algunos rayos terminan en el fondo y otros hacen mas rebotes, sombras e intersecciones; por eso `dynamic` o `guided` pueden mejorar el balance, aunque chunks demasiado pequenos agregan overhead. En la escena con 40 esferas aumenta el costo de interseccion y el balance de carga pesa mas.

## OpenMP vs Numba

Para cada punto se usa como referencia el tiempo `serial_pt` de la misma escena y configuracion. Se calcula `S(p)=Ts/T(p)` y `E(p)=S(p)/p`. Las siguientes tablas incluyen todos los puntos p medidos para Local y Cluster.

## Resultados paralelos completos - Local

### Local: scene.txt - small

| p | OMP T | OMP S | OMP E | Numba T | Numba S | Numba E | Mejor |
| - | ----- | ----- | ----- | ------- | ------- | ------- | ----- |
| 1 | 4.181 | 0.97  | 0.97  | 3.579   | 1.14    | 1.14    | Numba |
| 2 | 2.406 | 1.69  | 0.85  | 1.994   | 2.04    | 1.02    | Numba |
| 4 | 1.346 | 3.03  | 0.76  | 1.142   | 3.57    | 0.89    | Numba |
| 8 | 0.765 | 5.32  | 0.67  | 0.659   | 6.18    | 0.77    | Numba |

### Local: scene.txt - medium

| p | OMP T  | OMP S | OMP E | Numba T | Numba S | Numba E | Mejor |
| - | ------ | ----- | ----- | ------- | ------- | ------- | ----- |
| 1 | 70.217 | 0.92  | 0.92  | 51.965  | 1.24    | 1.24    | Numba |
| 2 | 39.678 | 1.63  | 0.82  | 32.416  | 2.00    | 1.00    | Numba |
| 4 | 23.280 | 2.78  | 0.69  | 18.847  | 3.43    | 0.86    | Numba |
| 8 | 15.464 | 4.18  | 0.52  | 12.602  | 5.13    | 0.64    | Numba |

### Local: scene.txt - large

| p | OMP T   | OMP S | OMP E | Numba T | Numba S | Numba E | Mejor |
| - | ------- | ----- | ----- | ------- | ------- | ------- | ----- |
| 1 | 581.278 | 0.92  | 0.92  | 399.574 | 1.34    | 1.34    | Numba |
| 2 | 302.865 | 1.76  | 0.88  | 261.006 | 2.05    | 1.02    | Numba |
| 4 | 175.561 | 3.04  | 0.76  | 159.330 | 3.35    | 0.84    | Numba |
| 8 | 112.857 | 4.73  | 0.59  | 102.854 | 5.19    | 0.65    | Numba |

### Local: scene_many.txt - small

| p | OMP T | OMP S | OMP E | Numba T | Numba S | Numba E | Mejor  |
| - | ----- | ----- | ----- | ------- | ------- | ------- | ------ |
| 1 | 6.308 | 0.98  | 0.98  | 5.488   | 1.13    | 1.13    | Numba  |
| 2 | 3.659 | 1.69  | 0.84  | 3.482   | 1.77    | 0.89    | Numba  |
| 4 | 2.227 | 2.77  | 0.69  | 2.049   | 3.02    | 0.75    | Numba  |
| 8 | 1.251 | 4.94  | 0.62  | 1.298   | 4.76    | 0.59    | OpenMP |

### Local: scene_many.txt - medium

| p | OMP T   | OMP S | OMP E | Numba T | Numba S | Numba E | Mejor  |
| - | ------- | ----- | ----- | ------- | ------- | ------- | ------ |
| 1 | 101.456 | 0.97  | 0.97  | 87.361  | 1.12    | 1.12    | Numba  |
| 2 | 58.990  | 1.66  | 0.83  | 56.068  | 1.75    | 0.87    | Numba  |
| 4 | 34.330  | 2.85  | 0.71  | 34.581  | 2.83    | 0.71    | OpenMP |
| 8 | 22.855  | 4.29  | 0.54  | 23.217  | 4.22    | 0.53    | OpenMP |

### Local: scene_many.txt - large

| p | OMP T   | OMP S | OMP E | Numba T | Numba S | Numba E | Mejor  |
| - | ------- | ----- | ----- | ------- | ------- | ------- | ------ |
| 1 | 796.495 | 0.98  | 0.98  | 696.564 | 1.12    | 1.12    | Numba  |
| 2 | 468.221 | 1.67  | 0.84  | 452.235 | 1.73    | 0.86    | Numba  |
| 4 | 279.796 | 2.79  | 0.70  | 284.197 | 2.75    | 0.69    | OpenMP |
| 8 | 182.725 | 4.28  | 0.53  | 185.490 | 4.22    | 0.53    | OpenMP |

En Local, Numba fue mas rapido que OpenMP en 19 de 24 puntos comparables. El cociente promedio `T_OpenMP/T_Numba` fue 1.13x. La mayor ventaja de Numba fue 1.45x en scene.txt `large` con p=1. La menor razon fue 0.96x en scene_many.txt `small` con p=8.

### Resumen a 8 threads - Local

| Escena         | Config. | Ts      | OMP T8  | OMP S8 | OMP E8 | Numba T8 | Numba S8 | Numba E8 | Mejor  |
| -------------- | ------- | ------- | ------- | ------ | ------ | -------- | -------- | -------- | ------ |
| scene.txt      | small   | 4.075   | 0.765   | 5.32   | 0.67   | 0.659    | 6.18     | 0.77     | Numba  |
| scene.txt      | medium  | 64.690  | 15.464  | 4.18   | 0.52   | 12.602   | 5.13     | 0.64     | Numba  |
| scene.txt      | large   | 533.884 | 112.857 | 4.73   | 0.59   | 102.854  | 5.19     | 0.65     | Numba  |
| scene_many.txt | small   | 6.177   | 1.251   | 4.94   | 0.62   | 1.298    | 4.76     | 0.59     | OpenMP |
| scene_many.txt | medium  | 98.010  | 22.855  | 4.29   | 0.54   | 23.217   | 4.22     | 0.53     | OpenMP |
| scene_many.txt | large   | 782.014 | 182.725 | 4.28   | 0.53   | 185.490  | 4.22     | 0.53     | OpenMP |

## Resultados paralelos completos - Cluster

### Cluster: scene.txt - small

| p | OMP T | OMP S | OMP E | Numba T | Numba S | Numba E | Mejor |
| - | ----- | ----- | ----- | ------- | ------- | ------- | ----- |
| 1 | 6.617 | 0.97  | 0.97  | 4.886   | 1.32    | 1.32    | Numba |
| 2 | 3.416 | 1.89  | 0.94  | 2.744   | 2.35    | 1.17    | Numba |
| 4 | 1.778 | 3.62  | 0.91  | 1.484   | 4.34    | 1.09    | Numba |
| 8 | 1.269 | 5.08  | 0.63  | 1.084   | 5.94    | 0.74    | Numba |

### Cluster: scene.txt - medium

| p | OMP T   | OMP S | OMP E | Numba T | Numba S | Numba E | Mejor |
| - | ------- | ----- | ----- | ------- | ------- | ------- | ----- |
| 1 | 103.303 | 0.98  | 0.98  | 73.706  | 1.37    | 1.37    | Numba |
| 2 | 52.479  | 1.92  | 0.96  | 44.085  | 2.29    | 1.15    | Numba |
| 4 | 27.837  | 3.63  | 0.91  | 23.239  | 4.35    | 1.09    | Numba |
| 8 | 19.699  | 5.13  | 0.64  | 16.977  | 5.95    | 0.74    | Numba |

### Cluster: scene.txt - large

| p | OMP T   | OMP S | OMP E | Numba T | Numba S | Numba E | Mejor |
| - | ------- | ----- | ----- | ------- | ------- | ------- | ----- |
| 1 | 822.579 | 0.99  | 0.99  | 581.332 | 1.40    | 1.40    | Numba |
| 2 | 421.544 | 1.93  | 0.96  | 352.311 | 2.30    | 1.15    | Numba |
| 4 | 219.374 | 3.70  | 0.93  | 185.739 | 4.37    | 1.09    | Numba |
| 8 | 157.145 | 5.17  | 0.65  | 135.203 | 6.00    | 0.75    | Numba |

### Cluster: scene_many.txt - small

| p | OMP T  | OMP S | OMP E | Numba T | Numba S | Numba E | Mejor |
| - | ------ | ----- | ----- | ------- | ------- | ------- | ----- |
| 1 | 11.421 | 1.00  | 1.00  | 8.166   | 1.40    | 1.40    | Numba |
| 2 | 5.732  | 1.99  | 1.00  | 4.711   | 2.43    | 1.21    | Numba |
| 4 | 3.062  | 3.73  | 0.93  | 2.596   | 4.40    | 1.10    | Numba |
| 8 | 2.380  | 4.80  | 0.60  | 2.013   | 5.68    | 0.71    | Numba |

### Cluster: scene_many.txt - medium

| p | OMP T   | OMP S | OMP E | Numba T | Numba S | Numba E | Mejor |
| - | ------- | ----- | ----- | ------- | ------- | ------- | ----- |
| 1 | 177.196 | 0.99  | 0.99  | 128.415 | 1.37    | 1.37    | Numba |
| 2 | 91.865  | 1.91  | 0.96  | 75.439  | 2.33    | 1.17    | Numba |
| 4 | 47.580  | 3.70  | 0.92  | 41.411  | 4.25    | 1.06    | Numba |
| 8 | 37.521  | 4.69  | 0.59  | 31.523  | 5.58    | 0.70    | Numba |

### Cluster: scene_many.txt - large

| p | OMP T    | OMP S | OMP E | Numba T  | Numba S | Numba E | Mejor |
| - | -------- | ----- | ----- | -------- | ------- | ------- | ----- |
| 1 | 1434.800 | 0.98  | 0.98  | 1043.959 | 1.35    | 1.35    | Numba |
| 2 | 732.822  | 1.92  | 0.96  | 613.289  | 2.29    | 1.15    | Numba |
| 4 | 381.005  | 3.69  | 0.92  | 332.149  | 4.23    | 1.06    | Numba |
| 8 | 298.016  | 4.72  | 0.59  | 252.487  | 5.57    | 0.70    | Numba |

En Cluster, Numba fue mas rapido que OpenMP en 24 de 24 puntos comparables. El cociente promedio `T_OpenMP/T_Numba` fue 1.24x. La mayor ventaja de Numba fue 1.41x en scene.txt `large` con p=1. La menor razon fue 1.15x en scene_many.txt `large` con p=4.

### Resumen a 8 threads - Cluster

| Escena         | Config. | Ts       | OMP T8  | OMP S8 | OMP E8 | Numba T8 | Numba S8 | Numba E8 | Mejor |
| -------------- | ------- | -------- | ------- | ------ | ------ | -------- | -------- | -------- | ----- |
| scene.txt      | small   | 6.443    | 1.269   | 5.08   | 0.63   | 1.084    | 5.94     | 0.74     | Numba |
| scene.txt      | medium  | 100.985  | 19.699  | 5.13   | 0.64   | 16.977   | 5.95     | 0.74     | Numba |
| scene.txt      | large   | 811.762  | 157.145 | 5.17   | 0.65   | 135.203  | 6.00     | 0.75     | Numba |
| scene_many.txt | small   | 11.424   | 2.380   | 4.80   | 0.60   | 2.013    | 5.68     | 0.71     | Numba |
| scene_many.txt | medium  | 175.809  | 37.521  | 4.69   | 0.59   | 31.523   | 5.58     | 0.70     | Numba |
| scene_many.txt | large   | 1406.140 | 298.016 | 4.72   | 0.59   | 252.487  | 5.57     | 0.70     | Numba |

La eficiencia cae al aumentar p por overhead de planificacion, barreras implicitas, sincronizacion, presion de cache y saturacion de recursos compartidos. Aunque el cluster tiene mas cores fisicos, estas corridas solo usan hasta 8 threads, por lo que no aprovechan los 20 cores fisicos completos del nodo.

## Comparacion entre computadores

La comparacion usa p=8 para las implementaciones paralelas. El cociente es `Cluster/Local`; valores mayores a 1 indican que el cluster demoro mas que el equipo local. La columna del computador de grupo queda preparada para completar despues.

### OpenMP p=8

| Escena         | Config. | Local T8 | Cluster T8 | Cluster/Local | Mas rapido actual | Grupo T8  |
| -------------- | ------- | -------- | ---------- | ------------- | ----------------- | --------- |
| scene.txt      | small   | 0.765    | 1.269      | 1.66x         | Local             | Pendiente |
| scene.txt      | medium  | 15.464   | 19.699     | 1.27x         | Local             | Pendiente |
| scene.txt      | large   | 112.857  | 157.145    | 1.39x         | Local             | Pendiente |
| scene_many.txt | small   | 1.251    | 2.380      | 1.90x         | Local             | Pendiente |
| scene_many.txt | medium  | 22.855   | 37.521     | 1.64x         | Local             | Pendiente |
| scene_many.txt | large   | 182.725  | 298.016    | 1.63x         | Local             | Pendiente |

### Numba p=8

| Escena         | Config. | Local T8 | Cluster T8 | Cluster/Local | Mas rapido actual | Grupo T8  |
| -------------- | ------- | -------- | ---------- | ------------- | ----------------- | --------- |
| scene.txt      | small   | 0.659    | 1.084      | 1.65x         | Local             | Pendiente |
| scene.txt      | medium  | 12.602   | 16.977     | 1.35x         | Local             | Pendiente |
| scene.txt      | large   | 102.854  | 135.203    | 1.31x         | Local             | Pendiente |
| scene_many.txt | small   | 1.298    | 2.013      | 1.55x         | Local             | Pendiente |
| scene_many.txt | medium  | 23.217   | 31.523     | 1.36x         | Local             | Pendiente |
| scene_many.txt | large   | 185.490  | 252.487    | 1.36x         | Local             | Pendiente |

En estas mediciones el equipo local fue mas rapido en todos los puntos p=8, pese a tener menos cores fisicos. Esto es plausible porque la comparacion limita p a 8, no a la capacidad total del cluster; ademas, el Xeon Silver 4210R tiene menor frecuencia base y el trabajo puede depender de rendimiento por thread, cache, politicas de frecuencia, contencion del nodo y overhead del entorno. El cluster sigue siendo valido como segundo computador porque entrega otra arquitectura y otra configuracion de cores/threads para comparar.

## Espacio para computador adicional del grupo

Completar esta seccion cuando otro integrante ejecute `python3 src/run_experiments.py --full --reps 1 --pdf --outdir "results/full_grupo_<nombre>"`. No inventar valores: copiar desde su `hardware.json` y `results.csv`.

### Hardware pendiente

| Dato                 | Valor            |
| -------------------- | ---------------- |
| Integrante           | ________________ |
| Procesador           | ________________ |
| Cores fisicos        | ________________ |
| Threads logicos      | ________________ |
| Threads por core     | ________________ |
| Frecuencia / max MHz | ________________ |
| Sistema operativo    | ________________ |

### Resultados seriales pendientes

| Escena         | Config. | serial.cpp | serial_pt.cpp |
| -------------- | ------- | ---------- | ------------- |
| scene.txt      | small   | ____       | ____          |
| scene.txt      | medium  | ____       | ____          |
| scene.txt      | large   | ____       | ____          |
| scene_many.txt | small   | ____       | ____          |
| scene_many.txt | medium  | ____       | ____          |
| scene_many.txt | large   | ____       | ____          |

### OpenMP y Numba p=8 pendientes

| Escena         | Config. | OMP T8 | OMP S8 | OMP E8 | Numba T8 | Numba S8 | Numba E8 | Mejor |
| -------------- | ------- | ------ | ------ | ------ | -------- | -------- | -------- | ----- |
| scene.txt      | small   | ____   | ____   | ____   | ____     | ____     | ____     | ____  |
| scene.txt      | medium  | ____   | ____   | ____   | ____     | ____     | ____     | ____  |
| scene.txt      | large   | ____   | ____   | ____   | ____     | ____     | ____     | ____  |
| scene_many.txt | small   | ____   | ____   | ____   | ____     | ____     | ____     | ____  |
| scene_many.txt | medium  | ____   | ____   | ____   | ____     | ____     | ____     | ____  |
| scene_many.txt | large   | ____   | ____   | ____   | ____     | ____     | ____     | ____  |

### Comparacion pendiente con Local y Cluster

- Diferencias mas notables: ________________________________________________
- Posibles causas: _________________________________________________________
- Efecto de cores/threads/frecuencia/cache: _______________________________

## Graficos

Los graficos siguientes fueron generados por el mismo script desde cada `results.csv`.

### Local

![Local: Scheduling scene.txt](local/plots/schedule_scene.png)

![Local: Scheduling scene_many.txt](local/plots/schedule_scene_many.png)

### Local - scene.txt small

![Local: Tiempo scene.txt small](local/plots/time_scene_small.png)

![Local: Speedup scene.txt small](local/plots/speedup_scene_small.png)

![Local: Eficiencia scene.txt small](local/plots/efficiency_scene_small.png)

### Local - scene.txt medium

![Local: Tiempo scene.txt medium](local/plots/time_scene_medium.png)

![Local: Speedup scene.txt medium](local/plots/speedup_scene_medium.png)

![Local: Eficiencia scene.txt medium](local/plots/efficiency_scene_medium.png)

### Local - scene.txt large

![Local: Tiempo scene.txt large](local/plots/time_scene_large.png)

![Local: Speedup scene.txt large](local/plots/speedup_scene_large.png)

![Local: Eficiencia scene.txt large](local/plots/efficiency_scene_large.png)

### Local - scene_many.txt small

![Local: Tiempo scene_many.txt small](local/plots/time_scene_many_small.png)

![Local: Speedup scene_many.txt small](local/plots/speedup_scene_many_small.png)

![Local: Eficiencia scene_many.txt small](local/plots/efficiency_scene_many_small.png)

### Local - scene_many.txt medium

![Local: Tiempo scene_many.txt medium](local/plots/time_scene_many_medium.png)

![Local: Speedup scene_many.txt medium](local/plots/speedup_scene_many_medium.png)

![Local: Eficiencia scene_many.txt medium](local/plots/efficiency_scene_many_medium.png)

### Local - scene_many.txt large

![Local: Tiempo scene_many.txt large](local/plots/time_scene_many_large.png)

![Local: Speedup scene_many.txt large](local/plots/speedup_scene_many_large.png)

![Local: Eficiencia scene_many.txt large](local/plots/efficiency_scene_many_large.png)

### Cluster

![Cluster: Scheduling scene.txt](cluster/plots/schedule_scene.png)

![Cluster: Scheduling scene_many.txt](cluster/plots/schedule_scene_many.png)

### Cluster - scene.txt small

![Cluster: Tiempo scene.txt small](cluster/plots/time_scene_small.png)

![Cluster: Speedup scene.txt small](cluster/plots/speedup_scene_small.png)

![Cluster: Eficiencia scene.txt small](cluster/plots/efficiency_scene_small.png)

### Cluster - scene.txt medium

![Cluster: Tiempo scene.txt medium](cluster/plots/time_scene_medium.png)

![Cluster: Speedup scene.txt medium](cluster/plots/speedup_scene_medium.png)

![Cluster: Eficiencia scene.txt medium](cluster/plots/efficiency_scene_medium.png)

### Cluster - scene.txt large

![Cluster: Tiempo scene.txt large](cluster/plots/time_scene_large.png)

![Cluster: Speedup scene.txt large](cluster/plots/speedup_scene_large.png)

![Cluster: Eficiencia scene.txt large](cluster/plots/efficiency_scene_large.png)

### Cluster - scene_many.txt small

![Cluster: Tiempo scene_many.txt small](cluster/plots/time_scene_many_small.png)

![Cluster: Speedup scene_many.txt small](cluster/plots/speedup_scene_many_small.png)

![Cluster: Eficiencia scene_many.txt small](cluster/plots/efficiency_scene_many_small.png)

### Cluster - scene_many.txt medium

![Cluster: Tiempo scene_many.txt medium](cluster/plots/time_scene_many_medium.png)

![Cluster: Speedup scene_many.txt medium](cluster/plots/speedup_scene_many_medium.png)

![Cluster: Eficiencia scene_many.txt medium](cluster/plots/efficiency_scene_many_medium.png)

### Cluster - scene_many.txt large

![Cluster: Tiempo scene_many.txt large](cluster/plots/time_scene_many_large.png)

![Cluster: Speedup scene_many.txt large](cluster/plots/speedup_scene_many_large.png)

![Cluster: Eficiencia scene_many.txt large](cluster/plots/efficiency_scene_many_large.png)

## Archivos de respaldo

- Resultados locales completos: `results/final/local/results.csv`, `hardware.json`, `report.md`, `report.pdf` y `plots/`.
- Resultados cluster completos: `results/final/cluster/results.csv`, `hardware.json`, `report.md`, `report.pdf`, logs `slurm_2289.out` y `slurm_2289.err`, y `plots/`.
- Informe con espacio para grupo: `results/final/informe_entrega_grupo.md` y `results/final/informe_entrega_grupo.pdf`.
