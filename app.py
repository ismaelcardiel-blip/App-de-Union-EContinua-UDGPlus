import streamlit as st
import pandas as pd
import io
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 1. CONFIGURACIÓN DE PÁGINA
if 'config_ok' not in st.session_state:
    st.set_page_config(page_title="Unión de Datos - UdeG", page_icon="📊", layout="wide")
    st.session_state.config_ok = True

# --- VARIABLES GLOBALES ---
SHEET_BASE_NOMBRE = "Acredita-Bach-base"

# --- FUNCIONES DE SOPORTE ---
def conectar_google(nombre_archivo):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        if "google_creds" in st.secrets:
            creds_dict = dict(st.secrets["google_creds"])
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        else:
            st.error("❌ No se encontraron los Secrets en Streamlit.")
            return None
        client = gspread.authorize(creds)
        return client.open(nombre_archivo).get_worksheet(0)
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

# --- INTERFAZ ---
st.title("📊 Plataforma de Datos UDGPlus")
st.subheader("Unidad de Educación Continua Virtual")
st.markdown("---")

tab1, tab2 = st.tabs(["🔗 Google Sheets Bridge", "💻 Unión Local"])

with tab1:
    st.header("Sincronización Segura con Drive")
    st.info(f"Base vinculada: **{SHEET_BASE_NOMBRE}**")
    st.caption("Esta versión añade columnas al final sin tocar tus datos previos.")
    
    archivo_nuevo_g = st.file_uploader("Subir archivo con datos nuevos:", type=['xlsx', 'csv'], key="up_g_v7")
    
    if archivo_nuevo_g:
        with st.spinner("Conectando con Google Drive..."):
            sheet = conectar_google(SHEET_BASE_NOMBRE)
            if sheet:
                # 1. Obtener dimensiones y datos
                encabezados_actuales = sheet.row_values(1)
                num_cols_actuales = len(encabezados_actuales)
                total_cols_grid = sheet.col_count
                
                datos_drive = sheet.get_all_records()
                df_drive = pd.DataFrame(datos_drive)
                
                df_subido = pd.read_csv(archivo_nuevo_g) if archivo_nuevo_g.name.endswith('.csv') else pd.read_excel(archivo_nuevo_g)
                
                if not df_drive.empty:
                    c1, c2 = st.columns(2)
                    id_d = c1.selectbox("ID en Drive (Base):", df_drive.columns, key="id_d_v7")
                    id_s = c2.selectbox("ID en archivo nuevo:", df_subido.columns, key="id_s_v7")
                    
                    cols_a_subir = st.multiselect("Columnas nuevas para añadir:", 
                                                 [c for c in df_subido.columns if c != id_s], key="cols_g_v7")
                    
                    if st.button("🚀 Iniciar Carga en Drive", key="btn_g_v7"):
                        if not cols_a_subir:
                            st.warning("Selecciona al menos una columna.")
                        else:
                            with st.spinner("Procesando..."):
                                # 2. Cruce de datos (Left Join)
                                df_res = pd.merge(df_drive[[id_d]], df_subido[[id_s] + cols_a_subir], 
                                                 left_on=id_d, right_on=id_s, how='left')
                                
                                # Preparamos los datos con encabezados
                                df_final_nuevas = df_res[cols_a_subir].fillna("")
                                cuerpo_datos = [cols_a_subir] + df_final_nuevas.values.tolist()
                                
                                # 3. Gestión de espacio (añadir columnas si falta espacio)
                                columnas_totales_necesarias = num_cols_actuales + len(cols_a_subir)
                                if columnas_totales_necesarias > total_cols_grid:
                                    columnas_a_añadir = columnas_totales_necesarias - total_cols_grid
                                    sheet.add_cols(columnas_a_añadir)
                                
                                # 4. Definir Rango
                                col_inicio = num_cols_actuales + 1
                                col_fin = columnas_totales_necesarias
                                
                                letra_inicio = gspread.utils.rowcol_to_a1(1, col_inicio).replace('1', '')
                                letra_fin = gspread.utils.rowcol_to_a1(1, col_fin).replace('1', '')
                                
                                rango_destino = f"{letra_inicio}1:{letra_fin}{len(cuerpo_datos)}"
                                
                                # 5. ACTUALIZACIÓN (Sintaxis universal sin keywords problemáticas)
                                try:
                                    # Pasamos los argumentos por posición para evitar el error de API
                                    sheet.update(rango_destino, cuerpo_datos, value_input_option='USER_ENTERED')
                                    st.success(f"✅ ¡Éxito! Se añadieron {len(cols_a_subir)} columnas nuevas a la derecha.")
                                    st.balloons()
                                except Exception as e:
                                    st.error(f"Error técnico al subir: {e}")
                else:
                    st.error("La base de datos en Drive no tiene registros.")

with tab2:
    st.header("Cruce Local (Excel)")
    f_base_l = st.file_uploader("Archivo Base:", type=['xlsx', 'csv'], key="up_l_b_v7")
    f_nuevo_l = st.file_uploader("Datos Nuevos:", type=['xlsx', 'csv'], key="up_l_n_v7")
    if f_base_l and f_nuevo_l:
        df_l_b = pd.read_csv(f_base_l) if f_base_l.name.endswith('.csv') else pd.read_excel(f_base_l)
        df_l_n = pd.read_csv(f_nuevo_l) if f_nuevo_l.name.endswith('.csv') else pd.read_excel(f_nuevo_l)
        c1, c2 = st.columns(2)
        id_lb = c1.selectbox("ID Base:", df_l_b.columns, key="id_lb_v7")
        id_ln = c2.selectbox("ID Nuevo:", df_l_n.columns, key="id_ln_v7")
        cols_l = st.multiselect("Columnas:", [c for c in df_l_n.columns if c != id_ln], key="cols_l_v7")
        if st.button("🚀 Procesar Localmente", key="btn_l_v7"):
            res_l = pd.merge(df_l_b, df_l_n[[id_ln] + cols_l], left_on=id_lb, right_on=id_ln, how='left')
            if id_lb != id_ln: res_l = res_l.drop(columns=[id_ln])
            st.dataframe(res_l.head(10))
            out = io.BytesIO()
            with pd.ExcelWriter(out) as w: res_l.to_excel(w, index=False)
            st.download_button("📥 Descargar Excel", out.getvalue(), "resultado_final.xlsx")

st.sidebar.markdown("---")
st.sidebar.caption("UDGPlus - Soporte de Datos 2026")
