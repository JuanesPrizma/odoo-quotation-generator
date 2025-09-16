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

autores_input = st.text_input("👥 Ingresa los nombres de los autores (separados por coma):")
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

      response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
      )

      # Extraer el JSON puro del texto
      json_text = response.choices[0].message.content.strip()

      # Opcional: eliminar ```json ... ```
      if json_text.startswith("```"):
        json_text = re.sub(r"^```[a-zA-Z]*\n", "", json_text)  # elimina ```json
        json_text = re.sub(r"\n```$", "", json_text)          # elimina ```

      try:
        data = json.loads(json_text)
      except json.JSONDecodeError as e:
        st.error(f"❌ JSON inválido: {e}")
        st.text(json_text)
        st.stop()

      # Sobrescribir autores con los ingresados por el usuario
      autores = [a.strip() for a in autores_input.split(",") if a.strip()]
      data["autores"] = autores

      # Convertir listas a bullet points para el Word
      def list_to_bullets(items):
        if not isinstance(items, list):
          return items
        return '\n'.join([f"• {item}" for item in items])

      # Procesar los campos tipo lista
      for key in ["alcance", "exclusiones"]:
        if key in data:
          data[key] = list_to_bullets(data[key])
      # Si hay más campos tipo lista, agregar aquí

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
