import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# Configuración de la página
st.set_page_config(page_title="Simulador de Saturación RTD", layout="wide")
st.title("🧪 Control de Cambio de Color y Saturación de Óxidos - Vidrio Flint")

# Parámetros fijos (Zonas de distribución y extracción)
MASA_EXTRA = 1.4

def calcular_dinamica(longitud, ancho, nivel, extraccion, temp):
    # 1. Correcciones de densidad por temperatura
    delta_t = temp - 1400
    densidad_actual = max(2.20, 2.35 - (delta_t * 0.00015))
    
    # 2. Corrección del VOLUMEN MUERTO basada en la geometría
    area = longitud * ancho
    f_muerto_base = 0.10 + (0.3325 / area)
    f_muerto_base = max(0.10, min(f_muerto_base, 0.30))
    
    # 3. Corrección por temperatura
    f_muerto_actual = max(0.05, f_muerto_base - (delta_t * 0.0002))
    f_piston = 0.30 

    # 4. Cálculos de masa
    volumen_fusion = area * nivel
    masa_fusion = volumen_fusion * densidad_actual
    masa_total = masa_fusion + MASA_EXTRA
    
    # 5. Cálculos de tiempos (en horas directamente para evitar confusiones)
    tau_teorico_h = (masa_total / extraccion) * 24
    tau_activo_h = tau_teorico_h * (1 - f_muerto_actual)
    
    t_piston_h = tau_activo_h * f_piston
    t_mezcla_h = tau_activo_h * (1 - f_piston)

    return masa_total, tau_teorico_h, t_piston_h, t_mezcla_h, f_muerto_actual

# --- INTERFAZ WEB (Barra lateral) ---
st.sidebar.header("📐 Dimensiones del Tanque")
longitud = st.sidebar.number_input("Longitud de Fusión (m)", min_value=1.0, max_value=20.0, value=3.5, step=0.1)
ancho = st.sidebar.number_input("Ancho de Fusión (m)", min_value=0.5, max_value=10.0, value=1.9, step=0.1)

st.sidebar.header("⚙️ Parámetros Operativos")
nivel = st.sidebar.number_input("Nivel de Vidrio (m)", min_value=0.2, max_value=2.0, value=0.60, step=0.01)
extraccion = st.sidebar.number_input("Extracción (t/día)", min_value=0.5, max_value=50.0, value=3.60, step=0.1)
temp = st.sidebar.number_input("Temperatura de Fusión (°C)", min_value=1250, max_value=1600, value=1400, step=10)

# Procesamiento de cálculos
masa_total, tau_teorico_h, t_piston_h, t_mezcla_h, f_muerto = calcular_dinamica(longitud, ancho, nivel, extraccion, temp)

# Tiempos clave de saturación (Matemática de reactores continuos)
# F(t) = 1 - exp(-(t-tp)/tm)
tiempo_50_saturacion = t_piston_h + (t_mezcla_h * np.log(2))
tiempo_90_saturacion = t_piston_h + (t_mezcla_h * np.log(10))
tiempo_99_saturacion = t_piston_h + (t_mezcla_h * np.log(100))

# --- MOSTRAR RESULTADOS EN MÉTRICAS ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Masa Total en Horno", f"{masa_total:.2f} t")
col2.metric("Inicio del Cambio (0.1%)", f"{t_piston_h:.1f} hrs")
col3.metric("Mitad del Cambio (50%)", f"{tiempo_50_saturacion:.1f} hrs")
col4.metric("Color Estable (95%)", f"{(t_piston_h + t_mezcla_h * 3):.1f} hrs")

# --- NUEVA GRÁFICA DE SATURACIÓN (%) ---
st.subheader("📈 Curva de Evolución y Saturación del Color Nuevo")
fig, ax = plt.subplots(figsize=(10, 4.5))

horas_max = max(240, tau_teorico_h * 2.5)
t_horas = np.linspace(0, horas_max, 500)
porcentaje_saturacion = np.zeros_like(t_horas)

for i, tiempo_h in enumerate(t_horas):
    if tiempo_h < t_piston_h:
        porcentaje_saturacion[i] = 0.0
    else:
        # Ecuación acumulada de la saturación
        porcentaje_saturacion[i] = (1.0 - np.exp(-(tiempo_h - t_piston_h) / t_mezcla_h)) * 100

# Graficar la curva de saturación
ax.plot(t_horas, porcentaje_saturacion, color='#3498db', linewidth=3, label='Saturación del Nuevo Color (%)')
ax.fill_between(t_horas, porcentaje_saturacion, alpha=0.15, color='#3498db')

# Dibujar líneas de control útiles para el operador
ax.axvline(x=t_piston_h, color='red', linestyle=':', label=f'Primer vidrio nuevo ({t_piston_h:.1f} hrs)')
ax.axhline(y=50, color='gray', linestyle='--', alpha=0.5)
ax.axhline(y=90, color='gray', linestyle='--', alpha=0.5)
ax.axhline(y=99, color='green', linestyle='--', label='99% Saturado (Estable)')

# Configuración de ejes
ax.set_xlabel("Tiempo transcurrido desde el cambio de mezcla (Horas)", fontsize=10)
ax.set_ylabel("Porcentaje de Vidrio Nuevo en la Salida (%)", fontsize=10)
ax.set_ylim(-5, 105)
ax.set_xlim(0, horas_max)
ax.grid(True, linestyle='--', alpha=0.5)
ax.legend(loc='lower right')

# Enviar gráfica a Streamlit
st.pyplot(fig)

# Tabla de estrategia de producción
st.subheader("📋 Tabla de Tiempos Estimados para Control de Calidad")
st.markdown(f"""
| Etapa del Cambio de Color | Tiempo Transcurrido | ¿Qué está pasando en las máquinas formadoras? |
| :--- | :--- | :--- |
| **Vidrio Viejo Puro** | De 0 a {t_piston_h:.1f} horas | El color sigue siendo 100% el anterior. No hay rastro de los nuevos óxidos. |
| **Arranque de Transición** | A las {t_piston_h:.1f} horas | Sale la primera botella con trazas del nuevo óxido. Comienza el viraje. |
| **Mitad del Cambio (50%)** | A las {tiempo_50_saturacion:.1f} horas | La producción es una mezcla exacta: 50% vidrio viejo y 50% vidrio nuevo. |
| **Zona de Alerta (90%)** | A las {tiempo_90_saturacion:.1f} horas | El vidrio ya es 90% la nueva fórmula. El color está casi listo pero quedan rezagos. |
| **Color Estable (99%)** | A las {tiempo_99_saturacion:.1f} horas | **Saturación total.** El horno se ha limpiado por completo. El color ya es estable. |
""")
