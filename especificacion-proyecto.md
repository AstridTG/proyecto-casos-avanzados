# Especificación del proyecto

> Plantilla. Complétenla en el grupo y manténganla actualizada. Claude la lee antes de generar
> código: lo que escriban aquí manda sobre cualquier otra suposición.
>
> **Estado de este borrador (30 oct 2026):** las cifras de la sección 3 se midieron directamente sobre
> `data/raw/Base_sintetica_creditos.csv`. Lo marcado **PROPUESTA – por confirmar** o **POR DEFINIR** es una
> decisión del grupo que todavía no se ha tomado.

## 1. Grupo

| Integrante | Rol (datos / modelado / app / negocio) |
|---|---|
| POR DEFINIR | |
| POR DEFINIR | |
| POR DEFINIR | |

Nombre de la "startup": POR DEFINIR   Repositorio (público): https://github.com/AstridTG/proyecto-casos-avanzados

## 2. Caso de negocio

**Contexto.** Iniciativa *Servicios Financieros 2.0* de Comfama: implementar capacidades digitales de
**autogestión para empresas** que modernicen la operación de **libranza** (crédito cuya cuota se descuenta
de la nómina a través de la empresa empleadora), optimicen la eficiencia operativa y fortalezcan la
experiencia del cliente. Contribuye a tres pilares: cultura de servicio (autonomía, transparencia y acceso
oportuno a la información), sostenibilidad financiera (menos carga operativa, menos riesgo regulatorio,
gestión basada en datos) e inclusión y equidad (acceso digital a servicios financieros para empresas y
colaboradores).

- **Pregunta de negocio** (PROPUESTA – por confirmar): ¿qué créditos de libranza tienen más probabilidad de
  llegar a **más de 30 días de mora**, para que la empresa (desde la autogestión) y el área de cartera actúen
  a tiempo?
- **¿Quién usará el resultado y qué decisión tomará con él?** (PROPUESTA – por confirmar): el equipo de cartera
  y servicio de Servicios Financieros, y las empresas en el portal de autogestión, para priorizar a qué
  créditos o colaboradores contactar primero. La persona conserva la decisión final.
- **¿Qué cuesta equivocarse?** (PROPUESTA – por confirmar) El error peor es **no detectar** un crédito que
  llegará a más de 30 días de mora: aumenta la cartera vencida y la provisión. Marcar como riesgoso un
  crédito sano genera gestiones innecesarias y una mala experiencia para la empresa y el colaborador. Los
  valores de cada costo: POR DEFINIR.

## 3. Datos

- **Fuente:** `Base_sintetica_creditos.csv`, base **sintética** de créditos (el nombre del archivo lo indica).
  Origen y autor: POR DEFINIR.
- **Filas / columnas:** 60.000 filas × 189 columnas. 26 columnas están 100 % vacías y 72 tienen un único
  valor, así que quedan **91 columnas con información**. Hay 5 nombres de columna repetidos (por ejemplo
  `CODIGO CIUDAD`, `NOMBRE CIUDAD`, `DIRECCION CODEUDOR`, `TELEFONO CODEUDOR`).
- **Unidad de análisis:** un **crédito** (`NUMERO DE LA COLOCACION` es único en las 60.000 filas).
  El 79,9 % (47.931) son libranza a través de una empresa (`DESCRIPCION DEL CANAL`, 421 valores); el resto
  aparecen como `PAGO PERSONAL` (12.069).
- **Variable objetivo** (PROPUESTA – por confirmar): `EN_RIESGO` = 1 si `DIAS DE MORA` > 30, si no 0. Es una
  columna **construida**, no viene en el archivo. Distribución: 1 = 11.397 (19,0 %), 0 = 48.603 (81,0 %).
  En libranza es 13,8 % y en pago personal 39,6 %.
- **Columna `EVENTO`: se omite.** Su significado no está documentado y en los datos no se relaciona con la mora
  (26,7 % vs 26,5 % de créditos con mora > 0 en cada clase). Se elimina al cargar y no se usa ni como objetivo
  ni como variable.
- **Tipo de problema:** ☒ clasificación  ☐ regresión  ☐ clusterización (binaria y desbalanceada: 19 % positivos)
- **¿Una misma entidad (cliente, paciente, empresa) aparece en varias filas?** ☐ no  ☒ sí → hay 41.855
  clientes distintos (`NUMERO DE IDENTIFICACION`): 29.228 con un crédito, 8.385 con 2, 2.966 con 3 y 1.276
  con 4. La partición será **por cliente** (`NUMERO DE IDENTIFICACION`) con `GroupKFold` /
  `StratifiedGroupKFold`. En 4.669 clientes, el objetivo cambia entre sus créditos.
- **Datos personales o confidenciales presentes:** ☐ no  ☒ sí → nombres (`NOMBRE O RAZON SOCIAL`,
  `NOMBRE CODEUDOR…`), documentos (`NUMERO DE IDENTIFICACION`, las dos `NUMERO DE IDENTIFICACION DEL`,
  `DIGITO DE CHEQUEO`, `NRO IDENTIDAD CODEUDOR…`), direcciones (`DIRECCION LINEA 1`, `DIRECCION CODEUDOR`,
  `DIRECCION GARANTIA`) y teléfonos (`TELEFONO 1-3`, `TELEFONO CODEUDOR`). También aparecen nombres y NIT de
  empresas (`DESCRIPCION DEL CANAL`, `NIT DEL CANAL`). Se eliminarán al cargar los datos; el documento del
  cliente se reemplaza por un identificador anónimo antes de eliminarlo, para poder partir por grupo.
- **Licencia o permiso de uso de los datos:** POR DEFINIR. Aunque la base sea sintética, contiene nombres de
  empresas y estructura de un sistema de cartera real. Confirmar con el instructor si puede ir al repositorio
  público. Mientras tanto, **el CSV no se sube** (ver sección 7).

## 4. Métrica

- **Métrica principal:** POR DEFINIR.   **Por qué esa y no otra:** POR DEFINIR.
  PROPUESTA: **recall de `EN_RIESGO` = 1** con una precisión mínima acordada, o un **costo esperado** con una
  matriz de costos del negocio, porque no detectar un crédito en riesgo cuesta más que gestionar uno de más.
- **Métricas secundarias:** PROPUESTA: AUC-PR (mejor que AUC-ROC con 19 % de positivos), F1 y precisión de
  la clase positiva.
- **Línea base:** predecir siempre "no en riesgo" da 81,0 % de exactitud y 0 % de recall. Por eso la
  exactitud no sirve como métrica principal.

## 5. Riesgos

- **Fuga de información (confirmada):** como `EN_RIESGO` sale de `DIAS DE MORA`, las columnas que describen la
  mora **actual** contienen la respuesta y **se excluyen del modelo**. Medido: `CAJA DE MORA A LA FECHA` = 1 →
  0 % en riesgo y 2 a 7 → 100 %; `CALIFICACION CARTERA` B a E → 100 %; `DESCRIPCION DEL ESTADO` `SUBNORMAL`,
  `DUDOSO`, `DIFICIL COBRO` y `VENCIDOS` → 100 %, y `VIGENTE` y `CANCELADO` → 0 %; `NRO CUOTAS VENCIDAS` = 0 →
  0 % y ≥ 2 → 100 %. También se excluyen `DIAS DE MORA` (de ahí sale el objetivo) y `ESTADO DEL PRESTAMO`
  (código de `DESCRIPCION DEL ESTADO`).
  **Sospechosas, sin medir todavía** (se miden con y sin ellas en la etapa 4, con el subagente
  `auditor-de-fuga`): `FEC CUOTA MAS ANTIG PEND PAG`, `VLR MORA PAGO MINIMO`, `INT. MORA PAGO TOTAL`,
  `INT MORA EN PESOS 1-6`, `T.INT.MORA EN PESOS`, `VLR MINIMO DE PAGO`, `VLR CAPITA DEBIDO`,
  `VLR INT CORR. DEBIDO`, `FECHA EFEC ULTIMO PAGO`, `VLR ULTIMO PAGO` y `VALOR SALDO SIN FECHA CORTE`.
- **Calidad del objetivo:** 386 créditos marcados `NORMAL (1-30)` / calificación `A` tienen más de 30 días de
  mora. Revisar en el EDA.
- **Sesgos o equidad:** hay `SEXO` (2: 30.179 / 1: 29.821), `EDAD DEL CLIENTE` (19-72 años, mediana 45) y
  `ESTADO CIVIL`. Revisar que el modelo no discrimine por estas variables (pilar de inclusión y equidad).
- **Datos faltantes o de mala calidad:** 26 columnas vacías, 72 constantes, nombres de columna repetidos,
  fechas como número `AAAAMMDD` con `0` como vacío (por ejemplo `FECHA EFEC ULTIMO PAGO`), `CALIFICACION
  CARTERA` vacía en 2.168 filas y montos guardados como texto con decimales `.00`.
- **Límites de lo que el modelo puede decir:** son datos sintéticos; los resultados no describen a clientes ni
  empresas reales de Comfama, y no reemplazan las políticas de crédito ni el análisis de riesgo.

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
| 2026-10-30 | El CSV no se sube al repositorio público hasta confirmar el permiso de uso | Contiene nombres, documentos, direcciones y teléfonos (aunque sean sintéticos) y nombres de empresas |
| 2026-10-30 | La partición será por cliente (`NUMERO DE IDENTIFICACION`) | 12.627 clientes tienen entre 2 y 4 créditos |
| 2026-10-30 | Se omite la columna `EVENTO` (ni objetivo ni variable) | Significado no documentado y sin relación con la mora en los datos |
| 2026-10-30 | Objetivo propuesto: `EN_RIESGO` = `DIAS DE MORA` > 30 (por confirmar) | Reemplaza a `EVENTO`; es medible y está ligado a la gestión de cartera |
| 2026-10-30 | Se excluyen `DIAS DE MORA`, `ESTADO DEL PRESTAMO`, `DESCRIPCION DEL ESTADO`, `CALIFICACION CARTERA`, `CAJA DE MORA A LA FECHA` y `NRO CUOTAS VENCIDAS` | Fuga confirmada: separan el objetivo al 100 % (ver sección 5) |
