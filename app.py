import streamlit as st
import pandas as pd
from pypdf import PdfWriter
from PIL import Image
import io
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Unión de Datos y Documentos - UdeG", 
    page_icon="📊",
    layout="wide"
)

# --- ESTILOS E IMAGEN INSTITUCIONAL ---
def mostrar_encabezado():
    col1, col2 = st.columns([1, 5])
    
    # Búsqueda flexible del logo
    posibles_rutas = ["assets/logo_u.png", "logo_u.png", "logo_u.png.png"]
    logo_final = None
    
    for ruta in posibles_rutas:
        if os.path.exists(ruta):
            logo_final = ruta
            break

    with col1:
        if logo_final:
            st.image(logo_final, width=150)
        else:
            st.warning("Logo no encontrado")
            
    with col2:
        st.title("Plataforma de Procesamiento de Datos y Documentos")
        st.subheader("Unidad de Educación Continua Virtual y Campus Digital Comunitario UDGPlus")

    # Aviso de Privacidad Integrado
    with st.expander("⚖️ Aviso de Privacidad (UdeG)"):
        st.caption("""
        La Universidad de Guadalajara (en adelante UdeG), con domicilio en Avenida Juárez 976, colonia Centro, 
        código postal 44100, en Guadalajara, Jalisco, hace de su conocimiento que se considerará como información 
        confidencial aquella que se encuentre contemplada en la normativa vigente. Los datos proporcionados serán única 
        y exclusivamente utilizados para los fines que fueron proporcionados.
        
        Esta aplicación procesa los archivos temporalmente en memoria RAM y NO almacena copias en el servidor.
        Consulte el aviso integral en: http://www.transparencia.udg.mx/aviso-confidencialidad-integral
        """)

# --- LÓGICA: UNIÓN TABULAR ---
def seccion_tabular():
    st.header("📑 Unión de Archivos Tabulados")
    st.write("Carga dos archivos para realizar una unión basada en un campo común (similar a Join en QGIS).")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        file_1 = st.file_uploader("1. Archivo Base (Capa destino)", type=['csv', 'xlsx'], help="Este es el archivo principal al que quieres agregarle datos.")
    with col_b:
        file_2 = st.file_uploader("2. Archivo a Unir (Capa origen)", type=['csv', 'xlsx'], help="De este archivo se extraerá la información nueva.")

    if file_1 and file_2:
        df1 = pd.read_csv(file_1) if file_1.name.endswith('.csv') else pd.read_excel(file_1)
        df2 = pd.read_csv(file_2) if file_2.name.endswith('.csv') else pd.read_excel(file_2)

        st.info(f"Registros detectados: Base ({len(df1)}) | A unir ({len(df2)})")
        
        c1, c2 = st.columns(2)
        key_1 = c1.selectbox("¿Cuál es la columna común en la Base?", df1.columns)
        key_2 = c2.selectbox("¿Cuál es la columna común en el segundo archivo?", df2.columns)
        
        available_cols = [c for c in df2.columns if c != key_2]
        cols_to_add = st.multiselect("¿Qué columnas nuevas quieres añadir a tu base?", available_cols)
        
        if st.button("🚀 Ejecutar Unión de Datos"):
            if not cols_to_add:
                st.warning("Por favor selecciona al menos una columna para añadir.")
            else:
                df2_subset = df2[[key_2] + cols_to_add]
                resultado = pd.merge(df1, df2_subset, left_on=key_1, right_on=key_2, how='left')
                
                st.success("¡Unión completada con éxito!")
                st.subheader("Previsualización del resultado:")
                st.dataframe(resultado.head(10))
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    resultado.to_excel(writer, index=False)
                
                st.download_button(
                    label="📥 Descargar Resultado en Excel",
                    data=output.getvalue(),
                    file_name="union_resultado_udg.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

# --- LÓGICA: UNIÓN DOCUMENTOS ---
def seccion_documentos():
    st.header("📂 Combinar PDF e Imágenes")
    st.write("Selecciona varios archivos para unirlos en un solo PDF final.")
    
    uploaded_files = st.file_uploader(
        "Carga tus archivos aquí (PDF, JPG, PNG)", 
        type=['pdf', 'jpg', 'png', 'jpeg'], 
        accept_multiple_files=True,
        help="Los archivos se unirán en el orden en que aparecen en esta lista."
    )
    
    if uploaded_files:
        nombre_final = st.text_input("Nombre para tu nuevo archivo:", "documento_unificado_udg.pdf")
        
        if st.button("🪄 Generar PDF Unificado"):
            merger = PdfWriter()
            
            with st.spinner("Creando tu documento..."):
                for uploaded_file in uploaded_files:
                    if uploaded_file.type == "application/pdf":
                        merger.append(uploaded_file)
                    else:
                        image = Image.open(uploaded_file).convert("RGB")
                        img_pdf = io.BytesIO()
                        image.save(img_pdf, format="PDF")
                        merger.append(img_pdf)
                
                output_pdf = io.BytesIO()
                merger.write(output_pdf)
                
                st.success("¡Documento generado!")
                st.download_button(
                    label="📥 Descargar PDF Final",
                    data=output_pdf.getvalue(),
                    file_name=nombre_final,
                    mime="application/pdf"
                )

# --- FUNCIÓN PRINCIPAL ---
def main():
    mostrar_encabezado()
    
    # Creación de pestañas para una navegación más amigable
    tab_inicio, tab_tablas, tab_docs = st.tabs([
        "🏠 Inicio", 
        "📑 Unión de Tablas", 
        "📂 Combinar Archivos"
    ])

    with tab_inicio:
        st.markdown("""
        ### 🎓 Bienvenido a la Plataforma de Procesamiento UDGPlus
        Esta herramienta ha sido diseñada para facilitar tareas administrativas comunes de forma segura y eficiente.
        
        #### ¿Qué puedes hacer aquí?
        1. **Unir Tablas:** Si tienes dos archivos de Excel y necesitas cruzar información (como poner nombres a una lista de códigos).
        2. **Combinar Archivos:** Si tienes varios PDFs o fotos de documentos y necesitas enviarlos como un solo archivo.
        
        ---
        **Instrucciones rápidas:**
        * Selecciona una de las pestañas de arriba para comenzar.
        * Tus archivos **nunca se guardan en el servidor**, la privacidad está garantizada.
        * Al terminar, simplemente cierra la pestaña del navegador.
        """)
        
    with tab_tablas:
        seccion_tabular()

    with tab_docs:
        seccion_documentos()

    # Footer en la barra lateral
    st.sidebar.markdown("---")
    st.sidebar.caption("Herramienta institucional © 2024 UdeG.")
    st.sidebar.info("Para reportar fallas, contacta al administrador del sistema.")

if __name__ == "__main__":
    main()
