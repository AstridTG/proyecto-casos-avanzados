# Informe del EDA

> Resultado de `notebooks/02_eda.ipynb`. Cada decisión está implementada en `src/proyecto/data/cleaning.py`
> y tiene su prueba en `tests/test_cleaning.py`. Los datos personales se eliminan al cargar: el EDA nunca los muestra.

## Qué son los datos

- **Filas × columnas:** 60.000 × 189 en la base cruda; 46.050 × 17 tras la limpieza.
- **Unidad de análisis (qué es una fila):** un crédito de libranza.
- **¿Una entidad aparece en varias filas?** Sí: el **cliente**. 41.855 clientes; 29.228 tienen 1 crédito, 8.385 tienen 2, 2.966 tienen 3 y 1.276 tienen 4 (12.627 con más de uno). 4.669 clientes tienen a la vez créditos en mora y al día.
- **Objetivo y distribución:** `mora_30` = `DIAS DE MORA` > 30. 19,0 % en la base cruda y **15,9 %** en la base limpia (46.050 créditos de 34.657 clientes).
- **Línea base** (regla trivial): "nunca predecir mora" acierta el 81 % y detecta el 0 % de las moras. "Revisar todo" detecta el 100 % con precisión del 15,9 % (< 20 % exigido). La regla de analista "plazo corto = más riesgo" es la línea base que el modelo debe superar (AUC 0,53).

## Calidad de los datos

- **49 columnas con datos personales:** nombres, documentos (del cliente y de 3 codeudores), direcciones, teléfonos y dirección de la garantía. Se eliminan al cargar; el cliente pasa a un seudónimo (`client_id`, hash SHA-256) que solo sirve para agrupar.
- **98 columnas vacías o constantes** en la base cruda (63 después de quitar las personales): moneda, agencia, cuenta, gestor, cargos fijos y todas las columnas en UVR, entre otras.
- **Sin duplicados:** 0 filas duplicadas y 0 números de crédito repetidos.
- **Objetivo completo:** `DIAS DE MORA` sin vacíos ni negativos. `CALIFICACION CARTERA` está vacía en el 3,6 %, pero es posterior a la aprobación y no se usa.
- **Tasa de interés:** viene multiplicada por 10⁷ (`230592400` = 23,06 % efectivo anual); se convierte a porcentaje. Rango limpio: 11,6 %–28,6 % EA.
- **Valores imposibles:** ninguno en las variables conservadas (edad 19–72, plazo 3–240 meses, montos positivos). Igual se deja la regla (`flag_impossible_values`) para la app.

## Sospechas de fuga de información

- **Todo lo posterior a la aprobación contiene la respuesta.** AUC de cada columna por sí sola frente a `mora_30` (`reports/02_auc_por_columna.csv`): `DIAS DE MORA` y `CAJA DE MORA` 1,00; `NRO CUOTAS VENCIDAS` 0,98; `VLR CAPITAL PAGO MINIMO` 0,97; `ESTADO DEL PRESTAMO` 0,91; intereses de mora 0,79–0,84; saldos y pagos 0,55–0,60. Ninguna existe el día de la aprobación.
- **Bloque reestructurado (`CONDICION ESPECIAL = 1`):** 3.619 créditos con 100 % de mora cuyas condiciones se **reescribieron después** de la mora: plazo = 1 mes, pagos pactados = 1, tasa de mora 950, 0 cuotas pagadas. Ningún otro crédito tiene plazo de 1 mes. Si se dejan, el modelo aprende "plazo de 1 mes = mora".
- **Señal aparente que era fuga:** "afiliación del canal" (21,5 % vs 13,9 % de mora) y "utilizaciones del plan" (27,8 % vs 13,9 %) pierden toda relación al quitar el bloque (13,8 %–13,9 % en todos los valores).
- **Fechas de apertura:** miden cuánto tiempo lleva el crédito (exposición), algo que no existe al aprobar.

## Decisiones

| # | Hallazgo (con cifra) | Decisión | Motivo | Función |
|---|---|---|---|---|
| 1 | 49 columnas con datos personales | Eliminarlas al cargar; cliente → seudónimo `client_id`; codeudor → `has_cosigner` (0/1) | Ley 1581; el modelo no las necesita | `drop_personal_data` |
| 2 | 63 columnas vacías o con un solo valor (98 en la base cruda) | Eliminarlas | No pueden informar nada | `drop_empty_and_constant` |
| 3 | `DIAS DE MORA` sin vacíos ni negativos; 19,0 % > 30 días | Objetivo `mora_30` = `DIAS DE MORA` > 30 | Definición de la ficha; falla si llegan vacíos o negativos | `add_target` |
| 4 | Créditos abiertos ago–oct 2026: 0 % de mora; julio 13,9 % frente a 15–23 % en los meses anteriores | Exigir **≥ 4 meses** de vida a la fecha de corte (30-oct-2026): −10.331 créditos | Un crédito sin tiempo de exposición parece "buen pagador" aunque no lo sea | `remove_unseasoned` |
| 5 | 3.619 créditos con plazo = 1, tasa de mora 950 y 100 % de mora | Excluir el bloque reestructurado | Sus condiciones de aprobación se reescribieron después de la mora (fuga) | `remove_restructured_block` |
| 6 | Saldos, pagos, intereses, estado y calificación con AUC 0,55–1,00 | Conservar solo 13 columnas conocidas al aprobar, renombradas y con unidades (tasa en %) | Todo lo posterior a la aprobación es fuga | `select_approval_columns` |
| 7 | 12.627 clientes con más de un crédito | Partir y validar **por cliente**; crear `prior_credits` (créditos abiertos antes que este) | Evitar fuga entre particiones; el historial sí se conoce al aprobar | `split_by_group`, `add_prior_credits` |
| 8 | Sexo (15,8 % vs 16,1 %) y estado civil (15,5 %–16,3 %) sin relación con la mora | No usarlos como variables | Atributos sensibles sin señal | `select_approval_columns` |
| 9 | Afiliación del canal y utilizaciones: sin señal fuera del bloque | No usarlas | La señal aparente venía de la fuga; son estados actuales, no del día de aprobación | `select_approval_columns` |
| 10 | Valores fuera de rango posible (p. ej. edad 7) en la app | Dejarlos vacíos (el Pipeline imputa) sin borrar la fila | No inventar ni descartar información | `flag_impossible_values` |

## Hallazgo central: la señal al aprobar es débil

En la base limpia, la tasa de mora casi no cambia entre quintiles de edad (15,8 %–16,1 %), cuota (15,7 %–16,2 %), tasa (15,2 %–16,8 %) o día de pago. Solo el **plazo** muestra una relación clara: 19,2 % en el quintil más corto frente a 14,2 %–15,8 % en el resto (AUC 0,534). Las diferencias de mora entre empresas pagadoras con ≥ 50 créditos (desviación 0,036) son las mismas que daría el azar (0,035). Por eso el torneo compara todo contra la regla del plazo corto.

## Qué queda abierto

- ¿Aportan algo el historial del cliente (`prior_credits`), la empresa pagadora y la edad? Se miden con y sin ellas en la etapa 4.
- La exposición no es igual para todos: un crédito de 2019 ha tenido años para caer en mora y uno de junio de 2026 solo 4 meses. El objetivo es "mora > 30 días **a la fecha de corte**", no "en los primeros N meses". La base no trae la historia de pagos con fechas para construir un objetivo a horizonte fijo; se declara como límite.
- La base es sintética: los patrones pueden no parecerse a los de una cartera real.
