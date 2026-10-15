import base64
import io
import re
from html import escape
from pathlib import Path
from datetime import datetime

import gspread
import numpy as np
import pandas as pd
import pdfplumber
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from google.oauth2.service_account import Credentials
from PIL import Image

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA Y ESTILOS VISUALES (UI/UX)
# -----------------------------------------------------------------------------
LOGO_RESPALDO = "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAQDAwMDAgQDAwMEBAQFBgoGBgUFBgwICQcKDgwPDg4MDQ0PERYTDxAVEQ0NExoTFRcYGRkZDxIbHRsYHRYYGRj/2wBDAQQEBAYFBgsGBgsYEA0QGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBj/wAARCACwALADASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAHRAPwDxdiNpqI9KlYfKahbpX26dz+jauxG3SonqVulRPVo4qhC9RmpHqM1aOKoRSVC1TScc1C1XE5p7ELdTUT1K3U1E9WjhmQvUL1M9QvVI4qmxC1RPURqiorWKCVqkepn6CoWqkcVQh1qCSon6VK3SqNx2qiD3NvuGoT0qZuuKgevn0j+haiBuqonqVuoqJ+taAcVSF6jNSPUZq0cVQiEqaiK1K1QvVpjiqEJUb1K9RPVR45kJSoT0qVuoqJ+tXE5KiIWFRP0qVupqJ+lUccyFupqJ+lSt1qF+laocFTIWFRP0qVuoqJ+tUcVSBuqNulSt1qNulaiOCmQt0qFqmbpUT9KtHIUIeKY1T0wqM1onY5qkWZreCeMwzQxujdVdQwP4GoP7J0n/AKBtr/35X/CrT1Ez1qx8VPH3iL4f3WjSaDY6dPFqEs6XBu0clAiIQAVccZY0ua0W0Jq6sc9/ZOk/wDQNtf+/K/4Uf2VpH/QNtf+/K/4V6H4p+IuuaL8RfCHhvT7LTrq08QCzM80kbiRPOnMbgEOBwBn61t3XxK1z/hf9r8P7CyzYXFk8lxMLd2aKZYy4O/dhVO0A8ZzWfPK3NbpcerdvI8p/srSP+gba/8Aflf8KP7K0j/oG2v/AH5X/CvUPib8SPEvg3x7oOjaDZ6bPb6nEkkr3SOXUmTaQm1hgEd67vX/AIu+IfCXxH0nwxquh6dc22rPEltdw70O3fscsCxyygjIB704yclypby0XmdU6TjGUn0Vzwn+ytI/6Btr/AN+V/wAKP7K0j/oG2v8A35X/AAr07XPib4gsPixp3gmw03S7iG8uIYWvXicMpkbaSuHwSPpXX+NvjB4m8I+JbPQdO0jSruS5dIftF1K8cY3sFUEq4IyeOtdHtFa/kcbqU403PZaHzl/ZOk/8Dtr/AN+VpDplgoJ+wW3H/TKvSvip8Qr74eatpemWOlWN3dXkElzLJc7j8qsoCgKR3brWj4h+I2veG/hdoviy/wBP0+S71VwsNuqP5SIM8uN2T09Rya4a9ZVZRhTjdp2b8h1aEqUHUqO0VufM39qWef+PSDx/zyphvrXP8Ax6Q//IVbXw0+JWqePvF+r6Pe6ZptuNMgMqNbCQM5DhcHLn1rpfjX8StW8BatoNrpGn6ZcR6krNKbpHYrgqPlw4x1rphjIyrvDuPvJX/p3OKlS9pQddP3V/wADb8jzL7dZnP8Ax6Qdf+mVAvoT/wAukH/fC17z4p+K/ifQ/AHhrxHZ6bptxc6vMJbiKWNwkQ25wGDc8+tY2v/FTxLpXwjsfG1ppmmvd3c4je1dJPKTOeVO4E9PWiGJUqbpqHvJ2fyJhh5upGk5LlbtdvNdjyD7fbZ/49IOP+mVAvrf8/wDp0H/fKvevjj4m1jw58QfCNpoGq3Wm3l4k7SSW0pQuFdNgOOo5PSuR1z4p+N9P+LOm+G7fxHfJpdzcRRyRNIWJUvhyXPIwOetY0686keaEd20vVJnVWwvsKjhVl8Kau+6uvI4r+3Lf/AJ9IOP8AzlqrNqdtJGR9jg/77evYvF3xR8WaB8ebLwnpuoJDpE1zZRSW4hQs4l2bzuxuB5PQ1k6x8UPG1n8ftL8M2utSrpE13aJJalEIKSbd4ztzzycZrSFaTjGSh8Tv8jxMtxNPE06s5VHJU24va97Xtb01vY8vTU7ZTzYw/jI1KmpW7dfstuc+sn/167b4r/FHxL4N+IV5omhX1vaafbRRlEaCNyWYAsWZlJ6njmkaVqkG4xvbu2XUo04VPY1avvcvNtrb1a2+5HD3GoW5hcfYrccf32/wAa52fWbNWOLKAgnP3m/wAa9R1n4o+LtQ+GuneIri9tTpr3jRLGIIw7YXO7zCu4Y6AAjHrXK/FXxdrPi/X9PuddvRcSW1skceI0TCk852gf57Vph5SqSk+XWK2uTg8PRwsJ16tdPlcldO2qVtve6+hzcmoWxf/jygH4t/jTTqdsc/wCgQD/vtv8AGhvvCoX6V6sYxUUuXsfJzqVpTk/avVvW3e3kO/tW1P8AzD4P++m/xqN9St3kG7TrY445Zv8Aaf7tNPrTG6VUYw0sjnqVKs5XdaX3iPUbcZ/4l1sc8fef/GqP7StwMHSrU/V3/wAatScabpp1L+0jTlHl5j0J+Xw1O77tfmc0uqWvy5021OemA//AMVUzapbnZ/xLLfn2f8Axrqda0PTdY02ezvbeJopQRv2jI+h7GuC+Lni3WfB/g1NS0SeOG5a5SLdJEkgIIPQFSOw7Vxc/tlyr9T2sVgnluWyzTE1JKmlzW5uW65rWTTV3eyXnsbdvqtvJHn+zrb6fN/jTH1a2QnOm2//fTf415V8P8A4meI9b+IthY65qkbaddM0TxC1iiRTtJQ71UMOQBkk9a9S+KniDUPCvw91LWtMlSK8tpIfLd0DAM8qoflPB4Y1vONSpVVKMvspv0bPPw+XZdl+U4nMq+IlKlOdSFFp+97SMU1F6fDzNa3vbWxyvxM+Mvhv4Y6dBNqsM1xeXbFLaytsCSTaMscsQAB6k9+lc18Pfjt4N+Iusf2Tpy6hp9+4zbwX8aq02ACdrKzDI5PJ5xXxd4m8U6x4v1q51jW72W8vrl98krnOB2VR0CgDgDAFZ2kanfaPrFhqWnzNDe2k8c0EinsGByM9iDgjoc08Vha9bFT5Z+7ZJdNPv1Pvsh+EHuPMcI/Z1Kkq0pQnKSUuaXvczT0XKrWXRdG9xLhCrsueFOPzpldP8AEHwld+DfFVxp06kW7EyW0oPEkeTgj34ORXMFc13QkpxUl1Pz7GYepg688PU+KLsYmktUptObrWpy1Eiao3qV6ieqOOrsQvULdKlL9KieoOKpIjaomqRutROK0RxVNgL1qNqkev86jakcVTsZ1qT9ka5gjkjaNshkUjqD1xWf8A2VpH/QNtP+/K/wCFRt0qNjXQcVKq/Z/Zt67nfQreynhXh6fN13t0tbbrvubWl+D/AA5e+F7XWb3R7eWWSaRJDgoowwVeAT6H9KpeNvhzpHhrw/b6lp88zNPMImV5AwGKzPC+saZp/h7VtOvdRa0nupImjCRs+7G4HgA8cn9Kq+KPE9hffh3pui6ddtd3FvOZZXwVRRzwM85yevH1rzquKlKpGEZWbteXo/8jmh7epRlWpuPL7zjHVq60u/l2NfaomqvupURrpRxVH//Z"


def _logo_b64():
    """Lee logo.jpg junto al app.py; si no existe, usa el logo incrustado."""
    try:
        return base64.b64encode((Path(__file__).parent / "logo.jpg").read_bytes()).decode()
    except Exception:
        return LOGO_RESPALDO


LOGO_B64 = _logo_b64()


def _icono():
    try:
        return Image.open(io.BytesIO(base64.b64decode(LOGO_B64)))
    except Exception:
        return "📊"


def fnum(valor, decimales=0):
    """Formato colombiano: punto para miles y coma para decimales."""
    return f"{valor:,.{decimales}f}".replace(",", "#").replace(".", ",").replace("#", ".")


def cop(valor):
    return "$" + fnum(valor)


st.set_page_config(page_title="Magic Print | Analytics", page_icon=_icono(), layout="wide", initial_sidebar_state="collapsed")
try:
    st.set_option("client.toolbarMode", "minimal")
except Exception:
    pass

st.markdown("""
<style>
/* Sistema visual inspirado en el dashboard de visitas comerciales */
.stApp { font-family: "Source Sans Pro", "Source Sans 3", sans-serif; }
.stApp { background: #F4F7F9; color: #2D2D2D; }
.stSidebar { background:#ffffff; }
.block-container { max-width: 1180px; padding-top: 2.8rem; padding-bottom: 3rem; }
[data-testid="stVerticalBlockBorderWrapper"] { background:#ffffff; border:1px solid #e1e6ec !important; border-radius:10px; padding:8px 12px !important; box-shadow:0 2px 8px rgba(28,35,99,.06); }
[data-testid="stVerticalBlockBorderWrapper"] > div { background:#ffffff; border-radius:9px; }
.stSubheader, [data-testid="stMarkdownContainer"] h3 { font-size:1.05rem !important; color:#17245f; }
.stSubheader { margin:0 0 .1rem !important; }
.data-status { color:#7a8495; font-size:10px; font-style:italic; line-height:1.25; margin:2px 0 4px; }
.filter-summary { background:#ffffff; border:1px solid #d7dce4; border-left:4px solid #22286d; border-radius:6px; color:#5f6b80; font-size:11px; line-height:1.45; margin:12px 0 4px; padding:7px 10px; }
.filter-summary strong { color:#17245f; }
.brand-header { background: #fff; border-top: 3px solid #22286d; border-radius: 0 0 8px 8px; padding: 16px 24px; margin-bottom: 16px; box-shadow: 0 1px 5px rgba(20,35,70,.08); display:flex; align-items:center; gap:16px; }
.brand-header img { width:64px; height:64px; object-fit:cover; border-radius:12px; }
.main-title { color:#17245f; font-size:27px; font-weight:700; margin:0; }
.main-subtitle { color:#68738b; font-size:13px; margin-top:4px; }
.section-title { color:#1C2363; font-size:18px; font-weight:700; margin:22px 0 10px; padding-left:10px; border-left:4px solid #00BEEA; }
.panel { background:#fff; border:1px solid #d4d9df; border-radius:9px; padding:14px 16px; }
.kpi-card { background:#fff; border:1px solid #dce1e7; border-top:4px solid #22286d; border-radius:8px; padding:13px 15px; min-height:98px; box-shadow:0 2px 5px rgba(24,38,72,.05); overflow:hidden; }
.kpi-card.blue { border-top-color:#22286d; } .kpi-card.green { border-top-color:#008d68; } .kpi-card.purple { border-top-color:#7755c9; } .kpi-card.orange { border-top-color:#f28b30; } .kpi-card.cyan { border-top-color:#13b9dc; }
.kpi-title { color:#65728a; font-size:10px; font-weight:600; text-transform:uppercase; letter-spacing:.2px; line-height:1.2; }
.kpi-value { color:#1C2363; font-size:clamp(18px, 1.6vw, 25px); line-height:1.15; font-weight:700; margin-top:6px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.kpi-row-gap { height:14px; }
.small-note { color:#68738b; font-size:11px; margin-top:3px; }
.mini-badge { display:inline-block; padding:4px 8px; border-radius:5px; background:#eef1fb; color:#22286d; font-size:10px; font-weight:700; }
.stButton > button { border-radius:6px; border-color:#cbd2dc; color:#17245f; }
.stButton > button[kind="primary"] { background:#22286d; color:#fff; border-color:#22286d; }
.stDataFrame { border:1px solid #dce1e7; }
.hd { display:flex; justify-content:space-between; align-items:center; gap:8px; margin:2px 0 2px; }
.hd h2 { margin:0; padding:0; font-size:1.05rem; font-weight:700; color:#1C2363; }
.tag { background:#eef0fa; color:#1C2363; font-size:11px; font-weight:600; border-radius:6px; padding:2px 8px; white-space:nowrap; }
.sub { margin:0 0 10px; color:#6b7280; font-size:12px; }
.sub2 { margin:12px 0 6px; font-size:11px; font-weight:700; color:#6b7280; letter-spacing:.04em; text-transform:uppercase; }
.seg { display:grid; gap:9px; }
.sr { display:grid; grid-template-columns:minmax(100px,160px) 1fr auto; gap:12px; align-items:center; font-size:13px; }
.sr .n { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.sr .t { height:10px; background:#eef1f5; border-radius:6px; overflow:hidden; }
.sr .t i { display:block; height:100%; border-radius:6px; }
.sr .v { font-weight:700; color:#1C2363; white-space:nowrap; text-align:right; }
#MainMenu, footer { visibility:hidden; }
</style>
""", unsafe_allow_html=True)

NOMBRE_ARCHIVO = "Base_Datos_Ventas"
NOMBRE_PESTANA = "Hoja1"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

COLUMNAS = [
    "Factura #", "Fecha", "Cliente", "Nit", "Ciudad", "Vendedor",
    "Codigo Articulo", "Descripcion", "Unidad", "Cantidad",
    "Precio Unitario", "Valor Total", "% IVA", "Forma de Pago",
    "Tipo de Venta"
]

MESES_PDF = {
    "JAN": "01", "FEB": "02", "MAR": "03", "APR": "04",
    "MAY": "05", "JUN": "06", "JUL": "07", "AUG": "08",
    "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12",
    "AGO": "08", "OCT": "10"
}

CODIGOS_SERVICIO = {"888912", "888923", "888916"}

# -----------------------------------------------------------------------------
# FUNCIONES DE CONEXIÓN Y ETL
# -----------------------------------------------------------------------------
@st.cache_resource
def conectar_hoja():
    try:
        credenciales = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=SCOPES
        )
        cliente = gspread.authorize(credenciales)
        return cliente.open(NOMBRE_ARCHIVO).worksheet(NOMBRE_PESTANA)
    except Exception as error:
        st.error(f"No fue posible conectar con Google Sheets: {error}")
        return None

def limpiar_texto(valor):
    if valor is None:
        return ""
    return re.sub(r"\s+", " ", str(valor).replace("\xa0", " ")).strip()

def limpiar_nit(valor):
    return re.sub(r"[^0-9]", "", limpiar_texto(valor))

def convertir_numero(valor):
    texto = limpiar_texto(valor).replace("$", "").replace(" ", "")
    if not texto:
        return 0.0
    try:
        if "," in texto and "." in texto:
            texto = (texto.replace(".", "").replace(",", ".")
                     if texto.rfind(",") > texto.rfind(".")
                     else texto.replace(",", ""))
        elif "," in texto:
            partes = texto.split(",")
            texto = (texto.replace(".", "").replace(",", ".")
                     if len(partes[-1]) <= 2 else texto.replace(",", ""))
        elif "." in texto:
            partes = texto.split(".")
            texto = texto if len(partes[-1]) <= 2 else texto.replace(".", "")
        return float(texto)
    except Exception:
        return 0.0

def convertir_fecha_pdf(fecha):
    partes = limpiar_texto(fecha).replace("−", "-").replace("–", "-").split("-")
    if len(partes) != 3:
        return ""
    try:
        mes_str = partes[1].upper()
        mes = MESES_PDF.get(mes_str, mes_str)
        return datetime.strptime(
            f"{partes[0]}-{mes}-{partes[2].zfill(2)}", "%Y-%m-%d"
        ).strftime("%Y-%m-%d")
    except Exception:
        return ""

def clasificar_tipo_venta(codigo):
    return "Servicio" if limpiar_texto(codigo) in CODIGOS_SERVICIO else "Bases Textiles"

def extraer_datos_pdf(archivo_pdf):
    registros = []
    contenido = archivo_pdf.read()
    if not contenido:
        raise ValueError("El archivo PDF está vacío.")

    palabras_invalidas = [
        "FACTURA", "NUMERO", "ESTABLECIM", "TELEFONO", "FAX", "DIRECCION", 
        "VENDEDOR", "CLIENTE", "NIT", "FORMA DE PAGO", "FECHA", "RESOLUCION", 
        "PESOS", "TOTAL", "SUBTOTAL", "ANEXO", "PLACA", "CIUDAD", "ORDEN", 
        "PAGINA", "REGIMEN", "CONTRIBUYENTE", "AUTORRETENEDOR"
    ]

    with pdfplumber.open(io.BytesIO(contenido)) as pdf:
        for pagina_num, pagina in enumerate(pdf.pages, start=1):
            texto = (pagina.extract_text() or "").replace("−", "-").replace("–", "-")
            if not texto.strip():
                continue

            es_traslado = "TR" in texto.upper() or "TRANSFERENCIA" in texto.upper()

            factura_match = re.search(r"\b(FM-\d+|TR-\d+)\b", texto, re.I)
            factura = factura_match.group(1).upper() if factura_match else f"FM-{13500+pagina_num}"

            fecha_match = re.search(r"(\d{4}-\d{2}-\d{2})", texto)
            if not fecha_match:
                fecha_match = re.search(r"(\d{4}-[A-Z]{3}-\d{2})", texto, re.I)
            fecha = convertir_fecha_pdf(fecha_match.group(1)) if fecha_match else datetime.now().strftime("%Y-%m-%d")

            cliente_match = re.search(r"Cliente\s*[:]?\s*(.*?)(?:\n|Establecim|Nit|Direccion|$)", texto, re.I)
            cliente = limpiar_texto(cliente_match.group(1)) if cliente_match else ("Bellatela SAS" if es_traslado else "CLIENTE GENERAL")

            nit_match = re.search(r"(?:Nit\s+o\s+C\.C\.|Nit)\s*[:]?\s*([0-9.\-]+)", texto, re.I)
            nit = limpiar_nit(nit_match.group(1)) if nit_match else ("800138082" if es_traslado else "0")

            ciudad_match = re.search(r"(?:Ciudad|Local\.\s*Destino)\s*[:]?\s*([A-ZÁÉÍÓÚÑ ]+)", texto, re.I)
            ciudad = limpiar_texto(ciudad_match.group(1)) if ciudad_match else ("INTERNO" if es_traslado else "CALI")

            vendedor_match = re.search(r"Vendedor\s*[:]?\s*(?:[0-9]+\s+)?(.*?)(?:\n|OC\.Nro|$)", texto, re.I)
            vendedor = limpiar_texto(vendedor_match.group(1)) if vendedor_match else ("WAGNER GIRALDO PAOLA ANDREA" if es_traslado else "GENERAL")

            pago_match = re.search(r"(CREDITO\s+\d+\s+DIAS?|CONTADO)", texto, re.I)
            forma_pago = limpiar_texto(pago_match.group(1)) if pago_match else "CONTADO"

            iva_match = re.search(r"Iva%|19\.00", texto)
            iva_porcentaje = 19.0 if iva_match else 0.0

            lineas = texto.split("\n")
            for linea in lineas:
                linea_clean = limpiar_texto(linea)
                if not linea_clean:
                    continue
                linea_upper = linea_clean.upper()
                if any(p in linea_upper for p in palabras_invalidas):
                    continue

                tokens = linea_clean.split()
                if len(tokens) < 3:
                    continue

                unidad = "MTS"
                for u in ["MTS", "KLS", "UND", "UN", "KG", "KGM", "SERV", "UNIDAD"]:
                    if u in linea_upper:
                        unidad = u
                        break

                numeros_encontrados = []
                texto_descripcion = []

                for t in tokens:
                    t_limpio = t.replace("$", "").replace("*", "").replace("|", "")
                    if re.match(r"^\d{1,3}(,\d{3})*\.\d{2}$", t_limpio) or re.match(r"^\d+\.\d+$", t_limpio) or (t_limpio.replace(".", "").isdigit() and len(t_limpio) <= 8 and not t_limpio.startswith("10000")):
                        val_num = convertir_numero(t_limpio)
                        if val_num > 0:
                            numeros_encontrados.append(val_num)
                    else:
                        if t_limpio.upper() not in {"MTS", "KLS", "UND", "UN", "KG", "KGM", "SERV", "UNIDAD", "19.00", "19.0"}:
                            texto_descripcion.append(t_limpio)

                if len(numeros_encontrados) >= 2:
                    total_val = numeros_encontrados[-1]
                    precio_val = numeros_encontrados[-2] if len(numeros_encontrados) >= 2 else total_val
                    cantidad_val = numeros_encontrados[0] if len(numeros_encontrados) >= 3 and numeros_encontrados[0] < 10000 else 1.0

                    codigo = "100000"
                    if texto_descripcion and texto_descripcion[0].isdigit() and len(texto_descripcion[0]) >= 3:
                        codigo = texto_descripcion.pop(0)

                    descripcion = " ".join(texto_descripcion)
                    if not descripcion:
                        descripcion = "ARTICULO FACTURADO"

                    registros.append([
                        factura, fecha, cliente, nit, ciudad, vendedor,
                        codigo, descripcion, unidad, cantidad_val,
                        precio_val, total_val, iva_porcentaje,
                        forma_pago, clasificar_tipo_venta(codigo)
                    ])

    if not registros:
        raise ValueError("No se pudieron extraer los ítems válidos del PDF.")
    return registros

def obtener_informacion_duplicados(hoja, registros_pdf):
    datos = hoja.get_all_values()
    facturas_pdf = {limpiar_texto(r[0]) for r in registros_pdf}
    if len(datos) < 2:
        return {"facturas_existentes": set(), "filas_a_borrar": [], "facturas_nuevas": facturas_pdf}

    encabezados = [limpiar_texto(x) for x in datos[0]]
    if "Factura #" not in encabezados:
        raise ValueError("No existe la columna 'Factura #' en Google Sheets.")
    posicion = encabezados.index("Factura #")
    existentes, filas = set(), []
    for numero_fila, fila in enumerate(datos[1:], start=2):
        if len(fila) > posicion and limpiar_texto(fila[posicion]) in facturas_pdf:
            existentes.add(limpiar_texto(fila[posicion]))
            filas.append(numero_fila)
    return {
        "facturas_existentes": existentes,
        "filas_a_borrar": filas,
        "facturas_nuevas": facturas_pdf - existentes,
    }

def agregar_facturas_nuevas(hoja, registros_pdf, facturas_existentes):
    nuevos = [r for r in registros_pdf if limpiar_texto(r[0]) not in facturas_existentes]
    if nuevos:
        hoja.append_rows(nuevos, value_input_option="USER_ENTERED")
    return nuevos

def reemplazar_facturas(hoja, registros_pdf, filas_a_borrar):
    for fila in sorted(filas_a_borrar, reverse=True):
        hoja.delete_rows(fila)
    hoja.append_rows(registros_pdf, value_input_option="USER_ENTERED")

@st.cache_data(ttl=30)
def cargar_datos():
    hoja = conectar_hoja()
    datos = hoja.get_all_values()
    if not datos:
        return pd.DataFrame(columns=COLUMNAS)

    encabezados = [limpiar_texto(x) for x in datos[0]]
    if len(datos) == 1:
        return pd.DataFrame(columns=encabezados)

    filas = []
    for fila in datos[1:]:
        fila = list(fila)
        fila.extend([""] * (len(encabezados) - len(fila)))
        filas.append(fila[:len(encabezados)])
    df = pd.DataFrame(filas, columns=encabezados)

    for columna in ["Cantidad", "Precio Unitario", "Valor Total", "% IVA"]:
        if columna in df.columns:
            df[columna] = df[columna].apply(convertir_numero)
    if "Fecha" in df.columns:
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    if "Codigo Articulo" in df.columns:
        df["Codigo Articulo"] = (df["Codigo Articulo"].astype(str)
                                  .str.replace(".0", "", regex=False).str.strip())
        df["Tipo de Venta"] = df["Codigo Articulo"].apply(clasificar_tipo_venta)
    return df

# -----------------------------------------------------------------------------
# ESTADOS DE SESIÓN (Inicialización segura)
# -----------------------------------------------------------------------------
if "registros_pdf" not in st.session_state:
    st.session_state["registros_pdf"] = None
if "mensaje_carga" not in st.session_state:
    st.session_state["mensaje_carga"] = ""
if "uploader_version" not in st.session_state:
    st.session_state["uploader_version"] = 0

# -----------------------------------------------------------------------------
# ENCABEZADO PRINCIPAL CON LOGOTIPO
# -----------------------------------------------------------------------------
col_izq, col_der = st.columns([8, 1])
with col_izq:
    st.markdown("""
        <div class="main-title">Magic Print Analytics</div>
        <div class="main-subtitle">Seguimiento de ventas, facturación y desempeño comercial</div>
    """, unsafe_allow_html=True)
with col_der:
    st.markdown(f'<img src="data:image/jpeg;base64,{LOGO_B64}" style="width:64px;height:64px;border-radius:12px;object-fit:cover">', unsafe_allow_html=True)

if st.session_state.get("mensaje_carga"):
    st.success(st.session_state.pop("mensaje_carga"))

hoja = conectar_hoja()
if hoja is None:
    st.stop()

# -----------------------------------------------------------------------------
# CARGA DE PDF EN LA BARRA LATERAL Y FILTROS DE ANÁLISIS
# -----------------------------------------------------------------------------
df_full = cargar_datos()

if not df_full.empty and "Fecha" in df_full.columns and df_full["Fecha"].notna().any():
    indice_ultima_factura = df_full["Fecha"].idxmax()
    fecha_ultima_factura = df_full.loc[indice_ultima_factura, "Fecha"].strftime("%d/%m/%Y")
    numero_ultima_factura = str(df_full.loc[indice_ultima_factura, "Factura #"]) if "Factura #" in df_full.columns else "No disponible"
    total_facturas_registradas = df_full["Factura #"].nunique() if "Factura #" in df_full.columns else 0
    estado_carga = f"Última factura registrada: {numero_ultima_factura} · {fecha_ultima_factura} · {fnum(total_facturas_registradas)} facturas en total"
else:
    estado_carga = "Aún no hay facturas registradas en la base de datos"

with st.sidebar:
    st.subheader("📤 Cargar facturas / TR")
    st.markdown(f'<div class="data-status">{estado_carga}</div>', unsafe_allow_html=True)
    archivo_pdf = st.file_uploader(
        "Selecciona un archivo PDF",
        type=["pdf"],
        key=f"archivo_pdf_{st.session_state['uploader_version']}"
    )
    if archivo_pdf:
        st.success(f"Archivo seleccionado: {archivo_pdf.name}")
        if st.button("Procesar PDF", type="primary", use_container_width=True):
            try:
                with st.spinner("Procesando el documento..."):
                    st.session_state["registros_pdf"] = extraer_datos_pdf(archivo_pdf)
                st.rerun()
            except Exception as error:
                st.error(f"El documento no es válido o está vacío: {error}")

with st.container(border=True):
    st.subheader("🔍 Filtros de análisis")
    ciudades_opc = sorted(df_full["Ciudad"].dropna().astype(str).unique()) if "Ciudad" in df_full.columns else []
    vendedores_opc = sorted(df_full["Vendedor"].dropna().astype(str).unique()) if "Vendedor" in df_full.columns else []
    clientes_opc = sorted(df_full["Cliente"].dropna().astype(str).unique()) if "Cliente" in df_full.columns else []
    tipos_venta_opc = sorted(df_full["Tipo de Venta"].dropna().astype(str).unique()) if "Tipo de Venta" in df_full.columns else []
    sel_ciudades, sel_vendedores, sel_clientes, sel_tipo_venta = [], [], [], []

    opciones_filtro = [("Ciudad", ciudades_opc), ("Vendedor", vendedores_opc), ("Cliente", clientes_opc), ("Tipo de venta", tipos_venta_opc)]
    filtros_visibles = [(nombre, opciones) for nombre, opciones in opciones_filtro if opciones]
    fila_1 = st.columns(3)
    fila_2 = st.columns([2, 1])
    destinos = {"Ciudad": fila_1[1], "Vendedor": fila_1[2], "Cliente": fila_2[0], "Tipo de venta": fila_2[1]}
    if not df_full.empty and "Fecha" in df_full.columns and not df_full["Fecha"].dropna().empty:
        f_min = df_full["Fecha"].min().date()
        f_max = df_full["Fecha"].max().date()
        with fila_1[0]:
            rango_fechas = st.date_input("Rango de fechas", (f_min, f_max), min_value=f_min, max_value=f_max)
    else:
        rango_fechas = None

    for nombre, opciones in filtros_visibles:
        with destinos[nombre]:
            seleccion = st.multiselect(nombre, opciones)
            if nombre == "Ciudad":
                sel_ciudades = seleccion
            elif nombre == "Vendedor":
                sel_vendedores = seleccion
            elif nombre == "Cliente":
                sel_clientes = seleccion
            elif nombre == "Tipo de venta":
                sel_tipo_venta = seleccion

# Aplicar filtros al DataFrame
