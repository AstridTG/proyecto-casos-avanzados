---
marp: true
theme: default
paginate: true
header: "Presentación ejecutiva · LibranzaRadar"
footer: "Casos Avanzados · Maestría en Ingeniería Analítica"
---

# 1 · ¿A qué créditos de libranza hay que hacerles seguimiento?

- **Quién decide:** el analista de crédito de la caja de compensación.
- **Qué decide:** a qué créditos recién aprobados dar **revisión y seguimiento prioritario** con la empresa pagadora.
- **Costo de equivocarse:** no detectar una mora = pérdida de cartera y cobranza (el peor error). Marcar a un buen cliente = una revisión de más.
- **Cada mes:** ≈ 2.400 créditos aprobados, ≈ 380 caerán en más de 30 días de mora.

> Queremos detectar el máximo de moras sin mandar a revisión a todo el mundo: **al menos 1 de cada 5 créditos priorizados debe caer en mora.**

---

# 2 · Cómo lo resolvimos

- **Datos:** 60.000 créditos sintéticos de libranza (41.855 clientes). Quitamos datos personales al cargar.
- **Solo lo que se sabe al aprobar:** plazo, monto, cuota, tasa, garantía, codeudor, producto y ciudad. Saldos, pagos y estado contienen la respuesta.
- **Dos trampas que evitamos:** 3.619 créditos vencidos con el plazo **reescrito a 1 mes** y 10.331 créditos **demasiado nuevos** para caer en mora.
- **Validación honesta:** partición **por cliente** y una prueba con clientes que el modelo nunca vio (abierta 3 veces, declarado en el informe).
- **Comparamos 5 modelos** contra una regla de analista ("plazo corto = más riesgo"). La historia del cliente, la empresa pagadora y la edad **no aportaron**.

---

# 3 · Resultado: el modelo no supera a la regla simple

| Al mes (≈ 385 moras) | Regla: plazo ≤ 6 meses | Modelo (LightGBM) |
|---|---|---|
| Créditos priorizados | ≈ 214 | ≈ 1 |
| Moras detectadas | ≈ 52 (13 %) | 0 |
| Precisión | 24 % | — |

- Con su umbral, el modelo **casi nunca prioriza**: la regla gana por **13 puntos de recall**, IC 95 % [11,6 ; 15,1].
- Para **ordenar** el riesgo, empatan (PR-AUC 0,193 frente a 0,186; la diferencia incluye el cero).
- Con lo que se sabe al aprobar, **casi 9 de cada 10 moras no se pueden anticipar.**
- *Cifras mensuales estimadas con las tasas de la prueba. Nota técnica:* AUC 0,54 en prueba (0,50 = azar).

---

# 4 · Demo de la app

**En local:** `streamlit run app/streamlit_app.py` (la app no se publica en la nube).

1. **Aviso al abrir:** la app dice que el modelo no supera a la regla y recomienda priorizar por plazo ≤ 6 meses.
2. **Caso normal:** crédito a 36 meses → 🟢 seguimiento normal (16 %, igual al promedio).
3. **Plazo corto:** crédito a 6 meses → 22 %, 1,4 veces el promedio, pero 🟢 seguimiento normal: no llega al umbral del modelo (30 %). La regla del plazo corto sí lo priorizaría. La app muestra qué dato pesó: el plazo.
4. **Dato inválido:** plazo = −5 → "Revisa los datos: Plazo (meses) debe estar entre 1 y 360".

> Plan B: captura con fecha y la app abierta antes de empezar.

---

# 5 · Riesgos y siguientes pasos

- **Qué NO hace:** no aprueba ni niega créditos, no fija tasas, no se usa para tratar distinto a un cliente. Decide el analista.
- **Límites:** base **sintética**; mora medida al corte (exposiciones distintas); el umbral del modelo, elegido en validación, casi no marca créditos.
- **Uso responsable:** no usa sexo, estado civil ni edad. Vigilar las tasas de marcado por ciudad.
- **Recomendación:** hoy, priorizar con la **regla del plazo corto** (transparente y mejor que el modelo con su umbral). Para mejorar de verdad, **capturar mejores datos al aprobar:** capacidad de pago, endeudamiento en centrales de riesgo, antigüedad laboral y salud de la empresa pagadora.

> **LibranzaRadar 2.0 (escenario futuro):** si la caja revisa 1 de cada 5 créditos (80 % de los créditos al día sin alerta), ordenar por **pérdida esperada = probabilidad × monto** cubre ≈ **75 % del dinero** que cae en mora, frente a ≈ 14 % del modelo actual y ≈ 20 % al azar. Hoy esa ganancia la da el monto; el modelo sumará con mejores datos. *Cifras de validación; requiere una prueba nueva.*
