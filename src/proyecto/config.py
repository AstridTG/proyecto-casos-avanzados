"""Constantes del proyecto LibranzaRadar: rutas, columnas, objetivo y reglas de negocio.

Todo lo que se decidió en el EDA (reports/01_eda.md) y que el código necesita está aquí, con su motivo.
"""
from pathlib import Path

# src/proyecto/config.py -> la raíz del repositorio está tres niveles arriba
ROOT = Path(__file__).resolve().parents[2]
RAW_CSV = ROOT / "data" / "raw" / "Base_sintetica_creditos.csv"
PROCESSED_DIR = ROOT / "data" / "processed"  # se regenera con el notebook 03; no se versiona
MODELS_DIR = ROOT / "models"
REPORTS_DIR = ROOT / "reports"

RANDOM_STATE = 42

# ---------------------------------------------------------------- unidad de análisis y objetivo
GROUP_COL = "client_id"  # un cliente puede tener hasta 4 créditos: se parte por cliente, no por fila
TARGET = "mora_30"       # 1 si DIAS DE MORA > 30
MORA_DAYS = 30

# ---------------------------------------------------------------- regla de negocio (ficha de caso)
# Métrica principal: recall de la clase "en mora" exigiendo una precisión mínima.
# 0,20 = de cada 5 créditos que el modelo manda a revisión, al menos 1 cae de verdad en mora
# (25 % más que revisar al azar, cuya precisión es la tasa de mora, ~16 %).
MIN_PRECISION = 0.20

# ---------------------------------------------------------------- ventana de observación
# Un crédito necesita tiempo para poder caer en más de 30 días de mora. Los abiertos en los últimos
# 4 meses antes del corte tienen tasas de 0 % a 14 % solo porque no ha pasado el tiempo (EDA, decisión 4).
MIN_SEASONING_MONTHS = 4

# ---------------------------------------------------------------- datos personales (se eliminan al cargar)
# El identificador del cliente se reemplaza por un número de cliente (c00001...) que solo sirve para agrupar.
CLIENT_ID_RAW = "NUMERO DE IDENTIFICACION"
COSIGNER_ID_RAW = "NRO IDENTIDAD CODEUDOR"
PII_COLUMNS = [
    "NUMERO DE IDENTIFICACION", "NUMERO DE IDENTIFICACION DEL", "NUMERO DE IDENTIFICACION DEL.1",
    "DIGITO DE CHEQUEO", "NOMBRE O RAZON SOCIAL", "DIRECCION LINEA 1", "DIRECCION LINEA 2", "DIRECCION LINEA 3",
    "TELEFONO 1", "TELEFONO 2", "TELEFONO 3", "ZONA POSTAL",
    "NRO IDENTIDAD CODEUDOR", "NOMBRE CODEUDOR", "DIRECCION CODEUDOR", "TELEFONO CODEUDOR",
    "NRO IDENTIDAD CODEUDOR 1", "NOMBRE CODEUDOR 1", "NRO IDENTIDAD CODEUDOR 2", "NOMBRE CODEUDOR 2",
    "NRO IDENTIDAD CODEUDOR 3", "NOMBRE CODEUDOR 3", "DIRECCION GARANTIA",
]
PII_PREFIXES = ("DIRECCION CODEUDOR", "TELEFONO CODEUDOR")  # columnas repetidas .1, .2, ...

# ---------------------------------------------------------------- variables conocidas al aprobar
# columna cruda -> nombre en el proyecto. Solo entran datos que el analista conoce el día que aprueba.
APPROVAL_COLUMNS = {
    "NUMERO DEL PRODUCTO": "product",
    "PLAZO UNIDAD TIEMPO PRODUCTO": "term_months",
    "VALOR ORIGINAL DEL PRESTAMO": "loan_amount",
    "VLR CUOTA MES": "monthly_installment",
    "VALOR EQUI. EFECTIVA VENCIDA": "interest_rate_ea",
    "DIA VENCIMIENTO CUOTA": "due_day",
    "TIPO NEGOCIO": "business_type",
    "DESTINO ECONOMICO": "economic_destination",
    "NOMBRE CIUDAD": "city",
    "EDAD DEL CLIENTE": "age",
    "GARANTIA S/N": "has_guarantee",
    "VALOR DE LA GARANTIA": "guarantee_value",
    "NRO DEL CANAL DEL PRESTAMO": "employer_id",
}
# Columnas que se crean al limpiar (también conocidas al aprobar)
DERIVED_COLUMNS = ["has_cosigner", "prior_credits"]

CATEGORICAL = ["product", "business_type", "economic_destination", "city", "employer_id"]
NUMERIC = ["term_months", "loan_amount", "monthly_installment", "interest_rate_ea", "due_day", "age",
           "has_guarantee", "guarantee_value", "has_cosigner", "prior_credits"]

# Rango POSIBLE en el mundo real (conocimiento del negocio, no de los datos). Fuera de él, el valor es imposible.
PLAUSIBLE_RANGE = {
    "term_months": (1, 360),
    "loan_amount": (100_000, 2_000_000_000),
    "monthly_installment": (1_000, 200_000_000),
    "interest_rate_ea": (0.0, 60.0),       # % efectivo anual (Colombia: tope de usura ~ 25-30 %)
    "due_day": (1, 31),
    "age": (18, 90),                       # libranza: trabajadores o pensionados mayores de edad
    "has_guarantee": (0, 1),
    "guarantee_value": (0, 5_000_000_000),
    "has_cosigner": (0, 1),
    "prior_credits": (0, 50),
}

# Columnas que se descartan a propósito (y por qué). Se documentan en reports/01_eda.md.
EXCLUDED_ON_PURPOSE = {
    "SEXO": "atributo sensible; sin relación con la mora (18,9 % vs 19,1 %)",
    "ESTADO CIVIL": "atributo sensible; sin relación con la mora (18,8 %–19,2 %)",
    "ESTADO AFILIACION DEL CANAL": "estado ACTUAL de la empresa, no el del día de aprobación; sin señal fuera del bloque reestructurado",
    "NRO DE UTILIZACINES DEL PLAN": "sin diccionario de datos; vale 1 en todo el bloque reestructurado (artefacto); sin señal fuera de él",
    "EVENTO": "sin diccionario de datos; vacío solo en el bloque reestructurado",
    "FECHA APERTURA DEL PRESTAMO": "mide cuánto tiempo lleva el crédito (exposición), que no existe al aprobar",
}
