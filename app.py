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
            st.error("❌ No se encontraron los Secrets.")
            return None
        client = gspread.authorize(creds)
        return client.open(nombre_archivo).get_worksheet(0)
    except Exception as e:
        st.error(f"Error conexión: {e}")
        return None

# --- INTERFAZ ---
st.title("📊 Plataforma de Datos UDGPlus")
st.subheader("Unidad de Educación Continua Virtual")
st.markdown("---")

tab1, tab2 = st.tabs(["🔗 Google Sheets Bridge", "💻 Unión Local"])

with tab1:
    st.header("Añadir Columnas al Final de Drive")
    st.info(f"Base: **{SHEET_BASE_NOMBRE}**")
    
    archivo_nuevo_g = st.file_uploader("Subir archivo con datos nuevos:", type=['xlsx', 'csv'], key="up_g_v6")
    
    if archivo_nuevo_g:
        with st.spinner("Conectando con Drive..."):
            sheet = conectar_google(SHEET_BASE_NOMBRE)
            if sheet:
                # 1. Obtener dimensiones actuales
                encabezados_actuales = sheet.row_values(1)
                num_cols_actuales = len(encabezados_actuales)
                total_cols_grid = sheet.col_count # Columnas físicas que tiene la hoja
                
                datos_drive = sheet.get_all_records()
                df_drive = pd.DataFrame(datos_drive)
                
                df_subido = pd.read_csv(archivo_nuevo_g) if archivo_nuevo_g.name.endswith('.csv') else pd.read_excel(archivo_nuevo_g)
                
                if not df_drive.empty:
                    c1, c2 = st.columns(2)
                    id_d = c1.selectbox("ID en Drive (Base):", df_drive.columns, key="id_d_v6")
                    id_s = c2.selectbox("ID en archivo nuevo:", df_subido.columns, key="id_s_v6")
                    
                    cols_a_subir = st.multiselect("Columnas nuevas para añadir:", 
                                                 [c for c in df_subido.columns if c != id_s], key="cols_g_v6")
                    
                    if st.button("🚀 Añadir al Final de Drive", key="btn_g_v6"):
                        if not cols_a_subir:
                            st.warning("Selecciona columnas.")
                        else:
                            with st.spinner("Procesando y expandiendo hoja..."):
                                # 2. Cruce de datos
                                df_res = pd.merge(df_drive[[id_d]], df_subido[[id_s] + cols_a_subir], 
                                                 left_on=id_d, right_on=id_s, how='left')
                                df_final_nuevas = df_res[cols_a_subir].fillna("")
                                cuerpo_datos = [cols_a_subir] + df_final_nuevas.values.tolist()
                                
                                # 3. Verificar si hay espacio suficiente en el "Grid"
                                columnas_necesarias = num_cols_actuales + len(cols_a_subir)
                                if columnas_necesarias > total_cols_grid:
                                    columnas_a_crear = columnas_necesarias - total_cols_grid
                                    sheet.add_cols(columnas_a_crear)
                                
                                # 4. Calcular rango
                                col_inicio = num_cols_actuales + 1
                                col_fin = columnas_necesarias
                                
                                letra_inicio = gspread.utils.rowcol_to_a1(1, col_inicio).replace('1', '')
                                letra_fin = gspread.utils.rowcol_to_a1(1, col_fin).replace('1', '')
                                
                                # Rango desde fila 1 hasta el final de las filas de datos
                                rango_destino = f"{letra_inicio}1:{letra_fin}{len(cuerpo_datos)}"
                                
                                # 5. Actualizar (USER_ENTERED para respetar formatos)
                                try:
                                    sheet.update(range_name=rango_destino, values=cuerpo_datos, value_input_option='USER_ENTERED')
                                    st.success(f"✅ ¡Hecho! Se añadieron {len(cols_a_subir)} columnas al final.")
                                    st.balloons()
                                except Exception as e:
                                    st.error(f"Error al subir: {e}")
                else:
                    st.error("No hay datos en la base de Drive.")

with tab2:
    st.header("Cruce Local")
    f_base_l = st.file_uploader("Archivo Base:", type=['xlsx', 'csv'], key="up_l_b_v6")
    f_nuevo_l = st.file_uploader("Datos Nuevos:", type=['xlsx', 'csv'], key="up_l_n_v6")
    if f_base_l and f_nuevo_l:
        df_l_b = pd.read_csv(f_base_l) if f_base_l.name.endswith('.csv') else pd.read_excel(f_base_l)
        df_l_n = pd.read_csv(f_nuevo_l) if f_nuevo_l.name.endswith('.csv') else pd.read_excel(f_nuevo_l)
        c1, c2 = st.columns(2)
        id_lb = c1.selectbox("ID Base:", df_l_b.columns, key="id_lb_v6")
        id_ln = c2.selectbox("ID Nuevo:", df_l_n.columns, key="id_ln_v6")
        cols_l = st.multiselect("Columnas:", [c for c in df_l_n.columns if c != id_ln], key="cols_l_v6")
        if st.button("🚀 Procesar Local", key="btn_l_v6"):
            res_l = pd.merge(df_l_b, df_l_n[[id_ln] + cols_l], left_on=id_lb, right_on=id_ln, how='left')
            if id_lb != id_ln: res_l = res_l.drop(columns=[id_ln])
            st.dataframe(res_l.head(10))
            out = io.BytesIO()
            with pd.ExcelWriter(out) as w: res_l.to_excel(w, index=False)
            st.download_button("📥 Descargar", out.getvalue(), "resultado.xlsx")

st.sidebar.markdown("---")
st.sidebar.caption("UDGPlus - 2026")
