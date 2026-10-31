# Especificación · Etapa 2 · EDA

> Se llena **antes** de abrir `notebooks/02_eda.ipynb` (las secciones 1 y 2) y se completa **mientras**
> lo ejecutan (3 y 4). El resultado final, con las decisiones, va a `reports/01_eda.md`.
> Guía: `material-del-curso/kit/guia-eda-y-preprocesamiento.md` · Ejemplo: `material-del-curso/ejemplo-creditsight/reports/01_eda.md`.
>
> **Borrador (30 oct 2026):** las cifras de las secciones 2 a 4 salen de una primera revisión de
> `data/Base_sintetica_creditos.csv`. Hay que confirmarlas cuando corra `notebooks/02_eda.ipynb`.

**Grupo:** POR DEFINIR   **Fecha:** 2026-10-30   **Estado:** ☒ borrador  ☐ cerrada

## 1. Qué esperamos encontrar (se escribe ANTES de mirar los datos)

Una hipótesis por pregunta. Si después no se cumple, es un hallazgo: anótenlo.

> Esta sección la llena el grupo con sus propias hipótesis; no se completó automáticamente.

| Pregunta | Lo que creemos |
|---|---|
| ¿Qué representa una fila? | |
| ¿Alguna entidad se repite en varias filas? | |
| ¿Qué variable **debería** ser estable y no cambiar? | |
| ¿Qué significaría un vacío en nuestras columnas clave? | |
| ¿Qué columna solo se conoce **después** de la decisión que queremos apoyar? | |

## 2. Qué vamos a medir

Marquen lo que aplica a su dataset. Lo que no aplique se tacha **con una razón** (no se deja en blanco).

| Chequeo (guía, sección 3) | ¿Aplica? | Columnas a revisar | Quién lo hace |
|---|---|---|---|
| 3.1 Números guardados como texto | ☒ sí ☐ no: | Montos con `.00` (`VALOR ORIGINAL DEL PRESTAMO`, `SALDO DEL PRESTAMO`, `VLR …`); fechas `AAAAMMDD` como número | |
| 3.2 Valores centinela (`-1`, `9999`, `?`) | ☒ sí ☐ no: | `0` como vacío en fechas (`FECHA EFEC ULTIMO PAGO`, `FEC ING. CONDICION`), teléfonos y `NRO IDENTIDAD CODEUDOR`; `99` en `ESTADO DEL PRESTAMO` | |
| 3.3 Valores imposibles (percentiles, negativos) | ☒ sí ☐ no: | `DIAS DE MORA` (0-2.600), `EDAD DEL CLIENTE` (19-72), `VALOR ORIGINAL DEL PRESTAMO` (150.031-349.949.605), `VLR TASA` | |
| 3.4 Constancia por entidad | ☒ sí ☐ no: | Por cliente: `SEXO`, `EDAD DEL CLIENTE`, `ESTADO CIVIL`, `NOMBRE CIUDAD` | |
| 3.5 Vacíos que significan algo | ☒ sí ☐ no: | `EVENTO` vacío (3.619) = créditos `VENCIDOS (+181)`; `CALIFICACION CARTERA` (2.168); `NOMBRE CODEUDOR` (57.186 = sin codeudor); `DIRECCION GARANTIA` (52.294 = sin garantía) | |
| 3.6 Duplicados | ☒ sí ☐ no: | Filas: `NUMERO DE LA COLOCACION` no se repite. Columnas: 5 nombres repetidos y columnas redundantes (`PLAZO UNIDAD TIEMPO PRODUCTO` = `NUMERO DE PAGOS PACTADOS`) | |
| 3.7 Fechas y orden temporal | ☒ sí ☐ no: | `FECHA APERTURA DEL PRESTAMO` y `FECHA DE DESEMBOLSO` (2005-09 a 2026-10), `FEC PROX PAGO`, `FECHA PRIM. FACTURA SIIF` | |
| 3.8 Categorías raras / alta cardinalidad | ☒ sí ☐ no: | `DESCRIPCION DEL CANAL` / `NIT DEL CANAL` (421 empresas), `NOMBRE CIUDAD` (22), `NUMERO DEL PRODUCTO` (7) | |
| 3.9 Identidad y datos personales | ☒ sí ☐ no: | Nombres, documentos, direcciones y teléfonos de clientes y codeudores (ver `especificacion-proyecto.md`, sección 3) | |

## 3. Lo que medimos (se llena mientras corre el notebook)

- **Filas × columnas:** 60.000 × 189 (26 vacías al 100 %, 72 constantes, 91 con información)
- **Unidad de análisis (una frase):** un crédito (colocación) de consumo o libranza; el 79,9 % se paga a
  través de una empresa.
- **Columna que identifica a la entidad (`ID_COL`):** `NUMERO DE IDENTIFICACION` (cliente)   **¿Se repite?**
  ☐ no ☒ sí, de 1 a 4 créditos por cliente (41.855 clientes; 12.627 con más de uno)
- **Objetivo (`TARGET`):** `EVENTO` (PROPUESTA – por confirmar su significado)   **Distribución:** 1 = 28.260
  (47,1 %), 0 = 28.121 (46,9 %), vacío = 3.619 (6,0 %)
- **Línea base** (regla trivial) y su resultado: siempre la clase 1 → ≈ 50,1 % de exactitud sobre las filas
  con objetivo
- **Vacíos en el objetivo:** 3.619, todos con `DESCRIPCION DEL ESTADO` = `VENCIDOS (CONSUMO +181)`
  **Qué haremos con esas filas:** POR DEFINIR (excluirlas, o asignarles una clase si se confirma qué es `EVENTO`)
- **Datos personales encontrados:** nombres, documentos, dígito de chequeo, direcciones y teléfonos de
  clientes y codeudores; nombres y NIT de empresas
- **Columnas sospechosas de fuga:** `DIAS DE MORA`, `ESTADO DEL PRESTAMO`, `DESCRIPCION DEL ESTADO`,
  `CALIFICACION CARTERA`, `CAJA DE MORA A LA FECHA`, `NRO CUOTAS VENCIDAS`, `VLR MORA PAGO MINIMO`,
  `INT MORA EN PESOS 1-6`, `T.INT.MORA EN PESOS`, `FECHA EFEC ULTIMO PAGO`, `VLR ULTIMO PAGO` (se miden con
  y sin ellas en la etapa 4)

## 4. Decisiones (mínimo 5)

> Cada una con **cifra**, acción **concreta** y **motivo**. Se copian tal cual a `reports/01_eda.md`.
> Cada decisión se convierte en una función de `src/proyecto/data/` y en una prueba (ver `03-preprocesamiento.md`).
>
> PROPUESTAS para discutir en el grupo. Los nombres de función son sugerencias.

| # | Hallazgo (con cifra) | Decisión | Motivo | Función que la implementa |
|---|---|---|---|---|
| 1 | 26 columnas 100 % vacías y 72 con un solo valor | Eliminarlas al cargar | No aportan información y hacen más pesado el modelo | `drop_uninformative_columns` |
| 2 | Datos personales en ~20 columnas (nombres, documentos, direcciones, teléfonos de clientes y codeudores) | Crear un ID anónimo del cliente y eliminar todas las columnas personales | Regla 2 del proyecto y criterio 8 del dataset | `anonymize_and_drop_pii` |
| 3 | 41.855 clientes con 1 a 4 créditos; en 6.819 clientes `EVENTO` cambia entre créditos | Partir por cliente con `StratifiedGroupKFold` / `GroupShuffleSplit` | Evitar que el mismo cliente esté en entrenamiento y prueba | `split_by_client` |
| 4 | 3.619 filas sin `EVENTO`, todas `VENCIDOS (+181)` | POR DEFINIR: excluirlas del entrenamiento o asignarles clase | El vacío no es aleatorio: coincide con un estado de cartera | `handle_missing_target` |
| 5 | Fechas `AAAAMMDD` con `0` como vacío; montos como texto con `.00` | Convertir a fecha y a número; `0` → vacío en las fechas | Poder calcular antigüedad y comparar montos | `parse_dates_and_amounts` |
| 6 | 5 nombres de columna repetidos y columnas redundantes (`PLAZO UNIDAD TIEMPO PRODUCTO` = `NUMERO DE PAGOS PACTADOS`) | Renombrar con sufijo y quitar las redundantes | Evitar columnas ambiguas y duplicadas | `deduplicate_columns` |
| 7 | Columnas de estado actual de la mora (ver sección 3) | Medir el modelo con y sin ellas en la etapa 4 | Riesgo de fuga si el objetivo se conoce en la misma fecha de corte | (etapa 4) |

## 5. Criterios de cierre

- ☐ `notebooks/02_eda.ipynb` corre de principio a fin sin errores.
- ☐ Unidad de análisis y `ID_COL` declarados por escrito (sección 3).
- ☐ Al menos **5 decisiones** con cifra, acción y motivo.
- ☐ Datos personales identificados y plan para eliminarlos al cargar.
- ☐ Valores imposibles, centinelas y significado de los vacíos revisados.
- ☐ Fuga sospechada: lista escrita, aunque sea "ninguna, porque…".
- ☐ `reports/01_eda.md` completado.
- ☐ Quien **no** escribió una decisión sabe explicar por qué se tomó.
