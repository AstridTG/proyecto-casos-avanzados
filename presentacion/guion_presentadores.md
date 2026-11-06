# Guion de la presentación · LibranzaRadar (H3, 6-nov-2026)

> Una diapositiva por integrante, **≈ 1 minuto cada una** (≈ 5–6 minutos en total).
> El orden de presentadores es una **sugerencia** (sigue el orden de `especificacion-proyecto.md`); cámbienlo como prefieran.
> Todas las cifras salen de `presentacion/ejecutiva.md`, `reports/07_validacion.md` y `reports/10_escenario_v2_contencion80.md`.

| # | Diapositiva | Presenta (sugerido) |
|---|---|---|
| 1 | El problema de negocio | Juan Rafael Taborda |
| 2 | Cómo lo resolvimos | Yenifer Tatiana Calle Zapata |
| 3 | Resultado: el modelo no supera a la regla | Daniela Acevedo Alvares |
| 4 | Demo de la app | Liliana Maria Garcia Builes |
| 5 | Riesgos, siguientes pasos y escenario 2.0 | Astrid Liliana Torres Gonzalez |

---

## 1 · ¿A qué créditos de libranza hay que hacerles seguimiento?

**Qué decir:**
"Somos LibranzaRadar. Ayudamos al analista de crédito de la caja de compensación a decidir a qué créditos recién
aprobados darles seguimiento prioritario con la empresa pagadora. Cada mes se aprueban unos 2.400 créditos y unos 380
caen en más de 30 días de mora. El error más caro es no detectar una mora: se pierde cartera y sube la cobranza.
Marcar a un buen cliente solo cuesta una revisión de más. Por eso nuestra meta fue detectar el máximo de moras,
pero con una condición: al menos 1 de cada 5 créditos priorizados debe caer de verdad en mora."

**Cifras clave:** ≈ 2.400 créditos al mes · ≈ 380 moras al mes · precisión mínima 20 %.

**Paso a la siguiente:** "¿Cómo lo resolvimos? Les cuenta Yenifer."

---

## 2 · Cómo lo resolvimos

**Qué decir:**
"Trabajamos con 60.000 créditos sintéticos de libranza y quitamos los datos personales al cargarlos. Usamos solo lo
que se sabe al momento de aprobar: plazo, monto, cuota, tasa, garantía, codeudor, producto y ciudad. Saldos, pagos y
estado no, porque ya contienen la respuesta. Evitamos dos trampas: 3.619 créditos vencidos con el plazo reescrito a
1 mes y 10.331 créditos demasiado nuevos para caer en mora. Partimos los datos por cliente, para que un mismo cliente
no quedara en entrenamiento y en prueba a la vez. Comparamos cinco modelos contra una regla de analista: 'plazo corto
es más riesgo'."

**Cifras clave:** 60.000 créditos · 3.619 reescritos · 10.331 demasiado nuevos · 5 modelos contra 1 regla.

**Paso a la siguiente:** "¿Y qué salió? Daniela."

---

## 3 · Resultado: el modelo no supera a la regla simple

**Qué decir:**
"El resultado honesto es que el modelo no le gana a la regla simple. Con el umbral que elegimos en validación, el
modelo casi nunca prioriza: un crédito al mes y ninguna mora detectada. La regla 'plazo menor o igual a 6 meses'
prioriza unos 214 créditos al mes y detecta unas 52 moras, el 13 %, con precisión del 24 %. Para ordenar el riesgo
empatan. La conclusión es que, con lo que se sabe al aprobar, casi 9 de cada 10 moras no se pueden anticipar con
estos datos."

**Cifras clave:** regla: 214 priorizados, 52 moras (13 %), precisión 24 % · modelo: ≈ 1 priorizado, 0 moras · AUC 0,54 (0,50 = azar).

**Paso a la siguiente:** "Igual construimos la herramienta. Liliana les muestra la app."

---

## 4 · Demo de la app

**Qué decir y hacer** (tener la app abierta antes de empezar con `scripts\run_app.bat`):
1. "Al abrir, la app avisa que el modelo no supera a la regla y recomienda priorizar por plazo ≤ 6 meses."
2. Caso normal, crédito a 36 meses → 🟢 seguimiento normal, 16 %, igual al promedio.
3. Plazo corto, crédito a 6 meses → 22 %, 1,4 veces el promedio, pero 🟢 seguimiento normal porque no llega al umbral del modelo (30 %). "La regla sí lo priorizaría. La app muestra que el dato que pesó fue el plazo."
4. Dato inválido, plazo −5 → "Revisa los datos: Plazo (meses) debe estar entre 1 y 360."

**Plan B:** si la app falla, mostrar `presentacion/captura_app.png`.

**Paso a la siguiente:** "Para cerrar, riesgos y lo que sigue. Astrid."

---

## 5 · Riesgos, siguientes pasos y escenario 2.0

**Qué decir:**
"La herramienta no aprueba ni niega créditos ni fija tasas: decide el analista. La base es sintética y no usamos
sexo, estado civil ni edad. Nuestra recomendación hoy es priorizar con la regla del plazo corto y capturar mejores
datos al aprobar: capacidad de pago, centrales de riesgo y antigüedad laboral.
Como escenario futuro, LibranzaRadar 2.0: si la caja acepta revisar 1 de cada 5 créditos, ordenar por probabilidad
por monto cubre cerca del 75 % del dinero que cae en mora, frente al 14 % del modelo actual y al 20 % al azar. Hoy
esa ganancia la explica el monto, no el modelo; el modelo sumará cuando tengamos mejores datos."

**Cifras clave:** 1 de cada 5 revisados · ≈ 75 % del dinero en mora (modelo actual ≈ 14 %, azar ≈ 20 %).

**Cierre:** "Gracias. ¿Preguntas?"

---

## Preguntas probables y quién responde

| Pregunta | Respuesta corta | Responde |
|---|---|---|
| ¿Por qué no usaron el modelo si lo entrenaron? | Porque en la prueba no superó a la regla. Recomendar algo que no gana sería engañar al negocio. | Daniela |
| ¿Por qué la prueba se abrió 3 veces? | Ver el argumento completo abajo. En corto: fueron dos ejecuciones, no tres; la segunda la causó una corrección de datos personales, y conservamos el resultado peor. | Yenifer |
| ¿El 75 % del escenario 2.0 es mérito del modelo? | No. Ordenar solo por monto da lo mismo: los créditos grandes concentran el dinero. La fórmula sirve para cuando el modelo mejore. | Astrid |
| ¿Ese escenario cumple la precisión del 20 %? | No, queda entre 14 % y 19 %. Adoptarlo sería un cambio de la regla del negocio, y necesita una prueba nueva. | Astrid |
| ¿Por qué no usaron la edad si podría ayudar? | Es un atributo sensible y además no aportó señal. | Juan Rafael |
| ¿La app consulta alguna base o la nube? | No. Corre en local y carga el modelo desde el repositorio. | Liliana |

---

## Argumento: ¿por qué la prueba se abrió 3 veces? (Yenifer)

**Versión de 30 segundos (para decir en voz alta):**
"La prueba aparece abierta tres veces, pero fueron dos ejecuciones. La primera falló al guardar después de calcular
las métricas, y la repetimos dos minutos después corrigiendo solo el nombre de una variable. La segunda ejecución,
al día siguiente, no fue para buscar un mejor resultado: corregimos un problema de datos personales. El identificador
del cliente era un hash con una sal publicada en el repositorio, y con eso se podía recuperar el documento. Al
cambiarlo por un número, la partición por cliente cambió y todo el proyecto quedó desactualizado. La prueba de que no
elegimos el resultado: la primera vez el modelo empataba con la regla y la segunda no detectó ninguna mora. Nos
quedamos con el resultado peor porque es el único que se puede reproducir con el código actual. Todo está declarado
en el informe."

**Los cuatro puntos, por si preguntan más:**

1. **Fueron dos ejecuciones, no tres.** Las aperturas del 30-oct (21:35 y 21:37) son la misma corrida: falló al
   guardar *después* de calcular las métricas y se corrigió solo el nombre de una variable. Nada del modelo cambió.
2. **La tercera tuvo una causa ajena al resultado: la protección de datos.** El identificador del cliente era un hash
   del documento con una sal pública; con la sal en el repositorio, el documento se podía recuperar probando números.
   Se cambió por una numeración (`c00001`…) (commit `94d0369`). Como la partición se hace por cliente, cambió quién
   quedaba en prueba (9.193 → 9.178 créditos) y hubo que regenerar los notebooks 03 a 09 para que todo el grupo
   obtuviera la misma partición.
3. **Con la prueba no se decidió nada.** El cambio de XGBoost a LightGBM lo hizo la regla del notebook 06, escrita
   antes y aplicada con clientes reservados de validación (estaban empatados: 0,1710 frente a 0,1705). El umbral se
   eligió con predicciones fuera de pliegue del entrenamiento. Las decisiones quedaron congeladas en
   `reports/07_decisiones_congeladas.json` antes de abrir la prueba.
4. **Nos quedamos con el resultado peor, y eso muestra que no hubo selección.** Primera apertura: el modelo empataba
   con la regla (recall 0,149 frente a 0,154). Apertura vigente: recall 0,000. Si hubiéramos usado la prueba para
   escoger, habríamos vuelto a la versión anterior. No lo hicimos, porque eso sí sería usar la prueba para decidir.

**Lo que reconocemos (no lo escondan si lo preguntan):**
- La prueba vigente no es tan limpia como una abierta una sola vez: el grupo ya había visto los resultados de la
  anterior, y parte de esos clientes quedó en el entrenamiento nuevo.
- Antes de abrir la prueba por tercera vez ya sabíamos, en validación, que el umbral de LightGBM marcaba solo el
  0,1 % de los créditos. Eso debió frenarnos. La regla de decisión no exigía un mínimo de créditos marcados; lo
  aprendimos y lo dejamos como lección.
- Por eso el informe pide una **prueba nueva con créditos de un periodo posterior** antes de usar cualquier modelo.

**Fuentes:** `reports/prueba_abierta.txt`, `reports/07_validacion.md` (sección 0) y `reports/informe_tecnico.md`.
