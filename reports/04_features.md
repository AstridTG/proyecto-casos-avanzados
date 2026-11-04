# Informe de variables

> Resultado de `notebooks/04_features.ipynb`. Cada idea es una **hipótesis medida** con la misma validación; se
> conserva solo si la mejora supera el ruido entre pliegues. Tabla completa: `reports/04_features_tabla.csv`.
>
> **Cifras vigentes:** ejecución del 31-oct-2026 con la nueva numeración de clientes (ver `reports/07_validacion.md`,
> sección 0). Las decisiones son las mismas que en la versión del 30-oct (commit `e026f23`).

## Cómo se midió

- **Modelo (parámetros fijos):** LightGBM con los parámetros de partida del torneo (300 árboles, tasa 0,03, 15 hojas, ≥ 100 créditos por hoja).
- **Métrica de decisión:** **PR-AUC** de la clase "en mora". La métrica de negocio (recall con precisión ≥ 20 %) es muy ruidosa con esta señal: la precisión exigida está cerca del máximo alcanzable, así que el recall varía ± 0,06–0,09 de un pliegue a otro, más que su propio valor medio. PR-AUC mide lo mismo (ordenar bien la mora) sin depender de un único umbral.
- **Métricas de control:** la métrica de negocio y el AUC.
- **Pliegues:** 5, `StratifiedGroupKFold` **por cliente**, semilla 42. Los mismos para todas las variantes.
- **Regla de decisión escrita antes de medir:** una idea se conserva si su mejora de PR-AUC es **≥ 1 vez el ruido** (desviación de la diferencia pareada entre pliegues) **y** no empeora la métrica de negocio.

## Tabla de ideas medidas

| # | Idea (variable y cómo se calcula) | ¿Se conoce al predecir? | PR-AUC (± ruido) | Mejora / ruido | Negocio (± ruido) | Decisión |
|---|---|---|---|---|---|---|
| 0 | **Referencia:** plazo, monto, cuota, tasa EA, día de pago, garantía (sí/no y valor), codeudor, producto, tipo de negocio, destino económico, ciudad | ☒ sí | 0,1714 ± 0,0058 | 0 | 0,059 ± 0,078 | — |
| 1 | **Razones financieras:** cuota ÷ monto, log(monto), garantía ÷ monto | ☒ sí ☐ no | 0,1700 ± 0,0071 | −0,71 | 0,055 ± 0,058 | ☐ conservar ☒ descartar |
| 2 | **Historial:** créditos que el cliente abrió antes que este | ☒ sí ☐ no | 0,1711 ± 0,0062 | −0,18 | 0,058 ± 0,079 | ☐ conservar ☒ descartar |
| 3 | **Empresa pagadora:** tasa de mora de la empresa en entrenamiento (`TargetEncoder` con validación cruzada interna) | ☒ sí ☐ no | 0,1709 ± 0,0091 | −0,15 | 0,053 ± 0,079 | ☐ conservar ☒ descartar |
| 4 | **Edad** del cliente | ☒ sí ☐ no | 0,1708 ± 0,0050 | −0,26 | 0,073 ± 0,082 | ☐ conservar ☒ descartar |
| 5 | Todas las ideas juntas | ☒ sí ☐ no | 0,1698 ± 0,0074 | −0,88 | 0,063 ± 0,087 | ☐ conservar ☒ descartar |

## Decisiones y motivos

- **Razones financieras: descartadas.** Bajan la PR-AUC en 0,0013 (−0,71 veces el ruido) y la métrica de negocio. La cuota y el monto ya están como variables: el árbol puede combinarlos solo.
- **Historial del cliente: descartado.** No mejora (−0,18 veces el ruido). Es coherente con el EDA: tener créditos previos no cambia la tasa de mora de forma distinguible.
- **Empresa pagadora: descartada.** No mejora (−0,15 veces el ruido) y es la variante con más ruido entre pliegues (± 0,0091). Con 421 empresas y una mediana de 32 créditos cada una, su tasa de mora es sobre todo azar (EDA: desviación 0,036 frente a 0,035 esperada por azar) y el modelo se ajusta a ese ruido.
- **Edad: descartada.** No mejora la PR-AUC (−0,26 veces el ruido) y es un atributo de uso regulado: no vale la pena el riesgo. Sube un poco la métrica de negocio (0,073 frente a 0,059), pero muy dentro de su ruido (± 0,08).
- **Todas juntas: descartadas.** Sumar ideas que no aportan agrega ruido.

## Supuestos y riesgos

- Todas las ideas se conocen al aprobar, así que no hay riesgo de fuga. La empresa pagadora sí lo tendría si se codificara con su tasa de mora de **toda** la base; por eso se codifica dentro del `Pipeline` con validación cruzada interna.
- Conservar la empresa obligaría a la app a pedir un código de empresa y a manejar empresas nuevas. Descartarla simplifica la app.

## Qué se lleva el pipeline final

Las **12 variables de la referencia** (`reports/04_features_finales.json`): `term_months`, `loan_amount`, `monthly_installment`, `interest_rate_ea`, `due_day`, `has_guarantee`, `guarantee_value`, `has_cosigner`, `product`, `business_type`, `economic_destination` y `city`.

Código: `src/proyecto/features/engineering.py` (`feature_set`, `build_preprocessor`, `add_features`). El preprocesamiento (mediana para numéricas, "desconocido" + one-hot con categorías raras agrupadas para categóricas) va dentro del `Pipeline` y se ajusta solo con entrenamiento.
