from docxtpl import DocxTemplate
import io


def prepare_data_for_word(data: dict, authors_input: str):
    """Normalize and format data for Word document rendering"""
    defaults = {"alcance": [], "exclusiones": [], "autores": []}
    for key, default_value in defaults.items():
        if key not in data or data[key] is None:
            data[key] = default_value

    # Override authors manually
    authors = [a.strip() for a in authors_input.split(",") if a.strip()]
    data["autores"] = authors

    # Convert lists to bullet points
    def list_to_bullets(items):
        if not isinstance(items, list):
            return items or ""
        return "\n".join([f"• {item}" for item in items])

    for key in ["alcance", "exclusiones"]:
        if key in data:
            data[key] = list_to_bullets(data[key])

    return data


def render_docx(data: dict, template_path="plantilla_cotizacion.docx"):
    doc = DocxTemplate(template_path)
    doc.render(data)
    output = io.BytesIO()
    doc.save(output)
    output.seek(0)
    return output
