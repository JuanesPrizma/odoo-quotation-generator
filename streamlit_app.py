import streamlit as st
from docxtpl import DocxTemplate
import io
import openai
import json
import os
import re

# Verificar que la versión del SDK sea suficientemente nueva (solo como debug, opcional)
# st.write("OpenAI SDK version:", openai.__version__)

# Configurar tu API Key en variable de entorno
openai.api_key = os.getenv("OPENAI_API_KEY")

st.title("Generador de Cotizaciones con IA")

# Entrada de autores
autores_input = st.text_input(
    "👥 Ingresa los nombres de los autores (separados por coma):"
)

# Campo de descripción manual
descripcion = st.text_area("✍️ Ingresa la descripción del ticket:")

# Cargar archivo (opcional)
uploaded_file = st.file_uploader(
    "📄 Sube un documento (.docx, .txt, .pdf)", type=["docx", "txt", "pdf"]
)

if st.button("Generar Cotización"):
    if not descripcion.strip() and not uploaded_file:
        st.warning(
            "Por favor escribe una descripción o sube un documento antes de generar la cotización."
        )
    else:
        with st.spinner("Generando la cotización con IA..."):

            # 1. Subir el archivo si existe
            file_id = None
            if uploaded_file:
                # Guardarlo temporalmente
                path_temp = f"/tmp/{uploaded_file.name}"
                with open(path_temp, "wb") as f:
                    f.write(uploaded_file.read())
                # Crear archivo en OpenAI con propósito 'assistants' o 'user_data' (revisa cuál soporte tu cuenta)
                file_resp = openai.files.create(
                    file=open(path_temp, "rb"), purpose="assistants"
                )
                file_id = file_resp.id

            # 2. Construir la entrada para responses.create()
            # Usamos lista de items tipo input para dar flexibilidad
            input_items = []

            # Siempre incluir el texto de descripción
            # Podrías querer usar "instructions" aparte si la API lo requiere
            # Pero aquí lo ponemos como parte de input.
            desc_text = descripcion.strip() if descripcion.strip() else ""
            if desc_text:
                input_items.append(
                    {"role": "user", "content": [{"type": "text", "text": desc_text}]}
                )

            # Si hay archivo, lo agregamos como otro item (o dentro del mismo contenido dependiendo de estructura)
            if file_id:
                input_items.append(
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Aquí está el documento adjunto:"},
                            {"type": "file", "file_id": file_id},
                        ],
                    }
                )

            # 3. Llamada a la API Responses
            response = openai.responses.create(
                model="gpt-4o-mini",  # asegúrate que ese modelo lo soporta en tu cuenta/región
                input=input_items,
                temperature=0.2,
            )

            # 4. Obtener el JSON desde la salida
            # En la Responses API, el texto generado normalmente está en
            # response.output_text o response.output[0].content etc.
            # Verifica cuál estructura devuelve tu versión
            try:
                # algunas versiones lo tienen como output_text
                json_text = response.output_text.strip()
            except AttributeError:
                # otras versiones usan estructura de contenido
                # puede estar en response.output → lista → contenido
                # esto es un ejemplo genérico:
                json_text = response.output[0].content[0].text.strip()

            # Limpiar marques de código si los hay
            if json_text.startswith("```"):
                json_text = re.sub(r"^```[a-zA-Z]*\n", "", json_text)
                json_text = re.sub(r"\n```$", "", json_text)

            # Parsear JSON
            try:
                data = json.loads(json_text)
            except json.JSONDecodeError as e:
                st.error(f"❌ JSON inválido: {e}")
                st.text(json_text)
                st.stop()

            # Sobrescribir autores con los ingresados
            autores = [a.strip() for a in autores_input.split(",") if a.strip()]
            data["autores"] = autores

            # Convertir listas a bullets
            def list_to_bullets(items):
                if not isinstance(items, list):
                    return items
                return "\n".join([f"• {item}" for item in items])

            for key in ["alcance", "exclusiones"]:
                if key in data:
                    data[key] = list_to_bullets(data[key])

            # 5. Renderizar a Word
            doc = DocxTemplate("plantilla_cotizacion.docx")
            doc.render(data)

            output = io.BytesIO()
            doc.save(output)
            output.seek(0)

            st.success("✅ Cotización generada con éxito")
            st.download_button(
                label="📥 Descargar Cotización",
                data=output,
                file_name="cotizacion.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
