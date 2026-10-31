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
- **Validación honesta:** partición **por cliente** y prueba abierta una sola vez.
- **Comparamos 5 modelos** contra una regla de analista ("plazo corto = más riesgo"). La historia del cliente, la empresa pagadora y la edad **no aportaron**.

---

# 3 · Resultado: el modelo empata con la regla simple

| Al mes (≈ 380 moras) | Regla: plazo ≤ 9 meses | Modelo (XGBoost) |
|---|---|---|
| Créditos priorizados | ≈ 296 | ≈ 280 |
| Moras detectadas | ≈ 59 (15 %) | ≈ 56 (15 %) |
| Precisión | 19 % | 19 % |

- Diferencia de recall modelo − regla: **−0,6 puntos**, IC 95 % [−2,0 ; +1,0]: **no hay mejora.**
- Con lo que se sabe al aprobar, **8 de cada 10 moras no se pueden anticipar.**
- *Nota técnica:* AUC 0,53 en prueba (0,50 = azar).

---

# 4 · Demo de la app

**Enlace:** _(completar con el enlace público)_

1. **Caso normal:** crédito a 36 meses → 🟢 seguimiento normal (15 %).
2. **Caso límite:** crédito a 6 meses → 🔴 priorizar (23 %, 1,5 veces el promedio). La app muestra qué dato pesó: el plazo.
3. **Dato inválido:** plazo = −5 → "Revisa los datos: Plazo (meses) debe estar entre 1 y 360".

> Plan B: captura con fecha y la app en local (`streamlit run app/streamlit_app.py`).

---

# 5 · Riesgos y siguientes pasos

- **Qué NO hace:** no aprueba ni niega créditos, no fija tasas, no se usa para tratar distinto a un cliente. Decide el analista.
- **Límites:** base **sintética**; mora medida al corte (exposiciones distintas); precisión en prueba 19 %, un poco por debajo del 20 % pedido.
- **Uso responsable:** no usa sexo, estado civil ni edad. Vigilar las tasas de marcado por ciudad.
- **Recomendación:** hoy, priorizar con la **regla del plazo corto** (transparente e igual de buena). Para mejorar de verdad, **capturar mejores datos al aprobar:** capacidad de pago, endeudamiento en centrales de riesgo, antigüedad laboral y salud de la empresa pagadora.
