import streamlit as st
from services.openai_service import upload_pdf, generate_quotation, get_openai_metadata
from services.word_service import prepare_data_for_word, render_docx

st.title("Generador de Cotizaciones con IA")

authors_input = st.text_input(
    "👥 Ingresa los nombres de los autores (separados por coma):"
)
description = st.text_area("✍️ Ingresa la descripción del ticket:")
uploaded_file = st.file_uploader(
    "📄 Sube un PDF (único formato soportado)", type=["pdf"]
)

if st.button("Generar Cotización"):
    if not description.strip() and not uploaded_file:
        st.warning(
            "Por favor escribe una descripción o sube un PDF antes de generar la cotización."
        )
    else:
        with st.spinner("Generando la cotización con GPT-5..."):
            file_id = upload_pdf(uploaded_file) if uploaded_file else None
            resp = generate_quotation(description, authors_input, file_id)
            data = resp.output_parsed.model_dump()

            data = prepare_data_for_word(data, authors_input)
            output = render_docx(data)

            st.success("✅ Cotización generada con éxito")
            st.download_button(
                label="📥 Descargar Cotización",
                data=output,
                file_name="cotizacion.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )

# Footer
meta = get_openai_metadata()
st.markdown(
    f"""
    <hr>
    <small>
    ⚙️ Model: <b>{meta['model']}</b><br>
    📦 OpenAI SDK: <b>{meta['sdk_version']}</b>
    </small>
    """,
    unsafe_allow_html=True,
)
