import tempfile, os, json, re
import streamlit as st
from openai import OpenAI, __version__ as openai_version
from schemas.cotizacion_schema import COTIZACION_SCHEMA

client = OpenAI()
MODEL_NAME = "gpt-5"


def upload_pdf(uploaded_file):
    """Sube un PDF a OpenAI y devuelve su file_id"""
    if not uploaded_file:
        return None
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name
    up = client.files.create(file=open(tmp_path, "rb"), purpose="user_data")
    os.remove(tmp_path)
    return up.id


def generate_quotation(descripcion, autores_input, file_id=None):
    """Construye input, llama a GPT-5 y devuelve (respuesta, payload)"""

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
                    {"type": "input_text", "text": "Documento adjunto para contexto:"},
                    {"type": "input_file", "file_id": file_id},
                ],
            }
        )

    payload = {
        "model": MODEL_NAME,
        "input": input_items,
        "max_output_tokens": 2000,
        "text": {
            "format": {
                "type": "json_schema",
                "name": "CotizacionTecnica",
                "schema": COTIZACION_SCHEMA,
                "strict": True,
            }
        },
    }

    resp = client.responses.create(**payload)
    return resp, payload


def extract_json(resp):
    """Extrae JSON válido desde la respuesta de OpenAI Responses API"""
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
        return json.loads(json_text)
    except json.JSONDecodeError:
        st.error("❌ La salida no es JSON válido. Aquí está lo que devolvió el modelo:")
        st.text(json_text)
        st.stop()


def get_openai_metadata():
    """Devuelve información del modelo y SDK"""
    return {"modelo": MODEL_NAME, "sdk_version": openai_version}
