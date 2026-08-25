import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Detector de Anomalías — Módulo 4", layout="wide")

st.title("🚨 Detector de Anomalías: Lógica + Big-O + NumPy")
st.caption(
    "Módulo 4 — Matemáticas Discretas y Complejidad. "
    "La misma decisión lógica, evaluada de forma ingenua vs. vectorizada."
)

tab1, tab2, tab3 = st.tabs(
    ["🔎 Simulación de alarma", "📈 Notación Big-O", "⚡ Benchmark en vivo"]
)


# ---------------------------------------------------------------------------
# Utilidades compartidas
# ---------------------------------------------------------------------------
def generar_datos(n, seed=42, prob_finde=2 / 7):
    """Genera n lecturas sintéticas de temperatura, humedad y día de la semana."""
    rng = np.random.default_rng(seed)
    temperaturas = rng.uniform(15, 40, n)
    humedades = rng.uniform(20, 80, n)
    es_fin_de_semana = rng.random(n) < prob_finde
    return temperaturas, humedades, es_fin_de_semana


def alarma_logica_loop(temperaturas, humedades, finde, temp_umbral, hum_umbral):
    """O(n) — recorre las lecturas una por una en el intérprete de Python.

    Ojo: el `and` de Python hace short-circuit. Si la primera proposición es
    falsa, las otras dos ni se evalúan.
    """
    resultados = []
    for temp, hum, es_finde in zip(temperaturas, humedades, finde):
        resultados.append(temp > temp_umbral and hum < hum_umbral and not es_finde)
    return np.array(resultados)


def alarma_logica_vectorizada(temperaturas, humedades, finde, temp_umbral, hum_umbral):
    """O(n) — misma lógica, pero las 3 máscaras se calculan completas en C.

    NumPy no hace short-circuit: evalúa las tres condiciones sobre todos los
    elementos y después las combina.
    """
    return (temperaturas > temp_umbral) & (humedades < hum_umbral) & ~finde


def alarma_logica_inplace(temperaturas, humedades, finde, temp_umbral, hum_umbral):
    """Igual que la vectorizada, pero reutilizando el buffer con `&=`.

    Evita crear arrays temporales intermedios en cada AND.
    """
    mask = temperaturas > temp_umbral
    mask &= humedades < hum_umbral
    mask &= ~finde
    return mask


# ---------------------------------------------------------------------------
# Tab 1: Simulación de alarma
# ---------------------------------------------------------------------------
with tab1:
    st.subheader("Alarma por regla lógica de tres proposiciones")
    st.write(
        "La alarma dispara combinando tres proposiciones: "
        "*temperatura > umbral* **Y** *humedad < umbral* **Y** **NOT** *es_fin_de_semana*."
    )
    st.latex(r"A = (T > t_{umbral}) \land (H < h_{umbral}) \land \lnot F")

    col_cfg, col_data = st.columns([1, 2])

    with col_cfg:
        n = st.slider("Número de lecturas (n)", 50, 5000, 500, step=50)
        temp_umbral = st.slider("Umbral temperatura (°C) — mayor que", 15, 40, 30)
        hum_umbral = st.slider("Umbral humedad (%) — menor que", 20, 80, 40)
        aplicar_finde = st.checkbox(
            "Aplicar la condición NOT (fin de semana)", value=True
        )

    temps, hums, finde = generar_datos(n)

    # Si el checkbox está apagado, tratamos todo como día hábil para poder
    # comparar el efecto de la tercera proposición.
    finde_activo = finde if aplicar_finde else np.zeros(n, dtype=bool)

    alarmas = alarma_logica_vectorizada(
        temps, hums, finde_activo, temp_umbral, hum_umbral
    )
    # Lecturas que cumplían temp+humedad pero fueron bloqueadas por el NOT
    bloqueadas = (temps > temp_umbral) & (hums < hum_umbral) & finde_activo
    normales = ~alarmas & ~bloqueadas

    with col_cfg:
        st.metric("Alarmas detectadas", f"{alarmas.sum()} / {n}")
        st.metric("Bloqueadas por fin de semana", f"{bloqueadas.sum()}")

    with col_data:
        fig, ax = plt.subplots(figsize=(6, 4.5))
        ax.scatter(
            temps[normales], hums[normales],
            c="steelblue", alpha=0.5, label="Normal", s=15,
        )
        ax.scatter(
            temps[bloqueadas], hums[bloqueadas],
            c="darkorange", alpha=0.8, label="Bloqueada por NOT (fin de semana)",
            s=25, marker="x",
        )
        ax.scatter(
            temps[alarmas], hums[alarmas],
            c="crimson", alpha=0.8, label="Alarma / anomalía", s=25,
        )
        ax.axvline(temp_umbral, color="gray", ls="--", lw=1, alpha=0.6)
        ax.axhline(hum_umbral, color="gray", ls="--", lw=1, alpha=0.6)
        ax.set_xlabel("Temperatura (°C)")
        ax.set_ylabel("Humedad (%)")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
        st.pyplot(fig)

    with st.expander("Ver datos y lógica aplicada"):
        df = pd.DataFrame({
            "temperatura": temps.round(2),
            "humedad": hums.round(2),
            "es_fin_de_semana": finde_activo,
            "alarma": alarmas,
        })
        st.dataframe(df, use_container_width=True, height=250)

    st.info(
        "Los puntos naranjas cumplen las dos primeras proposiciones pero caen en "
        "fin de semana, así que el **NOT** los desactiva. Desmarca la casilla para "
        "verlos convertirse en alarmas."
    )


# ---------------------------------------------------------------------------
# Tab 2: Notación Big-O
# ---------------------------------------------------------------------------
with tab2:
    st.subheader("¿Por qué importa la complejidad?")
    st.write(
        "El detector de arriba recorre `n` lecturas **una sola vez**: es un algoritmo "
        "**O(n)**. Aquí puedes ver qué tan distinto crece el número de operaciones "
        "frente a otras complejidades comunes, a medida que aumentan los datos."
    )

    col_a, col_b = st.columns([2, 1])
    with col_a:
        n_max = st.slider("Tamaño máximo de n para la gráfica", 10, 200, 50)
    with col_b:
        escala_log = st.checkbox("Escala logarítmica (eje Y)", value=True)
        mostrar_cubica = st.checkbox("Mostrar O(n³)", value=True)

    n_valores = np.arange(1, n_max + 1)

    fig2, ax2 = plt.subplots(figsize=(8, 5))
    ax2.plot(n_valores, np.ones_like(n_valores), label="O(1) — constante")
    ax2.plot(n_valores, n_valores, label="O(n) — lineal (nuestro detector)", lw=2.5)
    ax2.plot(
        n_valores,
        n_valores * np.log2(np.maximum(n_valores, 2)),
        label="O(n log n)",
    )
    ax2.plot(n_valores, n_valores ** 2, label="O(n²) — cuadrática")
    if mostrar_cubica:
        ax2.plot(n_valores, n_valores ** 3, label="O(n³) — cúbica")
    if escala_log:
        ax2.set_yscale("log")
    ax2.set_xlabel("Tamaño de los datos (n)")
    ax2.set_ylabel("Operaciones (teórico)")
    ax2.set_title("Crecimiento de distintas complejidades")
    ax2.legend()
    ax2.grid(alpha=0.3)
    st.pyplot(fig2)

    st.success(
        "**¿Cambia el Big-O al agregar una tercera proposición?** No: sigue siendo "
        "**O(n)**. Pasamos de 2 comparaciones a 3 comparaciones más una negación, "
        "pero eso es trabajo *constante por elemento*. O(3n + n) = O(n), porque la "
        "notación descarta constantes y coeficientes. La complejidad solo subiría si "
        "la condición nueva obligara a recorrer los datos otra vez **por cada** "
        "lectura — ahí sí tendríamos O(n²)."
    )

    st.info(
        "Nuestro detector es O(n) tanto con loop como con NumPy: la notación no cambia. "
        "Lo que cambia es la **constante** detrás de cada operación, y eso es justo lo "
        "que mides en la siguiente pestaña."
    )


# ---------------------------------------------------------------------------
# Tab 3: Benchmark en vivo
# ---------------------------------------------------------------------------
with tab3:
    st.subheader("Loop vs. NumPy: misma lógica, distinta velocidad real")
    st.write(
        "Ejecuta la condición lógica de tres proposiciones sobre datos sintéticos: "
        "una vez con un loop de Python puro, otra vectorizada con NumPy, y otra "
        "vectorizada evitando arrays temporales."
    )

    n_bench = st.select_slider(
        "Tamaño de datos para el benchmark",
        options=[1_000, 10_000, 100_000, 500_000, 1_000_000],
        value=1_000_000,
    )
    temp_umbral_b = st.slider("Umbral temperatura (°C)", 15, 40, 30, key="temp_bench")
    hum_umbral_b = st.slider("Umbral humedad (%)", 20, 80, 40, key="hum_bench")

    if st.button("▶️ Ejecutar benchmark", type="primary"):
        temps_b, hums_b, finde_b = generar_datos(n_bench)

        # perf_counter tiene mucha más resolución que time.time(), y repetimos
        # varias veces porque las versiones vectorizadas pueden ser demasiado
        # rápidas para medirse de forma confiable en una sola corrida.
        repeticiones_loop = 1
        repeticiones_vec = 20

        with st.spinner("Corriendo el loop de Python..."):
            inicio = time.perf_counter()
            for _ in range(repeticiones_loop):
                r_loop = alarma_logica_loop(
                    temps_b, hums_b, finde_b, temp_umbral_b, hum_umbral_b
                )
            t_loop = (time.perf_counter() - inicio) / repeticiones_loop

        inicio = time.perf_counter()
        for _ in range(repeticiones_vec):
            r_vec = alarma_logica_vectorizada(
                temps_b, hums_b, finde_b, temp_umbral_b, hum_umbral_b
            )
        t_vec = (time.perf_counter() - inicio) / repeticiones_vec

        inicio = time.perf_counter()
        for _ in range(repeticiones_vec):
            r_inp = alarma_logica_inplace(
                temps_b, hums_b, finde_b, temp_umbral_b, hum_umbral_b
            )
        t_inp = (time.perf_counter() - inicio) / repeticiones_vec

        # Verificación: las tres versiones deben dar exactamente lo mismo.
        iguales = np.array_equal(r_loop, r_vec) and np.array_equal(r_vec, r_inp)
        if iguales:
            st.success(
                f"✅ Las tres versiones coinciden — {r_vec.sum():,} alarmas "
                f"sobre {n_bench:,} lecturas."
            )
        else:
            st.error("❌ Las versiones NO coinciden. Revisa la lógica.")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Loop (Python)", f"{t_loop*1000:.3f} ms")
        col2.metric("NumPy", f"{t_vec*1000:.3f} ms")
        col3.metric("NumPy in-place", f"{t_inp*1000:.3f} ms")

        if t_vec > 0:
            col4.metric("Speedup NumPy", f"{t_loop / t_vec:,.0f}x")
        else:
            col4.metric("Speedup NumPy", "demasiado rápido")

        st.caption(
            f"Tiempo con loop promediado sobre {repeticiones_loop} corrida(s); "
            f"tiempos vectorizados promediados sobre {repeticiones_vec} corridas, "
            "para reducir el ruido de la medición."
        )

        fig3, ax3 = plt.subplots(figsize=(6, 3.5))
        barras = ax3.bar(
            ["Loop (Python)", "NumPy", "NumPy in-place"],
            [t_loop * 1000, t_vec * 1000, t_inp * 1000],
            color=["indianred", "seagreen", "darkcyan"],
        )
        ax3.bar_label(barras, fmt="%.2f ms", padding=3, fontsize=8)
        ax3.set_ylabel("Tiempo (milisegundos)")
        ax3.set_yscale("log")
        ax3.grid(alpha=0.3, axis="y")
        st.pyplot(fig3)

        st.info(
            "**¿Se mantiene la ventaja de NumPy con n = 1.000.000?** Sí, típicamente "
            "entre 50x y 200x. El speedup puede bajar un poco frente a la versión de "
            "dos condiciones por dos razones: el `and` de Python hace *short-circuit* "
            "(si la temperatura no pasa el umbral, ni evalúa las otras dos), mientras "
            "que NumPy calcula las tres máscaras completas y genera arrays temporales. "
            "Aun así, el loop opera en el intérprete con overhead de objeto por cada "
            "elemento y NumPy corre en C sobre memoria contigua: la diferencia de "
            "constante es de órdenes de magnitud."
        )
    else:
        st.caption(
            "Ajusta los parámetros y presiona **Ejecutar benchmark** para ver el "
            "resultado. Con n = 1.000.000 el loop puede tardar ~1 segundo."
        )
