import streamlit as st
from docxtpl import DocxTemplate
import io
import json
import os
import re
import tempfile

# Nuevo cliente OpenAI (SDK v1.x+)
from openai import OpenAI

client = OpenAI()  # Usa OPENAI_API_KEY del entorno

st.title("Generador de Cotizaciones con IA (gpt-5)")

# Entrada de autores
autores_input = st.text_input(
    "👥 Ingresa los nombres de los autores (separados por coma):"
)

# Campo de descripción manual
descripcion = st.text_area("✍️ Ingresa la descripción del ticket:")

# Cargar archivo (opcional)
uploaded_file = st.file_uploader(
    "📄 Sube un documento (.pdf, .docx, .txt)", type=["pdf", "docx", "txt"]
)

# Esquema de salida forzada (Structured Outputs)
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
                        "additionalProperties": False,
                    },
                },
                "total_horas": {"type": "integer"},
                "total_cop": {"type": "integer"},
            },
            "required": ["detalle", "total_horas", "total_cop"],
            "additionalProperties": False,
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
            "additionalProperties": False,
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
    "additionalProperties": False,
}

if st.button("Generar Cotización"):
    if not descripcion.strip() and not uploaded_file:
        st.warning(
            "Por favor escribe una descripción o sube un documento antes de generar la cotización."
        )
    else:
        with st.spinner("Generando la cotización con IA..."):

            # 1. Subir archivo a la API si existe
            file_id = None
            if uploaded_file:
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name
                try:
                    up = client.files.create(
                        file=open(tmp_path, "rb"),
                        purpose="user_data",  # en algunas cuentas puede ser 'assistants'
                    )
                    file_id = up.id
                finally:
                    os.remove(tmp_path)

            # 2. Construir entradas para la API
            instrucciones = f"""
Eres un asistente que genera cotizaciones técnicas en JSON.
Usa la descripción manual y, si hay, el documento adjunto.

Autores proporcionados: {autores_input}

Entrega únicamente un JSON que cumpla exactamente el esquema indicado.
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

            # 3. Llamada a la API Responses con gpt-5
            try:
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
            except Exception as e:
                st.error(f"❌ Error al llamar a la API de OpenAI: {e}")
                st.stop()

            # 4. Extraer el JSON
            json_text = ""
            if hasattr(resp, "output_text") and resp.output_text:
                json_text = resp.output_text.strip()
            elif hasattr(resp, "output") and resp.output:
                try:
                    json_text = resp.output[0].content[0].text.strip()
                except Exception:
                    pass

            if not json_text:
                st.error("No se pudo extraer texto de la respuesta del modelo.")
                st.stop()

            if json_text.startswith("```"):
                json_text = re.sub(r"^```[a-zA-Z]*\n", "", json_text)
                json_text = re.sub(r"\n```$", "", json_text)

            try:
                data = json.loads(json_text)
            except json.JSONDecodeError as e:
                st.error(f"❌ JSON inválido: {e}")
                st.text(json_text)
                st.stop()

            # 5. Sobrescribir autores con lo ingresado por el usuario
            autores = [a.strip() for a in autores_input.split(",") if a.strip()]
            data["autores"] = autores

            # 6. Convertir listas a viñetas
            def list_to_bullets(items):
                if not isinstance(items, list):
                    return items
                return "\n".join([f"• {item}" for item in items])

            for key in ["alcance", "exclusiones"]:
                if key in data:
                    data[key] = list_to_bullets(data[key])

            # 7. Renderizar la plantilla Word
            try:
                doc = DocxTemplate("plantilla_cotizacion.docx")
                doc.render(data)
            except Exception as e:
                st.error(f"❌ Error al renderizar la plantilla Word: {e}")
                st.stop()

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

# Debug opcional: versión del SDK
try:
    import openai as _openai_module

    st.caption(f"SDK OpenAI versión: v{_openai_module.__version__}")
except Exception:
    pass
