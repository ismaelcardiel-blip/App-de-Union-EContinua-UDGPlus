import streamlit as st
import pandas as pd
from pypdf import PdfWriter
from PIL import Image
import io
import os
import gspread
import datetime
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Unión de Datos - UdeG", 
    page_icon="📊",
    layout="wide"
)

# --- VARIABLES GLOBALES ---
SHEET_BASE_NOMBRE = "Acredita-Bach-base"

# --- FUNCIONES DE SOPORTE ---
def conectar_google_sheets(nombre_archivo):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        if not os.path.exists('credentials.json'):
            st.error("❌ Archivo 'credentials.json' no encontrado en el repositorio.")
            return None
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        client = gspread.authorize(creds)
        return client.open(nombre_archivo).get_worksheet(0)
    except Exception as e:
        st.error(f"❌ Error de conexión: {e}")
        return None

def crear_respaldo(sheet_obj):
    try:
        client = sheet_obj.client
        fecha = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
        nombre_copia = f"{SHEET_BASE_NOMBRE}_BACKUP_{fecha}"
        client.copy(sheet_obj.spreadsheet.id, title=nombre_copia)
        return True, nombre_copia
    except Exception as e:
        return False, str(e)

def mostrar_encabezado():
    col1, col2 = st.columns([1, 5])
    posibles_rutas = ["assets/logo_u.png", "logo_u.png"]
    logo_final = next((r for r in posibles_rutas if os.path.exists(r)), None)
    with col1:
        if logo_final: st.image(logo_final, width=150)
    with col2:
        st.title("Plataforma de Procesamiento de Datos UDGPlus")
        st.subheader("Unidad de Educación Continua Virtual")

# --- SECCIONES ---
def seccion_tabular():
    st.header("📑 Unión de Archivos Tabulados")
    modo = st.radio("Modo:", ["Local (Manual)", "Google Sheets Bridge (Auto)"], horizontal=True)

    if modo == "Local (Manual)":
        c1, c2 = st.columns(2)
        f1 = c1.file_uploader("Base", type=['csv', 'xlsx'])
        f2 = c2.file_uploader("Datos a añadir", type=['csv', 'xlsx'])
        if f1 and f2:
            df1 = pd.read_csv(f1) if f1.name.endswith('.csv') else pd.read_excel(f1)
            df2 = pd.read_csv(f2) if f2.name.endswith('.csv') else pd.read_excel(f2)
            procesar_union(df1, df2, "local")
    else:
        st.info(f"🔗 Base vinculada: **{SHEET_BASE_NOMBRE}**")
        f_origen = st.file_uploader("Subir archivo con datos nuevos:", type=['csv', 'xlsx'])
        if f_origen:
            sheet = conectar_google_sheets(SHEET_BASE_NOMBRE)
            if sheet:
                df_base = pd.DataFrame(sheet.get_all_records())
                df_nuevo = pd.read_csv(f_origen) if f_origen.name.endswith('.csv') else pd.read_excel(f_origen)
                procesar_union(df_base, df_nuevo, "google", sheet)

def procesar_union(df1, df2, destino, sheet_obj=None):
    st.write("---")
    col_keys = st.columns(2)
    k1 = col_keys[0].selectbox("Columna ID en Base:", df1.columns)
    k2 = col_keys[1].selectbox("Columna ID en Datos Nuevos:", df2.columns)
    cols = st.multiselect("Columnas a añadir:", [c for c in df2.columns if c != k2])

    if st.button("🚀 Iniciar Proceso"):
        if not cols:
            st.warning("Selecciona columnas.")
        else:
            res = pd.merge(df1, df2[[k2] + cols], left_on=k1, right_on=k2, how='left')
            if k1 != k2 and k2 in res.columns: res = res.drop(columns=[k2])
            
            st.dataframe(res.head(5))
            if destino == "google":
                with st.spinner("Creando respaldo y actualizando..."):
                    ok, msg = crear_respaldo(sheet_obj)
                    if ok:
                        res = res.astype(str).replace('nan', '')
                        sheet_obj.clear()
                        sheet_obj.update('A1', [res.columns.values.tolist()] + res.values.tolist())
                        st.success(f"✅ ¡Hecho! Respaldo creado como: {msg}")
                        st.balloons()
            else:
                output = io.BytesIO()
                with pd.ExcelWriter(output) as w: res.to_excel(w, index=False)
                st.download_button("📥 Descargar", output.getvalue(), "resultado.xlsx")

def seccion_documentos():
    st.header("📂 Combinar PDF")
    files = st.file_uploader("Archivos", type=['pdf', 'jpg', 'png'], accept_multiple_files=True)
    if files and st.button("🪄 Unir"):
        merger = PdfWriter()
        for f in files:
            if f.type == "application/pdf": merger.append(f)
            else:
                img = Image.open(f).convert("RGB")
                img_pdf = io.BytesIO()
                img.save(img_pdf, format="PDF")
                merger.append(img_pdf)
        out = io.BytesIO()
        merger.write(out)
        st.download_button("📥 Descargar PDF", out.getvalue(), "unificado.pdf")

# --- MAIN ---
def main():
    mostrar_encabezado()
    t1, t2, t3 = st.tabs(["🏠 Inicio", "📑 Tablas", "📂 Documentos"])
    with t2: seccion_tabular()
    with t3: seccion_documentos()

if __name__ == "__main__":
    main()
