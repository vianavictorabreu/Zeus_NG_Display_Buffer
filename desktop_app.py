import webview

from zeus_display_parser_v3 import (
    DLMSDisplayParser,
    DisplaySetup,
    ObisType,
    aplicar_setup,
    codigos_da_tela,
    get_screen_info,
    setup_do_frame,
    unidade_do_bitmask,
    valor_base_do_display,
)

# O painel de controle usa a MESMA linguagem visual do display gerado pelo parser
# (_HTML_CSS): fundo #cfd2d6, placa clara #eef0ea, moldura escura #3a3f44, Arial.
# O display em si nunca e alterado - ele vem pronto do parser, sempre desenhado
# em 7 segmentos, inclusive depois de reconfigurado.
PAGE_HTML = """<!doctype html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<title>ZEUS-NG Display Parser</title>
<style>
  * { box-sizing: border-box; }
  body {
    margin: 0;
    padding: 12px 14px 14px;
    background: #cfd2d6;
    color: #222;
    font-family: Arial, Helvetica, sans-serif;
  }

  /* ---- placa: mesma moldura do .lcd-panel do display ---- */
  .plate {
    background: #eef0ea;
    border: 10px solid #3a3f44;
    border-radius: 8px;
    box-shadow: 0 6px 20px rgba(0,0,0,.4);
    padding: 14px 16px;
  }
  .plate h2 {
    margin: 0 0 10px 0;
    font: bold 12px Arial;
    letter-spacing: .1em;
    text-transform: uppercase;
    color: #3a3f44;
  }
  .plate h2 small {
    display: block; margin-top: 3px;
    font: normal 11px Arial; letter-spacing: 0;
    text-transform: none; color: #74797f;
  }

  /* ---- entrada do frame ---- */
  #hexInput {
    width: 100%; min-height: 62px; resize: vertical;
    background: #dfe2db; color: #161616;
    border: 2px solid #a8aca4; border-radius: 4px;
    padding: 7px 9px; font: 13px Consolas, monospace;
  }
  #hexInput:focus, .ctl:focus { outline: none; border-color: #3a3f44; }
  .btn {
    padding: 8px 22px; border-radius: 4px; cursor: pointer;
    font: bold 13px Arial; border: 2px solid #2b2f33;
    background: #3a3f44; color: #eef0ea;
  }
  .btn:hover { background: #4b5157; }
  .btn.ghost { background: #dfe2db; color: #3a3f44; border-color: #a8aca4; }
  .btn.ghost:hover { background: #d3d5cd; }
  .row-actions { display: flex; gap: 10px; align-items: center; margin-top: 9px; }
  #status { font: 12.5px Arial; color: #a02020; margin-top: 6px; }
  #status:empty { display: none; }

  /* ---- corpo: display a esquerda, configuracao na lateral ---- */
  #main { display: flex; gap: 14px; align-items: flex-start; }
  #stage { flex: 1; min-width: 0; }
  #side { width: 316px; flex: none; display: flex; flex-direction: column; gap: 14px; }
  #resultFrame {
    width: 100%; border: none; background: transparent; display: block;
    overflow: hidden;            /* a altura acompanha o conteudo: nada de rolagem interna */
  }
  #setup[hidden] { display: none; }

  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px 12px; align-items: end; }
  .grid .wide { grid-column: span 2; }
  .field { display: flex; flex-direction: column; gap: 4px; }
  .field > span {
    font: bold 10.5px Arial; letter-spacing: .07em;
    text-transform: uppercase; color: #5d6268;
  }
  .ctl {
    width: 100%; padding: 6px 8px;
    background: #dfe2db; color: #161616;
    border: 2px solid #a8aca4; border-radius: 4px;
    font: 13px Arial; height: 32px;
  }
  .ctl:disabled { background: #d7d9d2; color: #8b8f88; }
  input.ctl[type=number] { font-family: Consolas, monospace; }

  /* escolhas no estilo dos rotulos do LCD: acendem em preto */
  .seg-switch { display: flex; border: 2px solid #a8aca4; border-radius: 4px; overflow: hidden; height: 32px; }
  .seg-switch button {
    flex: 1; border: none; cursor: pointer; padding: 0 6px;
    background: #dfe2db; color: #74797f;
    font: bold 12px Arial; letter-spacing: .03em;
  }
  .seg-switch button + button { border-left: 2px solid #a8aca4; }
  .seg-switch button.on { background: #3a3f44; color: #eef0ea; }
  .seg-switch button:disabled { cursor: default; opacity: .5; }

  .check { display: flex; align-items: center; gap: 7px; height: 32px; font: 12.5px Arial; color: #333; }
  #tcRow[hidden], #setupErr[hidden], #screenNote[hidden] { display: none; }

  .note { margin: 10px 0 0 0; padding: 8px 10px; border-radius: 4px; font: 12px Arial; line-height: 1.5; }
  #setupErr { background: #f3dede; border: 2px solid #b06a6a; color: #7a2020; }
  #screenNote { background: #e7e4d6; border: 2px solid #b3ac86; color: #5f5730; }
  #summary {
    margin-top: 12px; padding-top: 10px; border-top: 2px solid #d3d5cd;
    font: 12px Consolas, monospace; color: #3f4348; line-height: 1.65; word-break: break-word;
  }
  #summary b { color: #161616; }
  #summary .arrow { color: #a02020; font-weight: bold; }
</style>
</head>
<body>

  <div id="main">
    <div id="stage"><iframe id="resultFrame" scrolling="no"></iframe></div>

   <div id="side">
    <div class="plate">
      <h2>ZEUS-NG Smart Meter <small>Display Buffer &mdash; DISP.CMD.7</small></h2>
      <textarea id="hexInput" placeholder="Cole o payload HEX... (Ctrl+Enter)"></textarea>
      <div class="row-actions">
        <button class="btn" onclick="doParse()">Fazer Parse</button>
      </div>
      <div id="status"></div>
    </div>

    <div class="plate" id="setup" hidden>
      <h2>Configura&ccedil;&atilde;o da tela
        <small>Set_Display_Setup &mdash; 1|0.0.96.60.4.255</small>
      </h2>

      <div id="setupErr" class="note" hidden></div>
      <div id="screenNote" class="note" hidden></div>

      <div class="grid">
        <label class="field wide"><span>Valor vem de</span>
          <div class="seg-switch" id="cfgFonte">
            <button type="button" data-v="frame">Frame</button>
            <button type="button" data-v="registrador">Registrador</button>
          </div>
        </label>

        <label class="field wide"><span>Registrador (Wh/varh)</span>
          <input type="number" class="ctl" id="cfgRegistrador" min="0" step="1">
        </label>

        <label class="field"><span>Inteiros</span>
          <input type="number" class="ctl" id="cfgInt" min="0" max="8">
        </label>

        <label class="field"><span>Decimais</span>
          <input type="number" class="ctl" id="cfgDec" min="0" max="3">
        </label>

        <label class="field"><span>Magnitude</span>
          <div class="seg-switch" id="cfgMag">
            <button type="button" data-v="k">k</button>
            <button type="button" data-v="M">M</button>
          </div>
        </label>

        <label class="field"><span>C&oacute;digo</span>
          <div class="seg-switch" id="cfgObis">
            <button type="button" data-v="DLMS">DLMS</button>
            <button type="button" data-v="ABNT">ABNT</button>
          </div>
        </label>

        <label class="field wide"><span>Primário / secundário</span>
          <div class="seg-switch" id="cfgModo">
            <button type="button" data-v="secundario">Secund&aacute;rio</button>
            <button type="button" data-v="primario">Prim&aacute;rio (TC&times;TP)</button>
          </div>
        </label>

        <div id="tcRow" class="wide" hidden>
          <div class="grid">
            <label class="field"><span>RTC num</span><input type="number" class="ctl" id="cfgRtcNum" min="1" value="1"></label>
            <label class="field"><span>RTC den</span><input type="number" class="ctl" id="cfgRtcDen" min="1" value="1"></label>
            <label class="field"><span>RTP num</span><input type="number" class="ctl" id="cfgRtpNum" min="1" value="1"></label>
            <label class="field"><span>RTP den</span><input type="number" class="ctl" id="cfgRtpDen" min="1" value="1"></label>
          </div>
        </div>

        <label class="check wide">
          <input type="checkbox" id="cfgZeros"> Zeros &agrave; esquerda
        </label>
      </div>

      <div class="row-actions">
        <button class="btn ghost" onclick="restoreFrame()">Restaurar do frame</button>
      </div>

      <div id="summary"></div>
    </div>
   </div>
  </div>

<script>
  var frameCfg = null;      // configuracao detectada no frame
  var aplicando = false;    // evita reentrada durante o preenchimento

  function el(id) { return document.getElementById(id); }

  /* numero tolerante: campo vazio nao vira NaN/null para o python */
  function num(id, padrao) {
    var v = parseInt(el(id).value, 10);
    return isNaN(v) ? padrao : v;
  }

  /* --- seg-switch: grupo de botoes que se comporta como um radio --- */
  function switchValue(id) {
    var on = el(id).querySelector('button.on');
    return on ? on.dataset.v : null;
  }
  function setSwitch(id, valor) {
    Array.prototype.forEach.call(el(id).children, function (b) {
      b.classList.toggle('on', b.dataset.v === valor);
    });
  }
  ['cfgFonte', 'cfgMag', 'cfgModo', 'cfgObis'].forEach(function (id) {
    Array.prototype.forEach.call(el(id).children, function (b) {
      b.addEventListener('click', function () {
        if (b.disabled) { return; }
        setSwitch(id, b.dataset.v);
        aplicar();
      });
    });
  });

  /* O documento do display e injetado com um script que reporta a propria
     altura ao pai. Assim o iframe cresce junto com o conteudo e nunca cria
     barra de rolagem - inclusive quando o WebView isola o iframe e o pai nao
     consegue ler o contentDocument. */
  var ENXUTO = '<style>body{padding:6px 8px !important;}</style>';

  /* Mede o CONTEUDO, nunca o viewport. documentElement.scrollHeight nao serve:
     ele nunca fica menor que a altura do proprio iframe, entao mediria a altura
     que acabamos de aplicar e o quadro cresceria a cada geracao. */
  var MEDIDA = 'function h(){var b=document.body;if(!b)return 0;'
    + 'var cs=getComputedStyle(b);var pb=parseFloat(cs.paddingBottom)||0;'
    + 'var alt=b.getBoundingClientRect().height;'
    + 'for(var i=0;i<b.children.length;i++){'
    + 'var r=b.children[i].getBoundingClientRect();'
    + 'if(r.bottom+pb>alt){alt=r.bottom+pb;}}'
    + 'return Math.ceil(alt+(parseFloat(cs.marginTop)||0)+(parseFloat(cs.marginBottom)||0));}';

  var MEDIDOR = '<script>(function(){'
    + MEDIDA
    + 'var ultimo=0;'
    + 'function envia(){var v=h();if(v>0&&Math.abs(v-ultimo)>1){ultimo=v;'
    + 'try{parent.postMessage({zeusAltura:v},"*");}catch(e){}}}'
    + 'window.addEventListener("load",envia);'
    + 'if(window.ResizeObserver){new ResizeObserver(envia).observe(document.body);}'
    + '[0,80,250,600].forEach(function(t){setTimeout(envia,t);});'
    + 'envia();'
    + '})();<' + '/script>';   /* partido para nao fechar o script do pai */

  function aplicarAltura(px) {
    var f = el('resultFrame');
    if (!(px > 0)) { return; }
    /* so mexe quando muda de verdade: corta qualquer realimentacao residual */
    if (Math.abs(f.getBoundingClientRect().height - px) <= 2) { return; }
    f.style.height = px + 'px';
  }

  window.addEventListener('message', function (ev) {
    if (ev.data && typeof ev.data.zeusAltura === 'number') { aplicarAltura(ev.data.zeusAltura); }
  });

  /* caminho alternativo: quando o pai CONSEGUE ler o documento do iframe */
  function ajustarAltura() {
    var f = el('resultFrame');
    try {
      var doc = f.contentDocument, b = doc && doc.body;
      if (!b) { return; }
      var cs = doc.defaultView.getComputedStyle(b);
      var pb = parseFloat(cs.paddingBottom) || 0;
      var alvo = b.getBoundingClientRect().height;
      for (var i = 0; i < b.children.length; i++) {
        var r = b.children[i].getBoundingClientRect();
        if (r.bottom + pb > alvo) { alvo = r.bottom + pb; }
      }
      aplicarAltura(Math.ceil(alvo));
    } catch (e) { /* isolado: a altura chega por postMessage */ }
  }
  el('resultFrame').addEventListener('load', ajustarAltura);

  function mostrar(html) {
    var doc = String(html);
    var corte = doc.lastIndexOf('</body>');
    doc = corte === -1 ? doc + ENXUTO + MEDIDOR
                       : doc.slice(0, corte) + ENXUTO + MEDIDOR + doc.slice(corte);
    var f = el('resultFrame');
    f.style.height = '';          /* nao herda a altura do display anterior */
    f.srcdoc = doc;
    [80, 250, 600].forEach(function (t) { setTimeout(ajustarAltura, t); });
  }

  async function doParse() {
    var hex = el('hexInput').value;
    el('status').textContent = '';
    if (!hex.trim()) { return; }
    try {
      var res = await window.pywebview.api.parse(hex);
      if (res.error) {
        el('status').textContent = res.error;
        el('resultFrame').srcdoc = '';
        el('setup').hidden = true;
        frameCfg = null;
        return;
      }
      frameCfg = res.config;
      preencherPainel(res.config);
      el('setup').hidden = false;
      el('summary').innerHTML = res.summary;
      mostrar(res.html);
    } catch (e) {
      el('status').textContent = 'Erro inesperado: ' + e;
    }
  }

  function preencherPainel(c) {
    aplicando = true;
    el('cfgInt').value = c.integer_places;
    el('cfgDec').value = c.decimal_places;
    el('cfgZeros').checked = c.use_left_zeros;
    setSwitch('cfgMag', c.magnitude);
    setSwitch('cfgModo', c.primary ? 'primario' : 'secundario');
    setSwitch('cfgFonte', 'frame');
    el('cfgRtcNum').value = 1; el('cfgRtcDen').value = 1;
    el('cfgRtpNum').value = 1; el('cfgRtpDen').value = 1;

    // codigo exibido: desliga o formato que a tela nao tem no telas.xml
    Array.prototype.forEach.call(el('cfgObis').children, function (b) {
      b.disabled = c.formatos.indexOf(b.dataset.v) === -1;
    });
    setSwitch('cfgObis', c.obis_formato);

    el('cfgRegistrador').value = c.registrador;
    atualizarFonte(c);

    var nota = el('screenNote');
    nota.hidden = c.numerica;
    if (!c.numerica) {
      nota.innerHTML = '<b>Tela n&atilde;o num&eacute;rica</b> (data, hora, serial): o campo '
        + 'principal fica como veio no frame.';
    }
    el('tcRow').hidden = !c.primary;
    aplicando = false;
  }

  /* o campo do registrador so e editavel quando a fonte e "registrador" */
  function atualizarFonte(c) {
    var cfg = c || frameCfg;
    if (!cfg) { return; }
    var porRegistrador = switchValue('cfgFonte') === 'registrador';
    Array.prototype.forEach.call(el('cfgFonte').children, function (b) {
      b.disabled = !cfg.numerica;
    });
    el('cfgRegistrador').disabled = !porRegistrador || !cfg.numerica;
    if (!porRegistrador) { el('cfgRegistrador').value = cfg.registrador; }
  }

  async function aplicar() {
    if (aplicando || !frameCfg) { return; }
    el('tcRow').hidden = switchValue('cfgModo') !== 'primario';
    atualizarFonte();

    var porRegistrador = switchValue('cfgFonte') === 'registrador';
    var cfg = {
      integer_places: num('cfgInt', frameCfg.integer_places),
      decimal_places: num('cfgDec', frameCfg.decimal_places),
      magnitude: switchValue('cfgMag') || 'k',
      primary: switchValue('cfgModo') === 'primario',
      rtc: [num('cfgRtcNum', 1), num('cfgRtcDen', 1)],
      rtp: [num('cfgRtpNum', 1), num('cfgRtpDen', 1)],
      obis_formato: switchValue('cfgObis') || 'DLMS',
      use_left_zeros: el('cfgZeros').checked,
      fonte: porRegistrador ? 'registrador' : 'frame',
      registrador: porRegistrador ? num('cfgRegistrador', frameCfg.registrador) : null
    };
    try {
      var res = await window.pywebview.api.reconfigure(cfg);
      var box = el('setupErr');
      if (res.errors && res.errors.length) {
        box.hidden = false;
        box.innerHTML = '<b>Configura&ccedil;&atilde;o recusada:</b><br>&bull; '
          + res.errors.join('<br>&bull; ');
      } else {
        box.hidden = true;
      }
      el('summary').innerHTML = res.summary;
      mostrar(res.html);
    } catch (e) {
      el('status').textContent = 'Erro inesperado: ' + e;
    }
  }

  function restoreFrame() {
    if (!frameCfg) { return; }
    preencherPainel(frameCfg);
    el('setupErr').hidden = true;
    aplicar();
  }

  ['cfgRegistrador', 'cfgInt', 'cfgDec', 'cfgZeros',
   'cfgRtcNum', 'cfgRtcDen', 'cfgRtpNum', 'cfgRtpDen'].forEach(function (id) {
    var node = el(id);
    node.addEventListener('change', aplicar);
    if (node.type === 'number') { node.addEventListener('input', aplicar); }
  });

  el('hexInput').addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && e.ctrlKey) { doParse(); }
  });
</script>
</body>
</html>
"""


def _inteiro(valor, padrao: int) -> int:
    """Converte para int aceitando None/vazio/NaN vindos do formulario."""
    try:
        if valor is None or valor == "":
            return padrao
        return int(valor)
    except (TypeError, ValueError):
        return padrao


class Api:
    """Ponte pywebview: guarda o frame parseado e reformata sob outra configuracao."""

    def __init__(self):
        self.display = None

    # ---------------------------------------------------------------- parse
    def parse(self, hex_input: str):
        cleaned = "".join(str(hex_input).split())
        try:
            raw = bytes.fromhex(cleaned)
        except ValueError as exc:
            return {"error": f"Hex invalido: {exc}"}

        display = DLMSDisplayParser().parse(raw)
        if display is None:
            return {"error": "Erro ao processar o frame."}

        self.display = display
        return {
            "html": display.html,
            "config": self._config_do_frame(display),
            "summary": self._resumo(display, display),
        }

    # ---------------------------------------------------------- reconfigure
    def reconfigure(self, cfg: dict):
        if self.display is None:
            return {"error": "Nenhum frame carregado."}

        do_frame = setup_do_frame(self.display)
        rtc = cfg.get("rtc") or (1, 1)
        rtp = cfg.get("rtp") or (1, 1)

        setup = DisplaySetup(
            integer_places=_inteiro(cfg.get("integer_places"), do_frame.integer_places),
            decimal_places=_inteiro(cfg.get("decimal_places"), do_frame.decimal_places),
            magnitude=str(cfg.get("magnitude") or "k"),
            primary=bool(cfg.get("primary", False)),
            rtc=(_inteiro(rtc[0], 1), _inteiro(rtc[1], 1)),
            rtp=(_inteiro(rtp[0], 1), _inteiro(rtp[1], 1)),
            obis_type=int(
                ObisType.ABNT if cfg.get("obis_formato") == "ABNT" else ObisType.DLMS
            ),
            use_left_zeros=bool(cfg.get("use_left_zeros", False)),
            # familia fica de fora: valem so as regras fisicas do LCD
        )
        erros = setup.validar()
        if erros:
            # configuracao invalida: mantem o display do frame na tela
            return {
                "html": self.display.html,
                "errors": erros,
                "summary": self._resumo(self.display, self.display),
            }

        # fonte "frame": aplicar_setup reconstroi o valor do proprio frame.
        # fonte "registrador": usa o inteiro digitado.
        registrador = None
        if cfg.get("fonte") == "registrador":
            registrador = _inteiro(cfg.get("registrador"), 0)

        novo = aplicar_setup(self.display, setup, registrador=registrador)
        return {
            "html": novo.html,
            "errors": [],
            "summary": self._resumo(self.display, novo, fonte=cfg.get("fonte", "frame")),
        }

    # -------------------------------------------------------------- helpers
    @staticmethod
    def _config_do_frame(display) -> dict:
        do_frame = setup_do_frame(display)
        registrador = valor_base_do_display(display)
        equivalentes = codigos_da_tela(display.obis)
        formatos = [f for f in ("DLMS", "ABNT") if equivalentes.get(f)] or ["DLMS"]
        formato = "ABNT" if do_frame.obis_type == int(ObisType.ABNT) else "DLMS"
        return {
            "integer_places": do_frame.integer_places,
            "decimal_places": do_frame.decimal_places,
            "magnitude": do_frame.magnitude,
            "primary": do_frame.primary,
            "use_left_zeros": do_frame.use_left_zeros,
            "formatos": formatos,
            "obis_formato": formato if formato in formatos else formatos[0],
            "numerica": registrador is not None,
            "registrador": registrador if registrador is not None else 0,
        }

    @staticmethod
    def _resumo(original, mostrado, fonte: str = "frame") -> str:
        info = get_screen_info(original.obis)
        linhas = [
            f"<b>Tela:</b> {original.get_screen_name()}",
            f"<b>C&oacute;digo:</b> {mostrado.obis or '-'}"
            f" &nbsp; <b>Unidade:</b> {unidade_do_bitmask(mostrado.unit_bits)}",
        ]
        if info.get("descricao"):
            linhas.append(f"<b>Descri&ccedil;&atilde;o:</b> {info['descricao']}")
        if mostrado.data != original.data or mostrado.obis != original.obis:
            origem = "registrador digitado" if fonte == "registrador" else "valor do frame"
            linhas.append(
                f"<b>Do frame:</b> {original.obis} {original.data}"
                f" <span class='arrow'>&rarr;</span> <b>configurado</b> ({origem}):"
                f" {mostrado.obis} {mostrado.data}"
            )
        return "<br>".join(linhas)


if __name__ == "__main__":
    api = Api()
    webview.create_window(
        "ZEUS-NG Display Parser",
        html=PAGE_HTML,
        js_api=api,
        width=1060,
        height=900,
        min_size=(1000, 760),
    )
    webview.start()
