# Informe técnico — LibranzaRadar

> **Regla del informe:** cada decisión va con su motivo. Las secciones detalladas están en `reports/00_caso.md` a `reports/09_despliegue.md`.

**Grupo:** Juan Rafael Taborda, Yenifer Tatiana Calle Zapata, Daniela Acevedo Alvares, Liliana Maria Garcia Builes, Astrid Liliana Torres Gonzalez _(roles: completar)_ · **Repositorio:** <https://github.com/AstridTG/proyecto-casos-avanzados> · **App:** en local (`streamlit run app/streamlit_app.py`)

## Resumen ejecutivo

LibranzaRadar quería que el analista de crédito supiera, **al aprobar** un crédito de libranza, cuáles tienen más probabilidad de caer en más de 30 días de mora, para priorizar su seguimiento con la empresa pagadora. Construimos el flujo completo: limpieza reproducible, partición por cliente, torneo de 5 modelos, optimización con seguimiento en MLflow, validación con una prueba de clientes nunca vistos, registro con alias `champion` y una app en Streamlit.

**Resultado:** con la información disponible al aprobar, la base sintética casi no permite anticipar la mora. **Ningún modelo superó a la regla simple del plazo corto**, ni en validación cruzada ni en la prueba. El modelo elegido (LightGBM) ordena el riesgo igual que la regla (PR-AUC 0,193 frente a 0,186; diferencia +0,007, IC [−0,001 ; +0,016]). Pero con su umbral congelado marca solo el 0,1 % de los créditos y **no detecta ninguna mora**, mientras la regla "plazo ≤ 6 meses" detecta el **13,4 %** (IC [11,6 ; 15,1]) con precisión del 24,2 %. **Recomendamos priorizar con la regla del plazo corto** y capturar mejores datos al aprobar. El modelo y la app quedan listos para reentrenar cuando esos datos existan.

**Declaración:** la prueba se abrió tres veces. Dos el 30-oct con la partición anterior y una el 31-oct, al regenerar el proyecto tras cambiar el identificador del cliente por protección de datos. Con la prueba no se decidió nada sobre el modelo, el umbral ni la métrica. Detalle en `reports/07_validacion.md`, sección 0.

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
| **Regla del plazo corto** | **0,113 ± 0,068** | **0,175** | **0,533** |
| XGBoost | 0,095 ± 0,058 | 0,172 | 0,523 |
| Regresión logística | 0,059 ± 0,057 | 0,171 | 0,525 |
| LightGBM | 0,059 ± 0,078 | 0,171 | 0,522 |
| Random forest | 0,035 ± 0,038 | 0,169 | 0,518 |

- **La regla del plazo corto queda primera** en negocio, AUC y PR-AUC.
- **Finalistas:** XGBoost y LightGBM. **Motivo:** los dos modelos con mayor PR-AUC, con probabilidades sin inflar y rápidos. La regresión logística empata en PR-AUC, pero sus probabilidades están infladas por los pesos balanceados.
- **Comparación pareada** (mejor modelo, XGBoost, frente a la regla en los mismos pliegues): la regla gana en PR-AUC (0,48 veces el ruido) y en negocio (0,77), dentro del ruido, y **en AUC gana en los 5 pliegues por 3,09 veces el ruido**. **Ya en validación cruzada ningún modelo superaba a la regla.** (Corregida el 3-nov-2026; ver `reports/05_torneo.md`.)

## 5. Optimización y seguimiento

> Fuente: `reports/06_optimizacion.md`.

- **Búsqueda:** Optuna, 30 ensayos de LightGBM y 20 de XGBoost, objetivo PR-AUC, en el 80 % de los clientes de entrenamiento. El espacio favorece árboles pequeños y regularizados, por la señal débil.
- **Seguimiento:** cada ensayo es una ejecución anidada en MLflow con todas las métricas (52 ejecuciones en `libranzaradar-06-optimizacion`), además de los experimentos de variables (6), torneo (6) y registro (1). Todo queda en **MLflow local** (aprobado por el profesor el 3-nov-2026); no se usa Databricks.
- **Comprobación honesta** en el 20 % de clientes reservados: XGBoost +0,0030 de PR-AUC (IC [−0,0028 ; +0,0089]) y LightGBM +0,0027 (IC [−0,0035 ; +0,0098]). **Regla escrita antes:** adoptar los optimizados solo si el intervalo queda entero sobre 0. **No se cumple → parámetros de partida.**
- **Elección del modelo:** la regla escrita antes de la prueba toma al finalista con mayor PR-AUC en los reservados. Con los parámetros de partida, que son los que se usan, LightGBM gana por 0,0005 (0,1710 frente a 0,1705), unas 12 veces menos que el ruido: **es un empate** que la regla desempata a favor de LightGBM.

## 6. Validación e interpretación

> Fuente: `reports/07_validacion.md`.

- **Decisiones congeladas antes de abrir la prueba** (31-oct 11:39): LightGBM con parámetros de partida, 12 variables, **sin calibrar** (Brier 0,1332 sin calibrar y 0,1328 con isotónica en clientes reservados) y **umbral 0,3010** (el único con precisión ≥ 20 % en las predicciones fuera de pliegue).
- **⚠️ El umbral ya no servía en validación:** en las predicciones fuera de pliegue marcaba solo el 0,1 % de los créditos (recall 0,001). La regla de congelamiento no exigía un mínimo de créditos marcados, así que el umbral pasó a la prueba igual. Esto debió frenar el paso.
- **Declaración:** la prueba se abrió tres veces (`reports/prueba_abierta.txt`). Las dos del 30-oct (21:35 y 21:37, XGBoost, partición anterior) fueron la misma ejecución, repetida por un error al guardar. La del 31-oct (11:39, LightGBM) se hizo al regenerar los notebooks 03 a 09 para que la partición fuera reproducible en todos los equipos del grupo: mismo CSV original (verificado con su huella SHA-256), misma versión del código, semilla `RANDOM_STATE = 42` y librerías fijadas en `requirements.txt`. La partición anterior (36.857 / 9.193) venía de una versión distinta del código (identificador del cliente con hash); la nueva es 36.872 / 9.178. La prueba vigente es otro grupo de clientes y parte de los clientes de la prueba anterior quedó en entrenamiento. Detalle en `reports/07_validacion.md`, sección 0.
- **Resultado en la prueba vigente** (9.178 créditos, 6.932 clientes nuevos, mora 16,3 %):

| Métrica | Modelo | Regla del plazo corto | Modelo − regla (IC 95 %) |
|---|---|---|---|
| Recall de la mora | 0,000 [0,000 ; 0,000] | 0,134 [0,116 ; 0,151] | −0,134 [−0,151 ; −0,116] |
| Precisión | 0,000 | 0,242 [0,212 ; 0,271] | — |
| PR-AUC | 0,193 [0,180 ; 0,208] | 0,186 [0,174 ; 0,198] | +0,007 [−0,001 ; +0,016] |
| AUC | 0,544 [0,527 ; 0,560] | 0,537 [0,520 ; 0,553] | +0,007 [−0,008 ; +0,024] |

  **Con su umbral, el modelo es claramente peor que la regla; como puntaje para ordenar, empatan.**
- **Errores por segmento:** el modelo marca entre el 0,0 % y el 0,3 % en todos los plazos, productos y edades (`reports/07_errores_por_segmento.csv`): no hay segmento donde funcione la regla de decisión.
- **Interpretación (SHAP):** plazo, cuota, monto, tasa y garantía. **Límite:** SHAP explica al modelo, no al cliente, y con AUC 0,54 buena parte de lo explicado es ruido.

## 7. Registro del modelo

> Fuente: `reports/08_registro.md` y `models/ficha_modelo.md`.

`libranzaradar_mora30` versión 1, alias `champion`, con parámetros, métricas de la prueba, firma de 12 columnas, ejemplo de entrada, etiquetas y decisiones congeladas. **Ida y vuelta:** el modelo recuperado del registro y el local difieren 0,0 en 500 filas. `models/model.joblib` se exportó desde el registro y reproduce exactamente el recall de la prueba. **Motivo del alias:** la app y el notebook 09 piden "el modelo en producción" sin depender del número de versión.

## 8. Despliegue

> Fuente: `reports/09_despliegue.md`.

- **App:** `app/streamlit_app.py`. Carga `models/model.joblib` desde el repo y **no consulta Databricks**, así que no necesita credenciales y no depende de cuotas. Valida rangos posibles (por ejemplo, rechaza un plazo de −5 con un mensaje claro) y acepta "No sé" (el pipeline imputa). Muestra la probabilidad, cuántas veces está sobre el promedio, la sugerencia (priorizar o seguimiento normal), qué datos pesaron y un aviso de uso responsable.
- **Aviso visible:** la app dice al abrir que el modelo no supera a la regla del plazo corto y recomienda usar esa regla. La lógica de decisión no se cambió para el H2.
- **Pruebas en local** (3-nov, modelo vigente): caso normal → seguimiento normal (15,7 %); plazo 6 meses → **seguimiento normal** (22,2 %, bajo el umbral de 30,1 %); plazo −5 → rechazo; campos en "No sé" → responde. Carga masiva de la base: 47 de 56.381 créditos a priorizar (0,08 %).
- **Dónde corre:** **en local**, sin publicar en la nube (aprobado por el profesor el 3-nov-2026). Pasos en `reports/09_despliegue.md`.

## 9. Riesgos, límites y siguientes pasos

- **Qué no hace:** no aprueba ni niega créditos, no fija tasas y no debe usarse para tratar distinto a un cliente.
- **Límites de los datos:** la base es sintética. La mora se mide a la fecha de corte, con tiempos de exposición distintos. No hay historia de pagos con fechas para construir un objetivo a horizonte fijo ni validar por cohortes futuras.
- **Uso responsable:** sin sexo, estado civil ni edad. La ciudad sí entra y puede actuar como aproximación socioeconómica: vigilar las tasas de marcado por ciudad.
- **Mejora concreta:** capturar al aprobar **capacidad de pago** (ingreso y descuentos de nómina vigentes), **endeudamiento en centrales de riesgo**, **antigüedad laboral** y la **salud financiera de la empresa pagadora**. Con eso, reentrenar con el mismo pipeline (notebooks 03–09) y volver a compararlo contra la regla del plazo corto. En producción, vigilar la tasa de mora de los priorizados frente a los no priorizados.

### 9.1 Escenario futuro: LibranzaRadar 2.0 con contención del 80 %

> Fuente: `reports/10_escenario_v2_contencion80.md` (5-nov-2026). **Solo es un escenario:** no cambia el modelo, el
> umbral congelado ni la app, y **no se abrió la prueba**. Las cifras son predicciones fuera de pliegue del
> entrenamiento (36.872 créditos, validación por cliente) e intervalos del 95 % remuestreando clientes completos.

- **Qué es:** fijar el umbral para que el **80 % de los créditos al día quede sin alerta**. En la práctica se revisa
  1 de cada 5 créditos (≈ 490 al mes), frente al 0,1 % que marca hoy el umbral congelado.
- **Si "recuperar" es detectar más moras:** la mejor opción es ordenar por plazo corto y desempatar con el modelo.
  Detecta el **24,3 %** de las moras [23,1 ; 25,4], frente a 23,2 % de LightGBM y 20,4 % al azar (≈ 91 moras al mes).
- **Si "recuperar" es proteger pesos:** la mejor opción es ordenar por **pérdida esperada = probabilidad × monto**.
  Cubre el **74,6 %** del monto desembolsado de los créditos que caen en mora [72,9 ; 76,1], frente a 13,9 % de
  LightGBM y 20,2 % al azar.
- **Las dos metas se contraponen:** las moras se concentran en créditos cortos, que son pequeños.
- **Límites:**
  - **En pesos, el modelo no aporta hoy:** ordenar solo por monto da lo mismo (74,9 %; diferencia −0,3 pts [−0,9 ; +0,2]).
    El resultado lo explica la concentración del dinero en créditos grandes, no una mejor detección del riesgo.
  - **La precisión queda entre 14 % y 19 %,** por debajo del mínimo del 20 % fijado el 30-oct. Adoptarlo sería cambiar
    la regla del negocio.
  - **El monto es el desembolsado,** no la pérdida real (saldo y recuperación se conocen después de aprobar).
  - **Antes de usarlo hace falta una prueba nueva,** con créditos de un periodo posterior.
- **Recomendación para la versión 2.0:** priorizar por pérdida esperada, porque en cobranza la recuperación se mide en
  pesos. La fórmula queda lista para que, cuando el modelo mejore con mejores datos al aprobar, la mejora se note en
  los pesos. La app 2.0 mostraría la probabilidad, el monto y la pérdida esperada, y dejaría elegir la contención
  (70 %, 80 %, 90 %) viendo cuántas revisiones al mes implica.

## Anexo: cómo reproducir el proyecto

1. `uv venv --python 3.12 .venv` y `uv pip install --python .venv/bin/python -r requirements.txt` (en Windows: `.venv/Scripts/python.exe` y `$env:PYTHONUTF8=1`).
2. Copiar `Base_sintetica_creditos.csv` a `data/raw/`. No hace falta `.env`: el seguimiento usa MLflow local.
3. Ejecutar los notebooks `01` a `09` en orden (≈ 25 minutos; el 06 es el más largo).
4. `pytest -q` (57 pruebas).
5. `streamlit run app/streamlit_app.py`.

---

### Lista de comprobación antes de entregar

- [x] Las 9 secciones tienen contenido y cada decisión lleva su motivo.
- [x] Las cifras coinciden con `reports/07_validacion.md` y con la presentación.
- [x] No hay credenciales, `.env` ni datos personales (la base cruda está en `.gitignore`).
- [ ] La app abre en el computador de la demo (`streamlit run app/streamlit_app.py`).
- [ ] Un tercero reprodujo el proyecto con el anexo _(verificarlo en el grupo)_.
