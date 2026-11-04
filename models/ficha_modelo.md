# Ficha del modelo · LibranzaRadar `libranzaradar_mora30`

> **Resumen honesto:** con la información disponible al aprobar, el modelo **no supera** a la regla simple del plazo
> corto. Con su regla de decisión congelada casi nunca prioriza un crédito (0,1 %). **Para priorizar el seguimiento se
> recomienda la regla del plazo corto (plazo ≤ 6 meses).**

## Qué es

Estima la probabilidad de que un crédito de libranza recién aprobado caiga en **más de 30 días de mora**, para que el analista de crédito decida a cuáles dar **revisión y seguimiento prioritario** con la empresa pagadora. No aprueba ni niega créditos.

- **Modelo:** LightGBM (300 árboles, tasa 0,03, 15 hojas, `min_child_samples` 100, `subsample` 0,8, `colsample_bytree` 0,8, `reg_lambda` 1,0) dentro de un `Pipeline` de scikit-learn con imputación y codificación. Parámetros de partida: la optimización con Optuna no mejoró de forma distinguible en clientes reservados. Sin calibración (ya estaba calibrado).
- **Por qué LightGBM:** la regla de elección, escrita antes de abrir la prueba, toma al finalista con mayor PR-AUC en clientes reservados. LightGBM y XGBoost **empataron** (0,1710 frente a 0,1705, con un ruido de ±0,006). Ver `reports/07_validacion.md`, sección 0.
- **Registro:** `libranzaradar_mora30` versión 1, alias `champion` (MLflow local, aprobado por el profesor el 3-nov-2026; no se usa Databricks).
- **Regla de decisión congelada:** priorizar si la probabilidad es **≥ 0,3010**. Era el único umbral con precisión ≥ 20 % en las predicciones fuera de pliegue del entrenamiento, pero **ya ahí marcaba solo el 0,1 % de los créditos** (recall 0,001). En la práctica, no prioriza.

## Datos de entrenamiento

- **Fuente y licencia:** base **sintética** de cartera de libranza generada para el curso (uso académico).
- **Tamaño:** 36.872 créditos de 27.725 clientes (entrenamiento) y 9.178 créditos de 6.932 clientes (prueba). Vienen de 46.050 créditos tras excluir 3.619 con condiciones reescritas después de la mora y 10.331 con menos de 4 meses de vida.
- **Partición:** por **cliente** (`GroupShuffleSplit` 80/20, semilla 42; validación con `StratifiedGroupKFold`). `check_split_reproducibility` comprueba que cada integrante obtiene la misma partición.
- **Aperturas de la prueba:** **tres**. Dos el 30-oct con la partición anterior y una el 31-oct, al regenerar el proyecto con la nueva numeración de clientes. La prueba vigente es otro grupo de clientes y parte de los clientes de la prueba anterior quedó en entrenamiento. Detalle en `reports/07_validacion.md`, sección 0.
- **Datos personales:** se eliminan al cargar 49 columnas (nombres, documentos, direcciones, teléfonos, codeudores). El cliente se reemplaza por un número de cliente (`c00001`...) que no se calcula a partir del documento y solo sirve para agrupar.

## Rendimiento (prueba vigente: clientes nunca vistos, mora real 16,3 %)

| Métrica | LightGBM | Regla del plazo corto (plazo ≤ 6 meses) | Modelo − regla [IC 95 %] |
|---|---|---|---|
| **Recall de la mora** (métrica principal) | **0,000** [0,000 ; 0,000] | 0,134 [0,116 ; 0,151] | −0,134 [−0,151 ; −0,116] |
| Precisión (exigida ≥ 0,20) | 0,000 | 0,242 [0,212 ; 0,271] | — |
| PR-AUC | 0,193 [0,180 ; 0,208] | 0,186 [0,174 ; 0,198] | +0,007 [−0,001 ; +0,016] |
| AUC | 0,544 [0,527 ; 0,560] | 0,537 [0,520 ; 0,553] | +0,007 [−0,008 ; +0,024] |
| % de créditos marcados | 0,1 % | 9,0 % | — |

- **Con su regla de decisión, el modelo es claramente peor que la regla del plazo corto:** no detecta ninguna mora.
- **Como puntaje para ordenar** (PR-AUC y AUC), el modelo y la regla **empatan**: los intervalos de la diferencia incluyen el cero.

## Variables que más pesan

Plazo, cuota mensual, monto, tasa efectiva anual y valor de la garantía (SHAP). Entre más corto el plazo, mayor la probabilidad estimada.

## Límites y usos no recomendados

- **No usar su regla de decisión para priorizar:** casi nunca marca un crédito. Si se usa el modelo, que sea solo para ordenar la cola de revisión, sabiendo que ordena igual que el plazo.
- **Datos sintéticos:** los patrones pueden no parecerse a los de una cartera real. **No usar con clientes reales** sin volver a entrenar y validar con datos reales.
- **Supuestos de negocio:** solo usa información conocida al aprobar. El objetivo es la mora **a la fecha de corte** (30-oct-2026), así que los créditos tuvieron tiempos de exposición distintos (4 meses a varios años).
- **Atributos sensibles:** no usa sexo, estado civil ni edad. Usa la ciudad, que puede actuar como aproximación de condiciones socioeconómicas: vigilar las tasas de marcado por ciudad.
- **Qué no debe hacerse:** aprobar o negar créditos, fijar tasas o montos, cobrar distinto o tratar peor a un cliente por su puntaje. La decisión final es del analista.
- **Lo que no se evaluó:** estabilidad en el tiempo (no hubo validación por cohortes futuras), deriva de datos y desempeño en otras cajas de compensación.

## Reproducibilidad

Código en `src/`, pruebas en `tests/` (`pytest`), notebooks 01–09 en `notebooks/`. Python 3.12, scikit-learn 1.9.1, LightGBM 4.7.0, MLflow 3.17.1 (`requirements.txt`). Esquema de entrada: `models/input_schema.json`.
