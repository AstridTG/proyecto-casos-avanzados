# Ficha de caso

> Instrucciones y un ejemplo completo (CreditSight): `material-del-curso/evaluacion/ficha-de-caso.md`.
> Estados: `borrador` → (`devuelta` → `borrador`)* → `aprobada`. Solo con la ficha **aprobada** se avanza al EDA.
> Lo marcado **PROPUESTA – por confirmar** o **POR DEFINIR** lo decide el grupo antes de presentar la ficha.

- **case_id:** POR DEFINIR (PROPUESTA: `libranza-autogestion`)
- **business_question:** (PROPUESTA – por confirmar) Comfama, en su iniciativa *Servicios Financieros 2.0*,
  quiere que las empresas gestionen la libranza de sus colaboradores de forma digital y que el área de
  cartera trabaje con datos. Queremos un modelo que, a partir de las características de cada crédito,
  estime qué créditos tienen más probabilidad de llegar a más de 30 días de mora, para que la empresa (en el
  portal de autogestión) y el equipo de cartera prioricen a quién contactar primero. La persona conserva la
  decisión final.
- **dataset_source:** `Base_sintetica_creditos.csv`, base sintética de créditos de consumo y libranza.
  Origen y licencia: POR DEFINIR (confirmar con el instructor si puede publicarse).
- **dataset_rows:** 60.000 (cumple el mínimo de 50.000)
- **dataset_columns:** 189 (91 con información: 26 están vacías y 72 son constantes). Incluye datos personales
  sintéticos (nombres, documentos, direcciones y teléfonos de clientes y codeudores) que se eliminan al cargar.
- **target:** (PROPUESTA – por confirmar) `EN_RIESGO`, construida como `DIAS DE MORA` > 30: 1 = 19,0 %
  (11.397), 0 = 81,0 % (48.603). La columna `EVENTO` del archivo **se omite**: su significado no está
  documentado y no se relaciona con la mora. Unidad de análisis: **crédito**; 41.855 clientes con 1 a 4
  créditos cada uno, por eso la partición se hace **por cliente**. Las columnas de mora actual (caja de mora,
  calificación, estado, cuotas vencidas) se excluyen porque contienen la respuesta.
- **problem_type:** clasificación binaria (desbalanceada: 19 % positivos)
- **primary_metric:** POR DEFINIR. PROPUESTA: recall de `EN_RIESGO` = 1 con una precisión mínima acordada, o un
  costo esperado con una matriz de costos de negocio. La exactitud no sirve: predecir siempre "no en riesgo"
  ya da 81,0 %.
- **business_cost_note:** Un falso negativo (no detectar un crédito que llegará a más de 30 días de mora)
  aumenta la cartera vencida y la provisión; es el error más caro. Un falso positivo genera gestiones
  innecesarias y una mala experiencia para la empresa y el colaborador. Valores de cada costo: POR DEFINIR.
- **status:** borrador
- **reviewer_notes:** <!-- las llena el instructor -->
