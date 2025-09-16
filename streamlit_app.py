import streamlit as st
from docxtpl import DocxTemplate
import io
import json
import os
import re
import tempfile
from openai import OpenAI

client = OpenAI()

st.title("Generador de Cotizaciones con IA (GPT-5 + Responses API)")

autores_input = st.text_input(
    "👥 Ingresa los nombres de los autores (separados por coma):"
)
descripcion = st.text_area("✍️ Ingresa la descripción del ticket:")

uploaded_file = st.file_uploader(
    "📄 Sube un documento en formato PDF (único soportado directamente por la API de OpenAI)",
    type=["pdf"],
)

# === JSON Schema esperado ===
COTIZACION_SCHEMA = {
    "type": "object",
    "properties": {
        "nombre_requerimiento": {"type": "string"},
        "numero_oferta": {"type": "string"},
        "fecha_cotizacion": {"type": "string"},
        "autores": {"type": "array", "items": {"type": "string"}},
        "objetivo": {"type": "string"},
        "antecedentes": {"type": "string"},
        "alcance": {"type": "array", "items": {"type": "string"}},
        "tiempo_inversion": {
            "type": "object",
            "properties": {
                "detalle": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "actividad": {"type": "string"},
                            "horas": {"type": "integer"},
                            "tarifa": {"type": "integer"},
                            "subtotal": {"type": "integer"},
                        },
                        "required": ["actividad", "horas", "tarifa", "subtotal"],
                    },
                },
                "total_horas": {"type": "integer"},
                "total_cop": {"type": "integer"},
            },
            "required": ["detalle", "total_horas", "total_cop"],
        },
        "tiempo_desarrollo": {"type": "string"},
        "exclusiones": {"type": "array", "items": {"type": "string"}},
        "condiciones_comerciales": {
            "type": "object",
            "properties": {
                "pago": {"type": "string"},
                "garantia": {"type": "string"},
                "metodologia": {"type": "string"},
            },
            "required": ["pago", "garantia", "metodologia"],
        },
    },
    "required": [
        "nombre_requerimiento",
        "numero_oferta",
        "fecha_cotizacion",
        "autores",
        "objetivo",
        "antecedentes",
        "alcance",
        "tiempo_inversion",
        "tiempo_desarrollo",
        "exclusiones",
        "condiciones_comerciales",
    ],
}

if st.button("Generar Cotización"):
    if not descripcion.strip() and not uploaded_file:
        st.warning(
            "Por favor escribe una descripción o sube un documento PDF antes de generar la cotización."
        )
    else:
        with st.spinner("Generando la cotización con GPT-5..."):

            # Subir PDF a OpenAI si existe
            file_id = None
            if uploaded_file:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name
                up = client.files.create(file=open(tmp_path, "rb"), purpose="user_data")
                file_id = up.id
                os.remove(tmp_path)

            instrucciones = f"""
Eres un asistente experto en elaborar cotizaciones técnicas detalladas y profesionales en formato JSON.

Usa la descripción manual del ticket y, si está presente, el documento PDF adjunto. 
Genera textos largos, elaborados y claros en cada campo.

Autores proporcionados: {autores_input}

⚠️ Importante: si algún campo no aplica o no hay información suficiente,
devuelve un string vacío "" o una lista vacía [].
Nunca devuelvas null.

Entrega únicamente un JSON que cumpla exactamente con el esquema indicado.
"""

            input_items = [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": instrucciones},
                        {
                            "type": "input_text",
                            "text": f"Descripción del ticket: {descripcion.strip()}",
                        },
                    ],
                }
            ]

            if file_id:
                input_items.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": "Documento adjunto para contexto:",
                            },
                            {"type": "input_file", "file_id": file_id},
                        ],
                    }
                )

            # Llamada a GPT-5 con Responses API
            resp = client.responses.create(
                model="gpt-5",
                input=input_items,
                max_output_tokens=2000,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "CotizacionTecnica",
                        "schema": COTIZACION_SCHEMA,
                        "strict": True,
                    }
                },
            )

            # === Extracción robusta del JSON ===
            json_text = None

            if getattr(resp, "output_text", None):
                json_text = resp.output_text.strip()

            if not json_text and getattr(resp, "output", None):
                chunks = []
                for block in resp.output:
                    if hasattr(block, "content"):
                        for c in block.content:
                            if getattr(c, "type", None) == "output_text" and getattr(
                                c, "text", None
                            ):
                                chunks.append(c.text)
                if chunks:
                    json_text = "".join(chunks).strip()

            if not json_text:
                st.error("❌ El modelo no devolvió ningún JSON.")
                st.stop()

            if json_text.startswith("```"):
                json_text = re.sub(r"^```[a-zA-Z]*\n", "", json_text)
                json_text = re.sub(r"\n```$", "", json_text)

            try:
                data = json.loads(json_text)
            except json.JSONDecodeError:
                st.error(
                    "❌ La salida no es JSON válido. Aquí está lo que devolvió el modelo:"
                )
                st.text(json_text)
                st.stop()

            # Normalizar campos para evitar None
            defaults = {"alcance": [], "exclusiones": [], "autores": []}
            for key, default_value in defaults.items():
                if key not in data or data[key] is None:
                    data[key] = default_value

            # Sobrescribir autores con los ingresados manualmente
            autores = [a.strip() for a in autores_input.split(",") if a.strip()]
            data["autores"] = autores

            def list_to_bullets(items):
                if not isinstance(items, list):
                    return items or ""
                return "\n".join([f"• {item}" for item in items])

            for key in ["alcance", "exclusiones"]:
                if key in data:
                    data[key] = list_to_bullets(data[key])

            # Renderizar la plantilla Word
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
