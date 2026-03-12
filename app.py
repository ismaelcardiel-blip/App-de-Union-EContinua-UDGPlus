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
        
        # 1. Intentar conectar usando los Secrets de Streamlit
        if "google_creds" in st.secrets:
            creds_dict = dict(st.secrets["google_creds"])
            # Limpieza de la llave privada (algunas veces los saltos de línea \n fallan en Secrets)
            if "private_key" in creds_dict:
                creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        elif os.path.exists('credentials.json'):
            creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        else:
            st.error("❌ No se encontraron credenciales en 'Secrets' ni archivo local.")
            return None
            
        client = gspread.authorize(creds)
        
        # 2. Intentar abrir el archivo con manejo de errores específico
        try:
            spreadsheet = client.open(nombre_archivo)
            return spreadsheet.get_worksheet(0)
        except gspread.exceptions.SpreadsheetNotFound:
            st.error(f"❌ Error: No se encontró el archivo '{nombre_archivo}' en Drive.")
            st.info(f"Asegúrate de haber compartido el archivo con: **{creds_dict.get('client_email', 'tu correo de cuenta de servicio')}** como Editor.")
            return None
        except Exception as e:
            # Si el error contiene "200", intentamos un bypass rápido
            if "200" in str(e) or "Response [200]" in str(e):
                return client.open(nombre_archivo).get_worksheet(0)
            st.error(f"❌ Error de permisos o lectura: {e}")
            return None
            
    except Exception as e:
        st.error(f"❌ Error crítico de conexión: {e}")
        return None

def crear_respaldo(sheet_obj):
    try:
        client = sheet_obj.client
        fecha = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
        nombre_copia = f"{SHEET_BASE_NOMBRE}_BACKUP_{fecha}"
        # Copia el archivo usando la API de Drive
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
        f1 = c1.file_uploader("Subir Base Destino", type=['csv', 'xlsx'])
        f2 = c2.file_uploader("Subir Datos a Añadir", type=['csv', 'xlsx'])
        if f1 and f2:
            df1 = pd.read_csv(f1) if f1.name.endswith('.csv') else pd.read_excel(f1)
            df2 = pd.read_csv(f2) if f2.name.endswith('.csv') else pd.read_excel(f2)
            procesar_union(df1, df2, "local")
    else:
        st.info(f"🔗 Base vinculada: **{SHEET_BASE_NOMBRE}**")
        f_origen = st.file_uploader("Subir archivo con datos nuevos para añadir:", type=['csv', 'xlsx'])
        if f_origen:
            with st.spinner("Accediendo a la base de datos en la nube..."):
                sheet = conectar_google_sheets(SHEET_BASE_NOMBRE)
                if sheet:
                    # Extraer datos y limpiar encabezados
                    data = sheet.get_all_records()
                    if not data:
                        st.warning("⚠️ La base de datos en Drive parece no tener datos o encabezados.")
                        return
                    df_base = pd.DataFrame(data)
                    df_nuevo = pd.read_csv(f_origen) if f_origen.name.endswith('.csv') else pd.read_excel(f_origen)
                    procesar_union(df_base, df_nuevo, "google", sheet)

def procesar_union(df1, df2, destino, sheet_obj=None):
    st.write("---")
    c_keys = st.columns(2)
    k1 = c_keys[0].selectbox("Columna Identificadora en Base:", df1.columns)
    k2 = c_keys[1].selectbox("Columna Identificadora en Datos Nuevos:", df2.columns)
    
    cols = st.multiselect("Columnas a añadir del archivo nuevo:", [c for c in df2.columns if c != k2])
    
    if st.button("🚀 Ejecutar Procesamiento"):
        if not cols:
            st.warning("Selecciona al menos una columna para añadir.")
        else:
            # Merge tipo Left Join
            res = pd.merge(df1, df2[[k2] + cols], left_on=k1, right_on=k2, how='left')
            if k1 != k2 and k2 in res.columns:
                res = res.drop(columns=[k2])
            
            st.success("¡Cruce finalizado!")
            st.dataframe(res.head(10))

            if destino == "google":
                with st.spinner("Creando respaldo de seguridad y actualizando Drive..."):
                    ok, msg = crear_respaldo(sheet_obj)
                    if ok:
                        # Convertir todo a string y quitar nulos para compatibilidad total
                        res = res.astype(str).replace(['nan', 'NaN', 'None', '<NA>'], '')
                        datos_finales = [res.columns.values.tolist()] + res.values.tolist()
                        
                        sheet_obj.clear()
                        sheet_obj.update('A1', datos_finales)
                        
                        st.balloons()
                        st.success(f"✅ Base actualizada con éxito. Respaldo creado: {msg}")
                    else:
                        st.error(f"❌ Error al crear respaldo: {msg}. No se modificó la base por precaución.")
            else:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as w:
                    res.to_excel(w, index=False)
                st.download_button("📥 Descargar Excel", output.getvalue(), "resultado_union.xlsx")

def seccion_documentos():
    st.header("📂 Combinar PDF e Imágenes")
    files = st.file_uploader("Cargar archivos", type=['pdf', 'jpg', 'png', 'jpeg'], accept_multiple_files=True)
    if files and st.button("🪄 Unir en un solo PDF"):
        merger = PdfWriter()
        for f in files:
            if f.type == "application/pdf":
                merger.append(f)
            else:
                img = Image.open(f).convert("RGB")
                img_pdf = io.BytesIO()
                img.save(img_pdf, format="PDF")
                merger.append(img_pdf)
        out = io.BytesIO()
        merger.write(out)
        st.download_button("📥 Descargar PDF", out.getvalue(), "documento_unificado.pdf")

def main():
    mostrar_encabezado()
    tab_inicio, tab_tablas, tab_docs = st.tabs(["🏠 Inicio", "📑 Tablas", "📂 Documentos"])
    with tab_tablas: seccion_tabular()
    with tab_docs: seccion_documentos()
    with tab_inicio:
        st.info("Utiliza la pestaña 'Tablas' para conectar con Google Drive y cruzar datos.")

if __name__ == "__main__":
    main()
if __name__ == "__main__":
    main()
