# Registro del modelo

> Resultado de `notebooks/08_registro_modelo.ipynb`. Datos en `reports/08_registro.json`.
>
> **Cifras vigentes:** registro del 31-oct-2026 con la nueva numeración de clientes (ver `reports/07_validacion.md`,
> sección 0). La versión del 30-oct, con XGBoost, está en el historial de git (commit `e026f23`).

## 1. Dónde quedó registrado

| Dato | Valor |
|---|---|
| Plataforma | ☐ Databricks  ☒ **MLflow local** (`mlflow_local.db`) → motivo: decisión del grupo, aprobado por el profesor el 3-nov-2026. El código conserva la opción de Databricks (`src/proyecto/tracking/mlflow_utils.py`), pero no se usa. |
| Experimento | `libranzaradar-08-registro` |
| Nombre del modelo registrado | `libranzaradar_mora30` |
| Versión | 1 |
| Alias | `champion` |
| Quién lo registró y cuándo | _(completar: integrante)_ · 31-oct-2026 11:40 (run `309f85c4e934454f838ea98d449953f4`) |

## 2. Qué se registró junto al modelo

- **Parámetros:** algoritmo (LightGBM), origen de los parámetros (partida), calibrado (no), umbral (0,300989) y los 7 hiperparámetros.
- **Métricas de la prueba:** `test_recall` 0,000, `test_precision` 0,000, `test_pr_auc` 0,193, `test_auc` 0,544, `test_flag_rate` 0,0005. El recall es 0 porque el umbral congelado casi no marca créditos (`reports/07_validacion.md`, sección 0).
- **Firma y ejemplo de entrada:** 12 columnas crudas: `term_months`, `loan_amount`, `monthly_installment`, `interest_rate_ea`, `due_day`, `has_guarantee`, `guarantee_value`, `has_cosigner` (numéricas) y `product`, `business_type`, `economic_destination`, `city` (texto). Salida: probabilidad de cada clase. Se guardan 5 filas de ejemplo.
- **Etiquetas:** `etapa=08_registro`, `caso=libranzaradar`, `objetivo=mora_30`, `particion=por cliente (client_id)`, `prueba_abierta=3 veces` (corregida; ver el punto siguiente). También se adjunta `decisiones_congeladas.json`.
- **Etiqueta corregida (3-nov-2026):** el notebook 08 escribía fijo `prueba_abierta=una vez`, pero la prueba se abrió **tres veces** (`reports/prueba_abierta.txt`). Se corrigió sin volver a registrar el modelo: con `MlflowClient.set_tag` se cambió la etiqueta de la ejecución ya registrada (run `309f85c4…`) y se agregó a la versión 1 del modelo, con el valor `3 veces (ver reports/07_validacion.md, sección 0)`. La ejecución también lleva `prueba_abierta_corregida` para que el cambio quede visible. La celda 3 ahora cuenta las aperturas del archivo, así que una ejecución futura escribirá el número correcto. No se volvió a ejecutar el notebook: crearía una versión 2 y obligaría a correr el 09, que vuelve a medir con la prueba.
- **Formato:** `cloudpickle` (el pipeline incluye LightGBM y transformaciones de scikit-learn que `skops` no acepta). Solo se cargan modelos propios: `MLFLOW_ALLOW_PICKLE_DESERIALIZATION=true` se activa en los notebooks 08 y 09, nunca para modelos de terceros.

## 3. Comprobación de ida y vuelta

- ¿El modelo recuperado del registro predice igual que el local? ☒ sí  ☐ no
- **Cómo se comprobó:** se cargó `models:/libranzaradar_mora30@champion` y se comparó su `predict_proba` con el del pipeline local en 500 filas de la prueba. Diferencia máxima: **0,0**. *(Cambio del 3-nov-2026: la celda 5 ahora hace esta comprobación con 500 filas del **entrenamiento**, para que el notebook 08 no lea la prueba. El código no se volvió a ejecutar; el 0,0 de arriba es de la ejecución del 31-oct.)* En el notebook 09, `models/model.joblib` (exportado desde el registro) reproduce exactamente el recall de la prueba (0,000000, igual que en la etapa 7).

## 4. Tracking frente a registro

- **Tracking:** guarda **cada experimento**: las 6 variantes de variables (etapa 4), los 6 candidatos del torneo (etapa 5) y los 50 ensayos de Optuna con todas sus métricas (etapa 6). Lo usamos para comparar, ordenar por cualquier métrica y demostrar que la optimización no mejoró.
- **Registro:** guarda **el modelo elegido**, versionado, con su firma, métricas y decisiones. El alias `champion` hace que la app y el notebook 09 pidan "el modelo en producción" sin conocer el número de versión: si mañana se registra una versión 2 mejor, basta con mover el alias.

## 5. Reproducibilidad

- ¿Alguien de otro grupo podría recuperar el modelo con lo que dejamos escrito? ☒ sí  ☐ no — el modelo exportado está en `models/model.joblib` con su esquema (`models/input_schema.json`), y todo el flujo se regenera desde la base cruda con los notebooks 03–09 (instrucciones en el README). El registro local (`mlflow_local.db`) no se sube al repo: quien quiera ver el registro debe regenerarlo con los notebooks, o el grupo lo muestra en su computador con `mlflow ui`.
