# Ficha de caso

> Estados: `borrador` → (`devuelta` → `borrador`)* → `aprobada`. Solo con la ficha **aprobada** se avanza al EDA.

- **case_id:** libranzaradar
- **business_question:** LibranzaRadar es una startup que apoya a una caja de compensación en la modernización de su operación de libranza. Al momento de aprobar un crédito, el analista de crédito no sabe cuáles tienen más probabilidad de caer en mora. Queremos un modelo que, con la información disponible al aprobar el crédito, estime la probabilidad de que caiga en más de 30 días de mora, para priorizar la revisión y el seguimiento con las empresas pagadoras a través de un portal de autogestión. El analista conserva la decisión final.
- **dataset_source:** Base sintética de cartera de créditos generada para el curso (`Base_sintetica_creditos.csv`), con la estructura de columnas de un sistema de cartera de libranza. No contiene datos de clientes reales; las columnas con datos personales se eliminan al inicio (`load_raw`). Uso académico.
- **dataset_rows:** 60.000 (un crédito por fila; 41.855 clientes, 12.627 con más de un crédito)
- **dataset_columns:** 189 (98 vacías o constantes en la base cruda)
- **target:** `mora_30` = 1 si `DIAS DE MORA` > 30, 0 si no (19,0 % de los créditos en la base cruda; 15,9 % tras la limpieza)
- **problem_type:** clasificación binaria
- **primary_metric:** recall de la clase "en mora" exigiendo una **precisión mínima del 20 %** (de cada 5 créditos priorizados, al menos 1 cae en mora: 25 % mejor que revisar al azar, cuya precisión es la tasa de mora). Las clases están desbalanceadas, así que la exactitud no sirve: un modelo que nunca prediga mora acertaría el 81 % sin detectar nada. Métricas de control: PR-AUC, AUC y porcentaje de créditos marcados (carga de revisión).
- **business_cost_note:** No detectar un crédito que caerá en mora (falso negativo) genera pérdidas de cartera y costos de cobranza. Marcar como riesgoso a un buen cliente (falso positivo) genera revisiones innecesarias y puede afectar la experiencia del cliente. El falso negativo es el error más costoso; la precisión mínima limita la carga de revisiones innecesarias.
- **status:** borrador
- **reviewer_notes:** <!-- las llena el instructor -->
