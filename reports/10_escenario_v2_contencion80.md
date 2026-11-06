# Escenario futuro · LibranzaRadar 2.0: contención del 80 % de los créditos al día

> **Solo es un escenario.** No cambia el modelo, el umbral congelado, la app ni las decisiones del proyecto.
> No se abrió la prueba: todas las cifras salen de las **predicciones fuera de pliegue del entrenamiento**
> (`data/processed/oof_torneo.joblib`, 36.872 créditos, validación cruzada por cliente). Fecha: 5-nov-2026.

## 1. Qué significa "contención del 80 %"

El umbral se fija para que **8 de cada 10 créditos que están al día queden en seguimiento normal**, sin alerta. El
20 % restante de los créditos al día, más los que caen en mora, se marca para seguimiento prioritario. En la práctica
se revisa **1 de cada 5 créditos** (≈ 20 %), frente al 0,1 % que marca hoy el umbral congelado (0,301).

## 2. Opciones comparadas (misma contención: 80 % de los créditos al día sin marcar)

Mora en el entrenamiento: 15,8 %. Intervalos del 95 % remuestreando clientes completos (500 repeticiones).

### 2.1 Si "recuperar" = detectar más créditos en mora

| Opción | Créditos marcados | Moras detectadas (recall) | Precisión | Recall frente a LightGBM |
|---|---|---|---|---|
| **Plazo corto + LightGBM para desempatar** | 20,7 % | **24,3 %** [23,1 ; 25,4] | 18,6 % | +1,1 pts [+0,1 ; +2,1] |
| Promedio de los 3 modelos (LightGBM, XGBoost, logística) | 20,7 % | 24,1 % [23,0 ; 25,2] | 18,5 % | +0,9 pts [+0,2 ; +1,7] |
| LightGBM (modelo actual) | 20,5 % | 23,2 % [22,1 ; 24,2] | 17,9 % | — |
| XGBoost | 20,5 % | 23,0 % [21,9 ; 23,9] | 17,8 % | −0,2 pts [−1,0 ; +0,5] |
| Regresión logística | 20,5 % | 22,9 % [21,7 ; 23,9] | 17,7 % | −0,4 pts [−1,5 ; +0,8] |
| Al azar (referencia) | 20,1 % | 20,4 % [19,5 ; 21,5] | 16,1 % | −2,7 pts [−4,2 ; −1,2] |

"Plazo corto + LightGBM para desempatar" ordena primero por plazo (más corto = más riesgo) y, entre créditos con el
mismo plazo, usa la probabilidad del modelo.

### 2.2 Si "recuperar" = proteger más pesos de la cartera que cae en mora

Medida: qué parte del **monto desembolsado de los créditos que caen en mora** queda dentro de los marcados.

| Opción | Créditos marcados | Moras detectadas | % del monto en mora que queda marcado |
|---|---|---|---|
| **Pérdida esperada: probabilidad LightGBM × monto** | 19,6 % | 17,5 % | **74,6 %** [72,9 ; 76,1] |
| Solo monto (sin modelo) | 19,6 % | 17,5 % | 74,9 % [73,3 ; 76,4] |
| Al azar (referencia) | 20,1 % | 20,4 % | 20,2 % [18,1 ; 22,4] |
| LightGBM (probabilidad) | 20,5 % | 23,2 % | 13,9 % [12,2 ; 15,8] |
| Plazo corto + LightGBM para desempatar | 20,7 % | 24,3 % | 4,4 % |

## 3. En unidades del negocio (≈ 2.368 créditos aprobados y ≈ 375 moras al mes)

| Opción | Revisiones al mes | Moras detectadas al mes | Monto en mora cubierto |
|---|---|---|---|
| Hoy (umbral congelado 0,301) | ≈ 2 | ≈ 0 | ≈ 0 % |
| Plazo corto + desempate con el modelo | ≈ 490 | ≈ 91 | ≈ 4 % |
| Pérdida esperada (probabilidad × monto) | ≈ 465 | ≈ 66 | ≈ 75 % |

Cifras mensuales estimadas con las tasas de validación; no son resultados de la prueba.

## 4. Lo que hay que saber antes de presentarlo

1. **No cumple el criterio de precisión del proyecto.** Con la contención del 80 %, la precisión queda entre el 14 % y el
   18,6 %, por debajo del mínimo del 20 % fijado el 30-oct. Adoptarlo en una versión 2.0 sería **cambiar la regla
   del negocio**: aceptar más revisiones a cambio de detectar más moras. Lo decide el negocio, con su motivo escrito.
2. **Detectar más moras y proteger más pesos se contraponen.** Las moras se concentran en créditos de plazo corto, que
   son pequeños. Por eso las opciones que detectan más moras cubren muy poco dinero, y al revés.
3. **En pesos, el modelo no aporta hoy.** "Probabilidad × monto" rinde igual que ordenar solo por monto (diferencia
   −0,3 pts [−0,9 ; +0,2]). El 75 % sale de que **los créditos grandes concentran el dinero**, no de que el modelo
   detecte mejor el riesgo. La proporción de pesos marcados que cae en mora (13,9 %) es la misma que al azar (14,0 %).
   La ventaja de la fórmula es que, cuando el modelo mejore con mejores datos, ese avance pasa directo a los pesos.
4. **Las ganancias en número de moras son pequeñas:** como mucho 4 puntos sobre el azar. La señal sigue siendo débil (AUC ≈ 0,54).
5. **El monto es el desembolsado, no la pérdida real.** La pérdida real depende del saldo pendiente y de lo que se
   recupere en cobranza, datos que se conocen después de aprobar y que no se usan en el modelo para no generar fuga.
6. **Para validar la versión 2.0 hace falta una prueba nueva:** datos de créditos de un periodo posterior. La prueba
   actual ya se abrió tres veces y no se debe usar para elegir entre estas opciones.

## 5. Recomendación para la versión 2.0

**Priorizar por pérdida esperada (probabilidad de mora × monto del crédito), con una contención del 80 %.**

- **Motivo:** en libranza, la recuperación se mide en pesos. Con la misma carga de trabajo (1 de cada 5 créditos), esta
  opción cubre ≈ 75 % del monto que cae en mora. LightGBM solo cubre ≈ 14 %, y marcar al azar ≈ 20 %.
- **Con honestidad:** hoy ese resultado lo explica el monto, no el modelo. La fórmula queda lista para que el modelo
  aporte cuando se capturen mejores datos al aprobar (capacidad de pago, centrales de riesgo, antigüedad laboral, salud
  de la empresa pagadora).
- **Si el negocio prefiere contar moras y no pesos:** usar "plazo corto + modelo para desempatar". Es la opción con más
  recall (24,3 %), pero cubre muy poco dinero.
- **Cómo se vería en la app 2.0:** que muestre la probabilidad, el monto y la pérdida esperada, y que el analista pueda
  elegir la contención (70 %, 80 %, 90 %) viendo cuántas revisiones al mes implica.

## 6. Texto sugerido para la presentación (no se modificó `presentacion/ejecutiva.md`)

> **LibranzaRadar 2.0 (escenario futuro).** Si la caja acepta revisar 1 de cada 5 créditos (contención del 80 % de los
> créditos al día), ordenar por **pérdida esperada = probabilidad × monto** cubre ≈ **75 % del dinero** que cae en mora,
> frente a ≈ 14 % del modelo actual y ≈ 20 % al azar. Hoy esa ganancia la da el monto; el modelo sumará cuando
> tengamos mejores datos al aprobar. *Cifras de validación por cliente; requiere una prueba nueva antes de usarse.*

## Anexo: cómo reproducir las cifras

Desde la raíz del repositorio, en PowerShell: `$env:PYTHONUTF8=1; .venv\Scripts\python.exe` y pegar:

```python
import joblib, numpy as np
from scipy.stats import rankdata
o = joblib.load("data/processed/oof_torneo.joblib"); tr = joblib.load("data/processed/train.joblib")
y = o["mora_30"].values; amt = tr["loan_amount"].values.astype(float); term = tr["term_months"].values
r = lambda v: rankdata(v) / len(v)
scores = {
    "LightGBM": o["lightgbm"].values,
    "Promedio 3 modelos": (r(o["lightgbm"]) + r(o["xgboost"]) + r(o["regresión logística"])) / 3,
    "Plazo + desempate": r(-term) + r(o["lightgbm"]) * 1e-3,
    "Pérdida esperada": o["lightgbm"].values * amt,
    "Solo monto": amt,
}
for name, s in scores.items():
    f = s > np.quantile(s[y == 0], 0.80)          # 80 % de los créditos al día queda sin marcar
    tp = f & (y == 1)
    print(f"{name:20s} marcados {f.mean():.3f} recall {tp.sum()/(y==1).sum():.3f} "
          f"precisión {tp.sum()/f.sum():.3f} monto_en_mora_cubierto {amt[tp].sum()/amt[y==1].sum():.3f}")
```

Resultado esperado: LightGBM recall 0,232 y monto 0,139; Plazo + desempate recall 0,243; Pérdida esperada monto 0,746.
Los intervalos de confianza se calcularon aparte, remuestreando clientes completos (500 repeticiones, semilla 42).
