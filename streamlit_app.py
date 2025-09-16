import streamlit as st
from services.openai_service import (
    upload_pdf,
    generate_quotation,
    extract_json,
    get_openai_metadata,
)
from services.word_service import prepare_data_for_word, render_docx
import json

st.title("Generador de Cotizaciones con IA")

autores_input = st.text_input(
    "👥 Ingresa los nombres de los autores (separados por coma):"
)
descripcion = st.text_area("✍️ Ingresa la descripción del ticket:")
uploaded_file = st.file_uploader(
    "📄 Sube un PDF (único formato soportado)", type=["pdf"]
)

if st.button("Generar Cotización"):
    if not descripcion.strip() and not uploaded_file:
        st.warning(
            "Por favor escribe una descripción o sube un PDF antes de generar la cotización."
        )
    else:
        with st.spinner("Generando la cotización..."):
            file_id = upload_pdf(uploaded_file) if uploaded_file else None
            resp, payload = generate_quotation(descripcion, autores_input, file_id)
            data = extract_json(resp)
            data = prepare_data_for_word(data, autores_input)
            output = render_docx(data)

            st.success("✅ Cotización generada con éxito")
            st.download_button(
                label="📥 Descargar Cotización",
                data=output,
                file_name="cotizacion.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )

            # Mostrar cuerpo de la petición
            with st.expander("📦 Ver cuerpo de la petición enviada a OpenAI"):
                st.json(payload)

# Pie de página
meta = get_openai_metadata()
st.markdown(
    f"""
    <hr>
    <small>
    ⚙️ Modelo: <b>{meta['modelo']}</b> <br>
    📦 OpenAI SDK: <b>{meta['sdk_version']}</b>
    </small>
    """,
    unsafe_allow_html=True,
)
