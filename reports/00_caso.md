# Ficha de caso

> Instrucciones y un ejemplo completo (CreditSight): `material-del-curso/evaluacion/ficha-de-caso.md`.
> Estados: `borrador` → (`devuelta` → `borrador`)* → `aprobada`. Solo con la ficha **aprobada** se avanza al EDA.

- **case_id:** `libranzaradar`
- **business_question:** LibranzaRadar es una startup que apoya a una caja de compensación en la modernización
  de su operación de libranza. Al momento de aprobar un crédito, el analista de crédito no sabe cuáles tienen más
  probabilidad de caer en mora. Queremos un modelo que, con la información disponible al aprobar el crédito,
  estime la probabilidad de que caiga en más de 30 días de mora, para priorizar la revisión y el seguimiento con
  las empresas pagadoras a través de un portal de autogestión. El analista conserva la decisión final.
- **dataset_source:** Base sintética de cartera de créditos generada para el curso, con la estructura de columnas
  de un sistema de cartera de libranza. No contiene datos de clientes reales; las columnas con datos personales
  se eliminan al inicio.
- **dataset_rows:** 60.000 (un crédito por fila; 41.855 clientes, 12.627 con más de un crédito)
- **dataset_columns:** 189 (unas 98 vacías o constantes: 26 vacías al 100 % y 72 con un único valor)
- **target:** `mora_30` = 1 si `DIAS DE MORA` > 30, 0 si no (19 % de los créditos: 11.397 de 60.000). La columna
  `EVENTO` del archivo se omite: su significado no está documentado y no se relaciona con la mora. Como un
  mismo cliente tiene hasta 4 créditos, la partición se hace **por cliente** (`id_cliente`). Solo se usan
  variables conocidas al aprobar el crédito; las de mora y pagos posteriores se excluyen porque contienen la
  respuesta.
- **problem_type:** clasificación (binaria)
- **primary_metric:** recall de la clase "en mora", exigiendo una precisión mínima. Las clases están
  desbalanceadas (19 %), así que la exactitud no sirve: un modelo que nunca prediga mora acertaría el 81 % sin
  detectar nada.
- **business_cost_note:** No detectar un crédito que caerá en mora (falso negativo) genera pérdidas de cartera y
  costos de cobranza. Marcar como riesgoso a un buen cliente (falso positivo) genera revisiones innecesarias y
  puede afectar la experiencia del cliente. El falso negativo es el error más costoso. (El valor en pesos de
  cada error y la precisión mínima exigida están por definir.)
- **status:** borrador
- **reviewer_notes:**
