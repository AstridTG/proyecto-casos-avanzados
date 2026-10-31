# Especificación · Etapa 3 · Preprocesamiento (limpieza y partición)

> Se llena **antes** de pedirle código a Claude, a partir de la tabla de decisiones de
> `especificaciones/02-eda.md`. Claude la lee y la implementa; ustedes revisan que el código haga
> **exactamente** esto (`material-del-curso/kit/checklist-revision-ia.md`).
> Guía: `material-del-curso/kit/guia-eda-y-preprocesamiento.md`, sección 4 · Ejemplo: `material-del-curso/ejemplo-creditsight/src/creditsight/data/`.

**Grupo:** LibranzaRadar   **Fecha:** 30-oct-2026   **Estado:** ☐ borrador  ☒ cerrada

## 1. Unidad de análisis y partición

- **Una fila es:** un crédito de libranza
- **Entidad que se repite (columna):** `client_id` (seudónimo del documento del cliente)
- **Se parte por:** ☒ grupo (`GroupShuffleSplit` / `StratifiedGroupKFold`) ☐ fila
- **Proporción de prueba:** 20 % de los clientes   **Semilla:** 42
- **¿Hay orden temporal que respetar?** ☒ no ☐ sí → cada crédito se decide el día que se aprueba; la exposición se controla con la regla de 4 meses
- **Dónde se guarda la prueba:** `data/processed/` (cerrada: **no se mira** hasta la etapa 7)

## 2. Datos personales

| Columna | Qué es | Se elimina en | Prueba que lo verifica |
|---|---|---|---|
| NOMBRE O RAZON SOCIAL, NOMBRE CODEUDOR (1–3) | Nombres | `load_raw()` → `drop_personal_data` | `test_personal_data_is_removed_and_client_is_pseudonymized`, `test_load_raw_never_returns_personal_columns` |
| NUMERO DE IDENTIFICACION (y parciales), DIGITO DE CHEQUEO, NRO IDENTIDAD CODEUDOR (1–3) | Documentos | idem (el del cliente pasa a número de cliente `client_id` (`c00001`...); el del codeudor a `has_cosigner`) | idem |
| DIRECCION LINEA 1–3, DIRECCION CODEUDOR*, DIRECCION GARANTIA, ZONA POSTAL | Direcciones | idem | idem |
| TELEFONO 1–3, TELEFONO CODEUDOR* | Teléfonos | idem | idem |

## 3. Reglas de limpieza

Una fila por decisión del EDA. **Una función, una prueba.** Se marca como vacío lo imposible; no se borran filas sin criterio.

| # (de la tabla del EDA) | Columna(s) | Problema | Regla exacta (con el umbral o valor) | Función en `src/proyecto/data/cleaning.py` | Prueba en `tests/test_cleaning.py` |
|---|---|---|---|---|---|
| 2 | 63 columnas | Vacías o constantes | `nunique(dropna=True) <= 1` → se elimina | `drop_empty_and_constant` | `test_empty_and_constant_columns_are_dropped_but_kept_on_request` |
| 3 | DIAS DE MORA | Definir el objetivo | `mora_30 = DIAS DE MORA > 30`; vacíos o negativos → error | `add_target` | `test_target_is_more_than_30_days`, `test_target_refuses_missing_or_negative_days` |
| 4 | FECHA APERTURA | Sin exposición | apertura ≤ corte − 4 meses (corte = último pago, 30-oct-2026) | `remove_unseasoned` | `test_unseasoned_loans_are_removed` |
| 5 | CONDICION ESPECIAL | Condiciones reescritas tras la mora | `CONDICION ESPECIAL == 1` → excluir | `remove_restructured_block` | `test_restructured_block_is_removed` |
| 6 | 13 columnas al aprobar | Fuga y unidades | lista blanca `APPROVAL_COLUMNS`; tasa ÷ 10⁷; garantía S/N → 1/0 | `select_approval_columns` | `test_approval_columns_have_project_names_and_units`, `test_approval_columns_fail_loudly_if_a_column_is_missing` |
| 7 | historial | Créditos previos | cuenta de créditos del mismo cliente abiertos antes (base completa) | `add_prior_credits` | `test_prior_credits_counts_only_earlier_loans_of_the_same_client` |
| 10 | numéricas | Valores imposibles | fuera de `PLAUSIBLE_RANGE` → vacío; la fila se conserva | `flag_impossible_values` | `test_impossible_values_become_missing_without_dropping_rows` |

## 4. Vacíos

| Columna | Qué significa el vacío | Tratamiento hoy | Tratamiento en la etapa 4 (dentro del `Pipeline`) |
|---|---|---|---|
| Numéricas de la app ("No sé") | ☐ no aplica ☒ no se anotó ☐ perdido ☒ imposible | ☒ dejar vacío | Mediana del entrenamiento (`SimpleImputer`) |
| Categóricas de la app ("No sé") | ☐ no aplica ☒ no se anotó ☐ perdido ☐ imposible | ☒ dejar vacío | Categoría explícita "desconocido" |

> Imputar con medias o medianas **no se hace aquí**: depende del entrenamiento y va dentro del `Pipeline`.

## 5. Entradas y salidas

| | Ruta |
|---|---|
| Entrada | `data/raw/Base_sintetica_creditos.csv` (nunca se modifica) |
| Salida: entrenamiento | `data/processed/train.joblib` |
| Salida: prueba (cerrada) | `data/processed/test.joblib` |
| Código de limpieza | `src/proyecto/data/cleaning.py` |
| Código de partición | `src/proyecto/data/split.py` |
| Notebook que orquesta | `notebooks/03_preprocesamiento.ipynb` (solo llama a las funciones) |

## 6. Pruebas que deben existir

- ☒ **Partición:** ninguna entidad aparece en dos particiones y no se pierde ninguna fila (`tests/test_split.py`).
- ☒ **La prueba de partición falla** si se cambia temporalmente a partición por fila (compruébenlo y vuelvan a dejarla bien).
- ☒ **Una prueba por regla de limpieza** de la sección 3, con un caso normal y un caso sucio hechos a mano.
- ☒ **Datos personales:** el resultado de cargar no contiene las columnas de la sección 2.
- ☒ `pytest` en verde desde la raíz del repo.

## 7. Criterios de cierre (H1)

- ☒ La limpieza corre **de principio a fin desde cero** (`data/processed/` borrada y regenerada con el notebook 03), sin pasos manuales.
- ☒ Unidad de análisis y forma de partir **escritas** (sección 1) y documentadas en `reports/01_eda.md`.
- ☒ `pytest` en verde.
- ☒ Conjunto de prueba guardado y sin mirar.
- ☒ `data/raw/` intacta y `.env` fuera de Git (`git status`).
- ☐ Todo subido a GitHub (lo hace el grupo).
- ☐ Revisaron el código de Claude con `checklist-revision-ia.md` y cada integrante puede explicar una función (lo hace el grupo).
- ☒ **Hallazgo que no esperaban** (para la puesta en común): 3.619 créditos vencidos con el plazo reescrito a 1 mes hacían parecer predictivas a la afiliación del canal y a las utilizaciones del plan; sin ese bloque, ninguna variable conocida al aprobar supera AUC 0,54.
