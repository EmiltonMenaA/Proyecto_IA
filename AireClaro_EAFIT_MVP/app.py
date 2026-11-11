from __future__ import annotations

import json
import html
import os
import re
from pathlib import Path
from typing import Any

import httpx
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")
DATA = ROOT / "data" / "demo_air_quality.csv"
DOCS = ROOT / "knowledge"
SIATA_SERVICE = "https://siata.gov.co/siata_nuevo/index.php/capa_service/consultar_capa_carga"
SIATA_LAYERS = ("C_00000000000000000000602", "C_00000000000000000000603")
STATIONS = {
    "MED-BEME · Belén": (6.23, -75.59),
    "MED-ALTA · El Poblado": (6.19, -75.56),
    "MED-UNNV · Universidad": (6.27, -75.57),
    "ITA-CONC · Itagüí": (6.17, -75.61),
    "SAB-CJUS · Sabaneta": (6.15, -75.62),
    "COP-CIED · Copacabana": (6.35, -75.51),
}

st.set_page_config(page_title="AireClaro | Valle de Aburrá", page_icon="🌿", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
:root { --ink:#172E2A; --muted:#637570; --green:#1C6B58; --mint:#EAF3EE; --line:#E1EAE5; }
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
.stApp { background:linear-gradient(180deg,#F7FAF7 0%,#F4F8F5 100%); color:var(--ink); }
h1,h2,h3 { font-family:'Manrope',sans-serif; color:var(--ink); letter-spacing:-.035em; }
.hero { background:#173D35; border-radius:24px; padding:30px 34px; color:white; margin:4px 0 22px; box-shadow:0 14px 38px #173d351a; }
.hero h1 { color:white; font-size:2.35rem; margin:0 0 5px; }
.hero p { color:#D4E6DE; font-size:1rem; margin:0; }
.eyebrow { color:#A8D3BD; text-transform:uppercase; letter-spacing:.14em; font-weight:700; font-size:.72rem; margin-bottom:8px; }
.tag { display:inline-block; background:#E7F1EB; color:#275C4D; border-radius:100px; padding:6px 11px; font-size:.75rem; font-weight:700; }
div[data-testid="stMetric"] { background:white; border:1px solid var(--line); padding:17px 18px; border-radius:17px; box-shadow:0 4px 15px #173d3508; }
div[data-testid="stMetricLabel"] { color:#70817B; }
div[data-testid="stMetricValue"] { color:#173D35; }
.section-note { color:#73827D; font-size:.86rem; margin-top:-8px; }
.stChatMessage { border:1px solid #E6ECE8; border-radius:16px; background:#fff; }
.source-note { color:#7A8983; font-size:.77rem; }
button[kind="primary"] { background:#1C6B58; border-color:#1C6B58; }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA, parse_dates=["fecha"])
    return df


@st.cache_data(ttl=300, show_spinner=False)
def fetch_siata_pm25() -> pd.DataFrame:
    """Read SIATA's public POECA and NO-POECA 24-hour PM2.5 map layers."""
    rows = []
    with httpx.Client(timeout=20, follow_redirects=True) as client:
        for layer_id in SIATA_LAYERS:
            response = client.post(SIATA_SERVICE, data={"id_capa": layer_id})
            response.raise_for_status()
            payload = response.json()
            if not payload.get("feature_vector"):
                continue
            for feature in payload["feature_vector"]:
                attrs = feature.get("atributos", {}).get("descripcion", {})
                def value(key: str) -> str:
                    return str(attrs.get(key, {}).get("valor_alfanumerico") or "").strip()
                operator = value("maximo_operador").upper()
                if operator and "PM2.5" not in operator.replace(" ", ""):
                    continue
                try:
                    pm25 = float(value("concentracion_maximo_operador"))
                    lat = float(value("Latitud"))
                    lon = float(value("Longitud"))
                except (TypeError, ValueError):
                    continue
                if pm25 < 0 or pm25 > 1000:
                    continue
                municipality = html.unescape(value("Municipio")).replace("�", "").strip() or "Valle de Aburrá"
                code = value("Codigo") or feature.get("id_feature_vector", "").split("000000000000000000")[-1]
                updated = pd.to_datetime(value("fecha_ultima_actualizacion"), errors="coerce")
                geometry = json.loads(feature.get("geometry_text") or "{}")
                coordinates = geometry.get("coordinates", [lon, lat])
                rows.append({
                    "fecha": updated,
                    "estacion": f"SIATA {code} · {municipality}",
                    "municipio": municipality,
                    "latitud": float(coordinates[1]),
                    "longitud": float(coordinates[0]),
                    "pm25": pm25,
                    "categoria": value("ICA_PM25_Descripcion") or "Sin categoría",
                    "fuente": "SIATA · ICA PM2.5 promedio de 24 horas",
                    "url_fuente": "https://siata.gov.co/siata_nuevo/",
                })
    frame = pd.DataFrame(rows).dropna(subset=["fecha", "pm25"])
    if frame.empty:
        raise ValueError("SIATA respondió, pero no entregó registros válidos de PM2.5.")
    return frame.sort_values(["fecha", "estacion"]).reset_index(drop=True)


def label_pm25(value: float) -> str:
    # Ranges are simplified for this classroom demo; not an official alert decision.
    if value <= 12:
        return "Bajo"
    if value <= 25:
        return "Moderado"
    return "Alto"


def train_nb_and_score(df: pd.DataFrame) -> tuple[str, float, float]:
    """Small Gaussian Naive Bayes implemented here; compare with majority baseline."""
    ordered = df.sort_values("fecha").copy()
    ordered["pm_ayer"] = ordered.groupby("estacion")["pm25"].shift(1)
    ordered["label"] = ordered["pm25"].map(label_pm25)
    sample = ordered.dropna(subset=["pm_ayer"]).reset_index(drop=True)
    if len(sample) < 20:
        return "Moderado", 0.0, 0.0
    cut = int(len(sample) * .8)
    train, test = sample.iloc[:cut], sample.iloc[cut:]
    classes = sorted(train.label.unique())
    means = {c: float(train.loc[train.label == c, "pm_ayer"].mean()) for c in classes}
    variances = {c: max(float(train.loc[train.label == c, "pm_ayer"].var(ddof=0)), 1.0) for c in classes}
    priors = {c: (int((train.label == c).sum()) + 1) / (len(train) + len(classes)) for c in classes}
    predictions = []
    for x in test.pm_ayer.astype(float):
        scores = {c: np.log(priors[c]) - .5 * np.log(2*np.pi*variances[c]) - ((x-means[c])**2)/(2*variances[c]) for c in classes}
        predictions.append(max(scores, key=scores.get))
    accuracy = float(np.mean(np.array(predictions) == test.label.to_numpy()))
    majority = str(train.label.mode().iloc[0])
    baseline = float((test.label == majority).mean())
    latest = float(df.sort_values("fecha").groupby("estacion").tail(1).pm25.mean())
    prior = "Bajo" if latest <= 12 else "Moderado" if latest <= 25 else "Alto"
    predicted = max(classes, key=lambda c: np.log(priors[c]) - .5*np.log(2*np.pi*variances[c]) - ((latest-means[c])**2)/(2*variances[c]))
    return predicted if predicted in classes else prior, accuracy, baseline


def get_pm25(df: pd.DataFrame, station: str, data_mode: str) -> dict[str, Any]:
    row = df[df.estacion == station].sort_values("fecha").iloc[-1]
    category = str(row.get("categoria") or label_pm25(float(row.pm25)))
    return {"estacion": station, "fecha_actualizacion": row.fecha.strftime("%Y-%m-%d %H:%M"), "pm25_ug_m3": round(float(row.pm25), 1), "categoria": category, "periodo": "promedio de 24 horas" if data_mode.startswith("SIATA") else "último registro del CSV", "origen": data_mode, "fuente": str(row.get("url_fuente") or "CSV local")}


def predict_tomorrow(df: pd.DataFrame, data_mode: str) -> dict[str, Any]:
    if data_mode.startswith("SIATA"):
        return {"disponible": False, "motivo": "La capa consultada de SIATA entrega promedios móviles de 24 horas por estación, no una serie histórica suficiente para entrenar o validar una predicción de mañana.", "origen": data_mode}
    label, accuracy, baseline = train_nb_and_score(df)
    return {"disponible": True, "prediccion": label, "accuracy_holdout": round(accuracy, 3), "accuracy_baseline": round(baseline, 3), "metodo": "Naive Bayes gaussiano propio, con PM2.5 del día anterior", "origen": data_mode}


def retrieve_docs(question: str, k: int = 2) -> list[dict[str, str]]:
    terms = set(re.findall(r"[a-záéíóúñ0-9]+", question.lower()))
    results = []
    for path in DOCS.glob("*.md"):
        content = path.read_text(encoding="utf-8")
        title, _, body = content.partition("\n")
        words = set(re.findall(r"[a-záéíóúñ0-9]+", body.lower()))
        score = len(terms & words)
        if score:
            results.append({"title": title.lstrip("# "), "text": body[:1600], "source": path.name, "score": str(score)})
    return sorted(results, key=lambda item: int(item["score"]), reverse=True)[:k]


TOOL_DEFS = [
    {"type":"function","function":{"name":"get_pm25","description":"Consulta el último PM2.5 disponible para una estación del panel.","parameters":{"type":"object","properties":{"estacion":{"type":"string","description":"Nombre exacto de una estación disponible"}},"required":["estacion"]}}},
    {"type":"function","function":{"name":"predict_tomorrow","description":"Calcula la categoría estimada para mañana usando Naive Bayes propio y reporta la evaluación frente a una línea base.","parameters":{"type":"object","properties":{},"additionalProperties":False}}},
    {"type":"function","function":{"name":"search_docs","description":"Busca en el corpus local de documentos sobre calidad del aire y recomendaciones generales.","parameters":{"type":"object","properties":{"consulta":{"type":"string"}},"required":["consulta"]}}},
]


def run_tool(name: str, args: dict[str, Any], df: pd.DataFrame, data_mode: str) -> dict[str, Any]:
    if name == "get_pm25":
        station = args.get("estacion", "")
        if station not in set(df.estacion):
            station = next((s for s in df.estacion.unique() if s.lower() in station.lower() or station.lower() in s.lower()), df.estacion.iloc[0])
        return get_pm25(df, station, data_mode)
    if name == "predict_tomorrow":
        return predict_tomorrow(df, data_mode)
    if name == "search_docs":
        return retrieve_docs(args.get("consulta", "calidad aire"))
    return {"error":"Herramienta desconocida"}


def local_answer(question: str, df: pd.DataFrame, selected_station: str, data_mode: str) -> tuple[str, list[str]]:
    q = question.lower()
    if any(w in q for w in ["mañana", "predic", "pronóst", "pronost"]):
        result = predict_tomorrow(df, data_mode)
        if not result.get("disponible"):
            return (f"No puedo estimar mañana a partir de esta capa real: {result['motivo']} El panel sí consulta lecturas reales recientes de SIATA."), ["predict_tomorrow"]
        disclaimer = " El CSV usado es simulado, así que esto demuestra el flujo técnico, no una predicción ambiental real." if data_mode.startswith("Demo") else " El resultado se calcula sobre el CSV local; no es una predicción oficial ni un dato en tiempo real."
        return (f"Con el Naive Bayes, la categoría estimada para mañana es **{result['prediccion']}**. En la partición de prueba obtuvo {result['accuracy_holdout']:.0%} de exactitud; la línea base de clase mayoritaria obtuvo {result['accuracy_baseline']:.0%}. Origen: {data_mode}.{disclaimer}"), ["predict_tomorrow"]
    if any(w in q for w in ["estación", "estacion", "pm", "dato", "lectura", "hoy", "actual", "tiempo real"]):
        requested_station = next((s for s in df.estacion.unique() if s.lower() in q or s.split("·")[-1].strip().lower() in q), selected_station)
        result = get_pm25(df, requested_station, data_mode)
        if data_mode.startswith("SIATA"):
            answer = f"La capa pública de SIATA reporta **{result['pm25_ug_m3']} µg/m³** para **{result['estacion']}**, categoría **{result['categoria']}**, actualizada {result['fecha_actualizacion']}. Es el promedio de las últimas 24 horas, no una lectura instantánea. Fuente: {result['fuente']}"
        else:
            answer = f"La última lectura del modo demo para **{result['estacion']}** es **{result['pm25_ug_m3']} µg/m³** ({result['categoria']} en rangos didácticos), con fecha {result['fecha_actualizacion'][:10]}. Origen: {data_mode}; no es una medición real."
        return answer, ["get_pm25"]
    docs = retrieve_docs(question)
    if docs:
        source_lines = [line for line in docs[0]["text"].splitlines() if line.lower().startswith(("fuente:", "ejemplo de informe", "portal de siata", "ficha del ideam:"))]
        citations = "\n".join(source_lines)
        return (f"Encontré información en el corpus sobre **{docs[0]['title']}**. {docs[0]['text'][:360]}\n\n{citations}\n\nEsta respuesta usa recuperación local de documentos (RAG básico). Consulta la fuente para el contexto completo."), ["search_docs"]
    return ("Puedo consultar una estación, mostrar la predicción de mañana o buscar información en las fuentes del corpus. Prueba: *¿Cuál es el PM2.5 de Belén?* o *¿Qué predice el modelo para mañana?*"), []


def groq_answer(question: str, history: list[dict[str,str]], df: pd.DataFrame, station: str, data_mode: str) -> tuple[str, list[str]]:
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key:
        return local_answer(question, df, station, data_mode)
    if data_mode.startswith("SIATA"):
        data_context = "Las lecturas provienen de la capa pública de SIATA para ICA PM2.5 con promedio móvil de 24 horas por estación. Muestra la marca de actualización y cita SIATA. No digas que son instantáneas. La capa no tiene historia suficiente para predecir mañana; la herramienta de predicción debe explicar que no está disponible con esos datos."
    elif data_mode.startswith("Demo"):
        data_context = "El CSV activo es simulado y no representa mediciones reales."
    else:
        data_context = "Los datos provienen de un CSV cargado por el usuario; indica su origen y no afirmes que es oficial ni que está en tiempo real."
    q = question.lower()
    if any(term in q for term in ("mañana", "predice", "predicción", "prediccion", "pronóstico", "pronostico")):
        required_tool = "predict_tomorrow"
        tool_args = {}
    elif any(term in q for term in ("ideam", "documento", "informe", "fuente", "fuentes", "corpus", "conjunto de datos", "recomendaciones")):
        required_tool = "search_docs"
        tool_args = {"consulta": question}
    elif any(term in q for term in ("pm2.5", "pm25", "concentración", "concentracion", "categoría", "categoria", "estación", "estacion", "lectura", "medición", "medicion", "hora", "panel", "valor", "tiempo real")):
        required_tool = "get_pm25"
        tool_args = {"estacion": station}
    else:
        required_tool = ""
        tool_args = {}
    called = []
    messages: list[dict[str, Any]] = [{"role":"system","content":f"Eres AireClaro, asistente educativo del Valle de Aburrá. Usa herramientas para responder lecturas, predicciones o fuentes. Estación actualmente seleccionada: {station}. {data_context} No des consejo médico. Cita la fuente o URL cuando corresponda."}]
    if required_tool:
        tool_result = run_tool(required_tool, tool_args, df, data_mode)
        called.append(required_tool)
        messages.append({"role":"system","content":f"Consulta obligatoria ejecutada con {required_tool}. Usa exactamente este resultado como fuente primaria y no lo contradigas: {json.dumps(tool_result, ensure_ascii=False)}"})
    messages.extend(history[-8:])
    messages.append({"role":"user","content":question})
    try:
        with httpx.Client(timeout=35) as client:
            for _ in range(4):
                response = client.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization":f"Bearer {key}"}, json={"model":os.getenv("GROQ_MODEL","openai/gpt-oss-120b"),"messages":messages,"tools":TOOL_DEFS,"tool_choice":"auto","temperature":0.2})
                response.raise_for_status()
                choice = response.json()["choices"][0]["message"]
                if not choice.get("tool_calls"):
                    return choice.get("content") or "No pude generar una respuesta.", called
                messages.append(choice)
                for tool_call in choice["tool_calls"]:
                    name = tool_call["function"]["name"]
                    args = json.loads(tool_call["function"].get("arguments") or "{}")
                    if name == "get_pm25" and "estacion" not in args:
                        args["estacion"] = station
                    result = run_tool(name, args, df, data_mode)
                    called.append(name)
                    messages.append({"role":"tool","tool_call_id":tool_call["id"],"name":name,"content":json.dumps(result, ensure_ascii=False)})
            return "Llegué al máximo de pasos de herramientas. Reformula la pregunta con una estación o acción concreta.", called
    except Exception as exc:
        answer, tools = local_answer(question, df, station, data_mode)
        return f"No se pudo conectar con Groq ({type(exc).__name__}). Respuesta local de respaldo: {answer}", tools


df = load_data()
is_demo_data = True
is_siata_data = False
source_error = None
with st.sidebar:
    st.markdown("### 🌱 AireClaro")
    st.caption("Proyecto final · SI3003 · IA")
    source_choice = st.radio("Fuente de datos", ["SIATA · mediciones recientes", "Demo · datos simulados"], index=1 if os.getenv("AIRECLARO_SOURCE", "siata").lower() == "demo" else 0)
    if source_choice.startswith("SIATA"):
        try:
            with st.spinner("Consultando la capa pública de SIATA…"):
                df = fetch_siata_pm25()
            is_demo_data = False
            is_siata_data = True
        except Exception as exc:
            source_error = f"No pude consultar SIATA ({type(exc).__name__}). El panel pasa a los datos simulados; vuelve a elegir SIATA para intentar otra vez."
            df = load_data()
            is_demo_data = True
            st.warning(source_error)
    else:
        df = load_data()
    uploaded_csv = st.file_uploader("Datos reales en CSV (opcional)", type=["csv"], help="Columnas requeridas: fecha, estacion, municipio, pm25. latitud/longitud son opcionales.")
    if uploaded_csv is not None:
        try:
            real_df = pd.read_csv(uploaded_csv)
            required = {"fecha", "estacion", "municipio", "pm25"}
            missing = required - set(real_df.columns)
            if missing:
                st.error("Faltan columnas requeridas: " + ", ".join(sorted(missing)))
            else:
                real_df["estacion"] = real_df["estacion"].astype(str).str.strip()
                real_df["municipio"] = real_df["municipio"].astype(str).str.strip()
                real_df["fecha"] = pd.to_datetime(real_df["fecha"], errors="coerce")
                real_df["pm25"] = pd.to_numeric(real_df["pm25"], errors="coerce")
                real_df = real_df.dropna(subset=["fecha", "estacion", "municipio", "pm25"])
                if real_df.empty:
                    st.error("El CSV no contiene filas válidas.")
                else:
                    for col in ("latitud", "longitud"):
                        if col not in real_df:
                            real_df[col] = np.nan
                    if "categoria" not in real_df:
                        real_df["categoria"] = real_df["pm25"].map(label_pm25)
                    df = real_df
                    is_demo_data = False
                    is_siata_data = False
                    st.success(f"CSV cargado: {len(df)} filas. Verifica unidades y fechas en la fuente.")
        except Exception as exc:
            st.error(f"No pude leer el CSV: {type(exc).__name__}")
    if "categoria" not in df:
        df["categoria"] = df["pm25"].map(label_pm25)
    stations = list(df.estacion.unique())
    selected_station = st.selectbox("Estación para el chat", stations, index=0)
    st.markdown("---")
    if is_siata_data:
        st.success("SIATA conectado. La capa publica promedios de 24 horas por estación; no son lecturas instantáneas.")
    elif is_demo_data:
        st.info("Usando datos simulados. Elige SIATA para intentar consultar valores reales.")
    else:
        st.info("Usando el CSV local cargado en esta sesión; no es una conexión en vivo.")
    st.caption("Groq genera las respuestas del chat; SIATA es la fuente de mediciones.")
    st.markdown("**Fuentes del proyecto**")
    st.markdown("[Geoportal SIATA](https://siata.gov.co/siata_nuevo/)  \n[Dataset abierto IDEAM](https://www.datos.gov.co/d/g4t8-zkc3)")

st.markdown("""
<div class="hero"><div class="eyebrow">Valle de Aburrá · inteligencia ambiental</div>
<h1>AireClaro</h1><p>Entiende las tendencias de calidad del aire y conversa con un asistente que consulta datos, predice y busca sus fuentes.</p></div>
""", unsafe_allow_html=True)
data_badge = "SIATA · promedio móvil de 24 h" if is_siata_data else ("Demo · datos simulados" if is_demo_data else "CSV local cargado · no es tiempo real")
st.markdown(f'<span class="tag">{data_badge}</span>', unsafe_allow_html=True)

filtered = df[df.estacion == selected_station].sort_values("fecha")
latest = filtered.iloc[-1]
model_df = load_data() if is_siata_data else df
pred, model_acc, baseline_acc = train_nb_and_score(model_df)
c1,c2,c3,c4 = st.columns(4)
if is_siata_data:
    c1.metric("PM2.5 · promedio 24 h", f"{latest.pm25:.1f} µg/m³", help="Concentración del promedio móvil reportado por la capa oficial SIATA")
    c2.metric("Estación SIATA", selected_station)
    c3.metric("Categoría publicada", latest.categoria)
    c4.metric("Actualización SIATA", latest.fecha.strftime("%H:%M · %d %b"))
else:
    c1.metric("PM2.5 · último registro", f"{latest.pm25:.1f} µg/m³", help="Dato simulado para demostrar la interfaz" if is_demo_data else "Dato del CSV local cargado")
    c2.metric("Estación", selected_station)
    c3.metric("Pronóstico demo" if is_demo_data else "Pronóstico del modelo", pred, help="Naive Bayes gaussiano implementado en app.py")
    c4.metric("Registros", f"{len(df):,}")

left,right = st.columns([1.35, .9], gap="large")
with left:
    st.subheader("PM2.5 por estación" if is_siata_data else "Tendencia de PM2.5")
    trend_note = "Capa SIATA · promedio móvil de las últimas 24 h · valores en µg/m³" if is_siata_data else ("Serie diaria de la estación seleccionada · µg/m³ · datos simulados" if is_demo_data else "Serie diaria de la estación seleccionada · µg/m³ · CSV local")
    st.markdown(f'<p class="section-note">{trend_note}</p>', unsafe_allow_html=True)
    if is_siata_data:
        live_bar = px.bar(df.sort_values("pm25"), x="pm25", y="estacion", orientation="h", color="pm25", color_continuous_scale=["#B8DCC7","#F1BE67","#D8735D"])
        live_bar.update_layout(height=370, margin=dict(l=3,r=4,t=8,b=4), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="white", font_color="#52645E", xaxis_title="µg/m³ (24 h)", yaxis_title=None, coloraxis_showscale=False)
        live_bar.update_xaxes(gridcolor="#E9EFEB", zeroline=False)
        live_bar.update_yaxes(showgrid=False, tickfont_size=9)
        st.plotly_chart(live_bar, width="stretch", config={"displayModeBar":False})
    else:
        line = px.line(filtered, x="fecha", y="pm25", markers=True, color_discrete_sequence=["#22735E"])
        line.update_layout(height=310, margin=dict(l=4,r=6,t=12,b=4), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="white", font_color="#52645E", xaxis_title=None, yaxis_title="µg/m³", showlegend=False)
        line.update_traces(line_width=3, marker_size=6)
        line.update_xaxes(showgrid=False)
        line.update_yaxes(gridcolor="#E9EFEB", zeroline=False)
        st.plotly_chart(line, width="stretch", config={"displayModeBar":False})
with right:
    st.subheader("Estaciones por categoría" if is_siata_data else "Comparación por estación")
    station_note = "Categorías publicadas por SIATA en la misma capa de 24 h" if is_siata_data else ("Último valor disponible por estación · datos simulados" if is_demo_data else "Último valor disponible por estación · CSV local")
    st.markdown(f'<p class="section-note">{station_note}</p>', unsafe_allow_html=True)
    if is_siata_data:
        by_category = df.groupby("categoria", as_index=False).size().sort_values("size")
        bar = px.bar(by_category, x="size", y="categoria", orientation="h", color="categoria", color_discrete_sequence=["#2D806A", "#E2A443", "#D8735D", "#8067A8"])
        bar.update_layout(height=370, margin=dict(l=3,r=4,t=8,b=4), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="white", font_color="#52645E", xaxis_title="N.º de estaciones", yaxis_title=None, showlegend=False)
        bar.update_xaxes(gridcolor="#E9EFEB", zeroline=False, dtick=1)
        bar.update_yaxes(showgrid=False)
    else:
        latests = df.sort_values("fecha").groupby(["estacion","municipio"],as_index=False).tail(1).sort_values("pm25")
        bar = px.bar(latests, x="pm25", y="estacion", orientation="h", color="pm25", color_continuous_scale=["#B8DCC7","#F1BE67","#D8735D"])
        bar.update_layout(height=310, margin=dict(l=2,r=4,t=12,b=4), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="white", font_color="#52645E", xaxis_title="µg/m³", yaxis_title=None, coloraxis_showscale=False)
        bar.update_xaxes(gridcolor="#E9EFEB", zeroline=False)
        bar.update_yaxes(showgrid=False, tickfont_size=10)
    st.plotly_chart(bar, width="stretch", config={"displayModeBar":False})

with st.expander("🔬 Cómo se comprueba la técnica clásica"):
    st.write("El modelo es un Naive Bayes gaussiano de una variable, implementado en Python dentro del proyecto. Estima la categoría usando el PM2.5 del día anterior y se compara con una línea base que siempre predice la clase mayoritaria.")
    a,b,c = st.columns(3)
    a.metric("Exactitud · Naive Bayes", f"{model_acc:.0%}")
    b.metric("Exactitud · línea base", f"{baseline_acc:.0%}")
    c.metric("Variables", "PM2.5 día anterior")
    st.caption("Partición temporal 80/20. Las métricas y la predicción mostradas aquí usan el CSV simulado de demostración; la capa SIATA consultada tiene solo promedios recientes y no basta para entrenar un pronóstico real.")

st.markdown("---")
st.subheader("💬 Pregúntale a AireClaro")
st.caption("El chat consulta SIATA cuando esa fuente está seleccionada, ejecuta herramientas y recupera documentos. Ejemplos: “¿Cuál es el PM2.5 de la estación seleccionada?”, “¿Qué categoría publicó SIATA?”")
quick1, quick2, quick3 = st.columns(3)
if "quick_prompt" not in st.session_state:
    st.session_state.quick_prompt = None
if quick1.button("📍 Consultar estación", width="stretch"):
    st.session_state.quick_prompt = f"¿Cuál es el PM2.5 de {selected_station}?"
if quick2.button("🔮 Probar predicción", width="stretch"):
    st.session_state.quick_prompt = "¿Qué predice el modelo para mañana?"
if quick3.button("📚 Buscar en fuentes", width="stretch"):
    st.session_state.quick_prompt = "¿Qué información ofrece el IDEAM sobre calidad del aire?"
if "chat" not in st.session_state:
    st.session_state.chat = [{"role":"assistant","content":"¡Hola! Soy AireClaro. Puedo consultar la lectura de una estación, estimar la categoría de mañana y buscar información en el corpus local. ¿Qué te gustaría revisar?"}]
if "tool_log" not in st.session_state:
    st.session_state.tool_log = []
for item in st.session_state.chat:
    with st.chat_message(item["role"]):
        st.markdown(item["content"])
prompt = st.session_state.pop("quick_prompt", None) or st.chat_input("Escribe una pregunta sobre el aire…")
if prompt:
    st.session_state.chat.append({"role":"user","content":prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    prior = [{"role":m["role"],"content":m["content"]} for m in st.session_state.chat[:-1] if m["role"] in ("user","assistant")]
    with st.chat_message("assistant"):
        with st.spinner("Consultando datos y fuentes…"):
            data_mode = "SIATA · promedio móvil 24 horas" if is_siata_data else ("Demo · datos simulados" if is_demo_data else "CSV local cargado por el usuario")
            answer, used_tools = groq_answer(prompt, prior, df, selected_station, data_mode)
        st.markdown(answer)
        st.caption("Herramientas usadas: " + (", ".join(used_tools) if used_tools else "respuesta introductoria"))
    st.session_state.chat.append({"role":"assistant","content":answer})
    st.session_state.tool_log = used_tools

footer_note = "Las lecturas son simuladas, no representan condiciones actuales" if is_demo_data else ("SIATA publica promedios móviles de 24 horas por estación; consulta la hora de actualización y la fuente" if is_siata_data else "Las lecturas provienen del CSV cargado y no son mediciones en tiempo real")
st.markdown(f"<p class='source-note'>Prototipo educativo. {footer_note}. No es consejo médico. Fuentes: IDEAM y SIATA.</p>", unsafe_allow_html=True)
