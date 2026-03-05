`![Logo UdeG](logo_u.png)`
Markdown
# 📊 Herramienta de Unión de Datos y Documentos (UDGPlus Educación Continua)

Esta aplicación web ha sido diseñada para facilitar el procesamiento de información tabular y la gestión de documentos digitales. Inspirada en la lógica de **Join Attributes** de sistemas de información geográfica como **QGIS**, permite a investigadores, académicos y profesionales realizar cruces de bases de datos y combinar archivos PDF/imágenes sin necesidad de software especializado.

## 🚀 Funcionalidades Principales

### 1. Unión Tabular (Join)
* **Lógica SIG:** Realiza uniones (Left Join) entre archivos Excel (.xlsx) y CSV.
* **Flexibilidad:** Permite seleccionar columnas llave personalizadas y elegir qué atributos añadir al archivo base.
* **Previsualización:** Muestra los resultados en tiempo real antes de la descarga.

### 2. Unión de Documentos
* **Multiformato:** Combina archivos PDF e imágenes (JPG, PNG) en un único documento.
* **Conversión Automática:** Transforma imágenes a formato PDF de forma transparente para el usuario.
* **Orden Dinámico:** Los documentos se procesan en el orden de carga para garantizar la estructura deseada.

---

## 🛠️ Tecnologías Utilizadas

* **Lenguaje:** [Python 3.9+](https://www.python.org/)
* **Framework Web:** [Streamlit](https://streamlit.io/)
* **Procesamiento de Datos:** [Pandas](https://pandas.pydata.org/)
* **Gestión de PDF:** [PyPDF](https://pypdf.readthedocs.io/)
* **Manejo de Imágenes:** [Pillow](https://python-pillow.org/)

---

## 📦 Instalación y Uso Local

Si deseas ejecutar esta aplicación en tu propia máquina, sigue estos pasos:

1. **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/tu-usuario/App-de-Uni-n-Econtinua.git](https://github.com/tu-usuario/App-de-Uni-n-Econtinua.git)
   cd App-de-Uni-n-Econtinua
Instalar dependencias:

Bash
pip install -r requirements.txt
Ejecutar la aplicación:

Bash
streamlit run app.py
🔒 Aviso de Privacidad (UdeG)
La Universidad de Guadalajara (en adelante UdeG), con domicilio en Avenida Juárez 976, colonia Centro, código postal 44100, en Guadalajara, Jalisco, hace de su conocimiento que se considerará como información confidencial aquella que se encuentre contemplada en los artículos 3, fracciones IX y X de la LPDPPSOEJM; 21 de la LTAIPEJM; Lineamientos Cuadragésimo Octavo y Cuadragésimo Noveno de los Lineamientos de Clasificación; Lineamientos Décimo Sexto, Décimo Séptimo y Quincuagésimo Octavo de los Lineamientos de Protección, así como aquellos datos de una persona física identificada o identificable y la inherente a las personas jurídicas, los cuales podrán ser sometidos a tratamiento y serán única y exclusivamente utilizados para los fines que fueron proporcionados, de acuerdo con las finalidades y atribuciones establecidas en los artículos 1, 5 y 6 de la Ley Orgánica, así como 2 y 3 del Estatuto General, ambas legislaciones de la UdeG, de igual forma, para la prestación de los servicios que la misma ofrece conforme a las facultades y prerogativas de la entidad universitaria correspondiente y estarán a resguardo y protección de la misma.

Usted puede consultar nuestro Aviso de Privacidad integral en la siguiente página web: http://www.transparencia.udg.mx/aviso-confidencialidad-integral

Nota técnica sobre privacidad: Esta aplicación procesa todos los archivos en la memoria volátil del servidor (RAM). Los archivos cargados no se almacenan permanentemente en ninguna base de datos o disco duro, siendo eliminados automáticamente al finalizar la sesión del usuario.

Desarrollado para el uso de la Unidad de Educación Continua Virtual y Campus Digital Comunitario de UDGPlus.
