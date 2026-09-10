import streamlit as st

from zeus_display_parser_v3 import (
    DLMSDisplayParser,
    DISPLAY_CODES,
    DISPLAY_CODES_SOURCE,
    MAX_DECIMAIS_LCD,
    MAX_POSICOES_LCD,
    DisplaySetup,
    ObisType,
    aplicar_setup,
    codigos_da_tela,
    get_screen_info,
    setup_do_frame,
    unidade_do_bitmask,
    valor_base_do_display,
)

st.set_page_config(page_title="ZEUS-NG Display Parser", layout="wide")

CHAVES_CONFIG = [
    "cfg_fonte", "cfg_registrador", "cfg_modo", "cfg_rtc_num", "cfg_rtc_den",
    "cfg_rtp_num", "cfg_rtp_den", "cfg_int", "cfg_dec", "cfg_mag", "cfg_obis",
    "cfg_zeros",
]


def restaurar_do_frame():
    """Apaga as chaves dos widgets: eles voltam ao que veio no frame."""
    for chave in CHAVES_CONFIG:
        st.session_state.pop(chave, None)


def novo_frame():
    """Frame novo: descarta a configuracao que estava aplicada."""
    restaurar_do_frame()
    st.session_state.pop("display", None)


st.title("ZEUS-NG smart meter — display parser")
st.caption(
    f"{len(DISPLAY_CODES)} telas carregadas "
    + (
        "(mapa embutido — crie um telas.xml para atualizar)"
        if DISPLAY_CODES_SOURCE == "built-in"
        else f"de {DISPLAY_CODES_SOURCE}"
    )
)

hex_input = st.text_area(
    "Payload HEX bruto do medidor", key="hex_input", on_change=novo_frame, height=100
)

if st.button("Fazer parse", type="primary", icon=":material/play_arrow:"):
    restaurar_do_frame()
    limpo = "".join(hex_input.split())
    try:
        display = DLMSDisplayParser().parse(bytes.fromhex(limpo))
    except ValueError as erro:
        display = None
        st.error(f"HEX inválido: {erro}")
    if display:
        st.session_state.display = display
    elif limpo:
        st.error("Erro ao processar o frame.")

display = st.session_state.get("display")

if display is not None:
    do_frame = setup_do_frame(display)
    registrador_frame = valor_base_do_display(display)
    numerica = registrador_frame is not None

    controles, visor = st.columns([1, 2], gap="medium")

    with controles:
        st.subheader("Configuração da tela", anchor=False)
        st.caption(
            "Campos de `Set_Display_Setup` (objeto DLMS `1|0.0.96.60.4.255`). "
            "A configuração é por **família**, não por tela: mexer aqui muda "
            "todas as telas da mesma família no medidor."
        )

        if numerica:
            fonte = st.segmented_control(
                "Valor vem de",
                ["frame", "registrador"],
                key="cfg_fonte",
                default="frame",
                help="frame: usa o valor como veio no payload. registrador: usa o "
                "inteiro que você digitar abaixo.",
            ) or "frame"
            registrador = st.number_input(
                "Registrador (Wh/varh)",
                min_value=0,
                value=registrador_frame,
                step=1,
                key="cfg_registrador",
                disabled=fonte == "frame",
                help="Valor inteiro na unidade base, como vem do objeto DLMS. "
                "Foi reconstruído a partir do frame — os dígitos que a virada de "
                "tela cortou não voltam.",
            )
            if fonte == "frame":
                registrador = None      # aplicar_setup reconstroi do proprio frame
        else:
            registrador = None
            st.info(
                "Tela não numérica (data, hora, serial): o campo principal fica "
                "como veio no frame. Magnitude e código continuam configuráveis.",
                icon=":material/info:",
            )

        with st.container(horizontal=True):
            inteiros = st.number_input(
                "Casas inteiras",
                min_value=0,
                max_value=MAX_POSICOES_LCD,
                value=do_frame.integer_places,
                key="cfg_int",
                help="O LCD tem 8 posições no total (inteiros + decimais).",
            )
            decimais = st.number_input(
                "Casas decimais",
                min_value=0,
                max_value=MAX_DECIMAIS_LCD,
                value=do_frame.decimal_places,
                key="cfg_dec",
                help="O LCD só tem 3 segmentos de ponto decimal.",
            )

        magnitude = st.segmented_control(
            "Magnitude",
            ["k", "M"],
            key="cfg_mag",
            default=do_frame.magnitude,
            help="Escala da divisão: k = 10³, M = 10⁶.",
        ) or do_frame.magnitude

        modo = st.segmented_control(
            "Primário / secundário",
            ["secundário", "primário"],
            key="cfg_modo",
            default="primário" if do_frame.primary else "secundário",
            help="Secundário mostra o registrador cru. Primário multiplica por TC × TP "
            "antes de formatar — o frame não informa esse campo, então o padrão é secundário.",
        ) or "secundário"
        primario = modo == "primário"

        if primario:
            with st.container(horizontal=True):
                rtc_num = st.number_input("RTC num", min_value=1, value=1, key="cfg_rtc_num")
                rtc_den = st.number_input("RTC den", min_value=1, value=1, key="cfg_rtc_den")
            with st.container(horizontal=True):
                rtp_num = st.number_input("RTP num", min_value=1, value=1, key="cfg_rtp_num")
                rtp_den = st.number_input("RTP den", min_value=1, value=1, key="cfg_rtp_den")
        else:
            rtc_num = rtc_den = rtp_num = rtp_den = 1

        equivalentes = codigos_da_tela(display.obis)
        formatos = [f for f in ("DLMS", "ABNT") if equivalentes.get(f)] or ["DLMS"]
        padrao_obis = "ABNT" if do_frame.obis_type == int(ObisType.ABNT) else "DLMS"
        formato = st.segmented_control(
            "Código exibido (obis-type)",
            formatos,
            key="cfg_obis",
            default=padrao_obis if padrao_obis in formatos else formatos[0],
            help="Só muda o código escrito na linha superior, nunca o valor.",
        ) or formatos[0]
        if len(formatos) == 1:
            st.caption(":grey[Esta tela só tem um dos dois códigos no telas.xml.]")

        zeros = st.checkbox(
            "Zeros à esquerda",
            value=do_frame.use_left_zeros,
            key="cfg_zeros",
            help="use-left-zeros: preenche à esquerda até int + dec caracteres.",
        )

        st.button(
            "Restaurar do frame",
            on_click=restaurar_do_frame,
            icon=":material/restart_alt:",
            width="stretch",
            help="Volta todos os campos para a configuração que veio no frame.",
        )

    setup = DisplaySetup(
        integer_places=int(inteiros),
        decimal_places=int(decimais),
        magnitude=magnitude,
        primary=primario,
        rtc=(int(rtc_num), int(rtc_den)),
        rtp=(int(rtp_num), int(rtp_den)),
        obis_type=int(ObisType.ABNT if formato == "ABNT" else ObisType.DLMS),
        use_left_zeros=zeros,
    )
    erros = setup.validar()

    with visor:
        if erros:
            st.error(
                "Configuração recusada pelo medidor:\n\n"
                + "\n".join(f"- {e}" for e in erros),
                icon=":material/error:",
            )
            mostrado = display
        else:
            mostrado = aplicar_setup(display, setup, registrador=registrador)

        st.iframe(mostrado.html, height=620)

        info = get_screen_info(display.obis)
        with st.container(horizontal=True):
            st.metric("Tela", display.get_screen_name())
            st.metric("Código", mostrado.obis or "—")
            st.metric("Unidade", unidade_do_bitmask(mostrado.unit_bits))
        if info.get("descricao"):
            st.caption(info["descricao"])

        alterado = (mostrado.data != display.data) or (mostrado.obis != display.obis)
        if alterado and not erros:
            origem = "registrador digitado" if registrador is not None else "valor do frame"
            st.caption(
                f"Do frame: `{display.obis} {display.data}` → "
                f"configurado ({origem}): `{mostrado.obis} {mostrado.data}`"
            )
