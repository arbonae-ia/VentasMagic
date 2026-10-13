import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import gspread
from google.oauth2.service_account import Credentials

# ---------------------------------------------------
# 1. CONFIGURACIÓN DE LA PÁGINA Y ESTILOS (UI/UX)
# ---------------------------------------------------
st.set_page_config(page_title="Magic Print Analytics", page_icon="📊", layout="wide")

# CSS Personalizado para un diseño profesional (Tarjetas, sombras, tipografía)
st.markdown("""
    <style>
    .kpi-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        border-left: 5px solid #2563EB;
        margin-bottom: 20px;
    }
    .kpi-title {
        color: #64748B;
        font-size: 14px;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 5px;
    }
    .kpi-value {
        color: #0F172A;
        font-size: 28px;
        font-weight: bold;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Paleta de colores para gráficos
COLOR_PRINCIPAL = "#2563EB" # Azul rey
COLOR_SECUNDARIO = "#38BDF8" # Azul claro
COLOR_TERCIARIO = "#10B981" # Esmeralda
COLORES_CAT = ["#2563EB", "#38BDF8", "#818CF8", "#4F46E5", "#0EA5E9", "#10B981"]

# ---------------------------------------------------
# 2. CARGA Y PREPARACIÓN DE DATOS (ETL - Google Sheets)
# ---------------------------------------------------
@st.cache_data(ttl=600)
def cargar_y_limpiar_datos():
    scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

credentials = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scopes
)

client = gspread.authorize(credentials)

spreadsheet = client.open("Base_Datos_Ventas")

worksheet = spreadsheet.worksheet("Hoja1")

data = worksheet.get_all_values()
if len(data) < 2:
    raise ValueError("La pestaña 'Hoja1' no contiene datos.")

encabezados = [
    str(columna).replace("\ufeff", "").strip()
    for columna in data[0]
]

df = pd.DataFrame(
    data[1:],
    columns=encabezados
)

df.columns = (
    df.columns
    .astype(str)
    .str.strip()
)

df["Fecha"] = pd.to_datetime(
    df["Fecha"],
    errors="coerce"
)

# ---------------------------------------------------
# 3. BARRA LATERAL: FILTROS INTERACTIVOS
# ---------------------------------------------------
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3061/3061341.png", width=60)
st.sidebar.title("Filtros de Análisis")

fecha_min = df_base['Fecha'].min().date()
fecha_max = df_base['Fecha'].max().date()
fechas = st.sidebar.date_input("Rango de Fechas", [fecha_min, fecha_max], min_value=fecha_min, max_value=fecha_max)

df_filtrado = df_base.copy()
if len(fechas) == 2:
    df_filtrado = df_filtrado[(df_filtrado['Fecha'].dt.date >= fechas[0]) & (df_filtrado['Fecha'].dt.date <= fechas[1])]

ciudades = st.sidebar.multiselect("Ciudad", options=df_filtrado["Ciudad"].unique())
if ciudades: df_filtrado = df_filtrado[df_filtrado["Ciudad"].isin(ciudades)]

vendedores = st.sidebar.multiselect("Vendedor", options=df_filtrado["Vendedor"].unique())
if vendedores: df_filtrado = df_filtrado[df_filtrado["Vendedor"].isin(vendedores)]

clientes = st.sidebar.multiselect("Cliente", options=df_filtrado["Cliente"].unique())
if clientes: df_filtrado = df_filtrado[df_filtrado["Cliente"].isin(clientes)]

tipos = st.sidebar.multiselect("Tipo (Producto/Servicio)", options=df_filtrado["Tipo"].unique())
if tipos: df_filtrado = df_filtrado[df_filtrado["Tipo"].isin(tipos)]

# ---------------------------------------------------
# 4. CÁLCULO DE KPIs
# ---------------------------------------------------
facturas_unicas = df_filtrado["Factura #"].nunique()
clientes_unicos = df_filtrado["Cliente"].nunique()
cantidad_vendida = df_filtrado["Cantidad"].sum()

ventas_sin_iva = df_filtrado["Valor Total"].sum()
ventas_con_iva = df_filtrado["Ventas con IVA"].sum()
ticket_promedio = ventas_sin_iva / facturas_unicas if facturas_unicas > 0 else 0
precio_promedio_mts = ventas_sin_iva / cantidad_vendida if cantidad_vendida > 0 else 0

# ---------------------------------------------------
# 5. RENDERIZADO DEL DASHBOARD (LAYOUT)
# ---------------------------------------------------
st.title("Resumen Ejecutivo de Ventas")
st.markdown("---")

col1, col2, col3, col4, col5, col6 = st.columns(6)

def mostrar_kpi(col, titulo, valor, prefix="", sufix=""):
    col.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">{titulo}</div>
            <div class="kpi-value">{prefix}{valor}{sufix}</div>
        </div>
    """, unsafe_allow_html=True)

mostrar_kpi(col1, "Ventas (Sin IVA)", f"{ventas_sin_iva:,.0f}", prefix="$")
mostrar_kpi(col2, "Facturas Emitidas", f"{facturas_unicas}")
mostrar_kpi(col3, "Clientes Atendidos", f"{clientes_unicos}")
mostrar_kpi(col4, "Cantidad (MTS)", f"{cantidad_vendida:,.0f}")
mostrar_kpi(col5, "Ticket Promedio", f"{ticket_promedio:,.0f}", prefix="$")
mostrar_kpi(col6, "Precio Prom. MTS", f"{precio_promedio_mts:,.0f}", prefix="$")

st.markdown("<br>", unsafe_allow_html=True)

st.subheader("📈 Tendencia de Ventas en el Tiempo")
ventas_diarias = df_filtrado.groupby('Fecha')['Valor Total'].sum().reset_index()
fig_trend = px.line(ventas_diarias, x='Fecha', y='Valor Total', markers=True, 
                    color_discrete_sequence=[COLOR_PRINCIPAL])
fig_trend.update_layout(plot_bgcolor='rgba(0,0,0,0)', xaxis_title="", yaxis_title="Ventas (Sin IVA)")
fig_trend.update_xaxes(showgrid=False)
fig_trend.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#E2E8F0')
st.plotly_chart(fig_trend, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

col_c, col_v = st.columns(2)

with col_c:
    st.subheader("📍 Ventas por Ciudad")
    v_ciudad = df_filtrado.groupby('Ciudad')['Valor Total'].sum().reset_index().sort_values('Valor Total', ascending=True)
    fig_ciudad = px.bar(v_ciudad, x='Valor Total', y='Ciudad', orientation='h', text_auto='.2s', color_discrete_sequence=[COLOR_PRINCIPAL])
    fig_ciudad.update_layout(plot_bgcolor='rgba(0,0,0,0)', xaxis_title="Ventas (Sin IVA)", yaxis_title="")
    st.plotly_chart(fig_ciudad, use_container_width=True)

with col_v:
    st.subheader("💼 Desempeño por Vendedor")
    v_vendedor = df_filtrado.groupby(['Vendedor']).agg({'Valor Total':'sum', 'Factura #':'nunique'}).reset_index().sort_values('Valor Total', ascending=True)
    v_vendedor['Ticket Prom.'] = v_vendedor['Valor Total'] / v_vendedor['Factura #']
    
    fig_vend = px.bar(v_vendedor, x='Valor Total', y='Vendedor', orientation='h', text_auto='.2s', 
                      hover_data=['Factura #', 'Ticket Prom.'], color_discrete_sequence=[COLOR_SECUNDARIO])
    fig_vend.update_layout(plot_bgcolor='rgba(0,0,0,0)', xaxis_title="Ventas (Sin IVA)", yaxis_title="")
    st.plotly_chart(fig_vend, use_container_width=True)

col_p, col_comp = st.columns(2)

with col_p:
    st.subheader("🏷️ Ranking de Productos/Servicios")
    metrica_prod = st.radio("Métrica a visualizar:", ["Ventas (Valor)", "Cantidad Vendida", "Frecuencia (Líneas)"], horizontal=True)
    
    if metrica_prod == "Ventas (Valor)":
        v_prod = df_filtrado.groupby('Descripcion')['Valor Total'].sum().reset_index().sort_values('Valor Total', ascending=True).tail(10)
        x_val = 'Valor Total'
    elif metrica_prod == "Cantidad Vendida":
        v_prod = df_filtrado.groupby('Descripcion')['Cantidad'].sum().reset_index().sort_values('Cantidad', ascending=True).tail(10)
        x_val = 'Cantidad'
    else:
        v_prod = df_filtrado.groupby('Descripcion').size().reset_index(name='Frecuencia').sort_values('Frecuencia', ascending=True).tail(10)
        x_val = 'Frecuencia'
        
    fig_prod = px.bar(v_prod, x=x_val, y='Descripcion', orientation='h', text_auto='.2s', color_discrete_sequence=[COLOR_PRINCIPAL])
    fig_prod.update_layout(plot_bgcolor='rgba(0,0,0,0)', xaxis_title="", yaxis_title="")
    st.plotly_chart(fig_prod, use_container_width=True)

with col_comp:
    st.subheader("🏢 Productos vs Servicios por Ciudad")
    comp_ciudad = df_filtrado.groupby(['Ciudad', 'Tipo'])['Valor Total'].sum().reset_index()
    fig_comp = px.bar(comp_ciudad, x='Valor Total', y='Ciudad', color='Tipo', orientation='h', barmode='stack',
                      color_discrete_map={"Producto": COLOR_PRINCIPAL, "Servicio": COLOR_TERCIARIO})
    fig_comp.update_layout(plot_bgcolor='rgba(0,0,0,0)', xaxis_title="Ventas (Sin IVA)", yaxis_title="", legend_title="")
    st.plotly_chart(fig_comp, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

st.subheader("📋 Análisis Detallado")
tab1, tab2, tab3 = st.tabs(["👥 Ventas por Cliente", "💳 Forma de Pago", "🧾 Detalle de Facturas (Líneas)"])

with tab1:
    v_cliente = df_filtrado.groupby(['Cliente', 'Ciudad']).agg({'Valor Total':'sum', 'Factura #':'nunique'}).reset_index().sort_values('Valor Total', ascending=False)
    v_cliente.rename(columns={'Valor Total': 'Ventas', 'Factura #': 'Facturas'}, inplace=True)
    v_cliente['Ticket Promedio'] = v_cliente['Ventas'] / v_cliente['Facturas']
    st.dataframe(v_cliente.style.format({'Ventas': '${:,.0f}', 'Ticket Promedio': '${:,.0f}'}), use_container_width=True)

with tab2:
    v_pago = df_filtrado.groupby('Forma de Pago')['Valor Total'].sum().reset_index().sort_values('Valor Total', ascending=False)
    v_pago['Participación %'] = (v_pago['Valor Total'] / v_pago['Valor Total'].sum()) * 100
    st.dataframe(v_pago.style.format({'Valor Total': '${:,.0f}', 'Participación %': '{:.1f}%'}), use_container_width=True)

with tab3:
    columnas_mostrar = ['Factura #', 'Fecha', 'Cliente', 'Ciudad', 'Vendedor', 'Codigo Articulo', 'Descripcion', 'Cantidad', 'Valor Total']
    st.dataframe(df_filtrado[columnas_mostrar].style.format({'Valor Total': '${:,.0f}', 'Cantidad': '{:,.1f}'}), use_container_width=True)
