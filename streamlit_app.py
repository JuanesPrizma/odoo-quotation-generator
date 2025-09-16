import streamlit as st
from docxtpl import DocxTemplate
import io
import openai
import json
import os
import re
import tempfile

# Configurar tu API Key en variable de entorno
openai.api_key = os.getenv("OPENAI_API_KEY")

st.title("Generador de Cotizaciones con IA")

autores_input = st.text_input(
    "👥 Ingresa los nombres de los autores (separados por coma):"
)
descripcion = st.text_area("✍️ Ingresa la descripción del ticket:")

# Uploader: solo PDF
uploaded_file = st.file_uploader(
    "📄 Sube un documento en formato PDF (único soportado por la API de OpenAI)",
    type=["pdf"],
)

if st.button("Generar Cotización"):
    if not descripcion.strip() and not uploaded_file:
        st.warning(
            "Por favor escribe una descripción o sube un documento PDF antes de generar la cotización."
        )
    else:
        with st.spinner("Generando la cotización con IA..."):

            # Subir PDF a OpenAI si existe
            file_id = None
            if uploaded_file:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name
                up = openai.files.create(file=open(tmp_path, "rb"), purpose="user_data")
                file_id = up.id
                os.remove(tmp_path)

            # Construir prompt
            prompt = f"""
            Eres un asistente que genera cotizaciones técnicas en JSON.
            A partir de la siguiente descripción del ticket:

            '{descripcion}'

            Los autores de la cotización son: {autores_input}
            {( "Además, utiliza el documento adjunto en PDF como contexto adicional." if file_id else "" )}

            Devuelve **únicamente** un JSON válido con esta estructura exacta:
            {{
              "nombre_requerimiento": "texto",
              "numero_oferta": "texto",
              "fecha_cotizacion": "texto",
              "autores": ["autor1", "autor2"],
              "objetivo": "texto",
              "antecedentes": "texto",
              "alcance": ["item1", "item2", "item3"],
              "tiempo_inversion": {{
                "detalle": [
                  {{ "actividad": "texto", "horas": int, "tarifa": int, "subtotal": int }}
                ],
                "total_horas": int,
                "total_cop": int
              }},
              "tiempo_desarrollo": "texto",
              "exclusiones": ["item1", "item2"],
              "condiciones_comerciales": {{
                "pago": "texto",
                "garantia": "texto",
                "metodologia": "texto"
              }}
            }}
            """

            # Llamada al modelo
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )

            # Extraer JSON
            json_text = response.choices[0].message.content.strip()

            if json_text.startswith("```"):
                json_text = re.sub(r"^```[a-zA-Z]*\n", "", json_text)
                json_text = re.sub(r"\n```$", "", json_text)

            try:
                data = json.loads(json_text)
            except json.JSONDecodeError as e:
                st.error(f"❌ JSON inválido: {e}")
                st.text(json_text)
                st.stop()

            # Sobrescribir autores con los ingresados por el usuario
            autores = [a.strip() for a in autores_input.split(",") if a.strip()]
            data["autores"] = autores

            # Convertir listas a bullet points
            def list_to_bullets(items):
                if not isinstance(items, list):
                    return items
                return "\n".join([f"• {item}" for item in items])

            for key in ["alcance", "exclusiones"]:
                if key in data:
                    data[key] = list_to_bullets(data[key])

            # Generar Word
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
