# Especificación · Etapa 2 · EDA

> Se llena **antes** de abrir `notebooks/02_eda.ipynb` (las secciones 1 y 2) y se completa **mientras**
> lo ejecutan (3 y 4). El resultado final, con las decisiones, va a `reports/01_eda.md`.
> Guía: `material-del-curso/kit/guia-eda-y-preprocesamiento.md` · Ejemplo: `material-del-curso/ejemplo-creditsight/reports/01_eda.md`.

**Grupo:** LibranzaRadar   **Fecha:** 30-oct-2026   **Estado:** ☐ borrador  ☒ cerrada

## 1. Qué esperamos encontrar (se escribe ANTES de mirar los datos)

Una hipótesis por pregunta. Si después no se cumple, es un hallazgo: anótenlo.

| Pregunta | Lo que creemos |
|---|---|
| ¿Qué representa una fila? | Un crédito de libranza |
| ¿Alguna entidad se repite en varias filas? | Sí, el cliente (puede tener varios créditos) |
| ¿Qué variable **debería** ser estable y no cambiar? | Edad, sexo y ciudad del cliente entre sus créditos; plazo y monto pactados de un crédito |
| ¿Qué significaría un vacío en nuestras columnas clave? | En codeudor/garantía: que no hay (no un dato perdido) |
| ¿Qué columna solo se conoce **después** de la decisión que queremos apoyar? | Saldos, pagos, cuotas vencidas, intereses, estado y calificación de cartera |

## 2. Qué vamos a medir

Marquen lo que aplica a su dataset. Lo que no aplique se tacha **con una razón** (no se deja en blanco).

| Chequeo (guía, sección 3) | ¿Aplica? | Columnas a revisar | Quién lo hace |
|---|---|---|---|
| 3.1 Números guardados como texto | ☐ sí ☒ no: el CSV trae números; la tasa viene × 10⁷ | VALOR EQUI. EFECTIVA VENCIDA | datos |
| 3.2 Valores centinela (`-1`, `9999`, `?`) | ☒ sí ☐ no: | 0 en codeudor/garantía/teléfonos = "no hay" | datos |
| 3.3 Valores imposibles (percentiles, negativos) | ☒ sí ☐ no: | plazo = 1 mes solo en el bloque reestructurado | datos |
| 3.4 Constancia por entidad | ☒ sí ☐ no: | edad y ciudad por cliente | datos |
| 3.5 Vacíos que significan algo | ☒ sí ☐ no: | EVENTO vacío solo en el bloque; calificación vacía 3,6 % | datos |
| 3.6 Duplicados | ☒ sí ☐ no: | 0 duplicados | datos |
| 3.7 Fechas y orden temporal | ☒ sí ☐ no: | apertura vs corte: créditos sin exposición | datos |
| 3.8 Categorías raras / alta cardinalidad | ☒ sí ☐ no: | 421 empresas pagadoras; 22 ciudades | modelado |
| 3.9 Identidad y datos personales | ☒ sí ☐ no: | 49 columnas (nombres, documentos, direcciones, teléfonos) | datos |

## 3. Lo que medimos (se llena mientras corre el notebook)

- **Filas × columnas:** 60.000 × 189 (crudo); 46.050 × 17 (limpio)
- **Unidad de análisis (una frase):** un crédito de libranza aprobado
- **Columna que identifica a la entidad (`ID_COL`):** `client_id` (seudónimo)   **¿Se repite?** ☐ no ☒ sí, 1 a 4 filas por cliente
- **Objetivo (`TARGET`):** `mora_30`   **Distribución:** 19,0 % crudo; 15,9 % limpio
- **Línea base** (regla trivial) y su resultado: nunca mora → recall 0; regla del plazo corto → AUC 0,53
- **Vacíos en el objetivo:** 0   **Qué haremos con esas filas:** no aplica (la función falla si aparecen)
- **Datos personales encontrados:** 49 columnas; se eliminan en `load_raw`
- **Columnas sospechosas de fuga:** todo lo posterior a la aprobación y el bloque `CONDICION ESPECIAL = 1` (se excluyen; afiliación y utilizaciones se verificaron sin el bloque)

## 4. Decisiones (mínimo 5)

> Cada una con **cifra**, acción **concreta** y **motivo**. Se copian tal cual a `reports/01_eda.md`.
> Cada decisión se convierte en una función de `src/proyecto/data/` y en una prueba (ver `03-preprocesamiento.md`).

| # | Hallazgo (con cifra) | Decisión | Motivo | Función que la implementa |
|---|---|---|---|---|
| 1 | 49 columnas personales | Eliminarlas al cargar; seudónimo `client_id` | Ley 1581 | `drop_personal_data` |
| 2 | 63 columnas vacías o constantes | Eliminarlas | No informan | `drop_empty_and_constant` |
| 3 | 19,0 % con más de 30 días de mora | `mora_30` = DIAS DE MORA > 30 | Ficha | `add_target` |
| 4 | Abiertos ago–oct 2026: 0 % de mora | ≥ 4 meses de vida al corte | Sin exposición | `remove_unseasoned` |
| 5 | 3.619 créditos con plazo 1 y 100 % mora | Excluir el bloque | Fuga | `remove_restructured_block` |
| 6 | Columnas posteriores con AUC 0,55–1,00 | Solo 13 columnas al aprobar | Fuga | `select_approval_columns` |
| 7 | 12.627 clientes con varios créditos | Partir por cliente; `prior_credits` | Fuga entre particiones | `split_by_group`, `add_prior_credits` |
| 8 | Sexo y estado civil sin señal | No usarlos | Sensibles | `select_approval_columns` |

Detalle y motivos completos en `reports/01_eda.md`.

## 5. Criterios de cierre

- ☒ `notebooks/02_eda.ipynb` corre de principio a fin sin errores.
- ☒ Unidad de análisis y `ID_COL` declarados por escrito (sección 3).
- ☒ Al menos **5 decisiones** con cifra, acción y motivo.
- ☒ Datos personales identificados y plan para eliminarlos al cargar.
- ☒ Valores imposibles, centinelas y significado de los vacíos revisados.
- ☒ Fuga sospechada: lista escrita, aunque sea "ninguna, porque…".
- ☒ `reports/01_eda.md` completado.
- ☐ Quien **no** escribió una decisión sabe explicar por qué se tomó (lo verifica el grupo).
