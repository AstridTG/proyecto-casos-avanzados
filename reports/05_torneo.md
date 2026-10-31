# Informe del torneo de modelos

> Resultado de `notebooks/05_torneo.ipynb`. El torneo **descarta**: elige 1–2 finalistas con evidencia, no un campeón.
> Cada candidato quedó como una ejecución en MLflow (experimento `libranzaradar-05-torneo`).

## Reglas del torneo

- **Mismos datos y mismos pliegues para todos:** 36.857 créditos de entrenamiento (27.725 clientes), 5 pliegues `StratifiedGroupKFold` **por cliente**, semilla 42.
- **Líneas base:** (1) la tasa de mora sin modelo; (2) la **regla del plazo corto** de un analista (puntaje = 1 / plazo).
- **Métrica principal (negocio):** recall de la mora con precisión ≥ 20 %. **Métricas técnicas:** AUC, PR-AUC de la mora, exactitud balanceada, precisión, recall y F1 de la mora (con el umbral de negocio de cada pliegue), log loss y Brier.
- **Variables usadas:** las 12 de la referencia (`reports/04_features.md`).

## Tabla comparativa

> Media ± desviación entre pliegues, ordenada por la métrica principal.

| Modelo | Recall de mora con precisión ≥ 20 % (± ruido) | Precisión lograda | % de créditos marcados | Segundos de ajuste |
|---|---|---|---|---|
| Random forest | 0,195 ± 0,050 | 0,200 | 15,6 % | 13,2 |
| XGBoost | 0,188 ± 0,095 | 0,200 | 15,1 % | 0,8 |
| LightGBM | 0,186 ± 0,075 | 0,200 | 15,0 % | 0,8 |
| Línea base: regla del plazo corto | 0,149 ± 0,020 | 0,210 | 11,4 % | 0,0 |
| Regresión logística | 0,116 ± 0,092 | 0,200 | 9,3 % | 0,4 |
| Línea base: tasa de mora (sin modelo) | 0,000 ± 0,000 | — | 0 % | 0,0 |

## Métricas técnicas

| Modelo | AUC | PR-AUC mora | Exactitud balanceada | Precisión mora | Recall mora | F1 mora | Log loss | Brier |
|---|---|---|---|---|---|---|---|---|
| XGBoost | 0,533 ± 0,009 | 0,181 ± 0,004 | 0,522 | 0,200 | 0,188 | 0,185 | 0,440 | 0,135 |
| LightGBM | 0,533 ± 0,007 | 0,180 ± 0,004 | 0,522 | 0,200 | 0,186 | 0,187 | 0,441 | 0,135 |
| Random forest | 0,531 ± 0,007 | 0,179 ± 0,004 | 0,523 | 0,200 | 0,195 | 0,195 | 0,645 | 0,226 |
| Regla del plazo corto | 0,533 ± 0,009 | 0,178 ± 0,003 | 0,521 | 0,210 | 0,149 | 0,174 | 0,590 | 0,148 |
| Regresión logística | 0,528 ± 0,010 | 0,177 ± 0,008 | 0,514 | 0,200 | 0,116 | 0,129 | 0,691 | 0,249 |
| Tasa de mora (sin modelo) | 0,500 | 0,161 | 0,500 | 0 | 0 | 0 | 0,441 | 0,135 |

> Las métricas de AUC de la clase de interés y AUC macro coinciden en un problema binario. Log loss y Brier de la
> regla, la logística y el random forest no son comparables: los dos últimos usan pesos balanceados (inflan las
> probabilidades) y la regla no produce probabilidades reales.

## ¿Coinciden los rankings de negocio y técnico?

| Modelo | Negocio | AUC | PR-AUC | Log loss |
|---|---|---|---|---|
| XGBoost | 2 | 2 | 1 | 2 |
| LightGBM | 3 | 4 | 2 | 3 |
| Random forest | 1 | 5 | 3 | 5 |
| Regla del plazo corto | 4 | 3 | 4 | 4 |
| Regresión logística | 5 | 6 | 5 | 6 |

- **¿El mejor por la métrica de negocio también es el mejor por AUC?** No. El random forest gana en negocio, pero es 5.º en AUC. Las diferencias de la métrica de negocio (0,186–0,195) están muy por debajo de su ruido (± 0,05–0,10): el orden en negocio es casi azar.
- **¿Hay modelos con AUC casi igual pero costo distinto?** Sí. La regla del plazo corto tiene el **mismo AUC** que XGBoost (0,533) pero menor recall (0,149 frente a 0,188), porque solo tiene 15 valores de plazo: no puede ajustar el umbral fino, así que marca menos créditos (11,4 %) con una precisión algo mayor (21 %).
- **¿Hay alguna clase con recall casi nulo?** La línea base sin modelo nunca alcanza el 20 % de precisión: recall 0. Ningún modelo detecta más del ~20 % de las moras con la precisión exigida: **8 de cada 10 moras pasan sin marcar**.

## Comparación pareada de los mejores

| Mejor | Contra | Métrica | Diferencia media | Pliegues que gana | Diferencia / ruido |
|---|---|---|---|---|---|
| XGBoost | LightGBM | PR-AUC | +0,0008 | 3 de 5 | 0,35 |
| XGBoost | Regla del plazo corto | PR-AUC | +0,0024 | 4 de 5 | 0,92 |
| XGBoost | Regla del plazo corto | Recall con precisión ≥ 20 % | +0,039 | 4 de 5 | 0,47 |
| XGBoost | Regla del plazo corto | AUC | +0,0002 | 3 de 5 | 0,02 |

Ninguna diferencia llega a 1 vez su ruido: **en validación cruzada, ningún modelo supera con claridad a la regla del plazo corto.**

## ¿Cuánto vale la diferencia?

- **Decisiones estimadas al mes:** 2.368 créditos aprobados (promedio de enero–junio de 2026 en la base) → ~380 caerían en mora.
- **Con la regla del plazo corto:** se revisan ~271 créditos y se detectan ~57 moras al mes.
- **Con XGBoost:** se revisan ~358 y se detectan ~72 moras al mes: **+15 moras detectadas** a cambio de **+87 revisiones**, pero dentro del ruido.
- **Diferencia entre el mejor y el siguiente** (XGBoost frente a LightGBM): ~1 mora al mes; indistinguible.

## Finalistas

| Finalista | Por qué | Qué podría cambiar con la optimización |
|---|---|---|
| XGBoost | Mejor PR-AUC y AUC, probabilidades útiles (log loss y Brier iguales a la tasa base, sin inflar), 0,8 s por pliegue | Árboles más pequeños o más regularizados podrían estabilizar el ranking |
| LightGBM | Prácticamente empatado con XGBoost en todo, igual de rápido | Ídem; sirve de contraste |

**Modelos descartados y por qué:** el random forest gana en negocio por una diferencia dentro del ruido, pero es 16 veces más lento y sus probabilidades (balanceadas) no se pueden leer como probabilidades de mora. La regresión logística es la peor en todas las métricas técnicas.

**Por qué el torneo no elige un campeón:** la mejor puntuación de validación cruzada es optimista (se eligió mirando muchas puntuaciones) y las diferencias entre los tres primeros son menores que su ruido. Elegir finalistas y comprobarlos en datos no vistos evita casarse con un ganador por azar.

## Efectos que la métrica principal no ve

- **Carga de trabajo:** con precisión de 20 %, por cada mora detectada hay 4 revisiones a créditos que pagarán bien. El modelo marca el 15 % de los créditos aprobados (~358 al mes); la regla, el 11 %.
- **Poca separación:** las probabilidades del modelo van de ~10 % a ~30 %. Nadie queda "seguro" ni en un extremo ni en el otro: el modelo **ordena** la revisión, no predice con certeza.
- **La regla es más fácil de explicar** y rinde casi igual. Si el modelo no la supera en la prueba, la recomendación honesta al negocio es usar la regla y concentrar el esfuerzo en conseguir mejores datos (historial de pagos del cliente con fechas, capacidad de pago, endeudamiento).
