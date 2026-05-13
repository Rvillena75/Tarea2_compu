# Resultados

Esta carpeta esta pensada para guardar solo resultados finales curados para el
grupo. Las corridas temporales siguen ignoradas por Git.

Estructura sugerida:

```text
results/final/local/
results/final/cluster/
```

Cada carpeta final deberia contener:

- `results.csv`
- `hardware.json`
- `report.md`
- `report.pdf`, si se genero
- `plots/*.png`
- logs Slurm relevantes en el caso del cluster

No subir imagenes `.ppm` de cada render salvo que se necesiten explicitamente
para el informe.

## Descargar resultados del cluster

Cuando termine el job completo:

```bash
mkdir -p results/final/cluster
rsync -av \
  grupo40-iic3533@kraken.ing.puc.cl:~/Tarea2_compu/src/results/full_cluster_<JOBID>/ \
  results/final/cluster/
```

Para logs:

```bash
rsync -av \
  grupo40-iic3533@kraken.ing.puc.cl:~/Tarea2_compu/src/results/slurm_<JOBID>.* \
  results/final/cluster/
```

## Copiar resultados locales finales

Cuando exista una corrida local final:

```bash
mkdir -p results/final/local
rsync -av results/full_local_<STAMP>/ results/final/local/
```

Luego revisar:

```bash
find results/final -maxdepth 3 -type f -print
```
