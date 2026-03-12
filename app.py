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
# Debe ser SIEMPRE la primera instrucción de Streamlit
if 'config_ejecutada' not in st.session_state:
    st.set_page_config(
        page_title="Unión de Datos - UdeG", 
        page_icon="📊",
        layout="wide"
    )
    st.session_state.config_ejecutada = True

# --- VARIABLES GLOBALES ---
SHEET_BASE_NOMBRE = "Acredita-Bach-base"

# --- FUNCIONES DE SOPORTE ---
def conectar_google_sheets(nombre_archivo):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        if "google_creds" in st.secrets:
            creds_dict = dict(st.secrets["google_creds"])
            if "private_key" in creds_dict:
                creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        elif os.path.exists('credentials.json'):
            creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        else:
            st.error("❌ No se encontraron credenciales.")
            return None
            
        client = gspread.authorize(creds)
        try:
            return client.open(nombre_archivo).get_worksheet(0)
        except Exception as e:
            if "200" in str(e):
                return client.open(nombre_archivo).get_worksheet(0)
            st.error(f"❌ Error al abrir archivo: {e}")
            return None
    except Exception as e:
        st.error(f"❌ Error crítico: {e}")
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
    logo_final = "logo_u.png" if os.path.exists("logo_u.png") else None
    with col1:
        if logo_final: st.image(logo_final, width=150)
    with col2:
        st.title("Plataforma de Procesamiento de Datos UDGPlus")
        st.subheader("Unidad de Educación Continua Virtual")

# --- SECCIONES ---
def seccion_tabular():
    st.header("📑 Unión de Archivos Tabulados")
    # Añadimos un 'key' único para evitar el error de DuplicateElementId
    modo = st.radio("Selecciona el modo de trabajo:", 
                    ["Local (Manual)", "Google Sheets Bridge (Auto)"], 
                    horizontal=True,
                    key="selector_modo_principal")

    if modo == "Local (Manual)":
        c1, c2 = st.columns(2)
        f1 = c1.file_uploader("Archivo Base", type=['csv', 'xlsx'], key="file_base_local")
        f2 = c2.file_uploader("Datos a añadir", type=['csv', 'xlsx'], key="file_nuevo_local")
        if f1 and f2:
            df1 = pd.read_csv(f1) if f1.name.endswith('.csv') else pd.read_excel(f1)
            df2 = pd.read_csv(f2) if f2.name.endswith('.csv') else pd.read_excel(f2)
            procesar_union(df1, df2, "local")
    else:
        st.info(f"🔗 Base vinculada: **{SHEET_BASE_NOMBRE}**")
        f_origen = st.file_uploader("Subir datos nuevos:", type=['csv', 'xlsx'], key="file_google_upload")
        if f_origen:
            with st.spinner("Conectando..."):
                sheet = conectar_google_sheets(SHEET_BASE_NOMBRE)
                if sheet:
                    data = sheet.get_all_records()
                    if data:
                        df_base = pd.DataFrame(data)
                        df_nuevo = pd.read_csv(f_origen) if f_origen.name.endswith('.csv') else pd.read_excel(f_origen)
                        procesar_union(df_base, df_nuevo, "google", sheet)
                    else:
                        st.warning("La hoja en Drive está vacía.")

def procesar_union(df1, df2, destino, sheet_obj=None):
    st.write("---")
    c_keys = st.columns(2)
    k1 = c_keys[0].selectbox("ID Base:", df1.columns, key=f"k1_{destino}")
    k2 = c_keys[1].selectbox("ID Nuevo:", df2.columns, key=f"k2_{destino}")
    cols = st.multiselect("Columnas a añadir:", [c for c in df2.columns if c != k2], key=f"cols_{destino}")
    
    if st.button("🚀 Procesar Cruce", key=f"btn_{destino}"):
        if not cols:
            st.warning("Elige columnas.")
        else:
            res = pd.merge(df1, df2[[k2] + cols], left_on=k1, right_on=k2, how='left')
            if k1 != k2 and k2 in res.columns: res = res.drop(columns=[k2])
            st.dataframe(res.head(10))

            if destino == "google":
                with st.spinner("Guardando..."):
                    ok, msg = crear_respaldo(sheet_obj)
                    if ok:
                        res = res.astype(str).replace(['nan', 'NaN', 'None'], '')
                        sheet_obj.clear()
                        sheet_obj.update('A1', [res.columns.values.tolist()] + res.values.tolist())
                        st.success(f"✅ ¡Hecho! Respaldo: {msg}")
                        st.balloons()
            else:
                out = io.BytesIO()
                with pd.ExcelWriter(out, engine='openpyxl') as w: res.to_excel(w, index=False)
                st.download_button("📥 Descargar", out.getvalue(), "resultado.xlsx", key="down_btn")

def seccion_documentos():
    st.header("📂 Combinar PDF e Imágenes")
    files = st.file_uploader("Archivos", type=['pdf', 'jpg', 'png'], accept_multiple_files=True, key="doc_uploader")
    if files and st.button("🪄 Unir PDF", key="btn_merge_docs"):
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
        st.download_button("📥 Descargar PDF", out.getvalue(), "unificado.pdf", key="down_docs")

# --- MAIN ---
def main():
    mostrar_encabezado()
    tab_inicio, tab_tablas, tab_docs = st.tabs(["🏠 Inicio", "📑 Tablas", "📂 Documentos"])
    
    with tab_inicio:
        st.write("Bienvenido. Selecciona una pestaña para comenzar.")
    with tab_tablas: 
        seccion_tabular()
    with tab_docs: 
        seccion_documentos()

if __name__ == "__main__":
    main()
    main()
if __name__ == "__main__":
    main()
