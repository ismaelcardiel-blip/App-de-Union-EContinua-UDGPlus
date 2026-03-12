import streamlit as st
import pandas as pd
from pypdf import PdfWriter
from PIL import Image
import io
import os
import gspread
import datetime
from oauth2client.service_account import ServiceAccountCredentials

# 1. CONFIGURACIÓN ÚNICA (Solo una vez al inicio)
if 'iniciado' not in st.session_state:
    st.session_state.iniciado = True

# --- FUNCIONES ---
def conectar_google(nombre_archivo):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        if "google_creds" in st.secrets:
            creds_dict = dict(st.secrets["google_creds"])
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        elif os.path.exists('credentials.json'):
            creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        else:
            return None
        client = gspread.authorize(creds)
        return client.open(nombre_archivo).get_worksheet(0)
    except Exception as e:
        st.error(f"Error conexión: {e}")
        return None

def respaldar(sheet_obj):
    try:
        fecha = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        nombre = f"Backup_{fecha}_Base"
        sheet_obj.client.copy(sheet_obj.spreadsheet.id, title=nombre)
        return True, nombre
    except Exception as e:
        return False, str(e)

# --- INTERFAZ ---
st.title("📊 UDGPlus - Procesador de Datos")

tab1, tab2 = st.tabs(["📑 Unión de Tablas", "📂 Unir PDFs"])

with tab1:
    st.header("Gestión de Base de Datos")
    # Usamos una key dinámica para que nunca se duplique
    modo = st.radio("Origen de datos:", ["Local", "Google Drive"], key="modo_trabajo_v1")

    if modo == "Local":
        f1 = st.file_uploader("Base Principal", type=['xlsx', 'csv'], key="up_1")
        f2 = st.file_uploader("Datos Nuevos", type=['xlsx', 'csv'], key="up_2")
        
        if f1 and f2:
            df1 = pd.read_csv(f1) if f1.name.endswith('.csv') else pd.read_excel(f1)
            df2 = pd.read_csv(f2) if f2.name.endswith('.csv') else pd.read_excel(f2)
            
            c1, c2 = st.columns(2)
            id1 = c1.selectbox("ID Base", df1.columns, key="id_l1")
            id2 = c2.selectbox("ID Nuevo", df2.columns, key="id_l2")
            cols = st.multiselect("Columnas a añadir", [c for c in df2.columns if c != id2], key="cols_l")
            
            if st.button("Procesar Local", key="btn_l"):
                res = pd.merge(df1, df2[[id2] + cols], left_on=id1, right_on=id2, how='left')
                st.dataframe(res.head())
                out = io.BytesIO()
                with pd.ExcelWriter(out) as w: res.to_excel(w, index=False)
                st.download_button("Descargar", out.getvalue(), "resultado.xlsx")

    else:
        st.info("Conectado a: Acredita-Bach-base")
        f_nuevo = st.file_uploader("Subir Excel con nuevos datos", type=['xlsx', 'csv'], key="up_g")
        
        if f_nuevo:
            sheet = conectar_google("Acredita-Bach-base")
            if sheet:
                df_b = pd.DataFrame(sheet.get_all_records())
                df_n = pd.read_csv(f_nuevo) if f_nuevo.name.endswith('.csv') else pd.read_excel(f_nuevo)
                
                c1, c2 = st.columns(2)
                id1 = c1.selectbox("ID Drive", df_b.columns, key="id_g1")
                id2 = c2.selectbox("ID Subido", df_n.columns, key="id_g2")
                cols = st.multiselect("Columnas extra", [c for c in df_n.columns if c != id2], key="cols_g")
                
                if st.button("Actualizar Drive", key="btn_g"):
                    res = pd.merge(df_b, df_n[[id2] + cols], left_on=id1, right_on=id2, how='left')
                    ok, msg = respaldar(sheet)
                    if ok:
                        res = res.astype(str).replace(['nan', 'NaN'], '')
                        sheet.clear()
                        sheet.update('A1', [res.columns.tolist()] + res.values.tolist())
                        st.success(f"Listo. Respaldo: {msg}")
                    else:
                        st.error(f"Error backup: {msg}")

with tab2:
    st.header("Unificador de Documentos")
    archivos = st.file_uploader("PDFs o Fotos", accept_multiple_files=True, key="up_pdf")
    if archivos and st.button("Combinar", key="btn_pdf"):
        merger = PdfWriter()
        for a in archivos:
            if a.type == "application/pdf": merger.append(a)
            else:
                img = Image.open(a).convert("RGB")
                img_io = io.BytesIO()
                img.save(img_io, format="PDF")
                merger.append(img_io)
        out_p = io.BytesIO()
        merger.write(out_p)
        st.download_button("Descargar PDF", out_p.getvalue(), "unido.pdf")
