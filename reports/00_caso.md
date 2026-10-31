# Ficha de caso

> Instrucciones y un ejemplo completo (CreditSight): `material-del-curso/evaluacion/ficha-de-caso.md`.
> Estados: `borrador` → (`devuelta` → `borrador`)* → `aprobada`. Solo con la ficha **aprobada** se avanza al EDA.
> Lo marcado **PROPUESTA – por confirmar** o **POR DEFINIR** lo decide el grupo antes de presentar la ficha.

- **case_id:** POR DEFINIR (PROPUESTA: `libranza-autogestion`)
- **business_question:** (PROPUESTA – por confirmar) Comfama, en su iniciativa *Servicios Financieros 2.0*,
  quiere que las empresas gestionen la libranza de sus colaboradores de forma digital y que el área de
  cartera trabaje con datos. Queremos un modelo que, a partir de las características de cada crédito,
  estime qué créditos tienen más probabilidad de presentar el evento objetivo, para que la empresa (en el
  portal de autogestión) y el equipo de cartera prioricen a quién contactar primero. La persona conserva la
  decisión final.
- **dataset_source:** `Base_sintetica_creditos.csv`, base sintética de créditos de consumo y libranza.
  Origen y licencia: POR DEFINIR (confirmar con el instructor si puede publicarse).
- **dataset_rows:** 60.000 (cumple el mínimo de 50.000)
- **dataset_columns:** 189 (91 con información: 26 están vacías y 72 son constantes). Incluye datos personales
  sintéticos (nombres, documentos, direcciones y teléfonos de clientes y codeudores) que se eliminan al cargar.
- **target:** (PROPUESTA – por confirmar) `EVENTO`: 1 = 47,1 %, 0 = 46,9 %, vacío = 6,0 %. **El grupo debe
  confirmar qué significa**, porque en los datos no se relaciona con la mora. Unidad de análisis: **crédito**;
  41.855 clientes con 1 a 4 créditos cada uno, por eso la partición se hace **por cliente**.
- **problem_type:** clasificación binaria (balanceada)
- **primary_metric:** POR DEFINIR. PROPUESTA: costo esperado con una matriz de costos de negocio, o recall de la
  clase en riesgo con precisión mínima. La exactitud no sirve: la clase mayoritaria sola ya da ≈ 50 %.
- **business_cost_note:** POR DEFINIR al confirmar el objetivo. Un falso negativo (no detectar un crédito en
  riesgo) aumenta la cartera vencida y la provisión; un falso positivo genera gestiones innecesarias y una
  mala experiencia para la empresa y el colaborador.
- **status:** borrador
- **reviewer_notes:** <!-- las llena el instructor -->
