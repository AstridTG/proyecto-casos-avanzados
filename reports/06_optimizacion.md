# Informe de la optimización

> Resultado de `notebooks/06_optimizacion.ipynb`. La mejor puntuación de una búsqueda es **optimista**: se comprueba
> en clientes que la búsqueda no vio.
>
> **Cifras vigentes:** ejecución del 31-oct-2026 con la nueva numeración de clientes (ver `reports/07_validacion.md`,
> sección 0). La versión del 30-oct, con la partición anterior, está en el historial de git (commit `e026f23`).

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
- **Clientes reservados:** 20 % de los clientes de entrenamiento (7.404 créditos de 5.545 clientes), `GroupShuffleSplit` por cliente, semilla 42. La búsqueda usa el 80 % restante.

## Seguimiento (tracking)

- **Dónde quedó registrado:** MLflow **local** (`mlflow_local.db`), experimento `libranzaradar-06-optimizacion`. El código usa Databricks automáticamente si `.env` tiene credenciales (`src/proyecto/tracking/mlflow_utils.py`); esta corrida se hizo sin credenciales del grupo. **Pendiente del grupo:** volver a correr los notebooks 05, 06 y 08 con `.env` configurado para que queden en Databricks.
- **¿Está cada ensayo como una ejecución con parámetros, métrica y etiquetas?** ☒ sí ☐ no — 50 ejecuciones anidadas bajo `optuna-lightgbm` y `optuna-xgboost` (52 en total), cada una con todas las métricas de negocio y técnicas (media y desviación entre pliegues) y las etiquetas `etapa`, `modelo` y `metrica_optimizada`.
- **Mejor ejecución:** empate. LightGBM (ensayo 22) y XGBoost (ensayo 16) llegan a PR-AUC 0,1787 en la búsqueda (optimista).

## Resultados de la búsqueda

- El rango de PR-AUC entre todos los ensayos fue estrecho: 0,166–0,179 (LightGBM) y 0,169–0,179 (XGBoost) (`reports/06_optimizacion_tabla.csv`). La diferencia entre el mejor y el peor ensayo es del orden del ruido entre pliegues (± 0,004–0,005 en los mejores).
- Los parámetros optimizados que se comprobaron (`reports/06_mejores_parametros.json`) son árboles muy pequeños (LightGBM: 8 hojas con al menos 529 créditos por hoja; XGBoost: profundidad 2), con tasas de aprendizaje bajas y poca proporción de columnas: es decir, **modelos casi lineales en el plazo**, coherente con el EDA.

## Comprobación honesta (clientes reservados)

> Cada modelo se entrena con el 80 % de búsqueda y se evalúa en el 20 % reservado. Intervalo del 95 % remuestreando **clientes completos** (500 repeticiones).

| Modelo | PR-AUC con parámetros de partida | PR-AUC con parámetros optimizados | Diferencia (optimizado − partida) | Intervalo 95 % |
|---|---|---|---|---|
| XGBoost | 0,1705 | 0,1736 | +0,0030 | [−0,0028 ; 0,0089] |
| LightGBM | 0,1710 | 0,1738 | +0,0027 | [−0,0035 ; 0,0098] |

**Regla de decisión escrita antes de mirar:** se adoptan los parámetros optimizados solo si el intervalo del 95 % de la diferencia queda **entero por encima de 0**.

**Resultado de la regla:** en ambos modelos el intervalo incluye el 0. La mejora de la búsqueda **no se distingue del ruido**.

## Decisión

- **Parámetros que se usarán a partir de ahora:** los **de partida de LightGBM** (300 árboles, tasa 0,03, 15 hojas, `min_child_samples` 100, `subsample` 0,8, `colsample_bytree` 0,8, `reg_lambda` 1,0) (`reports/06_eleccion.json`).
- **Por qué LightGBM:** la regla de la celda 8, escrita antes de abrir la prueba, toma al finalista con mayor PR-AUC en los reservados **con los parámetros que se usarán** (aquí, los de partida). LightGBM gana por **0,0005** (0,1710 frente a 0,1705), una diferencia unas 12 veces menor que el ruido (± 0,006): **es un empate** y la regla lo desempata.
- **Por qué los de partida:** la optimización no demostró mejora en ninguno de los dos modelos.
- **Corrección de la regla (3-nov-2026):** la celda 8 comparaba el mayor PR-AUC entre parámetros de partida y optimizados, aunque después usara los de partida. Ahora compara el PR-AUC de los parámetros que de verdad se usarán. Se volvió a ejecutar el notebook 06, que solo usa el entrenamiento y carga las búsquedas de Optuna ya guardadas, sin ensayos nuevos. **Todos sus archivos salieron idénticos** y la elección no cambió: LightGBM con parámetros de partida.
- **Lo que no pudimos concluir:** si con más datos o variables nuevas la optimización ayudaría. Con esta señal, el límite lo ponen los datos, no los hiperparámetros.

## Para la clase siguiente

LightGBM con parámetros de partida pasa a la validación y al registro. La prueba se abrió por tercera vez con esta ejecución; ver `reports/07_validacion.md`, sección 0.
