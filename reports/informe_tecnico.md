# Informe técnico — LibranzaRadar

> **Regla del informe:** cada decisión va con su motivo. Las secciones detalladas están en `reports/00_caso.md` a `reports/09_despliegue.md`.

**Grupo:** _(completar integrantes y roles)_ · **Repositorio:** _(completar)_ · **App:** _(completar enlace público)_

## Resumen ejecutivo

LibranzaRadar quería que el analista de crédito supiera, **al aprobar** un crédito de libranza, cuáles tienen más probabilidad de caer en más de 30 días de mora, para priorizar su seguimiento con la empresa pagadora. Construimos el flujo completo: limpieza reproducible, partición por cliente, torneo de 5 modelos, optimización con seguimiento en MLflow, validación con la prueba abierta una sola vez, registro con alias `champion` y una app en Streamlit.

**Resultado:** con la información disponible al aprobar, la base sintética casi no permite anticipar la mora. El mejor modelo (XGBoost) detecta el **14,9 %** de las moras (IC 95 % [13,0 ; 16,7]) revisando el 11,8 % de los créditos, con precisión del 19,2 %. Eso es lo mismo que la regla simple "plazo ≤ 9 meses": diferencia de −0,6 puntos (IC [−2,0 ; +1,0]). En el mes típico (≈ 380 moras), ambos detectan ≈ 57. **Recomendamos priorizar con la regla del plazo corto** y capturar mejores datos al aprobar. El modelo y la app quedan listos para reentrenar cuando esos datos existan.

## 1. Caso de negocio

> Fuente: `reports/00_caso.md`.

- **Quién decide y qué:** el analista de crédito decide a qué créditos aprobados dar revisión y seguimiento prioritario. Conserva la decisión final.
- **Con qué información:** solo la conocida el día de la aprobación. **Motivo:** en ese momento se toma la decisión; usar saldos o pagos posteriores sería hacer trampa.
- **Costo del error:** el falso negativo (mora no detectada) es el más caro. **Métrica principal:** recall de la mora con **precisión ≥ 20 %**, fijada antes de entrenar. **Motivo:** detectar lo más posible sin mandar todo a revisión. 20 % es 25 % mejor que revisar al azar (tasa base 15,9 %). La exactitud se descartó porque "nunca mora" ya acierta el 81 %.

## 2. Datos y limpieza

> Fuente: `reports/01_eda.md` y `src/proyecto/data/` (10 decisiones, cada una con su prueba).

- **Unidad de análisis y partición:** una fila es un crédito; el cliente se repite hasta 4 veces (12.627 clientes con varios créditos). **Partición y validación por cliente** (`GroupShuffleSplit` 80/20 y `StratifiedGroupKFold`, semilla 42). **Motivo:** si un cliente cae a ambos lados, el modelo "reconoce" al cliente y la métrica se infla. Hay una prueba que falla si alguien parte por fila.
- **Hallazgos y decisiones:**
  - **Bloque reestructurado:** 3.619 créditos con plazo = 1 mes, tasa de mora 950 y 100 % de mora → **excluidos**. **Motivo:** sus condiciones se reescribieron después de la mora (fuga). Con el bloque, "afiliación del canal" y "utilizaciones del plan" parecían predictivas; sin él, su señal desaparece.
  - **Créditos sin exposición:** los abiertos en agosto–octubre de 2026 tienen 0 % de mora → se exigen **≥ 4 meses** de vida al corte (−10.331). **Motivo:** si no, "nuevo" parecería "buen pagador".
  - **Fuga por columnas posteriores:** saldos, pagos, intereses, estado y calificación tienen AUC de 0,55 a 1,00 por sí solos → se conservan **solo 13 columnas conocidas al aprobar**.
  - **Unidades:** la tasa venía multiplicada por 10⁷ → se pasa a % EA.
  - **Columnas sin información:** 98 vacías o constantes → eliminadas.
- **Datos personales:** 49 columnas (nombres, documentos, direcciones, teléfonos, codeudores) se eliminan **al cargar** (`load_raw`). El documento se reemplaza por un número de cliente (`c00001`...) que no se calcula a partir de él y se usa solo para agrupar (ver `reports/01_eda.md`, cambio en la decisión 1). Sexo y estado civil no se usan (sensibles y sin señal). La base cruda no se sube al repo.
- **Resultado:** 46.050 créditos de 34.657 clientes, 15,9 % en mora, 17 columnas.

## 3. Variables

> Fuente: `reports/04_features.md`.

Se midieron 4 ideas con LightGBM fijo y los mismos 5 pliegues por cliente. **Regla escrita antes de medir:** conservar una idea si mejora la PR-AUC ≥ 1 vez el ruido y no empeora la métrica de negocio.

| Idea | Mejora / ruido | Decisión |
|---|---|---|
| Razones financieras (cuota ÷ monto, garantía ÷ monto) | 0,47 | descartada |
| Historial (créditos anteriores del cliente) | −0,43 | descartada |
| Empresa pagadora (tasa de mora codificada dentro del pipeline) | −1,16 | descartada |
| Edad | −2,45 | descartada (además, es un atributo regulado) |

**Ninguna superó el ruido.** El pipeline final usa 12 condiciones del crédito. **Motivo:** menos variables = app más simple y sin atributos sensibles, sin perder rendimiento. Se eligió PR-AUC para decidir porque la métrica de negocio salta ± 0,08 entre pliegues con esta señal.

## 4. Torneo de modelos

> Fuente: `reports/05_torneo.md`.

Seis candidatos con los mismos pliegues por cliente: tasa base sin modelo, **regla del plazo corto**, regresión logística, random forest, LightGBM y XGBoost.

| Modelo | Recall con precisión ≥ 20 % | PR-AUC | AUC |
|---|---|---|---|
| Random forest | 0,195 ± 0,050 | 0,179 | 0,531 |
| XGBoost | 0,188 ± 0,095 | 0,181 | 0,533 |
| LightGBM | 0,186 ± 0,075 | 0,180 | 0,533 |
| Regla del plazo corto | 0,149 ± 0,020 | 0,178 | 0,533 |
| Regresión logística | 0,116 ± 0,092 | 0,177 | 0,528 |

- **Finalistas:** XGBoost y LightGBM. **Motivo:** mejores en PR-AUC, probabilidades bien calibradas y rápidos (0,8 s por pliegue). El random forest gana en negocio por una diferencia menor que su ruido, es 16 veces más lento y sus probabilidades están infladas.
- **Comparación pareada:** XGBoost frente a la regla, diferencia/ruido 0,92 en PR-AUC y 0,02 en AUC. **Ya en validación cruzada no había una mejora clara sobre la regla.**

## 5. Optimización y seguimiento

> Fuente: `reports/06_optimizacion.md`.

- **Búsqueda:** Optuna, 30 ensayos de LightGBM y 20 de XGBoost, objetivo PR-AUC, en el 80 % de los clientes de entrenamiento. El espacio favorece árboles pequeños y regularizados, por la señal débil.
- **Seguimiento:** cada ensayo es una ejecución anidada en MLflow con todas las métricas (52 ejecuciones en `libranzaradar-06-optimizacion`), además de los experimentos de variables (6), torneo (6) y registro (1). Corrida de referencia en **MLflow local**; el código cambia a Databricks con `.env`.
- **Comprobación honesta** en el 20 % de clientes reservados: XGBoost +0,0020 de PR-AUC (IC [−0,0042 ; +0,0081]) y LightGBM +0,0018 (IC [−0,0048 ; +0,0093]). **Regla escrita antes:** adoptar los optimizados solo si el intervalo queda entero sobre 0. **No se cumple → se usan los parámetros de partida de XGBoost.**

## 6. Validación e interpretación

> Fuente: `reports/07_validacion.md`.

- **Decisiones congeladas antes de abrir la prueba:** XGBoost con parámetros de partida, 12 variables, **sin calibrar** (Brier 0,1307 con y sin isotónica en clientes reservados) y **umbral 0,1927** (mayor recall con precisión ≥ 20 % en predicciones fuera de pliegue).
- **Declaración:** la prueba quedó registrada dos veces (21:35 y 21:37). La primera ejecución falló al **guardar** los resultados por un error de nombre de variable; se corrigió y se volvió a ejecutar **sin cambiar ninguna decisión** (archivo de decisiones idéntico).
- **Resultado en la prueba** (9.193 créditos, 6.932 clientes nuevos):

| Métrica | Modelo | Regla del plazo corto | Modelo − regla (IC 95 %) |
|---|---|---|---|
| Recall de la mora | 0,149 [0,130 ; 0,167] | 0,154 [0,135 ; 0,172] | −0,006 [−0,020 ; +0,010] |
| Precisión | 0,192 [0,169 ; 0,214] | 0,189 [0,168 ; 0,210] | — |
| AUC | 0,527 [0,509 ; 0,544] | 0,538 [0,520 ; 0,554] | −0,011 [−0,028 ; +0,006] |

  **No mejora a la regla con confianza.** La precisión (19,2 %) quedó un poco por debajo del 20 % exigido.
- **Errores por segmento:** el modelo marca el 38 % de los créditos de plazo ≤ 12 meses y casi ninguno de plazo largo, aunque los de plazo largo también caen en mora (13 %–15 %): en la práctica, es la regla del plazo con matices. Por edad (no usada), el % marcado es parejo (11,7 %–12,6 %).
- **Interpretación (SHAP):** plazo, cuota, monto, tasa y garantía. **Límite:** SHAP explica al modelo, no al cliente, y con AUC 0,53 buena parte de lo explicado es ruido.

## 7. Registro del modelo

> Fuente: `reports/08_registro.md` y `models/ficha_modelo.md`.

`libranzaradar_mora30` versión 1, alias `champion`, con parámetros, métricas de la prueba, firma de 12 columnas, ejemplo de entrada, etiquetas y decisiones congeladas. **Ida y vuelta:** el modelo recuperado del registro y el local difieren 0,0 en 500 filas. `models/model.joblib` se exportó desde el registro y reproduce exactamente el recall de la prueba. **Motivo del alias:** la app y el notebook 09 piden "el modelo en producción" sin depender del número de versión.

## 8. Despliegue

> Fuente: `reports/09_despliegue.md`.

- **App:** `app/streamlit_app.py`. Carga `models/model.joblib` desde el repo y **no consulta Databricks**, así que no necesita credenciales y no depende de cuotas. Valida rangos posibles (por ejemplo, rechaza un plazo de −5 con un mensaje claro) y acepta "No sé" (el pipeline imputa). Muestra la probabilidad, cuántas veces está sobre el promedio, la sugerencia (priorizar o seguimiento normal), qué datos pesaron y un aviso de uso responsable.
- **Pruebas en local:** caso normal → seguimiento normal (15,1 %); plazo 6 meses → priorizar (23,5 %); plazo −5 → rechazo; campos en "No sé" → responde.
- **Enlace público:** _(completar tras desplegar en Streamlit Community Cloud, Python 3.12)_.

## 9. Riesgos, límites y siguientes pasos

- **Qué no hace:** no aprueba ni niega créditos, no fija tasas y no debe usarse para tratar distinto a un cliente.
- **Límites de los datos:** la base es sintética. La mora se mide a la fecha de corte, con tiempos de exposición distintos. No hay historia de pagos con fechas para construir un objetivo a horizonte fijo ni validar por cohortes futuras.
- **Uso responsable:** sin sexo, estado civil ni edad. La ciudad sí entra y puede actuar como aproximación socioeconómica: vigilar las tasas de marcado por ciudad.
- **Mejora concreta:** capturar al aprobar **capacidad de pago** (ingreso y descuentos de nómina vigentes), **endeudamiento en centrales de riesgo**, **antigüedad laboral** y la **salud financiera de la empresa pagadora**. Con eso, reentrenar con el mismo pipeline (notebooks 03–09) y volver a compararlo contra la regla del plazo corto. En producción, vigilar la tasa de mora de los priorizados frente a los no priorizados.

## Anexo: cómo reproducir el proyecto

1. `uv venv --python 3.12 .venv` y `uv pip install --python .venv/bin/python -r requirements.txt` (en Windows: `.venv/Scripts/python.exe` y `$env:PYTHONUTF8=1`).
2. Copiar `Base_sintetica_creditos.csv` a `data/raw/`. Opcional: `cp .env.example .env` con credenciales de Databricks.
3. Ejecutar los notebooks `01` a `09` en orden (≈ 25 minutos; el 06 es el más largo).
4. `pytest -q` (49 pruebas).
5. `streamlit run app/streamlit_app.py`.

---

### Lista de comprobación antes de entregar

- [x] Las 9 secciones tienen contenido y cada decisión lleva su motivo.
- [x] Las cifras coinciden con `reports/07_validacion.md` y con la presentación.
- [x] No hay credenciales, `.env` ni datos personales (la base cruda está en `.gitignore`).
- [ ] El enlace de la app abre en una ventana privada _(tras desplegar)_.
- [ ] Un tercero reprodujo el proyecto con el anexo _(verificarlo en el grupo)_.
