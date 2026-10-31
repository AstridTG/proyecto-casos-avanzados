# Validación e interpretación

> Resultado de `notebooks/07_validacion_interpretacion.ipynb`. Cifras en `reports/07_metricas_test.json`.

## 1. Decisiones congeladas (escritas ANTES de abrir la prueba)

| Decisión | Valor | Cómo se decidió (con qué datos) |
|---|---|---|
| Modelo final | XGBoost | Torneo (validación cruzada por cliente) y comprobación en clientes reservados |
| Parámetros | De partida (300 árboles, tasa 0,03, profundidad 4) | La optimización no mejoró de forma distinguible en clientes reservados (`reports/06_optimizacion.md`) |
| Variables | 12 condiciones del crédito conocidas al aprobar | Ninguna idea adicional superó el ruido (`reports/04_features.md`) |
| ¿Calibrar las probabilidades? | No | Brier igual con y sin calibración isotónica en clientes reservados (0,1307) |
| Métrica principal | Recall de la mora con el **umbral fijo** elegido en validación | Ficha de caso |
| Regla de decisión | Priorizar revisión si probabilidad ≥ **0,1927** | Umbral con mayor recall y precisión ≥ 20 % en predicciones fuera de pliegue de todo el entrenamiento (recall 15,1 %, 12,2 % marcados) |
| Baseline | Regla del plazo corto: priorizar si plazo ≤ 9 meses | Mismo criterio de umbral sobre 1/plazo en el entrenamiento |
| **Fecha y hora en que se congelaron** | 30-oct-2026 21:35 (primera ejecución) y 21:37 (segunda, idénticas) | `reports/07_decisiones_congeladas.json` |

## 2. Calibración (con clientes reservados, no con la prueba)

- ¿Se evaluó? ☒ sí  ☐ no
- **Resultado y decisión:** el modelo sin calibrar ya está bien calibrado: probabilidad media 16,2 % frente a 15,5 % real; Brier 0,1307 sin calibrar y 0,1307 con isotónica; log loss 0,4301 frente a 0,4302. En la curva de calibración, las probabilidades predichas (12 %–22 %) siguen a las observadas (12 %–20 %). **No se calibra.** La app puede mostrar la probabilidad como "probabilidad estimada de mora".

## 3. La prueba, abierta **una sola vez**

- **Fecha y hora:** 30-oct-2026 21:35:38 (`reports/prueba_abierta.txt`).
- **Declaración:** la marca registra **dos aperturas** (21:35:38 y 21:37:46). La primera ejecución del notebook falló **después** de calcular las métricas, por un error de programación en la celda de guardado: la variable `filas` se sobrescribía con la tabla de segmentos. Se corrigió solo el nombre de la variable y se volvió a ejecutar. **Las decisiones congeladas son idénticas en las dos ejecuciones** (se comparó el archivo) y no se cambió nada del modelo, el umbral ni la métrica.
- ¿Se cambió algo del modelo después de verla? ☒ no  ☐ sí

**Prueba:** 9.193 créditos de 6.932 clientes que el modelo nunca vio; mora real 15,3 %.

| Métrica | Modelo final (XGBoost) | Baseline (regla del plazo corto) | Intervalo del 95 % (clientes) |
|---|---|---|---|
| **Recall de la mora** (métrica principal) | **0,149** | 0,154 | modelo [0,130 ; 0,167] · regla [0,135 ; 0,172] |
| Precisión (exigida ≥ 0,20) | 0,192 | 0,189 | modelo [0,169 ; 0,214] · regla [0,168 ; 0,210] |
| PR-AUC | 0,171 | 0,171 | modelo [0,159 ; 0,184] · regla [0,160 ; 0,183] |
| AUC | 0,527 | 0,538 | modelo [0,509 ; 0,544] · regla [0,520 ; 0,554] |
| % de créditos marcados | 11,8 % | 12,5 % | — |

**¿Mejora al baseline con confianza?** **No.** Diferencias modelo − regla, remuestreando clientes completos (1.000 repeticiones):

| Métrica | Modelo − regla | Intervalo del 95 % |
|---|---|---|
| Recall de la mora | −0,006 | [−0,020 ; +0,010] |
| PR-AUC | +0,000 | [−0,007 ; +0,008] |
| AUC | −0,011 | [−0,028 ; +0,006] |

Todos los intervalos incluyen el cero: **el modelo y la regla del plazo corto rinden igual.** Además, la precisión en la prueba (19,2 %) quedó un poco por debajo del 20 % exigido, aunque su intervalo lo incluye: el umbral elegido en validación no garantiza el 20 % en datos nuevos.

**En unidades del negocio** (≈ 2.368 créditos aprobados y ≈ 380 moras al mes): el modelo prioriza ≈ 280 créditos y detecta ≈ 56 moras al mes; la regla prioriza ≈ 296 y detecta ≈ 59. **Unas 324 de cada 380 moras pasan sin marcar con cualquiera de los dos.**

## 4. Errores y carga de trabajo

| Segmento | Casos | Mora real | % que el modelo marca | Recall | Precisión |
|---|---|---|---|---|---|
| Plazo ≤ 12 meses | 2.556 | 17,9 % | 38,1 % | 41,4 % | 19,4 % |
| Plazo 13–36 meses | 3.031 | 15,0 % | 2,1 % | 2,4 % | 17,2 % |
| Plazo 37–72 meses | 1.642 | 13,1 % | 0,2 % | 0,0 % | — |
| Plazo > 72 meses | 1.964 | 14,2 % | 2,3 % | 3,2 % | 19,6 % |
| Producto 128 | 864 | 16,2 % | 36,6 % | 37,1 % | 16,5 % |
| Producto 120 | 2.585 | 14,1 % | 1,9 % | 1,4 % | 10,0 % |
| Edad 18–30 | 2.006 | 16,0 % | 12,1 % | 16,8 % | 22,2 % |
| Edad 46–60 | 2.532 | 15,4 % | 12,6 % | 11,0 % | 13,5 % |
| Edad > 60 | 2.054 | 14,4 % | 11,7 % | 18,3 % | 22,4 % |

Tabla completa: `reports/07_errores_por_segmento.csv`.

- **¿Hay un segmento al que le va peor?** Sí, a los créditos de **plazo largo**: el modelo casi no los marca (0,2 %–2,3 %), aunque el 13 %–15 % caen en mora. En la práctica, el modelo es la regla del plazo corto con matices: el 38 % de los créditos a ≤ 12 meses se marcan. Por edad (que el modelo **no** usa), el % marcado es parejo (11,7 %–12,6 %), pero la precisión en 46–60 años es menor (13,5 %).
- **Carga de trabajo:** el modelo marca el 11,8 % de los créditos frente a una mora real del 15,3 %: la carga es manejable (~280 revisiones al mes), pero 4 de cada 5 revisiones son a créditos que pagarán bien.

## 5. Interpretación

- **Variables que más pesan (SHAP medio absoluto, `reports/07_importancia_shap.csv`):** plazo (0,082), cuota mensual (0,050), monto (0,047), tasa EA (0,040) y valor de la garantía (0,029); después, el producto 120 y algunas ciudades con pesos pequeños. **Para el negocio:** el plazo corto concentra el riesgo; la cuota, el monto y la tasa matizan dentro de cada plazo.
- **Límite de la explicación:** SHAP explica **al modelo, no al mundo**. Dice qué datos movieron la probabilidad calculada, no por qué una persona deja de pagar, y no dice si el modelo acertó. Con AUC 0,53, buena parte de lo que "explica" es ruido.
- **Atributos sensibles o de uso regulado:** sexo, estado civil y edad **no** son variables del modelo. La ciudad sí lo es (pesos pequeños); puede actuar como aproximación de condiciones socioeconómicas, así que conviene vigilar las tasas de marcado por ciudad antes de usarlo con datos reales.

## 6. Conclusión

- **¿El modelo sirve para la decisión del caso?** No mejor que la regla simple. Con la información disponible al aprobar, **ni el modelo ni la regla** separan bien a quienes caerán en mora: cualquiera de los dos detecta ~15 % de las moras revisando ~12 % de los créditos. La recomendación honesta al negocio es: (1) usar la **regla del plazo corto** como criterio transparente de priorización, o el modelo si se prefiere un puntaje continuo para ordenar la cola; y (2) invertir en **mejores datos al aprobar**: capacidad de pago (ingreso, descuentos de nómina vigentes), endeudamiento externo (centrales de riesgo), antigüedad laboral y estabilidad de la empresa pagadora.
- **Qué NO debe hacerse con él:** negar o aprobar créditos, fijar tasas o montos, o tratar distinto a un cliente por su puntaje. Tampoco usarlo con clientes reales sin volver a entrenarlo y validarlo con datos reales (la base es sintética).
