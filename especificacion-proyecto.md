# Especificación del proyecto

> Plantilla. Complétenla en el grupo y manténganla actualizada. Claude la lee antes de generar
> código: lo que escriban aquí manda sobre cualquier otra suposición.
>
> **Estado (30 oct 2026):** coherente con la ficha de caso del grupo (`reports/00_caso.md`). Las cifras se
> midieron directamente sobre `data/raw/Base_sintetica_creditos.csv`. Lo marcado **POR DEFINIR** o
> **PROPUESTA – por confirmar** es una decisión del grupo que todavía no se ha tomado.

## 1. Grupo

| Integrante | Rol (datos / modelado / app / negocio) |
|---|---|
| POR DEFINIR | |
| POR DEFINIR | |
| POR DEFINIR | |

Nombre de la "startup": **LibranzaRadar** (`case_id`: `libranzaradar`)   Repositorio (público): https://github.com/AstridTG/proyecto-casos-avanzados

## 2. Caso de negocio

**Contexto.** LibranzaRadar apoya a una caja de compensación en la modernización de su operación de
**libranza** (crédito cuya cuota se descuenta de la nómina a través de la empresa empleadora), dentro de una
iniciativa de servicios financieros que busca capacidades digitales de **autogestión para empresas**, más
eficiencia operativa y una mejor experiencia del cliente. Contribuye a tres pilares: cultura de servicio
(autonomía, transparencia y acceso oportuno a la información), sostenibilidad financiera (menos carga
operativa, menos riesgo regulatorio, gestión basada en datos) e inclusión y equidad (acceso digital a
servicios financieros para empresas y colaboradores).

- **Pregunta de negocio:** con la información disponible **al aprobar** un crédito de libranza, ¿cuál es la
  probabilidad de que caiga en **más de 30 días de mora**?
- **¿Quién usará el resultado y qué decisión tomará con él?** El **analista de crédito**, al aprobar, para
  priorizar la revisión de los créditos con más riesgo y el seguimiento con las **empresas pagadoras** a través
  del portal de autogestión. El analista conserva la decisión final.
- **¿Qué cuesta equivocarse?** El error más costoso es el **falso negativo**: no detectar un crédito que caerá
  en mora genera pérdidas de cartera y costos de cobranza. El **falso positivo** (marcar como riesgoso a un buen
  cliente) genera revisiones innecesarias y puede afectar la experiencia del cliente. Valor en pesos de cada
  error: POR DEFINIR.

## 3. Datos

- **Fuente:** base sintética de cartera de créditos generada para el curso (`Base_sintetica_creditos.csv`),
  con la estructura de columnas de un sistema de cartera de libranza. No contiene datos de clientes reales.
- **Filas / columnas:** 60.000 filas × 189 columnas. 26 columnas están 100 % vacías y 72 tienen un único
  valor (98 en total), así que quedan **91 columnas con información**. Hay 5 nombres de columna repetidos
  (por ejemplo `CODIGO CIUDAD`, `NOMBRE CIUDAD`, `DIRECCION CODEUDOR`, `TELEFONO CODEUDOR`).
- **Unidad de análisis:** un **crédito** (`NUMERO DE LA COLOCACION` es único en las 60.000 filas).
  El 79,9 % (47.931) son libranza a través de una empresa pagadora (`DESCRIPCION DEL CANAL`, 421 valores); el
  resto aparecen como `PAGO PERSONAL` (12.069).
- **Variable objetivo:** `mora_30` = 1 si `DIAS DE MORA` > 30, 0 si no. Es una columna **construida**, no viene
  en el archivo. Distribución: 1 = 11.397 (19,0 %), 0 = 48.603 (81,0 %). En libranza es 13,8 % y en pago
  personal 39,6 %.
- **Columna `EVENTO`: se omite.** Su significado no está documentado y en los datos no se relaciona con la mora
  (26,7 % vs 26,5 % de créditos con mora > 0 en cada clase). Se elimina al cargar y no se usa ni como objetivo
  ni como variable.
- **Tipo de problema:** ☒ clasificación  ☐ regresión  ☐ clusterización (binaria y desbalanceada: 19 % positivos)
- **¿Una misma entidad (cliente, paciente, empresa) aparece en varias filas?** ☐ no  ☒ sí → hay 41.855
  clientes distintos: 29.228 con un crédito, 8.385 con 2, 2.966 con 3 y 1.276 con 4 (12.627 con más de uno).
  La partición será **por cliente** (`id_cliente`, código anónimo de `NUMERO DE IDENTIFICACION`) con
  `StratifiedGroupKFold` / `GroupShuffleSplit`. En 4.669 clientes, el objetivo cambia entre sus créditos.
- **Datos personales o confidenciales presentes:** ☐ no  ☒ sí (sintéticos) → nombres, documentos, dígito de
  chequeo, direcciones y teléfonos de clientes y codeudores, y la dirección de la garantía. Se eliminan al
  cargar con `src/proyecto/data/cleaning.py` (53 columnas, incluida `EVENTO`); antes se crea `id_cliente` con
  un HMAC-SHA256 y una clave secreta (`ANON_KEY` en `.env`). También aparecen nombres y NIT de empresas
  pagadoras (`DESCRIPCION DEL CANAL`, `NIT DEL CANAL`), que se conservan porque son empresas, no personas.
- **Licencia o permiso de uso de los datos:** base sintética generada para el curso. El CSV original queda en
  `data/raw/`, que no se sube al repositorio (ver `.gitignore`).

## 4. Métrica

- **Métrica principal:** **recall de la clase "en mora"** (`mora_30` = 1), exigiendo una **precisión mínima**
  (valor POR DEFINIR).   **Por qué esa y no otra:** el falso negativo es el error más costoso, así que importa
  detectar la mayor parte de los créditos que caerán en mora; la precisión mínima evita marcar a todos como
  riesgosos. La exactitud no sirve con clases desbalanceadas (19 %).
- **Métricas secundarias:** PROPUESTA: AUC-PR (mejor que AUC-ROC con 19 % de positivos), F1 y precisión de
  la clase "en mora".
- **Línea base:** un modelo que nunca prediga mora acierta el 81,0 % y tiene 0 % de recall: no detecta nada.

## 5. Riesgos

- **Fuga de información — regla general:** el modelo predice **al aprobar**, así que solo puede usar lo que
  se conoce ese día. PROPUESTA (se confirma en el EDA): producto, plazo, número de pagos pactados, valor
  original, tasa, valor de la cuota, día de vencimiento, destino económico, tipo de negocio, ciudad, empresa
  pagadora, garantía (sí/no, tipo y valor), si tiene codeudor, fechas de apertura y desembolso, sexo, estado
  civil y edad. **Todo lo que ocurre después de aprobar se excluye**: saldos, capital pendiente, cuotas pagadas,
  restantes y vencidas, último pago, intereses corrientes y de mora, valores de pago mínimo y total, estado,
  calificación y mora.
- **Fuga confirmada (medida):** `CAJA DE MORA A LA FECHA` = 1 → 0 % en mora y 2 a 7 → 100 %;
  `CALIFICACION CARTERA` B a E → 100 %; `DESCRIPCION DEL ESTADO` `SUBNORMAL`, `DUDOSO`, `DIFICIL COBRO` y
  `VENCIDOS` → 100 %, y `VIGENTE` y `CANCELADO` → 0 %; `NRO CUOTAS VENCIDAS` = 0 → 0 % y ≥ 2 → 100 %. También
  `DIAS DE MORA` (de ahí sale el objetivo) y `ESTADO DEL PRESTAMO` (código de `DESCRIPCION DEL ESTADO`). La
  lista final se revisa con el subagente `auditor-de-fuga`.
- **Variables que pueden no reflejar el día de aprobación:** `EDAD DEL CLIENTE` y `ESTADO CIVIL` pueden ser
  los datos de hoy y no los del día de aprobación. Revisar en el EDA; por ejemplo, la edad al aprobar puede
  calcularse con la fecha de apertura.
- **Créditos demasiado recientes:** 2.144 créditos (3,6 %) se abrieron en los últimos 30 días (desde el
  2026-09-29) y ninguno tiene más de 30 días de mora porque aún no pueden tenerla. Su `mora_30` = 0 no
  significa "buen pagador". POR DEFINIR: excluirlos o exigir una antigüedad mínima.
- **Calidad del objetivo:** 386 créditos marcados `NORMAL (1-30)` / calificación `A` tienen más de 30 días de
  mora. Revisar en el EDA.
- **Sesgos o equidad:** hay `SEXO` (2: 30.179 / 1: 29.821), `EDAD DEL CLIENTE` (19-72 años, mediana 45) y
  `ESTADO CIVIL`. Revisar que el modelo no discrimine por estas variables (pilar de inclusión y equidad).
- **Datos faltantes o de mala calidad:** 26 columnas vacías, 72 constantes, nombres de columna repetidos,
  fechas como número `AAAAMMDD` con `0` como vacío (por ejemplo `FECHA EFEC ULTIMO PAGO`), `CALIFICACION
  CARTERA` vacía en 2.168 filas y montos guardados como texto con decimales `.00`.
- **Límites de lo que el modelo puede decir:** son datos sintéticos; los resultados no describen a clientes ni
  empresas reales, y no reemplazan las políticas de crédito ni el criterio del analista.

## 6. Entregables y fechas

| Hito | Contenido | Fecha |
|---|---|---|
| H1 | Ficha aprobada, EDA y preprocesamiento reproducible | Cierre de la clase 2 (vie 30 oct) |
| H2 | Torneo, optimización con tracking, modelo registrado, repo modular, app local | Cierre de la clase 4 (jue 5 nov) |
| H3 | App desplegada y presentación (≤ 5 diapositivas) | Clase 5 (vie 6 nov) |
| H4 | Informe técnico final (hasta 8 días tras la última clase) | Domingo 15 nov |

## 7. Decisiones tomadas (agréguenlas a medida que avancen)

| Fecha | Decisión | Motivo |
|---|---|---|
| 2026-10-30 | El CSV original queda en `data/raw/` y no se sube al repositorio | Contiene nombres, documentos, direcciones y teléfonos (aunque sean sintéticos) |
| 2026-10-30 | La partición será por cliente (`id_cliente`) | 12.627 clientes tienen entre 2 y 4 créditos |
| 2026-10-30 | Se omite la columna `EVENTO` (ni objetivo ni variable) | Significado no documentado y sin relación con la mora en los datos |
| 2026-10-30 | Objetivo: `mora_30` = `DIAS DE MORA` > 30 | Ficha de caso del grupo; es medible y está ligado a la gestión de cartera |
| 2026-10-30 | Se excluyen `DIAS DE MORA`, `ESTADO DEL PRESTAMO`, `DESCRIPCION DEL ESTADO`, `CALIFICACION CARTERA`, `CAJA DE MORA A LA FECHA` y `NRO CUOTAS VENCIDAS` | Fuga confirmada: separan el objetivo al 100 % (ver sección 5) |
| 2026-10-30 | Se anonimizan 53 columnas y se crea `id_cliente` con HMAC-SHA256 y clave secreta | Criterio 8 del dataset; un hash sin clave permitiría recuperar las cédulas |
| 2026-10-30 | Caso definido como LibranzaRadar: el modelo predice al **aprobar** el crédito | Ficha de caso del grupo; solo se usan variables conocidas ese día (ver sección 5) |
| 2026-10-30 | Métrica principal: recall de "en mora" con precisión mínima | El falso negativo es el error más costoso; la exactitud no sirve con 19 % de positivos |
