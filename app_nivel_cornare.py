"""
Monitor de Nivel — Quebrada Yarumal (Rionegro)
Red Agua - Estación Cód. 6 — CORNARE

App de una sola estación: no permite seleccionar otra estación.
Ejecutar con:  streamlit run monitor_yarumal.py
"""

import requests
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ──────────────────────────────────────────────────────────────
# CONFIGURACIÓN FIJA DE LA ESTACIÓN (no editable desde la UI)
# ──────────────────────────────────────────────────────────────
CODIGO_ESTACION = "6"
NOMBRE_ESTACION = "Quebrada Yarumal"
MUNICIPIO = "Rionegro"
RED = "Red Agua"

LAT_DEFECTO = 6.1385
LON_DEFECTO = -75.3735

API_BASE_URL = "https://marco.cornare.gov.co/api/v1/estaciones"

LLAVE_FECHA = "level_date"
LLAVE_VALOR = "level"
CANDIDATOS_LAT = ["lat", "latitude", "latitud"]
CANDIDATOS_LON = ["lng", "lon", "longitude", "longitud"]

# ──────────────────────────────────────────────────────────────
# CONFIGURACIÓN DE PÁGINA Y ESTILOS
# ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title=f"{NOMBRE_ESTACION} — Monitor de nivel",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

PALETA = {
    "fondo_grad_1": "#052e2b",
    "fondo_grad_2": "#0a5c4f",
    "acento": "#34d1a3",
    "acento_suave": "#a7f3d9",
    "texto_claro": "#e6fff7",
    "tarjeta": "#f4fbf9",
    "borde": "#d6f0e6",
}

st.markdown(
    f"""
    <style>
        .stApp {{
            background: linear-gradient(180deg, #f7fdfb 0%, #eefaf5 100%);
        }}
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, {PALETA['fondo_grad_1']}, {PALETA['fondo_grad_2']});
        }}
        section[data-testid="stSidebar"] * {{
            color: {PALETA['texto_claro']} !important;
        }}
        section[data-testid="stSidebar"] input {{
            color: #0a2e28 !important;
        }}
        div[data-testid="stMetric"] {{
            background: {PALETA['tarjeta']};
            border: 1px solid {PALETA['borde']};
            border-radius: 14px;
            padding: 14px 16px 10px 16px;
            box-shadow: 0 2px 10px rgba(10, 92, 79, 0.06);
        }}
        div[data-testid="stMetricLabel"] {{
            font-weight: 600;
            color: #0a5c4f;
        }}
        h1, h2, h3 {{
            color: #063b32;
        }}
        .tarjeta-info {{
            padding: 14px 18px;
            border-radius: 14px;
            background: {PALETA['tarjeta']};
            border: 1px solid {PALETA['borde']};
            text-align: center;
            height: 100%;
        }}
        .badge-fija {{
            display:inline-block;
            padding: 3px 12px;
            border-radius: 999px;
            background: rgba(52, 209, 163, 0.18);
            color: #0a5c4f;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: .03em;
            margin-bottom: 6px;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ──────────────────────────────────────────────────────────────
# FUNCIONES DE DATOS
# ──────────────────────────────────────────────────────────────
def obtener_serie_nivel(codigo_estacion, desde, hasta, calidad=1, timeout=30):
    url = f"{API_BASE_URL}/{codigo_estacion}/nivel"
    params = {"desde": desde, "hasta": hasta, "calidad": calidad}
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
    }
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=timeout, verify=False)
        if resp.status_code == 200:
            return resp.json(), None
        return None, f"HTTP {resp.status_code}"
    except requests.exceptions.RequestException as e:
        return None, f"Error de red: {e}"


def obtener_todas_las_paginas(datos_json, timeout=30):
    registros = list(datos_json.get("values", []))
    siguiente_url = datos_json.get("next")
    while siguiente_url:
        try:
            resp = requests.get(siguiente_url, timeout=timeout, verify=False)
        except requests.exceptions.RequestException:
            break
        if resp.status_code != 200:
            break
        pagina = resp.json()
        registros.extend(pagina.get("values", []))
        siguiente_url = pagina.get("next")
    return registros


def detectar_coordenadas(datos_json):
    if not isinstance(datos_json, dict):
        return LAT_DEFECTO, LON_DEFECTO, False
    lat = next((datos_json[k] for k in CANDIDATOS_LAT if k in datos_json), None)
    lon = next((datos_json[k] for k in CANDIDATOS_LON if k in datos_json), None)
    if lat is not None and lon is not None:
        try:
            return float(lat), float(lon), True
        except (TypeError, ValueError):
            pass
    return LAT_DEFECTO, LON_DEFECTO, False


def calcular_indice_calidad(df):
    if df.empty or len(df) < 2:
        return 0.0, 0, 0

    df_idx = df.set_index("fecha")
    frecuencia_tipica = df["fecha"].diff().dropna().mode()
    if len(frecuencia_tipica) == 0:
        return 0.0, 0, 0
    frecuencia_tipica = frecuencia_tipica[0]

    rango_completo = pd.date_range(
        start=df_idx.index.min(), end=df_idx.index.max(), freq=frecuencia_tipica
    )
    esperados = len(rango_completo)
    huecos = esperados - len(df_idx)
    completitud = max(0.0, 1 - (huecos / esperados)) if esperados > 0 else 0.0

    q1 = df["nivel"].quantile(0.25)
    q3 = df["nivel"].quantile(0.75)
    iqr = q3 - q1
    lim_inf = q1 - 1.5 * iqr
    lim_sup = q3 + 1.5 * iqr
    es_outlier = (df["nivel"] < lim_inf) | (df["nivel"] > lim_sup) | (df["nivel"] < 0)
    proporcion_outliers = es_outlier.mean()

    indice = (completitud * 0.7 + (1 - proporcion_outliers) * 0.3) * 100
    return round(indice, 1), int(huecos), int(es_outlier.sum())


def calcular_metricas_avanzadas(df):
    serie = df["nivel"]
    actual = serie.iloc[-1]
    anterior = serie.iloc[-2] if len(serie) > 1 else actual
    minimo, maximo = serie.min(), serie.max()
    promedio, mediana = serie.mean(), serie.median()
    desviacion = serie.std() if len(serie) > 1 else 0
    rango = maximo - minimo

    variacion_absoluta = actual - anterior
    variacion_porcentual = ((actual - anterior) / abs(anterior)) * 100 if anterior != 0 else 0

    if len(serie) >= 3:
        x = np.arange(len(serie))
        pendiente = np.polyfit(x, serie.values, 1)[0]
    else:
        pendiente = 0

    cambios = serie.diff().dropna()
    subidas = int((cambios > 0).sum())
    bajadas = int((cambios < 0).sum())
    estables = int((cambios == 0).sum())
    mayor_subida = cambios.max() if not cambios.empty else 0
    mayor_bajada = cambios.min() if not cambios.empty else 0

    percentil_actual = ((serie <= actual).sum() / len(serie)) * 100
    coef_variacion = (desviacion / promedio) * 100 if promedio != 0 else 0

    if pendiente > 0.01:
        tendencia, tendencia_icono = "Ascendente", "📈"
    elif pendiente < -0.01:
        tendencia, tendencia_icono = "Descendente", "📉"
    else:
        tendencia, tendencia_icono = "Estable", "➡️"

    if coef_variacion < 10:
        estabilidad, estabilidad_score = "Muy estable", 95
    elif coef_variacion < 20:
        estabilidad, estabilidad_score = "Estable", 80
    elif coef_variacion < 35:
        estabilidad, estabilidad_score = "Variable", 60
    else:
        estabilidad, estabilidad_score = "Muy variable", 35

    if actual > promedio * 1.5:
        riesgo, riesgo_icono = "Nivel elevado", "🔴"
    elif actual > promedio * 1.2:
        riesgo, riesgo_icono = "Vigilancia", "🟠"
    elif actual < promedio * 0.5:
        riesgo, riesgo_icono = "Nivel bajo", "🔵"
    else:
        riesgo, riesgo_icono = "Normal", "🟢"

    return {
        "actual": actual, "anterior": anterior, "minimo": minimo, "maximo": maximo,
        "promedio": promedio, "mediana": mediana, "desviacion": desviacion, "rango": rango,
        "variacion_absoluta": variacion_absoluta, "variacion_porcentual": variacion_porcentual,
        "pendiente": pendiente, "subidas": subidas, "bajadas": bajadas, "estables": estables,
        "mayor_subida": mayor_subida, "mayor_bajada": mayor_bajada,
        "percentil_actual": percentil_actual, "coef_variacion": coef_variacion,
        "tendencia": tendencia, "tendencia_icono": tendencia_icono,
        "estabilidad": estabilidad, "estabilidad_score": estabilidad_score,
        "riesgo": riesgo, "riesgo_icono": riesgo_icono,
    }


# ──────────────────────────────────────────────────────────────
# SIDEBAR — SOLO FECHAS Y CALIDAD (estación fija, no seleccionable)
# ──────────────────────────────────────────────────────────────
st.sidebar.markdown("### 🌿 Estación monitoreada")
st.sidebar.markdown(
    f"""
    <div style="
        padding:14px; border-radius:12px;
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.15);
        margin-bottom: 18px;
    ">
        <div style="font-size:13px; opacity:0.8;">{RED} · Cód. {CODIGO_ESTACION}</div>
        <div style="font-size:19px; font-weight:700; margin-top:2px;">{NOMBRE_ESTACION}</div>
        <div style="font-size:14px; opacity:0.85;">{MUNICIPIO}, Antioquia</div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.sidebar.caption("Esta app está fijada a una sola estación. No es posible seleccionar otra.")

st.sidebar.markdown("### 📅 Rango de consulta")

nombre_estudiante = st.sidebar.text_input("Nombre del estudiante", "Tu Nombre Aquí")

fecha_desde = st.sidebar.date_input("Desde", pd.to_datetime("2026-08-23")).strftime("%Y-%m-%d")
fecha_hasta = st.sidebar.date_input("Hasta", pd.to_datetime("2026-08-30")).strftime("%Y-%m-%d")

calidad = st.sidebar.selectbox("Calidad", [1, 0], index=0, help="1 = solo datos validados")

consultar = st.sidebar.button("🔍 Consultar", type="primary", use_container_width=True)

# ──────────────────────────────────────────────────────────────
# ENCABEZADO
# ──────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style="
        padding:26px 30px;
        border-radius:20px;
        background: linear-gradient(135deg, {PALETA['fondo_grad_1']}, {PALETA['fondo_grad_2']} 70%, #0e7a63);
        color: {PALETA['texto_claro']};
        margin-bottom: 22px;
        box-shadow: 0 8px 24px rgba(6,59,50,0.18);
    ">
        <span class="badge-fija">ESTACIÓN FIJA · SIN SELECCIÓN</span>
        <h1 style="margin:6px 0 2px 0; color:{PALETA['texto_claro']};">🌿 {NOMBRE_ESTACION}</h1>
        <p style="margin:0; font-size:15px; opacity:0.92;">
            {RED} · Código {CODIGO_ESTACION} · {MUNICIPIO}, Antioquia — CORNARE
        </p>
        <p style="margin:6px 0 0 0; font-size:13px; opacity:0.75;">
            Estudiante: {nombre_estudiante}
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────
# CUERPO PRINCIPAL
# ──────────────────────────────────────────────────────────────
if consultar:

    with st.spinner("Consultando la API de CORNARE..."):
        datos_crudos, error = obtener_serie_nivel(CODIGO_ESTACION, fecha_desde, fecha_hasta, calidad)

    if error:
        st.error(f"❌ {error}")

    else:
        registros = obtener_todas_las_paginas(datos_crudos)

        if not registros:
            st.warning(
                "No hay registros para este rango de fechas en la Quebrada Yarumal. "
                "Prueba con otro rango de fechas."
            )

        else:
            df = pd.DataFrame(registros)
            df = df.rename(columns={LLAVE_FECHA: "fecha", LLAVE_VALOR: "nivel"})
            df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
            df["nivel"] = pd.to_numeric(df["nivel"], errors="coerce")
            df = df.dropna(subset=["fecha", "nivel"]).sort_values("fecha").reset_index(drop=True)

            lat, lon, coords_reales = detectar_coordenadas(datos_crudos)
            indice_calidad, huecos, n_outliers = calcular_indice_calidad(df)
            metricas = calcular_metricas_avanzadas(df)

            df["promedio_movil"] = df["nivel"].rolling(window=min(10, len(df)), min_periods=1).mean()
            df["variacion"] = df["nivel"].diff()

            VERDE = "#0a5c4f"
            VERDE_CLARO = "#34d1a3"
            NARANJA = "#f59e0b"
            ROJO = "#ef4444"

            # ── Métricas principales ──
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("🌊 Nivel actual", f"{metricas['actual']:.2f}", f"{metricas['variacion_absoluta']:+.2f}")
            col2.metric("📊 Nivel promedio", f"{metricas['promedio']:.2f}", f"{metricas['actual'] - metricas['promedio']:+.2f}")
            col3.metric("📈 Tendencia", f"{metricas['tendencia_icono']} {metricas['tendencia']}", f"{metricas['pendiente']:+.4f}")
            col4.metric("🧭 Estado", f"{metricas['riesgo_icono']} {metricas['riesgo']}", f"{metricas['variacion_porcentual']:+.1f}%")

            st.divider()

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("🔼 Nivel máximo", f"{metricas['maximo']:.2f}")
            col2.metric("🔽 Nivel mínimo", f"{metricas['minimo']:.2f}")
            col3.metric("↔️ Rango", f"{metricas['rango']:.2f}")
            col4.metric("📐 Mediana", f"{metricas['mediana']:.2f}")

            # ── Gráfico principal: nivel + promedio móvil (Plotly) ──
            st.subheader("📡 Comportamiento del nivel")

            fig_linea = go.Figure()
            fig_linea.add_trace(go.Scatter(
                x=df["fecha"], y=df["nivel"], mode="lines",
                name="Nivel", line=dict(color=VERDE_CLARO, width=2),
                fill="tozeroy", fillcolor="rgba(52, 209, 163, 0.12)"
            ))
            fig_linea.add_trace(go.Scatter(
                x=df["fecha"], y=df["promedio_movil"], mode="lines",
                name="Promedio móvil", line=dict(color=VERDE, width=2, dash="dash")
            ))
            fig_linea.update_layout(
                height=420, margin=dict(l=10, r=10, t=10, b=10),
                plot_bgcolor="white", paper_bgcolor="white",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis_title=None, yaxis_title="Nivel",
            )
            st.plotly_chart(fig_linea, use_container_width=True)

            col1, col2, col3 = st.columns(3)
            col1.metric("⚡ Mayor aumento", f"{metricas['mayor_subida']:.2f}")
            col2.metric("⚡ Mayor descenso", f"{metricas['mayor_bajada']:.2f}")
            col3.metric("🎯 Percentil actual", f"{metricas['percentil_actual']:.1f}%")

            # ── Lectura inteligente ──
            st.subheader("🧠 Lectura inteligente de la quebrada")
            estado_col1, estado_col2, estado_col3 = st.columns(3)
            with estado_col1:
                st.markdown(
                    f"""<div class="tarjeta-info">
                        <div style="font-size:38px;">{metricas['tendencia_icono']}</div>
                        <h3>{metricas['tendencia']}</h3>
                        <p>Tendencia general <b>{metricas['tendencia'].lower()}</b> en el período consultado.</p>
                    </div>""",
                    unsafe_allow_html=True,
                )
            with estado_col2:
                st.markdown(
                    f"""<div class="tarjeta-info">
                        <div style="font-size:38px;">🧘</div>
                        <h3>{metricas['estabilidad']}</h3>
                        <p>Variabilidad relativa: <b>{metricas['coef_variacion']:.1f}%</b></p>
                    </div>""",
                    unsafe_allow_html=True,
                )
            with estado_col3:
                st.markdown(
                    f"""<div class="tarjeta-info">
                        <div style="font-size:38px;">{metricas['riesgo_icono']}</div>
                        <h3>{metricas['riesgo']}</h3>
                        <p>Nivel actual: <b>{metricas['actual']:.2f}</b></p>
                    </div>""",
                    unsafe_allow_html=True,
                )

            # ── Fila de gráficos secundarios ──
            st.subheader("📊 Análisis de variaciones y distribución")
            gcol1, gcol2 = st.columns(2)

            with gcol1:
                cambios_df = pd.DataFrame({
                    "Movimiento": ["Subidas", "Bajadas", "Estables"],
                    "Cantidad": [metricas["subidas"], metricas["bajadas"], metricas["estables"]],
                })
                fig_barras = px.bar(
                    cambios_df, x="Movimiento", y="Cantidad",
                    color="Movimiento",
                    color_discrete_map={"Subidas": VERDE_CLARO, "Bajadas": ROJO, "Estables": "#94a3b8"},
                    title="Distribución de cambios entre lecturas",
                )
                fig_barras.update_layout(
                    height=340, showlegend=False, margin=dict(l=10, r=10, t=50, b=10),
                    plot_bgcolor="white", paper_bgcolor="white",
                )
                st.plotly_chart(fig_barras, use_container_width=True)

            with gcol2:
                fig_hist = px.histogram(
                    df, x="nivel", nbins=25,
                    title="Distribución de niveles registrados",
                    color_discrete_sequence=[VERDE],
                )
                fig_hist.update_layout(
                    height=340, margin=dict(l=10, r=10, t=50, b=10),
                    plot_bgcolor="white", paper_bgcolor="white",
                    xaxis_title="Nivel", yaxis_title="Frecuencia",
                )
                st.plotly_chart(fig_hist, use_container_width=True)

            gcol3, gcol4 = st.columns(2)

            with gcol3:
                fig_box = go.Figure()
                fig_box.add_trace(go.Box(
                    y=df["nivel"], name="Nivel", marker_color=VERDE_CLARO,
                    boxmean=True
                ))
                fig_box.update_layout(
                    height=340, title="Caja y bigotes — outliers de nivel",
                    margin=dict(l=10, r=10, t=50, b=10),
                    plot_bgcolor="white", paper_bgcolor="white",
                )
                st.plotly_chart(fig_box, use_container_width=True)

            with gcol4:
                fig_var = go.Figure()
                colores_var = [VERDE_CLARO if v >= 0 else ROJO for v in df["variacion"].fillna(0)]
                fig_var.add_trace(go.Bar(
                    x=df["fecha"], y=df["variacion"], marker_color=colores_var, name="Variación"
                ))
                fig_var.update_layout(
                    height=340, title="Variación entre lecturas consecutivas",
                    margin=dict(l=10, r=10, t=50, b=10),
                    plot_bgcolor="white", paper_bgcolor="white",
                    xaxis_title=None, yaxis_title="Δ Nivel",
                )
                st.plotly_chart(fig_var, use_container_width=True)

            # ── Calidad de datos ──
            st.subheader("🎯 Indicadores de calidad")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Lecturas", f"{len(df):,}")
            col2.metric("Calidad", f"{indice_calidad}/100")
            col3.metric("Huecos", f"{huecos}")
            col4.metric("Outliers", f"{n_outliers}")

            calidad_barra = max(0, min(100, indice_calidad))
            st.progress(calidad_barra / 100, text=f"Calidad de datos: {calidad_barra:.1f}%")

            # ── Ubicación ──
            st.subheader(f"📍 Ubicación — {NOMBRE_ESTACION}")
            if not coords_reales:
                st.caption(
                    "La API no trajo latitud/longitud de la estación. "
                    "Se muestra una ubicación aproximada de Rionegro."
                )
            st.map(pd.DataFrame({"lat": [lat], "lon": [lon]}), zoom=12)

            # ── Detalles adicionales ──
            with st.expander("🔎 Detalle avanzado del índice de calidad"):
                st.write(f"Completitud estimada: **{max(0, indice_calidad):.1f}%**")
                st.write(f"Huecos de reporte detectados: **{huecos}**")
                st.write(f"Outliers detectados: **{n_outliers}** de **{len(df)}** lecturas")
                st.write(
                    "El índice combina completitud de la serie (70%) "
                    "y proporción de datos sin outliers (30%)."
                )

            with st.expander("📈 Estadísticas avanzadas"):
                estadisticas = pd.DataFrame({
                    "Métrica": [
                        "Nivel actual", "Promedio", "Mediana", "Máximo", "Mínimo", "Rango",
                        "Desviación estándar", "Coeficiente de variación",
                        "Variación última lectura", "Variación porcentual",
                        "Subidas", "Bajadas", "Estables",
                    ],
                    "Valor": [
                        f"{metricas['actual']:.4f}", f"{metricas['promedio']:.4f}",
                        f"{metricas['mediana']:.4f}", f"{metricas['maximo']:.4f}",
                        f"{metricas['minimo']:.4f}", f"{metricas['rango']:.4f}",
                        f"{metricas['desviacion']:.4f}", f"{metricas['coef_variacion']:.2f}%",
                        f"{metricas['variacion_absoluta']:+.4f}", f"{metricas['variacion_porcentual']:+.2f}%",
                        metricas["subidas"], metricas["bajadas"], metricas["estables"],
                    ],
                })
                st.dataframe(estadisticas, use_container_width=True, hide_index=True)

            with st.expander("🗃️ Ver datos crudos"):
                tabla = df.copy()
                tabla["fecha"] = tabla["fecha"].dt.strftime("%Y-%m-%d %H:%M:%S")
                st.dataframe(tabla, use_container_width=True, hide_index=True)

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Descargar CSV",
                csv,
                file_name=f"nivel_quebrada_yarumal_{fecha_desde}_a_{fecha_hasta}.csv",
                mime="text/csv",
            )

else:
    st.info("Ajusta el rango de fechas en el panel lateral y presiona **Consultar**.")
    st.caption(
        f"Esta app consulta únicamente la estación **{NOMBRE_ESTACION}** "
        f"({RED}, Cód. {CODIGO_ESTACION}) en {MUNICIPIO}. No hay selector de otras estaciones."
    )
