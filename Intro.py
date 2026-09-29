"""Portafolio de aplicaciones (Streamlit).

Todo vive en este único archivo.
Para añadir una app nueva: agrega un diccionario a la lista APPS.
  - icon: una clave del diccionario ICONS (si no existe, se usa un icono genérico).
  - kind: "Sesión N" muestra el número grande en la tarjeta; cualquier otro texto se muestra tal cual.
"""
import html
import re
from collections import Counter

import streamlit as st

# ─────────────────────────── Configuración ───────────────────────────
st.set_page_config(page_title="Portafolio", page_icon="✨", layout="wide")

SITE_URL = "https://sites.google.com/view/aplicacionesdeia/inicio"
# Si escribes tu usuario de GitHub, los repositorios se vuelven enlaces.
# Vacío = se muestra solo el nombre del repositorio (no se inventa ninguna URL).
GITHUB_USER = ""

# Cada categoría: color de acento
CATEGORIES = {
    "Fundamentos": "#0891b2",
    "Datos": "#d946ef",
    "Modelos predictivos": "#f43f5e",
    "Sensores e IoT": "#84cc16",
    "Voz y audio": "#0a7cff",
    "Visión": "#a347e6",
    "Lenguaje": "#1797b5",
}

# ─────────────────────────── Iconos (SVG en línea) ───────────────────────────
# Trazos de 24×24; se dibujan con el color de la categoría.
ICONS = {
    # Gradiente: ascenso hacia el máximo
    "gradiente": '<path d="M3 17l6-6 4 4 8-8"/><path d="M14 7h7v7"/>',
    # Anomalías: nube de puntos con un punto aislado resaltado
    "anomalias": '<path d="M3 3v18h18"/><circle cx="7" cy="16" r="1.2"/><circle cx="10" cy="14" r="1.2"/>'
                 '<circle cx="9" cy="18" r="1.2"/><circle cx="12" cy="17" r="1.2"/>'
                 '<circle cx="18" cy="7" r="1.4"/><circle cx="18" cy="7" r="3.6" stroke-dasharray="2 2"/>',
    # Preparación de datos: embudo / filtro
    "filtro": '<path d="M3 4h18l-7 8.5V18l-4 2v-7.5z"/>',
    # Análisis con MARCO: lupa sobre barras
    "analisis": '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.6-4.6"/>'
                '<path d="M8 13v-2"/><path d="M11 13V8"/><path d="M14 13v-3"/>',
    # Regresión lineal: ejes, puntos y recta
    "regresion": '<path d="M3 3v18h18"/><path d="M6 18L20 6"/><circle cx="8" cy="13" r="1.1"/>'
                 '<circle cx="12" cy="14" r="1.1"/><circle cx="15" cy="8" r="1.1"/><circle cx="18" cy="10" r="1.1"/>',
    # Series de tiempo: pulso a lo largo del tiempo
    "series": '<path d="M3 12h4l3-8 4 16 3-8h4"/>',
    # Calidad del aire: viento
    "aire": '<path d="M9.6 4.6A2 2 0 1 1 11 8H2"/><path d="M12.6 19.4A2 2 0 1 0 14 16H2"/>'
            '<path d="M17.7 7.7A2.5 2.5 0 1 1 19.5 12H2"/>',
    # Sensor de humedad IoT: gota con señal
    "humedad": '<path d="M12 3l5 5.5a7 7 0 1 1-10 0z"/><path d="M9.5 14.5a2.5 2.5 0 0 0 2.5 2.5"/>'
               '<path d="M19 3.5a4 4 0 0 1 2 3"/><path d="M17.5 5a2 2 0 0 1 1 1.3"/>',
    # ¿Llueve o no?: nube con lluvia
    "lluvia": '<path d="M20 16.6A5 5 0 0 0 18 7h-1.3A8 8 0 1 0 4 15.3"/>'
              '<path d="M8 19v2"/><path d="M8 13v2"/><path d="M16 19v2"/><path d="M16 13v2"/>'
              '<path d="M12 21v1"/><path d="M12 15v2"/>',
    # De la tierra al algoritmo: brote
    "brote": '<path d="M7 20h10"/><path d="M10 20c5.5-2.5.8-6.4 3-10"/>'
             '<path d="M9.5 9.4c1.1.8 1.8 2.2 2.3 3.7-2 .4-3.5.4-4.8-.3-1.2-.6-2.3-1.9-3-4.2 2.8-.5 4.4 0 5.5.8z"/>'
             '<path d="M14.1 6a7 7 0 0 0-1.1 4c1.9-.1 3.3-.6 4.3-1.4 1-1 1.6-2.3 1.7-4.6-2.7.1-4 1-4.9 2z"/>',
    # Genérico
    "chispa": '<path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/><path d="M19 17v4"/><path d="M17 19h4"/>',
    # Iconos de interfaz
    "_flecha": '<path d="M7 17L17 7"/><path d="M8 7h9v9"/>',
    "_repo": '<path d="M4 19.5V5a2 2 0 0 1 2-2h14v14H6a2 2 0 0 0-2 2.5z"/><path d="M6 21h14v-4"/>',
}


def svg(name, size=24, width=1.8):
    body = ICONS.get(name, ICONS["chispa"])
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" '
            f'fill="none" stroke="currentColor" stroke-width="{width}" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true">{body}</svg>')


# ─────────────────────────── Datos ───────────────────────────
APPS = [
    dict(title="Cálculo aplicado: el gradiente", category="Fundamentos", kind="Sesión 3", icon="gradiente",
         description="Explora cómo el gradiente indica hacia dónde mejora una función.",
         url="https://calculo-aplicado-gradiente.streamlit.app",
         repository="Calculo-aplicado-gradiente", technologies=["Gradiente"]),
    dict(title="Detector de anomalías", category="Fundamentos", kind="Sesión 4", icon="anomalias",
         description="Practica lógica, eficiencia (Big-O) y vectorización para encontrar datos extraños.",
         url="https://detector-anomalias-pujphzyih8brne8nhox5zv.streamlit.app",
         repository="detector-anomalias", technologies=["Big-O", "Vectorización"]),
    dict(title="Preparación de datos", category="Datos", kind="Sesión 5", icon="filtro",
         description="Aprende a dejar los datos limpios y listos antes de analizarlos.",
         url="https://preparaci-n-de-datos-yupvhtm8dhjnmfslfsmt3u.streamlit.app",
         repository="Preparaci-n-de-datos", technologies=["Limpieza de datos"]),
    dict(title="Análisis y preparación con MARCO", category="Datos", kind="Sesión 6", icon="analisis",
         description="Una aplicación para revisar y preparar tus datos paso a paso.",
         url="https://preparacion.streamlit.app",
         repository="aplicacion-de-analisis-y-preparacion-de-datos-con-MARCO",
         technologies=["MARCO"]),
    dict(title="Regresión lineal", category="Modelos predictivos", kind="Sesión 7", icon="regresion",
         description="Mira cómo una línea puede describir la relación entre dos variables.",
         url="https://regresion-lineal-py.streamlit.app",
         repository="regresion-lineal", technologies=["Regresión lineal"]),
    dict(title="Series de tiempo", category="Modelos predictivos", kind="Sesión 8", icon="series",
         description="Analiza datos que cambian con el tiempo y observa sus patrones.",
         url="https://time-series-intelligence.streamlit.app",
         repository="Time_Series_Intelligence", technologies=["Series de tiempo"]),
    dict(title="Pronóstico de calidad del aire", category="Modelos predictivos", kind="Aplicación", icon="aire",
         description="Consulta una predicción de la calidad del aire a partir de datos.",
         url="https://pronosticador-de-calidad-de-aire.streamlit.app",
         repository="pronosticador-de-calidad-de-aire", technologies=["Predicción"]),
    dict(title="Sensor de humedad IoT", category="Sensores e IoT", kind="Sesión 10", icon="humedad",
         description="Sigue cómo un dispositivo captura datos de humedad y cómo se procesan.",
         url="https://dispositivo-iot-humedad.streamlit.app",
         repository="streamlit-dispositivo-iot-humedad", technologies=["IoT", "Captura de datos"]),
    dict(title="¿Llueve o no llueve?", category="Modelos predictivos", kind="Sesión 11", icon="lluvia",
         description="Pasa de predecir un número a tomar una decisión de sí o no.",
         url="https://decisiones-binarias-llueve-o-no-j6ardkm39sqb4dvdqvtqf3.streamlit.app",
         repository="decisiones-binarias-llueve-o-no", technologies=["Regresión logística"]),
    dict(title="De la tierra al algoritmo", category="Modelos predictivos", kind="Sesión 12", icon="brote",
         description="Clasifica la fertilidad de un suelo comparándolo con casos parecidos.",
         url="https://de-la-tierra-al-algoritmo.streamlit.app",
         repository="De-la-Tierra-al-Algoritmo", technologies=["KNN", "Clasificación"]),
]

# ─────────────────────────── Estilos ───────────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700;12..96,800&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500&display=swap');
:root{--ink:#16161d;--mute:#5f6070;--soft:#8a8b99;--line:#e7e5df;--paper:#f6f7fb;--card:#ffffff;}
.stApp{background:radial-gradient(900px 400px at 100% 0%,#fce7f366,transparent 60%),radial-gradient(800px 400px at 0% 30%,#cffafe66,transparent 60%),var(--paper)!important;}
html,body,.stApp{font-family:'Inter',system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;}
.stApp{background:var(--paper);color:var(--ink);}
#MainMenu,footer{visibility:hidden;}
header[data-testid="stHeader"]{background:transparent;}
.block-container{max-width:1200px;padding-top:1.5rem;padding-bottom:5rem;}
.stApp p,.stApp li,.stApp label,.stApp span{color:var(--ink);}

/* ---------- Hero ---------- */
.hero{position:relative;overflow:hidden;border-radius:28px;padding:clamp(2rem,5vw,3.6rem);
 background:#0b1026;color:#fff;isolation:isolate;margin-bottom:2.2rem;}
.hero::before{content:"";position:absolute;inset:0;z-index:-2;
 background:radial-gradient(600px 320px at 85% 10%,#06b6d4aa,transparent 65%),
            radial-gradient(520px 300px at 70% 110%,#ec489988,transparent 65%),
            radial-gradient(420px 260px at 5% 120%,#a3e63566,transparent 70%);}
.hero::after{content:"";position:absolute;inset:0;z-index:-1;opacity:.35;
 background-image:linear-gradient(#ffffff14 1px,transparent 1px),linear-gradient(90deg,#ffffff14 1px,transparent 1px);
 background-size:36px 36px;mask-image:linear-gradient(90deg,transparent,#000 60%);
 -webkit-mask-image:linear-gradient(90deg,transparent,#000 60%);}
.eyebrow{display:inline-flex;align-items:center;gap:.5rem;font-family:'JetBrains Mono',monospace;font-size:.75rem;
 letter-spacing:.08em;text-transform:uppercase;color:#a5f3fc!important;background:#ffffff12;border:1px solid #ffffff22;
 padding:.35rem .75rem;border-radius:999px;margin-bottom:1.3rem;}
.eyebrow i{width:7px;height:7px;border-radius:50%;background:#4ade80;box-shadow:0 0 0 4px #4ade8033;}
.hero h1{font-family:'Bricolage Grotesque',sans-serif;font-size:clamp(2.3rem,6vw,4.4rem);line-height:1;
 font-weight:800;letter-spacing:-.035em;margin:0 0 1.1rem;color:#fff!important;max-width:760px;padding:0;}
.hero h1 em{font-style:normal;background:linear-gradient(90deg,#22d3ee,#f472b6 55%,#facc15);-webkit-background-clip:text;
 background-clip:text;color:transparent!important;}
.hero p.lead{font-size:1.1rem;line-height:1.6;color:#c4c4d0!important;max-width:560px;margin:0 0 1.8rem;}
.hero-actions{display:flex;gap:.7rem;flex-wrap:wrap;}
.btn{display:inline-flex;align-items:center;gap:.45rem;padding:.7rem 1.2rem;border-radius:999px;font-weight:600;
 font-size:.92rem;text-decoration:none!important;transition:transform .2s ease,background .2s ease,box-shadow .2s ease;}
.btn:focus-visible{outline:3px solid #22d3ee;outline-offset:2px;}
.btn.light{background:#fff;color:#0b1026!important;}
.btn.light:hover{transform:translateY(-1px);box-shadow:0 8px 24px #00000055;}
.btn.glass{background:#ffffff14;color:#fff!important;border:1px solid #ffffff2e;}
.btn.glass:hover{background:#ffffff24;}
.btn svg{flex:none;}
.stats{display:flex;gap:0;flex-wrap:wrap;margin-top:2.6rem;border-top:1px solid #ffffff1f;padding-top:1.4rem;}
.stat{padding-right:2.4rem;margin-right:2.4rem;border-right:1px solid #ffffff1f;}
.stat:last-child{border-right:0;margin-right:0;}
.stat b{display:block;font-family:'Bricolage Grotesque',sans-serif;font-size:2.2rem;font-weight:700;color:#fff!important;line-height:1.1;}
.stat span{color:#9d9daf!important;font-size:.85rem;}

/* ---------- Encabezado de sección ---------- */
.section-head{display:flex;align-items:end;justify-content:space-between;gap:1rem;flex-wrap:wrap;margin:.5rem 0 1rem;}
.section-head h2{font-family:'Bricolage Grotesque',sans-serif;font-size:1.9rem;font-weight:700;letter-spacing:-.02em;margin:0;padding:0;}
.section-head span{color:var(--soft)!important;font-size:.9rem;}

/* Buscador */
.stTextInput input{background:#fff!important;color:var(--ink)!important;border-radius:14px!important;
 border:1px solid var(--line)!important;padding:.8rem 1rem!important;font-size:1rem!important;}
.stTextInput input:focus{border-color:#06b6d4!important;box-shadow:0 0 0 3px #06b6d422!important;}
.stTextInput input::placeholder{color:var(--soft)!important;}

/* ---------- Tarjetas ---------- */
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:1.2rem;margin-top:1.2rem;}
.card{--c:#0891b2;position:relative;background:var(--card);border:1px solid var(--line);border-radius:22px;
 padding:1.35rem 1.35rem 1.2rem;display:flex;flex-direction:column;gap:.75rem;overflow:hidden;
 transition:transform .25s ease,box-shadow .25s ease,border-color .25s ease;}
.card::before{content:"";position:absolute;inset:0 0 auto 0;height:4px;background:var(--c);opacity:.9;}
.card:hover{transform:translateY(-4px);border-color:color-mix(in srgb,var(--c) 35%,var(--line));
 box-shadow:0 20px 44px -18px color-mix(in srgb,var(--c) 45%,transparent);}
.card-top{display:flex;align-items:flex-start;justify-content:space-between;}
.icon{width:54px;height:54px;border-radius:16px;display:grid;place-items:center;color:var(--c);
 background:color-mix(in srgb,var(--c) 12%,#fff);border:1px solid color-mix(in srgb,var(--c) 22%,#fff);
 transition:transform .3s ease;}
.card:hover .icon{transform:rotate(-6deg) scale(1.06);}
.icon svg{color:var(--c);}
.num{text-align:right;line-height:1;}
.num b{display:block;font-family:'Bricolage Grotesque',sans-serif;font-size:2.4rem;font-weight:800;
 color:color-mix(in srgb,var(--c) 22%,#e9e7e1)!important;letter-spacing:-.04em;}
.num small{font-family:'JetBrains Mono',monospace;font-size:.68rem;letter-spacing:.08em;text-transform:uppercase;color:var(--soft)!important;}
.cat{display:inline-flex;align-items:center;gap:.4rem;font-size:.78rem;font-weight:600;color:var(--c)!important;}
.cat i{width:6px;height:6px;border-radius:50%;background:var(--c);}
.card h3{font-family:'Bricolage Grotesque',sans-serif;margin:0;padding:0;font-size:1.28rem;font-weight:700;
 letter-spacing:-.015em;line-height:1.2;color:var(--ink)!important;}
.card p{margin:0;color:var(--mute)!important;font-size:.93rem;line-height:1.55;}
.tags{display:flex;flex-wrap:wrap;gap:.35rem;}
.tag{font-family:'JetBrains Mono',monospace;background:#f3f2ee;border-radius:7px;padding:.18rem .5rem;
 font-size:.72rem;color:#4a4a57!important;}
.actions{margin-top:auto;padding-top:.9rem;border-top:1px dashed var(--line);display:flex;gap:.6rem;
 align-items:center;justify-content:space-between;flex-wrap:wrap;}
.open{display:inline-flex;align-items:center;gap:.4rem;padding:.55rem 1rem;border-radius:999px;font-weight:600;
 font-size:.86rem;background:var(--ink);color:#fff!important;text-decoration:none!important;
 transition:background .2s ease,gap .2s ease;}
.open:hover{background:var(--c);gap:.6rem;}
.open:focus-visible{outline:3px solid var(--c);outline-offset:2px;}
.repo{display:inline-flex;align-items:center;gap:.35rem;font-size:.76rem;color:var(--soft)!important;
 max-width:55%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;text-decoration:none!important;}
.repo span{overflow:hidden;text-overflow:ellipsis;color:inherit!important;}
a.repo:hover{color:var(--ink)!important;}
.repo svg{flex:none;}
.empty{text-align:center;padding:4rem 1rem;border:1px dashed var(--line);border-radius:22px;margin-top:1.2rem;}
.empty h3{font-family:'Bricolage Grotesque',sans-serif;margin:0 0 .4rem;}
.empty p{color:var(--mute)!important;margin:0;}

/* ---------- Pie ---------- */
.foot{margin-top:3rem;padding-top:1.4rem;border-top:1px solid var(--line);display:flex;justify-content:space-between;
 flex-wrap:wrap;gap:.6rem;font-size:.85rem;color:var(--soft)!important;}
.foot a{color:var(--ink)!important;font-weight:600;}

@media (prefers-reduced-motion:reduce){*{transition:none!important;}}
@media (max-width:640px){
 .stat{padding-right:1.2rem;margin-right:1.2rem;}
 .stat b{font-size:1.7rem;}
 .grid{grid-template-columns:1fr;}
}
</style>
"""


# ─────────────────────────── Funciones ───────────────────────────
def esc(text):
    return html.escape(str(text), quote=True)


def session_number(kind):
    m = re.search(r"\d+", kind)
    return f"{int(m.group()):02d}" if m else None


def render_card(app):
    color = CATEGORIES.get(app["category"], "#0891b2")
    number = session_number(app["kind"])
    num_html = (f'<div class="num"><b>{number}</b><small>Sesión</small></div>' if number
                else f'<div class="num"><b>✦</b><small>{esc(app["kind"])}</small></div>')
    tags = "".join(f'<span class="tag">{esc(t)}</span>' for t in app.get("technologies", []))

    repo = app.get("repository")
    repo_html = ""
    if repo:
        inner = f'{svg("_repo", 14)}<span>{esc(repo)}</span>'
        if GITHUB_USER:
            repo_html = (f'<a class="repo" href="https://github.com/{esc(GITHUB_USER)}/{esc(repo)}" '
                         f'target="_blank" rel="noopener" title="{esc(repo)}">{inner}</a>')
        else:
            repo_html = f'<span class="repo" title="{esc(repo)}">{inner}</span>'

    return (
        f'<article class="card" style="--c:{color}">'
        f'<div class="card-top"><div class="icon">{svg(app.get("icon"), 28)}</div>{num_html}</div>'
        f'<span class="cat"><i></i>{esc(app["category"])}</span>'
        f'<h3>{esc(app["title"])}</h3>'
        f'<p>{esc(app["description"])}</p>'
        f'<div class="tags">{tags}</div>'
        f'<div class="actions"><a class="open" href="{esc(app["url"])}" target="_blank" rel="noopener">'
        f'Abrir aplicación {svg("_flecha", 15, 2.2)}</a>{repo_html}</div>'
        '</article>'
    )


def matches(app, query, category):
    if category != "Todas" and app["category"] != category:
        return False
    if not query:
        return True
    haystack = " ".join([app["title"], app["description"], app["category"], app["kind"],
                         " ".join(app.get("technologies", []))]).lower()
    return all(word in haystack for word in query.lower().split())


# ─────────────────────────── Interfaz ───────────────────────────
st.markdown(CSS, unsafe_allow_html=True)

counts = Counter(a["category"] for a in APPS)
n_repos = sum(1 for a in APPS if a.get("repository"))
n_techs = len({t for a in APPS for t in a.get("technologies", [])})

st.markdown(
    '<section class="hero">'
    '<span class="eyebrow"><i></i>Portafolio interactivo</span>'
    '<h1>Portafolio <em>de aplicaciones.</em></h1>'
    '<p class="lead">Aplicaciones para aprender haciendo: del gradiente y la limpieza de datos '
    'a la regresión, las series de tiempo, los sensores IoT y la clasificación. Abre cualquiera y experimenta.</p>'
    '<div class="hero-actions">'
    f'<a class="btn light" href="#catalogo">Ver aplicaciones</a>'
    f'<a class="btn glass" href="{esc(SITE_URL)}" target="_blank" rel="noopener">'
    f'Ejercicios y páginas {svg("_flecha", 15, 2.2)}</a></div>'
    f'<div class="stats"><div class="stat"><b>{len(APPS)}</b><span>aplicaciones</span></div>'
    f'<div class="stat"><b>{len(counts)}</b><span>temas</span></div>'
    f'<div class="stat"><b>{n_techs}</b><span>técnicas</span></div>'
    f'<div class="stat"><b>{n_repos}</b><span>con repositorio</span></div></div>'
    '</section><div id="catalogo"></div>',
    unsafe_allow_html=True,
)

query = st.text_input("Buscar", placeholder="🔍  Busca por nombre, tema o técnica (por ejemplo: KNN, datos, humedad)",
                      label_visibility="collapsed")
options = ["Todas"] + [c for c in CATEGORIES if counts.get(c)]
category = st.pills("Tema", options, default="Todas", label_visibility="collapsed",
                    format_func=lambda c: f"Todas ({len(APPS)})" if c == "Todas" else f"{c} ({counts[c]})") or "Todas"

visible = [a for a in APPS if matches(a, query, category)]

st.markdown(
    f'<div class="section-head"><h2>{"Aplicaciones" if category == "Todas" else esc(category)}</h2>'
    f'<span>{len(visible)} de {len(APPS)} aplicaciones</span></div>',
    unsafe_allow_html=True,
)

if visible:
    st.markdown('<div class="grid">' + "".join(render_card(a) for a in visible) + "</div>",
                unsafe_allow_html=True)
else:
    st.markdown('<div class="empty"><h3>No encontramos resultados</h3>'
                '<p>Prueba con otra palabra o elige "Todas" en los temas.</p></div>',
                unsafe_allow_html=True)

# ─────────────────────────── Información adicional ───────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
with st.expander("¿Qué temas y técnicas aparecen en este portafolio?"):
    left, right = st.columns(2)
    with left:
        st.markdown("**Temas**")
        for cat, n in counts.most_common():
            st.markdown(f"- {cat}: {n} {'aplicación' if n == 1 else 'aplicaciones'}")
    with right:
        st.markdown("**Técnicas y conceptos**")
        st.markdown(", ".join(sorted({t for a in APPS for t in a.get("technologies", [])})))

st.markdown(
    '<div class="foot"><span>Portafolio de aplicaciones · hecho con Streamlit</span>'
    f'<span>Más material en <a href="{esc(SITE_URL)}" target="_blank" rel="noopener">el sitio del curso</a></span></div>',
    unsafe_allow_html=True,
)
