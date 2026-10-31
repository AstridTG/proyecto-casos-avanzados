# Informe de la optimización

> Resultado de `notebooks/06_optimizacion.ipynb`. La mejor puntuación de una búsqueda es **optimista**: se comprueba
> en clientes que la búsqueda no vio.

## Diseño de la búsqueda

- **Finalistas optimizados:** XGBoost y LightGBM (`reports/05_torneo.md`).
- **Espacio de búsqueda:** pensado para una señal débil: árboles pequeños, hojas con muchos créditos y regularización, para no memorizar ruido.

| Parámetro | Rango | Motivo |
|---|---|---|
| `n_estimators` | 100–600 | Con tasa baja hacen falta más árboles; más de 600 no cambia con esta señal |
| `learning_rate` | 0,005–0,1 (log) | Tasas bajas suavizan el ajuste |
| `num_leaves` (LightGBM) / `max_depth` (XGBoost) | 4–31 / 2–6 | Árboles poco profundos: pocas interacciones reales |
| `min_child_samples` / `min_child_weight` | 50–800 / 5–200 (log) | Hojas con muchos créditos: estimaciones de mora estables |
| `subsample`, `colsample_bytree` | 0,5–1,0 / 0,4–1,0 | Aleatoriedad que reduce la varianza |
| `reg_lambda` | 0,001–30 (log) | Penaliza hojas extremas |

- **Presupuesto:** 30 ensayos para LightGBM y 20 para XGBoost, fijados antes de empezar (≈ 10 s por ensayo con 5 pliegues: ~10 minutos en total). Con 7 parámetros y una señal plana, más ensayos solo agregan oportunidades de ganar por azar.
- **Objetivo:** PR-AUC de la mora en 5 pliegues por cliente (la métrica de negocio es demasiado ruidosa para guiar una búsqueda; ver `reports/04_features.md`).
- **Clientes reservados:** 20 % de los clientes de entrenamiento (7.372 créditos), `GroupShuffleSplit` por cliente, semilla 42. La búsqueda usa el 80 % restante.

## Seguimiento (tracking)

- **Dónde quedó registrado:** MLflow **local** (`mlflow_local.db`), experimento `libranzaradar-06-optimizacion`. El código usa Databricks automáticamente si `.env` tiene credenciales (`src/proyecto/tracking/mlflow_utils.py`); esta corrida se hizo sin credenciales del grupo. **Pendiente del grupo:** volver a correr los notebooks 05, 06 y 08 con `.env` configurado para que queden en Databricks.
- **¿Está cada ensayo como una ejecución con parámetros, métrica y etiquetas?** ☒ sí ☐ no — 50 ejecuciones anidadas bajo `optuna-lightgbm` y `optuna-xgboost` (52 en total), cada una con todas las métricas de negocio y técnicas (media y desviación entre pliegues) y las etiquetas `etapa`, `modelo` y `metrica_optimizada`.
- **Mejor ejecución:** LightGBM, ensayo 21, PR-AUC 0,1851 en la búsqueda (optimista). XGBoost: 0,1841.

## Resultados de la búsqueda

- El rango de PR-AUC entre todos los ensayos fue estrecho: 0,173–0,185 (LightGBM) y 0,173–0,184 (XGBoost). La diferencia entre el mejor y el peor ensayo es del orden del ruido entre pliegues (± 0,003–0,005).
- Los mejores ensayos prefieren árboles muy pequeños (LightGBM: 4 hojas; XGBoost: profundidad 3), tasas de aprendizaje bajas y poca proporción de columnas: es decir, **modelos casi lineales en el plazo**, coherente con el EDA.

## Comprobación honesta (clientes reservados)

> Cada modelo se entrena con el 80 % de búsqueda y se evalúa en el 20 % reservado. Intervalo del 95 % remuestreando **clientes completos** (500 repeticiones).

| Modelo | PR-AUC con parámetros de partida | PR-AUC con parámetros optimizados | Diferencia (optimizado − partida) | Intervalo 95 % |
|---|---|---|---|---|
| XGBoost | 0,1806 | 0,1827 | +0,0020 | [−0,0042 ; 0,0081] |
| LightGBM | 0,1787 | 0,1805 | +0,0018 | [−0,0048 ; 0,0093] |

**Regla de decisión escrita antes de mirar:** se adoptan los parámetros optimizados solo si el intervalo del 95 % de la diferencia queda **entero por encima de 0**.

**Resultado de la regla:** en ambos modelos el intervalo incluye el 0. La mejora de la búsqueda **no se distingue del ruido**.

## Decisión

- **Parámetros que se usarán a partir de ahora:** los **de partida de XGBoost** (300 árboles, tasa 0,03, profundidad 4, `min_child_weight` 20, `subsample` 0,8, `colsample_bytree` 0,8). XGBoost es el finalista con mejor PR-AUC en los reservados; los de partida, porque la optimización no demostró mejora (`reports/06_eleccion.json`).
- **Lo que no pudimos concluir:** si con más datos o variables nuevas la optimización ayudaría. Con esta señal, el límite lo ponen los datos, no los hiperparámetros.

## Para la clase siguiente

XGBoost con parámetros de partida pasa a la validación (prueba abierta una sola vez) y al registro.
