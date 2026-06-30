import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# Configuración de la página
st.set_page_config(page_title="Simulador RTD Horno", layout="wide")
st.title("🔥 Simulador de Tiempo de Residencia (RTD) - Vidrio Flint")

# Parámetros fijos (Zonas de distribución y extracción)
MASA_EXTRA = 1.4

def calcular_dinamica(longitud, ancho, nivel, extraccion, temp):
    # 1. Correcciones de densidad por temperatura
    delta_t = temp - 1400
    densidad_actual = max(2.20, 2.35 - (delta_t * 0.00015))
    
    # 2. Corrección del VOLUMEN MUERTO basada en el tamaño del horno
    area = longitud * ancho
    # Fórmula heurística: a menor área, mayor impacto de la fricción de paredes (más volumen muerto)
    # Para un área de 6.65 m2 (3.5 x 1.9), esto da exactamente 0.15 (15%)
    f_muerto_base = 0.10 + (0.3325 / area)
    
    # Limitamos los extremos lógicos (nunca menos del 10% ni más del 30% por geometría pura)
    f_muerto_base = max(0.10, min(f_muerto_base, 0.30))
    
    # 3. Sumamos la corrección de viscosidad por temperatura
    f_muerto_actual = max(0.05, f_muerto_base - (delta_t * 0.0002))
    f_piston = 0.30 

    # 4. Cálculos de masa
    volumen_fusion = area * nivel
    masa_fusion = volumen_fusion * densidad_actual
    masa_total = masa_fusion + MASA_EXTRA
    
    # 5. Cálculos de tiempos de residencia
    tau_teorico = masa_total / extraccion
    tau_activo = tau_teorico * (1 - f_muerto_actual)
    
    t_piston = tau_activo * f_piston
    t_mezcla = tau_activo * (1 - f_piston)

    return masa_total, tau_teorico, t_piston, t_mezcla, f_muerto_actual

# --- INTERFAZ WEB (Barra lateral) ---
st.sidebar.header("📐 Dimensiones del Tanque")
longitud = st.sidebar.number_input("Longitud de Fusión (m)", min_value=1.0, max_value=20.0, value=3.5, step=0.1)
ancho = st.sidebar.number_input("Ancho de Fusión (m)", min_value=0.5, max_value=10.0, value=1.9, step=0.1)

st.sidebar.header("⚙️ Parámetros Operativos")
nivel = st.sidebar.number_input("Nivel de Vidrio (m)", min_value=0.2, max_value=2.0, value=0.60, step=0.01)
extraccion = st.sidebar.number_input("Extracción (t/día)", min_value=0.5, max_value=50.0, value=3.60, step=0.1)
temp = st.sidebar.number_input("Temperatura de Fusión (°C)", min_value=1250, max_value=1600, value=1400, step=10)

# Procesamiento de cálculos
masa_total, tau_teorico, t_piston, t_mezcla, f_muerto = calcular_dinamica(longitud, ancho, nivel, extraccion, temp)

# Conversión a horas
tau_teorico_h = tau_teorico * 24
t_piston_h = t_piston * 24
t_mezcla_h = t_mezcla * 24

# --- MOSTRAR RESULTADOS ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Masa Total Estimada", f"{masa_total:.2f} t")
col2.metric("Promedio Teórico", f"{tau_teorico_h:.1f} hrs")
col3.metric("Tiempo Mínimo (Primer Trazador)", f"{t_piston_h:.1f} hrs")
col4.metric("Volumen Muerto Calculado", f"{f_muerto*100:.1f} %")

# --- GRÁFICA RTD ---
st.subheader("Distribución de Tiempo de Residencia")
fig, ax = plt.subplots(figsize=(10, 4))

horas_max = max(240, tau_teorico_h * 2.5)
t_horas = np.linspace(0, horas_max, 500)
c = np.zeros_like(t_horas)

for i, tiempo_h in enumerate(t_horas):
    if tiempo_h >= t_piston_h:
        c[i] = (1 / t_mezcla_h) * np.exp(-(tiempo_h - t_piston_h) / t_mezcla_h)

ax.plot(t_horas, c, color='#27ae60', linewidth=2.5)
ax.fill_between(t_horas, c, alpha=0.2, color='#2ecc71')
ax.axvline(x=tau_teorico_h, color='black', linestyle='--', alpha=0.6, label=f'Promedio Teórico ({tau_teorico_h:.1f} hrs)')
ax.axvline(x=t_piston_h, color='blue', linestyle=':', label=f'Tiempo Mínimo ({t_piston_h:.1f} hrs)')

ax.set_xlabel("Tiempo (Horas)")
ax.set_ylabel("Concentración E(t)")
ax.grid(True, linestyle='--', alpha=0.5)
ax.legend()

# Enviar gráfica a Streamlit
st.pyplot(fig)

# Nota al pie
st.markdown("---")
st.caption("Nota: El modelo asume 1.4 t constantes en zonas de distribución/extracción. El volumen muerto se ajusta dinámicamente según la geometría del tanque y la viscosidad derivada de la temperatura.")