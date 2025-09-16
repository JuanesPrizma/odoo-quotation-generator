import tempfile, os
from openai import OpenAI, __version__ as openai_version
from models.quotation_model import Quotation

client = OpenAI()
MODEL_NAME = "gpt-5"


def upload_pdf(uploaded_file):
    """Upload a PDF to OpenAI and return its file_id"""
    if not uploaded_file:
        return None
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name
    up = client.files.create(file=open(tmp_path, "rb"), purpose="user_data")
    os.remove(tmp_path)
    return up.id


def generate_quotation(description: str, authors_input: str, file_id: str = None):
    instructions = f"""
Eres un asistente experto en elaborar cotizaciones técnicas detalladas y profesionales.

Usa la descripción manual del ticket y, si está presente, el documento PDF adjunto. 
Genera textos largos, elaborados y claros en cada campo.

Autores proporcionados: {authors_input}

⚠️ Importante: si algún campo no aplica o no hay información suficiente,
devuelve un string vacío "" o una lista vacía [].
Nunca devuelvas null.
"""

    input_items = [
        {"role": "system", "content": "You are a quotation assistant."},
        {"role": "user", "content": instructions},
        {"role": "user", "content": f"Descripción del ticket: {description.strip()}"},
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

    response = client.responses.parse(
        model=MODEL_NAME, input=input_items, text_format=Quotation
    )

    return response


def get_openai_metadata():
    return {"model": MODEL_NAME, "sdk_version": openai_version}
