# Especificación del proyecto

> Claude la lee antes de generar código: lo que está aquí manda sobre cualquier otra suposición.

## 1. Grupo

| Integrante | Rol (datos / modelado / app / negocio) |
|---|---|
| _(completar)_ | |
| _(completar)_ | |
| _(completar)_ | |

Nombre de la "startup": **LibranzaRadar**   Repositorio (público): _(completar enlace de GitHub)_

## 2. Caso de negocio

- **Pregunta de negocio:** al aprobar un crédito de libranza, ¿cuáles tienen más probabilidad de caer en más de 30 días de mora, para darles revisión y seguimiento prioritario con la empresa pagadora?
- **¿Quién usará el resultado y qué decisión tomará con él?** El analista de crédito de la caja de compensación: decide a qué créditos aprobados dar seguimiento prioritario en el portal de autogestión con la empresa pagadora. Conserva la decisión final.
- **¿Qué cuesta equivocarse?** El falso negativo (no detectar un crédito que caerá en mora) es el error más caro: pérdida de cartera y costos de cobranza. El falso positivo genera revisiones innecesarias y puede afectar la experiencia del cliente.

## 3. Datos

- **Fuente:** base sintética de cartera de libranza generada para el curso (`data/raw/Base_sintetica_creditos.csv`, no se sube al repo).
- **Filas / columnas:** 60.000 / 189 (46.050 / 17 tras la limpieza).
- **Variable objetivo:** `mora_30` = 1 si `DIAS DE MORA` > 30.
- **Tipo de problema:** ☒ clasificación  ☐ regresión  ☐ clusterización
- **¿Una misma entidad aparece en varias filas?** ☐ no  ☒ sí → la partición será por: **cliente** (`client_id`, seudónimo del documento).
- **Datos personales o confidenciales presentes:** ☐ no  ☒ sí → se eliminan al cargar (`load_raw`): nombres, documentos, direcciones, teléfonos y codeudores (49 columnas). El documento se reemplaza por un número de cliente (`c00001`...) que no se calcula a partir de él (sin clave secreta).
- **Licencia o permiso de uso de los datos:** base sintética entregada por el curso para uso académico.

## 4. Métrica

- **Métrica principal:** recall de la clase "en mora" con **precisión ≥ 20 %**. **Por qué:** el falso negativo es el error más caro (recall), pero no se puede mandar todo a revisión (precisión mínima). La exactitud engaña con 16 % de mora.
- **Métricas secundarias:** PR-AUC y AUC (capacidad de ordenar), log loss y Brier (calidad de las probabilidades), % de créditos marcados (carga de trabajo).
- **Línea base:** "nunca predecir mora" (recall 0); "revisar todo" (precisión 15,9 %, no cumple); **regla del plazo corto** (1/plazo), la que el modelo debe superar.

## 5. Riesgos

- **Fuga de información posible:** columnas posteriores a la aprobación (saldos, pagos, mora, estado, calificación); bloque de 3.619 créditos con condiciones reescritas tras la mora; créditos sin tiempo de exposición. Todo se trata en la limpieza.
- **Sesgos o equidad:** sexo, estado civil y edad no se usan como variables. Se revisan errores por segmento de plazo, producto y edad.
- **Datos faltantes o de mala calidad:** base sintética; tasa multiplicada por 10⁷; 98 columnas vacías o constantes.
- **Límites de lo que el modelo puede decir:** con la información al aprobar, la señal es débil (AUC ≈ 0,53). El modelo ordena la revisión; no predice con certeza quién caerá en mora.

## 6. Entregables y fechas

| Hito | Contenido | Fecha |
|---|---|---|
| H1 | Ficha, EDA y preprocesamiento reproducible | Cierre de la clase 2 (vie 30 oct) |
| H2 | Torneo, optimización con tracking, modelo registrado, repo modular, app local | Cierre de la clase 4 (jue 5 nov) |
| H3 | App desplegada y presentación (≤ 5 diapositivas) | Clase 5 (vie 6 nov) |
| H4 | Informe técnico final | Domingo 15 nov |

## 7. Decisiones tomadas

| Fecha | Decisión | Motivo |
|---|---|---|
| 30-oct-2026 | Precisión mínima = 20 % | 25 % mejor que revisar al azar; se fija antes de entrenar |
| 30-oct-2026 | Excluir el bloque `CONDICION ESPECIAL = 1` (3.619) | Condiciones reescritas después de la mora (fuga) |
| 30-oct-2026 | Exigir ≥ 4 meses de vida al corte (−10.331) | Sin exposición no hay tiempo de caer en mora |
| 30-oct-2026 | Partición y validación por cliente | 12.627 clientes con varios créditos |
| 30-oct-2026 | No usar sexo, estado civil ni edad | Atributos sensibles sin señal |
| 30-oct-2026 | Variables finales: 12 condiciones del crédito | Ninguna idea adicional superó el ruido (etapa 4) |
