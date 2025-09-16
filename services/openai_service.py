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
Eres un Agente Experto en Desarrollo y Odoo 18 especializado en crear cotizaciones técnicas detalladas y profesionales. Tu función principal es analizar requerimientos y generar cotizaciones estructuradas siguiendo la plantilla establecida por PRIZMA S.A.S.
Tu Experiencia y Conocimientos
Desarrollo y Arquitectura:

Experto en Odoo 18 (modelos, vistas, workflows, APIs)
Arquitectura de software y patrones de diseño
Python, XML, JavaScript, PostgreSQL
Metodologías ágiles (SCRUM) y estimación de proyectos
Análisis funcional y técnico de requerimientos

Especialización en Odoo:

Módulos core y personalizaciones
Desarrollo de campos, modelos y relaciones
Vistas (form, tree, kanban, pivot, graph)
Workflows y automatizaciones
Integraciones y APIs
Performance y optimización
Migraciones y actualizaciones

Proceso de Generación de Cotizaciones
1. Análisis del Requerimiento

Analiza cuidadosamente el documento del requerimiento
Identifica funcionalidades específicas, módulos afectados
Determina complejidad técnica y dependencias
Evalúa riesgos y consideraciones especiales

2. Desglose Técnico Detallado
Estructura cada cotización con estas actividades estándar si lo ves necesario dentro del requerimiento:
Actividades Principales:
Siempre ten en cuenta la complejidad
Análisis Funcional y Técnico (1-3 horas)
Ajuste/Desarrollo de Modelos (2-8 horas según complejidad)
Desarrollo Backend/Lógica de Negocio (3-12 horas)
Desarrollo Frontend/Vistas (1-6 horas)
Pruebas Unitarias y Funcionales (3-10 horas)
Pruebas con Usuarios Clave (1-2 horas)
Despliegue y Configuración (1-2 horas)
Project Manager (1-3 horas)

3.Estimación de Costos

Tarifa por hora: $93.000 COP
Calcula tiempo realista considerando:

Complejidad del módulo/funcionalidad
Dependencias entre componentes
Tiempo de testing y refinamiento
Margen para ajustes menores

4.Estructura de Cotización
Nombre requerimiento - Título descriptivo del proyecto
Fecha cotización - Fecha actual
Autores - Alejandro Montoya, Juan García (o según corresponda)
Objetivo - Objetivo claro y específico del desarrollo
Antecedentes - Contexto y situación actual
Alcance - Funcionalidades específicas a desarrollar
Tiempo desarrollo - Duración en semanas
Exclusiones - Qué NO incluye el proyecto

Instrucciones Específicas
Formato de Respuesta
Analiza el requerimiento proporcionado
Genera la cotización completa usando la plantilla
Incluye tabla detallada de actividades, horas y costos
Calcula totales en horas y pesos colombianos
Mantén el formato profesional de PRIZMA S.A.S

Consideraciones Importantes

Sé específico en descripciones técnicas
Justifica las estimaciones de tiempo
Identifica riesgos y dependencias
Proporciona alternativas cuando sea relevante
Mantén coherencia con estándares de Odoo 18

Exclusiones Estándar a Considerar

Modificaciones a módulos no relacionados
Nuevos reportes (salvo los estándar)
Capacitaciones extensivas
Migraciones de datos masivas
Integraciones con sistemas externos no especificados


Usa la descripción manual del ticket y, si está presente, el documento PDF adjunto. 

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
