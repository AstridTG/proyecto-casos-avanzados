# Informe del torneo de modelos

> Resultado de `notebooks/05_torneo.ipynb`. El torneo **descarta**: elige 1–2 finalistas con evidencia, no un campeón.
> Cada candidato quedó como una ejecución en MLflow (experimento `libranzaradar-05-torneo`).
>
> **Cifras vigentes:** ejecución del 31-oct-2026 con la nueva numeración de clientes (ver `reports/07_validacion.md`,
> sección 0). La versión del 30-oct, con la partición anterior, está en el historial de git (commit `e026f23`).

## Reglas del torneo

- **Mismos datos y mismos pliegues para todos:** 36.872 créditos de entrenamiento (27.725 clientes, mora 15,8 %), 5 pliegues `StratifiedGroupKFold` **por cliente**, semilla 42.
- **Líneas base:** (1) la tasa de mora sin modelo; (2) la **regla del plazo corto** de un analista (puntaje = 1 / plazo).
- **Métrica principal (negocio):** recall de la mora con precisión ≥ 20 %. **Métricas técnicas:** AUC, PR-AUC de la mora, exactitud balanceada, precisión, recall y F1 de la mora (con el umbral de negocio de cada pliegue), log loss y Brier.
- **Variables usadas:** las 12 de la referencia (`reports/04_features.md`).

## Tabla comparativa

> Media ± desviación entre pliegues, ordenada por la métrica principal (`reports/05_torneo_tabla.csv`).

| Modelo | Recall de mora con precisión ≥ 20 % (± ruido) | Precisión lograda | % de créditos marcados | Segundos de ajuste |
|---|---|---|---|---|
| **Línea base: regla del plazo corto** | **0,113 ± 0,068** | 0,168 | 8,5 % | 0,0 |
| XGBoost | 0,095 ± 0,058 | 0,200 | 7,5 % | 0,8 |
| Regresión logística | 0,059 ± 0,057 | 0,160 | 4,7 % | 0,2 |
| LightGBM | 0,059 ± 0,078 | 0,200 | 4,7 % | 0,4 |
| Random forest | 0,035 ± 0,038 | 0,160 | 2,8 % | 3,4 |
| Línea base: tasa de mora (sin modelo) | 0,000 ± 0,000 | — | 0 % | 0,0 |

> "Precisión lograda" es la media entre pliegues. Una media menor que 0,20 indica que en algunos pliegues ningún
> umbral alcanzó el 20 % y el candidato no marcó nada.

## Métricas técnicas

> `reports/05_torneo_tecnicas.csv`.

| Modelo | AUC | PR-AUC mora | Exactitud balanceada | Precisión mora | Recall mora | F1 mora | Log loss | Brier |
|---|---|---|---|---|---|---|---|---|
| Regla del plazo corto | 0,533 ± 0,007 | 0,175 ± 0,005 | 0,517 | 0,168 | 0,113 | 0,134 | 0,581 | 0,146 |
| XGBoost | 0,523 ± 0,008 | 0,172 ± 0,007 | 0,512 | 0,200 | 0,095 | 0,119 | 0,438 | 0,133 |
| LightGBM | 0,522 ± 0,008 | 0,171 ± 0,006 | 0,507 | 0,200 | 0,059 | 0,070 | 0,438 | 0,134 |
| Regresión logística | 0,525 ± 0,007 | 0,171 ± 0,005 | 0,507 | 0,160 | 0,059 | 0,079 | 0,692 | 0,249 |
| Random forest | 0,518 ± 0,005 | 0,169 ± 0,005 | 0,504 | 0,160 | 0,035 | 0,053 | 0,646 | 0,227 |
| Tasa de mora (sin modelo) | 0,500 | 0,158 | 0,500 | 0 | 0 | 0 | 0,437 | 0,133 |

> Log loss y Brier de la regla, la logística y el random forest no son comparables: los dos últimos usan pesos
> balanceados (inflan las probabilidades) y la regla no produce probabilidades reales.

## ¿Coinciden los rankings de negocio y técnico?

> `reports/05_torneo_rangos.csv` (1 = mejor).

| Modelo | Negocio | AUC | PR-AUC | Log loss |
|---|---|---|---|---|
| Regla del plazo corto | 1 | 1 | 1 | 4 |
| XGBoost | 2 | 3 | 2 | 2 |
| Regresión logística | 3 | 2 | 4 | 6 |
| LightGBM | 4 | 4 | 3 | 3 |
| Random forest | 5 | 5 | 5 | 5 |
| Tasa de mora (sin modelo) | 6 | 6 | 6 | 1 |

- **¿El mejor por la métrica de negocio también es el mejor por AUC?** Sí, y es **la regla del plazo corto**: queda primera en negocio, AUC y PR-AUC. Ningún modelo de machine learning la supera en validación cruzada.
- **¿Hay modelos con AUC casi igual pero costo distinto?** Sí. Todos los candidatos están entre 0,518 y 0,533 de AUC, una diferencia del orden de su ruido (± 0,005–0,008). XGBoost y LightGBM tienen casi el mismo AUC y PR-AUC, pero con la precisión exigida XGBoost detecta más (0,095 frente a 0,059).
- **¿Hay alguna clase con recall casi nulo?** Sí. Con la precisión exigida, el mejor candidato detecta el ~11 % de las moras: **casi 9 de cada 10 moras pasan sin marcar.** El random forest y LightGBM quedan por debajo del 6 %.

## Comparación pareada

> `reports/05_torneo_pareada.csv`. **Error del notebook:** la celda 9 toma como "mejor" al primero de la tabla
> técnica. Con la nueva partición ese primero es la propia regla del plazo corto, así que tres de las cuatro filas
> comparan la regla contra sí misma (diferencia 0) y no sirven. Solo vale la primera fila. Para corregirlo, la celda
> debería tomar el mejor *modelo* (sin líneas base) y compararlo contra la regla. Esa corrección no se ha ejecutado.

| A | B | Métrica | Diferencia media (A − B) | Pliegues que gana A | Diferencia / ruido |
|---|---|---|---|---|---|
| Regla del plazo corto | XGBoost | PR-AUC | +0,0026 | 4 de 5 | 0,48 |

La diferencia no llega a 1 vez su ruido: **la regla y XGBoost están empatados en PR-AUC.** Ningún modelo supera a la regla del plazo corto.

## ¿Cuánto vale la diferencia?

> `reports/05_torneo_valor.csv`.

- **Decisiones estimadas al mes:** 2.368 créditos aprobados (promedio de enero–junio de 2026 en la base) → ~375 caerían en mora.
- **Con la regla del plazo corto:** se revisan ~201 créditos y se detectan ~42 moras al mes.
- **Con XGBoost:** se revisan ~179 y se detectan ~36.
- **Con LightGBM:** se revisan ~110 y se detectan ~22.
- **En resumen:** ningún modelo detecta más moras que la regla, y todas las diferencias están dentro del ruido.

## Finalistas

| Finalista | Por qué | Qué podría cambiar con la optimización |
|---|---|---|
| XGBoost | Mejor PR-AUC entre los modelos (0,1722) y mejor recall con la precisión exigida (0,095); probabilidades sin inflar | Árboles más pequeños o más regularizados podrían estabilizar el ranking |
| LightGBM | Segundo en PR-AUC entre los modelos (0,1714), prácticamente empatado con XGBoost; probabilidades sin inflar | Ídem; sirve de contraste |

**Regla de selección** (celda 13 del notebook): los dos modelos con mayor PR-AUC, sin contar las líneas base, restringidos a XGBoost y LightGBM. La regresión logística (0,1707) quedó a 0,0007 de LightGBM, muy dentro del ruido; se descarta porque sus probabilidades están infladas por los pesos balanceados.

**Modelos descartados y por qué:** el random forest es el peor en todas las métricas. La regresión logística empata en PR-AUC, pero sus probabilidades no se pueden leer como probabilidades de mora.

**Por qué el torneo no elige un campeón:** la mejor puntuación de validación cruzada es optimista (se eligió mirando muchas puntuaciones) y las diferencias entre los candidatos son menores que su ruido. Elegir finalistas y comprobarlos en datos no vistos evita casarse con un ganador por azar.

## Efectos que la métrica principal no ve

- **Carga de trabajo:** con precisión cercana al 20 %, por cada mora detectada hay unas 4 revisiones a créditos que pagarán bien.
- **Precisión inestable:** en varios pliegues los modelos no alcanzan el 20 % de precisión con ningún umbral útil. Por eso el umbral que luego se congeló (`reports/07_validacion.md`, sección 0) marca solo el 0,1 % de los créditos.
- **La regla es más fácil de explicar** y rinde igual o mejor. La recomendación honesta al negocio es usarla y concentrar el esfuerzo en conseguir mejores datos (historial de pagos del cliente con fechas, capacidad de pago, endeudamiento).
