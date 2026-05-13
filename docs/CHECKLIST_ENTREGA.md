# Checklist de entrega

## Experimentos

- [ ] Corrida local completa terminada.
- [ ] Corrida cluster completa terminada.
- [ ] `results.csv` local revisado.
- [ ] `results.csv` cluster revisado.
- [ ] `hardware.json` local revisado.
- [ ] `hardware.json` cluster revisado.
- [ ] Graficos generados y legibles.

## Pauta

- [ ] Ambas escenas: `scene.txt` y `scene_many.txt`.
- [ ] Configuraciones `small`, `medium` y `large`.
- [ ] Serial RT y serial PT medidos.
- [ ] OpenMP medido con `p = 1, 2, 4, 8`.
- [ ] Barrido `static`, `dynamic` y `guided`.
- [ ] Numba medido con `p = 1, 2, 4, 8`.
- [ ] Speedup calculado.
- [ ] Eficiencia calculada.
- [ ] Segundo computador declarado.

## Informe

- [ ] Se declara uso de IA.
- [ ] Se declaran cores fisicos, threads logicos y frecuencia del computador local.
- [ ] Se declaran cores fisicos, threads logicos y frecuencia del cluster.
- [ ] Se explica el crecimiento al duplicar resolucion.
- [ ] Se explica el crecimiento al duplicar `N`.
- [ ] Se identifica el mejor schedule por escena.
- [ ] Se explica la irregularidad del trabajo por pixel.
- [ ] Se compara OpenMP vs Numba.
- [ ] Se comenta desde donde cae la eficiencia.
- [ ] Se comparan las diferencias entre local y cluster.
- [ ] El PDF final abre correctamente.

## GitHub

- [ ] No hay binarios compilados.
- [ ] No hay caches de Python/Numba.
- [ ] No hay resultados generados accidentalmente.
- [ ] No hay contrasenas ni secretos.
- [ ] `README.md` explica como reproducir.
- [ ] `docs/USO_CLUSTER.md` explica como correr en cluster.
