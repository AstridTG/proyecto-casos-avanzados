# Especificación del proyecto

> Plantilla. Complétenla en el grupo y manténganla actualizada. Claude la lee antes de generar
> código: lo que escriban aquí manda sobre cualquier otra suposición.
>
> **Estado de este borrador (30 oct 2026):** las cifras de la sección 3 se midieron directamente sobre
> `data/Base_sintetica_creditos.csv`. Lo marcado **PROPUESTA – por confirmar** o **POR DEFINIR** es una
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
  caer en el evento de riesgo definido como objetivo, para que la empresa (desde la autogestión) y el área de
  cartera actúen a tiempo?
- **¿Quién usará el resultado y qué decisión tomará con él?** (PROPUESTA – por confirmar): el equipo de cartera
  y servicio de Servicios Financieros, y las empresas en el portal de autogestión, para priorizar a qué
  créditos o colaboradores contactar primero. La persona conserva la decisión final.
- **¿Qué cuesta equivocarse?** POR DEFINIR cuando se confirme el objetivo. En general: no detectar un crédito
  en riesgo aumenta la cartera vencida y la provisión; marcar como riesgoso un crédito sano genera gestiones
  innecesarias y una mala experiencia para la empresa y el colaborador.

## 3. Datos

- **Fuente:** `Base_sintetica_creditos.csv`, base **sintética** de créditos (el nombre del archivo lo indica).
  Origen y autor: POR DEFINIR.
- **Filas / columnas:** 60.000 filas × 189 columnas. 26 columnas están 100 % vacías y 72 tienen un único
  valor, así que quedan **91 columnas con información**. Hay 5 nombres de columna repetidos (por ejemplo
  `CODIGO CIUDAD`, `NOMBRE CIUDAD`, `DIRECCION CODEUDOR`, `TELEFONO CODEUDOR`).
- **Unidad de análisis:** un **crédito** (`NUMERO DE LA COLOCACION` es único en las 60.000 filas).
  El 79,9 % (47.931) son libranza a través de una empresa (`DESCRIPCION DEL CANAL`, 421 valores); el resto
  aparecen como `PAGO PERSONAL` (12.069).
- **Variable objetivo** (PROPUESTA – por confirmar): `EVENTO` (0/1). Distribución: 1 = 28.260 (47,1 %),
  0 = 28.121 (46,9 %), vacío = 3.619 (6,0 %). **Su significado no está documentado.** En los datos, los
  créditos con `EVENTO` = 0 y = 1 tienen la misma mora (26,7 % vs 26,5 % con mora > 0) y la misma
  distribución de estados, y las 3.619 filas vacías son exactamente los créditos `VENCIDOS (+181 días)`.
  El grupo debe confirmar qué es `EVENTO` antes de usarlo. Alternativa: un objetivo construido a partir de
  la mora (por ejemplo, mora > 30 días: 19,0 % de los créditos), definiendo bien la fecha de corte para
  evitar fuga (ver sección 5).
- **Tipo de problema:** ☒ clasificación  ☐ regresión  ☐ clusterización (binaria, si se confirma `EVENTO`)
- **¿Una misma entidad (cliente, paciente, empresa) aparece en varias filas?** ☐ no  ☒ sí → hay 41.855
  clientes distintos (`NUMERO DE IDENTIFICACION`): 29.228 con un crédito, 8.385 con 2, 2.966 con 3 y 1.276
  con 4. La partición será **por cliente** (`NUMERO DE IDENTIFICACION`) con `GroupKFold` /
  `StratifiedGroupKFold`. En 6.819 clientes, `EVENTO` cambia entre sus créditos.
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

- **Métrica principal:** POR DEFINIR (depende del objetivo).   **Por qué esa y no otra:** POR DEFINIR.
  PROPUESTA: si el objetivo es de riesgo, usar un **costo esperado** con una matriz de costos del negocio, o
  **recall de la clase en riesgo** con un mínimo de precisión, porque no detectar un crédito en riesgo
  cuesta más que gestionar uno de más.
- **Métricas secundarias:** PROPUESTA: AUC-ROC, F1 y precisión de la clase positiva.
- **Línea base:** con `EVENTO`, predecir siempre la clase mayoritaria da ≈ 50 % de exactitud (las clases
  están balanceadas). Por eso la exactitud no sirve como métrica principal.

## 5. Riesgos

- **Fuga de información posible:** muchas columnas describen el estado **actual** del crédito (`DIAS DE MORA`,
  `ESTADO DEL PRESTAMO`, `DESCRIPCION DEL ESTADO`, `CALIFICACION CARTERA`, `CAJA DE MORA A LA FECHA`,
  `NRO CUOTAS VENCIDAS`, intereses de mora, `FECHA EFEC ULTIMO PAGO`, `VLR ULTIMO PAGO`…). Si el objetivo se
  conoce en la misma fecha de corte, estas columnas pueden contener la respuesta. Además, los vacíos de
  `EVENTO` coinciden 100 % con `VENCIDOS (+181)`.
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
