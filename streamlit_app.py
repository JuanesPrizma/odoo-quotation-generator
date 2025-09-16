import streamlit as st
from docxtpl import DocxTemplate
import io
import openai
import json
import os
import re

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

            messages = []

            # Prompt principal
            prompt = f"""
            Eres un asistente que genera cotizaciones técnicas en JSON.

            Descripción manual del ticket:
            '{descripcion}'

            Los autores de la cotización son: {autores_input}

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

            messages.append({"role": "user", "content": prompt})

            # Subir archivo si lo hay
            if uploaded_file:
                with open(uploaded_file.name, "wb") as f:
                    f.write(uploaded_file.read())

                uploaded = openai.files.create(
                    file=open(uploaded_file.name, "rb"), purpose="assistants"
                )

                # Adjuntar archivo al mensaje
                messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": "Aquí está el documento adjunto:",
                            },
                            {"type": "input_file", "file_id": uploaded.id},
                        ],
                    }
                )

            # Llamada a la API
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
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

            # Renderizar docx
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
