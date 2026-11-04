"""LibranzaRadar · app de priorización de seguimiento de créditos de libranza.

- Carga `models/model.joblib` y `models/input_schema.json` desde ESTE repositorio. NO consulta Databricks.
- Valida las entradas: si un dato es imposible, explica qué corregir en vez de responder cualquier cosa.
- La decisión final es del analista de crédito: la app solo sugiere a qué créditos dar seguimiento prioritario.

Ejecutar en local (desde la raíz del repo):  streamlit run app/streamlit_app.py
"""
import importlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "model.joblib"
SCHEMA_PATH = ROOT / "models" / "input_schema.json"
UNKNOWN = "(no sé)"

SRC = ROOT / "src"
sys.path.insert(0, str(SRC))
PACKAGE = next((p.name for p in sorted(SRC.iterdir()) if p.is_dir() and (p / "__init__.py").exists()), "proyecto")
predict_module = importlib.import_module(f"{PACKAGE}.inference.predict")
batch_module = importlib.import_module(f"{PACKAGE}.inference.batch")
schema_module = importlib.import_module(f"{PACKAGE}.inference.schema")

RESPONSIBLE_USE = """
- **Qué apoya:** decidir a qué créditos aprobados dar **revisión y seguimiento prioritario** con la empresa pagadora.
- **Qué NO decide:** no aprueba ni niega créditos, no fija tasas ni montos y no se usa para cobrar distinto a nadie.
  **La decisión final es del analista de crédito.**
- **Qué tan bueno es:** con la información disponible al aprobar, el modelo **no supera** a la regla simple del plazo
  corto. Con su umbral casi nunca sugiere priorizar (0,1 % de los créditos en la prueba). Como puntaje para ordenar
  rinde igual que el plazo. **Para priorizar se recomienda la regla del plazo corto (plazo ≤ 6 meses)**; ver la ficha
  del modelo (`models/ficha_modelo.md`).
- **Datos:** fue entrenado con una base **sintética** de cartera de libranza. Antes de usarlo con clientes reales
  hay que volver a entrenarlo y validarlo con datos reales.
- No usa sexo, estado civil ni edad. No ingrese nombres, documentos ni datos de contacto.
"""

PLAIN_NAMES = {
    "term_months": "el plazo", "loan_amount": "el monto", "monthly_installment": "la cuota mensual",
    "interest_rate_ea": "la tasa", "due_day": "el día de pago", "has_guarantee": "la garantía",
    "guarantee_value": "el valor de la garantía", "has_cosigner": "el codeudor", "product": "el producto",
    "business_type": "el tipo de negocio", "economic_destination": "el destino económico", "city": "la ciudad",
}
YES_NO = {"has_guarantee", "has_cosigner"}


@st.cache_resource
def get_model():
    return predict_module.load_model(MODEL_PATH)


@st.cache_data
def get_schema() -> dict:
    return schema_module.load_schema(SCHEMA_PATH)


def label(schema: dict, column: str) -> str:
    return schema.get("labels", {}).get(column, column).replace(" (1 = sí)", "")


def numeric_field(schema: dict, column: str, default, key: str):
    """Campo numérico con su rango posible y una casilla 'no sé' que deja el dato vacío (el modelo lo imputa)."""
    low, high = schema.get("valid_range", {}).get(column) or schema["observed_range"][column]
    if column in YES_NO:
        choice = st.radio(label(schema, column), ["No", "Sí", UNKNOWN], index=0 if not default else 1, horizontal=True, key=key)
        return np.nan if choice == UNKNOWN else int(choice == "Sí")
    if st.checkbox(f"No sé: {label(schema, column)}", key=f"unk_{key}"):
        return np.nan
    # Sin límites duros en el campo: así un valor imposible llega a la validación y se explica qué corregir
    if column in schema.get("integer_columns", []):
        return st.number_input(label(schema, column), value=int(round(float(default))), step=1, key=key,
                               help=f"Valor posible entre {low:,.0f} y {high:,.0f}")
    return st.number_input(label(schema, column), value=float(default), key=key, format="%.2f",
                           help=f"Valor posible entre {low:,.2f} y {high:,.2f}")


def build_form(schema: dict, defaults: dict, prefix: str = "") -> dict:
    """Formulario en tres columnas. `prefix` cambia con el ejemplo elegido para que sus valores se carguen."""
    row = {}
    columns = schema["numeric"] + schema["categorical"]
    cols = st.columns(3)
    for i, column in enumerate(columns):
        with cols[i % 3]:
            if column in schema["categorical"]:
                options = schema["categories"][column] + [UNKNOWN]
                current = str(defaults.get(column, options[0]))
                choice = st.selectbox(label(schema, column), options, index=options.index(current) if current in options else 0,
                                      key=f"{prefix}cat_{column}")
                row[column] = np.nan if choice == UNKNOWN else choice
            else:
                default = defaults.get(column, schema["median"][column])
                row[column] = numeric_field(schema, column, default, f"{prefix}num_{column}")
    return row


def explain(model, schema: dict, row: dict) -> pd.DataFrame:
    """Qué datos suben o bajan el riesgo: cambia cada dato por el valor típico y mira cuánto se mueve la probabilidad."""
    base = pd.DataFrame([row])
    p0 = model.predict_proba(base)[:, 1][0]
    effects = []
    for column in schema["numeric"] + schema["categorical"]:
        if pd.isna(row[column]):
            continue
        typical = schema["median"][column] if column in schema["numeric"] else schema["categories"][column][0]
        if column in schema["categorical"]:
            typical = schema.get("mode", {}).get(column, typical)
        changed = base.copy()
        changed[column] = typical
        effects.append({"dato": column, "efecto": p0 - model.predict_proba(changed)[:, 1][0], "típico": typical})
    return pd.DataFrame(effects).sort_values("efecto", key=np.abs, ascending=False)


def single_credit(model, schema: dict, examples: dict, chosen: str) -> None:
    """Pestaña 1: un crédito a la vez, con explicación."""
    threshold, base_rate = float(schema["threshold"]), float(schema["base_rate"])
    with st.form("entrada"):
        row = build_form(schema, examples.get(chosen, {}), prefix=f"{chosen}_")
        submitted = st.form_submit_button("Evaluar crédito", type="primary")
    if not submitted:
        st.info("Completa los datos del crédito y pulsa **Evaluar crédito**. Marca *No sé* en lo que no conozcas.")
        return
    try:
        result = predict_module.predict_with_scores(pd.DataFrame([row]), model, schema)
    except predict_module.InputValidationError as error:
        message = str(error)
        for column in schema["numeric"] + schema["categorical"]:
            message = message.replace(f"{column}:", f"{label(schema, column)}:")
        st.error(f"**Revisa los datos:** {message}")
        return

    first = result.iloc[0]
    proba = float(first[f"proba_{schema['class_names'][1]}"])
    left, right = st.columns([1, 1])
    with left:
        if proba >= threshold:
            st.error("### 🔴 Priorizar revisión y seguimiento")
        else:
            st.success("### 🟢 Seguimiento normal")
        st.metric("Probabilidad estimada de mora > 30 días", f"{proba:.1%}")
        comparison = "más" if proba > base_rate else "menos"
        st.markdown(f"Es **{proba / base_rate:.2f} veces** la tasa promedio de mora ({base_rate:.1%}): "
                    f"riesgo **{comparison}** que el promedio.")
        st.caption(f"El modelo prioriza cuando la probabilidad es ≥ {threshold:.1%}. Ese umbral buscaba que, de cada "
                   "5 créditos priorizados, al menos 1 cayera en mora, pero casi nunca se alcanza: en la prueba marcó "
                   "el 0,1 % de los créditos y no detectó ninguna mora. Un resultado verde no significa riesgo bajo.")
        if bool(first["needs_review"]):
            st.warning("La probabilidad está muy cerca del umbral: la sugerencia podría cambiar con poco. Use su criterio.")
        for message in result.attrs.get("warnings", []):
            st.warning(f"Dato inusual: {message}. El modelo vio pocos casos así; tome el resultado con cautela.")
    with right:
        st.write("**¿Qué datos mueven el resultado?** (frente a un crédito típico)")
        for _, e in explain(model, schema, row).head(4).iterrows():
            if abs(e["efecto"]) < 0.001:
                continue
            arrow = "sube" if e["efecto"] > 0 else "baja"
            st.markdown(f"- **{PLAIN_NAMES.get(e['dato'], e['dato']).capitalize()}** {arrow} el riesgo "
                        f"{abs(e['efecto']) * 100:.1f} puntos porcentuales")
        st.caption("Explica al modelo, no al cliente: dice qué datos pesaron en este cálculo, no por qué una persona paga o no.")


@st.cache_data(show_spinner="Calificando los créditos…")
def score_file(content: bytes, name: str) -> pd.DataFrame:
    import io
    df = batch_module.read_table(io.BytesIO(content), name)
    return batch_module.score_batch(df, get_model(), get_schema())


def miles(n: int) -> str:
    """1234567 -> 1.234.567 (formato colombiano)."""
    return f"{int(n):,}".replace(",", ".")


RESULT_COLUMN_HELP = {
    "credito": "Número del crédito en el sistema (NUMERO DE LA COLOCACION). No es un dato personal. "
               "Si el archivo no lo trae, se numera 1, 2, 3…",
    "veces_el_promedio": "Probabilidad dividida por la tasa de mora promedio del entrenamiento. "
                         "1 = riesgo promedio; 1,4 = 40 % más que el promedio; menos de 1 = menos que el promedio.",
    "prioridad": "Sugerencia del modelo: «Priorizar revisión» si la probabilidad supera su umbral; si no, «Seguimiento "
                 "normal». Casi nunca prioriza: «Seguimiento normal» NO significa riesgo bajo. Se recomienda priorizar "
                 "con la regla del plazo corto (plazo ≤ 6 meses). Los reestructurados tras la mora salen como «Excluido».",
    "cerca_del_umbral": "Sí, si la probabilidad queda a menos de 0,5 puntos del umbral: un pequeño cambio en los datos "
                        "cambiaría la sugerencia. Revíselo con su criterio.",
    "datos_corregidos": "Columnas que traían un valor imposible o no numérico. Ese dato se dejó vacío y el modelo lo "
                        "completó: revise ese dato en el sistema. Vacía = todo bien.",
    "mora_30_real": "1 si el archivo dice que el crédito YA tiene más de 30 días de mora (DIAS DE MORA). Solo para "
                    "comparar: no mide qué tan bueno es el modelo, porque el archivo puede incluir créditos con los que "
                    "se entrenó y créditos muy nuevos.",
}


def batch_column_config(schema: dict, max_proba: float) -> dict:
    """Encabezados de la tabla de carga masiva con una explicación al pasar el mouse (tooltip)."""
    threshold = float(schema["threshold"])
    config = {name: st.column_config.Column(name, help=text) for name, text in RESULT_COLUMN_HELP.items()}
    config["probabilidad_mora_30"] = st.column_config.ProgressColumn(
        "Probabilidad de mora > 30 días", format="%.3f", min_value=0.0, max_value=max_proba,
        help=f"Probabilidad estimada de que el crédito pase de 30 días de mora (0,22 = 22 %). Ordena el riesgo; no es "
             f"una certeza. El modelo prioriza desde {threshold:.1%}.")
    for column in schema["numeric"] + schema["categorical"]:   # los 12 datos que usó el modelo
        config[column] = st.column_config.Column(
            column, help=f"Dato usado por el modelo: {label(schema, column)}. Si está vacío, faltaba o se corrigió y el "
                         "modelo lo completó con un valor típico.")
    return config


def batch_credits(schema: dict) -> None:
    """Pestaña 2: un archivo con muchos créditos."""
    st.markdown(
        "Sube un archivo **CSV o Excel** con muchos créditos. Sirve en dos formatos:\n"
        "- el del **sistema de cartera** (las columnas originales, como `Base_sintetica_creditos.csv`);\n"
        "- o uno con las **12 columnas del modelo**: " + ", ".join(f"`{c}`" for c in schema["numeric"] + schema["categorical"]) + ".\n\n"
        "Los datos personales del archivo **no se usan ni se muestran**, y el archivo no se guarda.")
    file = st.file_uploader("Archivo de créditos", type=["csv", "xlsx"])
    if file is None:
        return
    try:
        scored = score_file(file.getvalue(), file.name)
    except batch_module.BatchFormatError as error:
        st.error(str(error))
        return
    except Exception as error:  # archivo dañado, codificación rara...
        st.error(f"No pude leer el archivo: {error}")
        return

    summary = batch_module.summarize_batch(scored)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Créditos calificados", miles(summary["calificados"]))
    c2.metric("A priorizar", miles(summary["priorizados"]))
    c2.caption(f"{summary['porcentaje_priorizado']:.1%} de los calificados")
    c3.metric("Probabilidad media", f"{summary['probabilidad_media']:.1%}")
    c4.metric("Excluidos", miles(summary["excluidos"]), help="Créditos reestructurados tras la mora "
              "(CONDICION ESPECIAL = 1): ya están vencidos y sus condiciones fueron reescritas.")
    if summary["con_datos_corregidos"]:
        st.warning(f"{summary['con_datos_corregidos']} créditos tenían datos imposibles o no numéricos: ese dato se dejó "
                   "vacío y el modelo lo completó. Vea la columna `datos_corregidos`.")
    if "moras_reales" in summary:
        st.info(f"El archivo trae la mora real (`DIAS DE MORA`). De {miles(summary['moras_reales'])} moras, la priorización "
                f"marca {miles(summary['moras_detectadas'])} (recall {summary['recall']:.0%}) con precisión de "
                f"{summary['precision']:.0%}. **No es una validación**: el archivo puede incluir créditos con los que "
                "se entrenó el modelo y créditos todavía muy nuevos.")

    only_priority = st.toggle("Ver solo los créditos a priorizar", value=True)
    view = scored[scored["prioridad"] == batch_module.PRIORITY] if only_priority else scored
    st.caption("Pase el mouse por el encabezado de una columna para ver qué significa.")
    st.dataframe(view, use_container_width=True, hide_index=True,
                 column_config=batch_column_config(schema, float(max(0.5, scored["probabilidad_mora_30"].max()))))
    csv = scored.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")  # se abre bien en Excel en español
    st.download_button("⬇ Descargar resultados (CSV para Excel)", csv, file_name="libranzaradar_resultados.csv",
                       mime="text/csv", type="primary")


def main() -> None:
    st.set_page_config(page_title="LibranzaRadar", page_icon="📡", layout="wide")
    if not MODEL_PATH.exists() or not SCHEMA_PATH.exists():
        st.title("LibranzaRadar")
        st.error("Falta `models/model.joblib` o `models/input_schema.json`. Ejecuta el notebook `notebooks/09_inferencia.ipynb`.")
        st.stop()

    model, schema = get_model(), get_schema()
    base_rate = float(schema["base_rate"])
    st.title(schema.get("app_title", "LibranzaRadar"))
    st.caption("Herramienta de apoyo para el analista de crédito: sugiere a qué créditos de libranza aprobados dar "
               "seguimiento prioritario con la empresa pagadora. **No aprueba ni niega créditos.**")
    st.warning("**Aviso:** con la información disponible al aprobar, este modelo no supera a la regla simple del plazo "
               "corto y, con su umbral, casi nunca sugiere priorizar. **Para priorizar el seguimiento se recomienda "
               "la regla del plazo corto (plazo ≤ 6 meses).** Use la probabilidad solo como referencia.")

    examples = schema.get("examples", {})
    with st.sidebar:
        st.header("Ejemplos (un crédito)")
        chosen = st.radio("Perfil", list(examples) or ["(sin ejemplos)"], label_visibility="collapsed")
        st.divider()
        st.markdown(f"**Modelo:** {schema.get('model_version', '—')}")
        tm = schema.get("test_metrics", {})
        if tm:
            st.markdown(f"**En prueba** (clientes nunca vistos): detecta el **{tm['recall'][0]:.0%}** de las moras "
                        f"revisando el **{tm['flag_rate']:.0%}** de los créditos, con precisión de **{tm['precision'][0]:.0%}**.")
        st.markdown(f"Tasa de mora promedio: **{base_rate:.1%}**")

    tab_one, tab_many = st.tabs(["📝 Un crédito", "📂 Carga masiva"])
    with tab_one:
        single_credit(model, schema, examples, chosen)
    with tab_many:
        batch_credits(schema)

    with st.expander("Uso responsable"):
        st.markdown(RESPONSIBLE_USE)


if __name__ == "__main__":  # `streamlit run` ejecuta el archivo como programa principal
    main()
