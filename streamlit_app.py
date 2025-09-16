import streamlit as st
from docxtpl import DocxTemplate
import io
import openai
import json
import os

# Configurar tu API Key en variable de entorno
openai.api_key = os.getenv("OPENAI_API_KEY")

st.title("Generador de Cotizaciones con IA")

descripcion = st.text_area("✍️ Ingresa la descripción del ticket:")

if st.button("Generar Cotización"):
    if not descripcion.strip():
        st.warning("Por favor escribe una descripción antes de generar la cotización.")
    else:
        with st.spinner("Generando la cotización con IA..."):
            # Prompt para guiar a la IA
            prompt = f"""
            Eres un asistente que genera cotizaciones técnicas en JSON.
            A partir de la siguiente descripción del ticket:

            '{descripcion}'

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

            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )

            # Extraer el JSON
            json_text = response.choices[0].message["content"]
            try:
                data = json.loads(json_text)
            except json.JSONDecodeError:
                st.error("❌ La IA no devolvió un JSON válido. Respuesta cruda:")
                st.text(json_text)
                st.stop()

        # Generar el documento Word con docxtpl
        doc = DocxTemplate("plantilla.docx")
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
