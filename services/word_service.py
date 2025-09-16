from docxtpl import DocxTemplate
import io


def prepare_data_for_word(data, autores_input):
    """Normaliza y formatea los datos para el Word"""
    defaults = {"alcance": [], "exclusiones": [], "autores": []}
    for key, default_value in defaults.items():
        if key not in data or data[key] is None:
            data[key] = default_value

    # Sobrescribir autores manuales
    autores = [a.strip() for a in autores_input.split(",") if a.strip()]
    data["autores"] = autores

    # Helper para listas → viñetas
    def list_to_bullets(items):
        if not isinstance(items, list):
            return items or ""
        return "\n".join([f"• {item}" for item in items])

    for key in ["alcance", "exclusiones"]:
        if key in data:
            data[key] = list_to_bullets(data[key])

    return data


def render_docx(data, template_path="plantilla_cotizacion.docx"):
    """Renderiza la cotización en un Word a partir de los datos formateados"""
    doc = DocxTemplate(template_path)
    doc.render(data)
    output = io.BytesIO()
    doc.save(output)
    output.seek(0)
    return output
