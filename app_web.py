import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import datetime

st.set_page_config(page_title="Simulador de Saturación RTD", layout="wide")
st.title("🧪 Control de Cambio de Color y Saturación de Óxidos - Vidrio Flint")

MASA_EXTRA = 1.8

def calcular_dinamica(longitud, ancho, nivel, extraccion, temp):
    delta_t = temp - 1400
    densidad_actual = max(2.20, 2.35 - (delta_t * 0.00015))
    
    area = longitud * ancho
    f_muerto_base = 0.10 + (0.3325 / area)
    f_muerto_base = max(0.10, min(f_muerto_base, 0.30))
    f_muerto_actual = max(0.05, f_muerto_base - (delta_t * 0.0002))
    
    f_piston = max(0.10, min(0.50, 0.30 - (delta_t * 0.0015))) 

    volumen_fusion = area * nivel
    masa_fusion = volumen_fusion * densidad_actual
    masa_total = masa_fusion + MASA_EXTRA
    
    tau_teorico_h = (masa_total / extraccion) * 24
    tau_activo_h = tau_teorico_h * (1 - f_muerto_actual)
    
    t_piston_h = tau_activo_h * f_piston
    t_mezcla_h = tau_activo_h * (1 - f_piston)

    return masa_total, tau_teorico_h, t_piston_h, t_mezcla_h, f_muerto_actual, f_piston

# --- INTERFAZ WEB (Formulario en Barra lateral) ---
with st.sidebar.form("formulario_datos"):
    st.header("🗓️ Inicio del Cambio de Mezcla")
    # Al estar en un form, no se sobreescribirá cuando teclees
    fecha_inicio = st.date_input("Fecha", datetime.date.today())
    hora_inicio = st.time_input("Hora", datetime.datetime.now().time())

    st.header("📐 Dimensiones del Tanque")
    longitud = st.number_input("Longitud de Fusión (m)", min_value=1.0, max_value=20.0, value=3.5, step=0.1)
    ancho = st.number_input("Ancho de Fusión (m)", min_value=0.5, max_value=10.0, value=1.9, step=0.1)

    st.header("⚙️ Parámetros Operativos")
    nivel = st.number_input("Nivel de Vidrio (m)", min_value=0.2, max_value=2.0, value=0.60, step=0.01)
    extraccion = st.number_input("Extracción (t/día)", min_value=0.5, max_value=50.0, value=3.60, step=0.1)
    temp = st.number_input("Temperatura de Fusión (°C)", min_value=1250, max_value=1600, value=1400, step=10)
    
    # Botón para procesar todo a la vez
    btn_calcular = st.form_submit_button("Actualizar Cálculos")

# Combinar fecha y hora
inicio_real = datetime.datetime.combine(fecha_inicio, hora_inicio)

# Procesamiento de cálculos
masa_total, tau_teorico_h, t_piston_h, t_mezcla_h, f_muerto, f_piston = calcular_dinamica(longitud, ancho, nivel, extraccion, temp)

tiempo_50_saturacion = t_piston_h + (t_mezcla_h * np.log(2))
tiempo_90_saturacion = t_piston_h + (t_mezcla_h * np.log(10))
tiempo_99_saturacion = t_piston_h + (t_mezcla_h * np.log(100))

# --- CÁLCULO DE FECHAS Y HORAS EXACTAS ---
formato_fecha = "%d %b %Y, %I:%M %p" 
fecha_arranque = inicio_real + datetime.timedelta(hours=t_piston_h)
fecha_50 = inicio_real + datetime.timedelta(hours=tiempo_50_saturacion)
fecha_90 = inicio_real + datetime.timedelta(hours=tiempo_90_saturacion)
fecha_99 = inicio_real + datetime.timedelta(hours=tiempo_99_saturacion)

# --- MOSTRAR RESULTADOS EN MÉTRICAS ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Masa Total en Horno", f"{masa_total:.2f} t")
col2.metric("Inicio del Cambio", f"{t_piston_h:.1f} hrs")
col3.metric("Mitad del Cambio", f"{tiempo_50_saturacion:.1f} hrs")
col4.metric("Convección (Mezcla)", f"{(1-f_piston)*100:.1f} %") 

# --- GRÁFICA DE SATURACIÓN ---
st.subheader("📈 Curva de Evolución y Saturación del Color Nuevo")
fig, ax = plt.subplots(figsize=(10, 4.5))

horas_max = max(240, tau_teorico_h * 2.5)
t_horas = np.linspace(0, horas_max, 500)
porcentaje_saturacion = np.zeros_like(t_horas)

for i, tiempo_h in enumerate(t_horas):
    if tiempo_h < t_piston_h:
        porcentaje_saturacion[i] = 0.0
    else:
        porcentaje_saturacion[i] = (1.0 - np.exp(-(tiempo_h - t_piston_h) / t_mezcla_h)) * 100

ax.plot(t_horas, porcentaje_saturacion, color='#3498db', linewidth=3, label='Saturación del Nuevo Color (%)')
ax.fill_between(t_horas, porcentaje_saturacion, alpha=0.15, color='#3498db')

ax.axvline(x=t_piston_h, color='red', linestyle=':', label=f'Primer vidrio nuevo ({t_piston_h:.1f} hrs)')
ax.axhline(y=50, color='gray', linestyle='--', alpha=0.5)
ax.axhline(y=90, color='gray', linestyle='--', alpha=0.5)
ax.axhline(y=99, color='green', linestyle='--', label='99% Saturado (Estable)')

ax.set_xlabel("Tiempo transcurrido desde el cambio de mezcla (Horas)", fontsize=10)
ax.set_ylabel("Porcentaje de Vidrio Nuevo en la Salida (%)", fontsize=10)
ax.set_ylim(-5, 105)
ax.set_xlim(0, horas_max)
ax.grid(True, linestyle='--', alpha=0.5)
ax.legend(loc='lower right')
st.pyplot(fig)

# --- TABLA DE EVENTOS CON FECHA Y HORA ---
st.subheader("📋 Calendario de Control de Calidad")
st.markdown(f"""
| Etapa de Transición | Tiempo Transcurrido | ⏰ Fecha y Hora Exacta Estimada | ¿Qué observar en máquinas? |
| :--- | :--- | :--- | :--- |
| **Ingreso de nueva mezcla** | 0 horas | **{inicio_real.strftime(formato_fecha)}** | Se carga el nuevo material en las tolvas. |
| **Aparición (0.1%)** | {t_piston_h:.1f} horas | **<span style='color:#e74c3c'>{fecha_arranque.strftime(formato_fecha)}</span>** | Sale la primera gota con trazas. Inicia el viraje. |
| **Mitad del Cambio (50%)** | {tiempo_50_saturacion:.1f} horas | **<span style='color:#f39c12'>{fecha_50.strftime(formato_fecha)}</span>** | Producción mezclada. Momento crítico de transición. |
| **Casi Estable (90%)** | {tiempo_90_saturacion:.1f} horas | **<span style='color:#27ae60'>{fecha_90.strftime(formato_fecha)}</span>** | El color está casi listo, quedan pocos rezagos del viejo. |
| **Estabilidad Total (99%)** | {tiempo_99_saturacion:.1f} horas | **<span style='color:#2ecc71'>{fecha_99.strftime(formato_fecha)}</span>** | Horno limpio y saturado. Color completamente estable. |
""", unsafe_allow_html=True)
