import streamlit as st
from zeus_display_parser_v3 import DLMSDisplayParser

st.text("ZEUS-NG Smart Meter - Display Parser")
hex_input = st.text_area("Cole o Payload HEX bruto do medidor:", value=" ")

if st.button("Fazer Parse"):
    if hex_input:
        display = DLMSDisplayParser().parse(bytes.fromhex(hex_input.replace(" ", "")))
        if display:
            st.components.v1.html(display.html, height=700)
            # st.success(f"**Tela:** {display.get_screen_name()}")
            # st.metric("OBIS", display.obis)
            # st.metric("Dados", display.data)
            # st.text(str(display))

            # Mostra o HTML renderizado diretamente na página
            # st.subheader("Visualização do Display")
        else:
            st.error("Erro ao processar o frame.")
