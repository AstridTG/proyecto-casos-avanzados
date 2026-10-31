# Ficha del modelo · LibranzaRadar `libranzaradar_mora30`

## Qué es

Estima la probabilidad de que un crédito de libranza recién aprobado caiga en **más de 30 días de mora**, para que el analista de crédito decida a cuáles dar **revisión y seguimiento prioritario** con la empresa pagadora. No aprueba ni niega créditos.

- **Modelo:** XGBoost (300 árboles, tasa 0,03, profundidad 4, `min_child_weight` 20, `subsample` 0,8, `colsample_bytree` 0,8) dentro de un `Pipeline` de scikit-learn con imputación y codificación. Sin calibración (ya estaba calibrado).
- **Registro:** `libranzaradar_mora30` versión 1, alias `champion` (MLflow local; pendiente de registrar en Databricks).
- **Regla de decisión:** priorizar si la probabilidad es **≥ 0,1927**. Ese umbral daba el mayor recall con precisión ≥ 20 % en validación cruzada por cliente.

## Datos de entrenamiento

- **Fuente y licencia:** base **sintética** de cartera de libranza generada para el curso (uso académico).
- **Tamaño:** 36.857 créditos de 27.725 clientes (entrenamiento) y 9.193 créditos de 6.932 clientes (prueba). Vienen de 46.050 créditos tras excluir 3.619 con condiciones reescritas después de la mora y 10.331 con menos de 4 meses de vida.
- **Partición:** por **cliente** (`GroupShuffleSplit` 80/20, semilla 42; validación con `StratifiedGroupKFold`). La prueba se abrió una sola vez (con una reejecución declarada por un error de código; ver `reports/07_validacion.md`).
- **Datos personales:** se eliminan al cargar 49 columnas (nombres, documentos, direcciones, teléfonos, codeudores). El cliente se reemplaza por un número de cliente (`c00001`...) que no se calcula a partir del documento y solo sirve para agrupar.

## Rendimiento (prueba: clientes nunca vistos)

| Métrica | Valor | Intervalo del 95 % (clientes) |
|---|---|---|
| **Recall de la mora** (métrica principal, umbral 0,1927) | 0,149 | [0,130 ; 0,167] |
| Precisión (exigida ≥ 0,20) | 0,192 | [0,169 ; 0,214] |
| Baseline: regla del plazo corto (plazo ≤ 9 meses), recall | 0,154 | [0,135 ; 0,172] |
| Diferencia de recall, modelo − regla | −0,006 | [−0,020 ; +0,010] |
| AUC | 0,527 | [0,509 ; 0,544] |
| PR-AUC (tasa base: 0,153) | 0,171 | [0,159 ; 0,184] |
| % de créditos marcados | 11,8 % | — |

**El modelo no supera a la regla del plazo corto.** Ambos detectan ~15 % de las moras revisando ~12 % de los créditos.

## Variables que más pesan

Plazo, cuota mensual, monto, tasa efectiva anual y valor de la garantía (SHAP). Entre más corto el plazo, mayor la probabilidad estimada.

## Límites y usos no recomendados

- **Datos sintéticos:** los patrones pueden no parecerse a los de una cartera real. **No usar con clientes reales** sin volver a entrenar y validar con datos reales.
- **Supuestos de negocio:** solo usa información conocida al aprobar. El objetivo es la mora **a la fecha de corte** (30-oct-2026), así que los créditos tuvieron tiempos de exposición distintos (4 meses a varios años).
- **Atributos sensibles:** no usa sexo, estado civil ni edad. Usa la ciudad, que puede actuar como aproximación de condiciones socioeconómicas: vigilar las tasas de marcado por ciudad.
- **Qué no debe hacerse:** aprobar o negar créditos, fijar tasas o montos, cobrar distinto o tratar peor a un cliente por su puntaje. La decisión final es del analista.
- **Lo que no se evaluó:** estabilidad en el tiempo (no hubo validación por cohortes futuras), deriva de datos y desempeño en otras cajas de compensación.

## Reproducibilidad

Código en `src/`, pruebas en `tests/` (`pytest`), notebooks 01–09 en `notebooks/`. Python 3.12, scikit-learn 1.9.1, XGBoost 3.4.1, MLflow 3.17.1 (`requirements.txt`). Esquema de entrada: `models/input_schema.json`.
