# Parser DLMS para Display Buffer (DISP.CMD.7) - ZEUS-NG Smart Meter

Parser Python para interpretar o Display Buffer (DISP.CMD.7) do medidor inteligente ZEUS-NG, conforme especificação Hexing/Eletra (Smart Meter ZEUS-NG Family: Product Specification, Revision 2.6 - March 2023).

## Identificação

- **OBIS Code**: 1 |0.0.96.55.9.255
- **Classe**: DisplayBuffer
- **Tipo**: Estrutura DLMS com 9 atributos
- **Atributo 2 (Value)**: struct com os campos abaixo

## Campos da Estrutura

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `obis` | visible-string[6] | Código OBIS (6 bytes) |
| `data` | visible-string[8] | Dados do display (8 bytes) |
| `tariff_num` | unsigned | Número da tarifa (0 = off) |
| `nic_signal_strength` | enum | Força do sinal NIC (0-5) |
| `nic_type` | enum | Tipo de NIC (RF, PLC, Cellular) |
| `quadrant` | enum | Quadrante do display (0-6) |
| `unit` | enum | Unidade de medida |
| `flags` | double-long-unsigned (32-bit) | Flags de status (bits 0-31) |
| `flags2` | double-long-unsigned (32-bit) | Flags secundárias (bits 0-10) |

## Enumerações

### Signal Strength (nic_signal_strength)
```
0x00 = SIGNAL_NONE      (Signal total off)
0x01 = SIGNAL_0         (no bar, only antenna)
0x02 = SIGNAL_1         (one bar)
0x03 = SIGNAL_2         (two bars)
0x04 = SIGNAL_3         (three bars)
0x05 = SIGNAL_4         (four bars)
```

### NIC Type (nic_type)
```
0x00 = NIC_NONE
0x01 = NIC_RF           (Radio Frequency)
0x02 = NIC_PLC          (Power Line Communication)
0x03 = NIC_CELLULAR     (Cellular)
```

### Quadrant (quadrant)
```
0x00 = QUADRANT_NONE    (no quadrant displayed)
0x01 = QUADRANT_0       (only the axis)
0x02 = QUADRANT_1
0x03 = QUADRANT_2
0x04 = QUADRANT_3
0x05 = QUADRANT_4
0x06 = QUADRANT_ALL     (all quadrants displayed)
```

### Unit (unit)
```
0x00 = No unit          0x01 = Celsius (°C)
0x02 = Hertz (Hz)       0x03 = Percentage (%)
0x04 = kW               0x05 = kWh
0x06 = MWh              0x07 = kvar
0x08 = kvarh            0x09 = Mvarh
0x10 = Volt (V)         0x11 = Ampere (A)
0x12 = VA               0x13 = Degrees (°)
```

### Flags (32-bit bitmap)
```
Bit  0-2   = L1, L2, L3 (fases)
Bit  3-5   = -> (L1, L2, L3) - saída
Bit  6-8   = <- (L1, L2, L3) - entrada
Bit  9-10  = CAP, IND (capacitivo, indutivo)
Bit  11-12 = ALT, MAN (alternativo, manual)
Bit  13-14 = RELAY_CLOSED, RELAY_OPEN (relé)
Bit  15    = COMMUNICATION
Bit  16    = LOW_BATTERY
Bit  17    = RTC_TEST
Bit  18    = DEM (demanda)
Bit  19    = BLOCKING_HAND
Bit  20-25 = ALARM_1 a ALARM_6
Bit  26    = ALARM_EXCLAMATION
Bit  27-30 = ARROW_1 a ARROW_5 (DST, COV, TER, NIC, RESERVED)
Bit  31    = ARROW_5 (reserved)
```

### Flags2 (32-bit bitmap)
```
Bit  0-3   = DATA_DECIMAL_1 a DATA_DECIMAL_4
Bit  4-5   = DATA_DECIMAL_2_UPPER, DATA_DECIMAL_4_UPPER
Bit  6-10  = OBIS_DECIMAL_1 a OBIS_DECIMAL_5
Bit  11+   = RESERVED
```

## Uso Básico

### Instalação
```bash
# Não há dependências externas, apenas Python 3.6+
python3 zeus_display_parser.py
```

### Exemplo 1: Usando dados manuais

```python
from zeus_display_parser import DisplayBuffer, SignalStrength, NICType, Unit

# Cria um DisplayBuffer com dados de teste
display = DisplayBuffer(
    obis="1.0.0.9.255",
    data="12,345",
    tariff_num=1,
    nic_signal_strength=SignalStrength.SIGNAL_3,
    nic_type=NICType.NIC_PLC,
    quadrant=0x02,
    unit=Unit.KWH,
    flags=0x0600000003,
    flags2=0x0600000003,
)

# Imprime a interpretação
print(display)

# Acessa campos individuais
print(f"OBIS: {display.obis}")
print(f"Sinal: {display.get_signal_strength_text()}")
print(f"Tipo NIC: {display.get_nic_type_text()}")
print(f"Unidade: {display.get_unit_text()}")

# Lista flags ativas
for bit, name in display.get_active_flags():
    print(f"Flag {bit}: {name}")
```

### Exemplo 2: Fazendo parse de um frame DLMS

```python
from zeus_display_parser import DLMSDisplayParser

# Frame DLMS bruto (exemplo do PDF)
frame_hex = "02 08 0A 06 20 20 20 20 20 20 0A 08 20 20 46 41 43 20 20 20 11 00 16 00 16 00 16 00 06 00 00 00 00 06 00 00 00 00"
frame_bytes = bytes.fromhex(frame_hex.replace(" ", ""))

# Faz parse
parser = DLMSDisplayParser()
display_buffer = parser.parse(frame_bytes, verbose=False)

if display_buffer:
    print(display_buffer)
    
    # Acessa dados específicos
    print(f"OBIS: {display_buffer.obis}")
    print(f"Data: {display_buffer.data}")
    print(f"Tariff: {display_buffer.tariff_num}")
```

### Exemplo 3: Factory helper

```python
from zeus_display_parser import parse_from_dict

display = parse_from_dict(
    obis="1.0.0.9.255",
    data="50.25",
    unit=0x05,  # kWh
    flags=0x0600000003,
)

print(display)
```

## Estrutura DLMS Esperada

O parser espera um frame DLMS com a seguinte estrutura:

```
Byte 0      = 0x02 (Structure tag)
Byte 1      = 0x08 (Number of elements = 8)
Bytes 2-N   = Elementos da estrutura

Cada elemento segue o formato DLMS com tag de tipo:
  0x09 ou 0x0A = visible-string/octet-string
  0x05         = unsigned
  0x06         = enum
  0x07         = double-long-unsigned
```

### Exemplo de parse estruturado (do PDF):

```
02 08              Structure com 8 elementos
0A 06 ... ...      visible-string[6] - OBIS (tag 0x0A, length 6)
0A 08 ... ... ...  visible-string[8] - Data (tag 0x0A, length 8)
11 00              unsigned - Tariff (tag 0x11, value 0x00)
16 00              enum - Signal (tag 0x16, value 0x00)
16 00              enum - NIC Type (tag 0x16, value 0x00)
16 00              enum - Quadrant (tag 0x16, value 0x00)
16 00              enum - Unit (tag 0x16, value 0x00)
06 00 00 00 00     double-long-unsigned - Flags
06 00 00 00 00     double-long-unsigned - Flags2
```

## Métodos Principais

### DisplayBuffer

```python
class DisplayBuffer:
    # Propiedades
    obis: str                    # Código OBIS
    data: str                    # Dados do display
    tariff_num: int              # Número da tarifa
    nic_signal_strength: int     # Força do sinal
    nic_type: int                # Tipo de NIC
    quadrant: int                # Quadrante
    unit: int                    # Unidade
    flags: int                   # Flags principais (32-bit)
    flags2: int                  # Flags secundárias (32-bit)
    
    # Métodos
    get_signal_strength_text() -> str      # Descrição legível do sinal
    get_nic_type_text() -> str             # Descrição legível do tipo NIC
    get_quadrant_text() -> str             # Descrição legível do quadrante
    get_unit_text() -> str                 # Descrição legível da unidade
    get_active_flags() -> list[tuple]      # Lista de (bit, nome) para flags ativas
    get_active_flags2() -> list[tuple]     # Lista de (bit, nome) para flags2 ativas
    __str__() -> str                       # Representação formatada
```

### DLMSDisplayParser

```python
class DLMSDisplayParser:
    @classmethod
    def parse(cls, raw_bytes: bytes, verbose: bool = False) -> Optional[DisplayBuffer]
        """Faz parse de um frame DLMS bruto"""
    
    @staticmethod
    def bytes_to_visible_string(data, length, offset) -> tuple[str, int]
        """Extrai visible-string"""
    
    @staticmethod
    def bytes_to_unsigned(data, offset) -> tuple[int, int]
        """Extrai unsigned"""
    
    @staticmethod
    def bytes_to_enum(data, offset) -> tuple[int, int]
        """Extrai enum"""
    
    @staticmethod
    def bytes_to_double_long_unsigned(data, offset) -> tuple[int, int]
        """Extrai double-long-unsigned (32-bit)"""
```

## Troubleshooting

### Parser retorna campos vazios

**Problema**: O frame pode estar em um formato diferente ou ter headers DLMS diferentes.

**Solução**: Use `verbose=True` no parse para debug detalhado:
```python
display = parser.parse(frame_bytes, verbose=True)
```

### Campos não são reconhecidos corretamente

**Problema**: Tags DLMS podem variar dependendo da implementação.

**Solução**: Use dados manuais ou parse_from_dict para inserir os dados diretamente:
```python
from zeus_display_parser import parse_from_dict

display = parse_from_dict(
    obis="1.0.0.9.255",
    data="12,345",
    tariff_num=0,
    unit=0x05,
)
```

## Referência

- **Especificação**: SMART METER ZEUS-NG FAMILY: Product Specification (Rev 2.6 - March 2023)
- **Identificação OBIS**: 1 |0.0.96.55.9.255
- **Padrão DLMS**: COSEM (Companion Specification for Energy Metering)

## Autor

Desenvolvido para Eletra Energy Solutions - QA/R&D Testing

## Licença

Documentação interna - Eletra Energy Solutions

## Arquivo de telas (telas.xml)

O mapa de telas (código → nome) vem do arquivo `telas.xml`, gerado a partir da tabela
oficial *Zeus NG Screens – Version 1* (387 itens). Para atualizar as telas basta editar
esse arquivo — **não é preciso mexer no código nem recompilar o executável**.

Estrutura de cada linha:

```xml
<tela doc="17" codigo="1.8.0" abnt="03" nome="Active_Direct_Energy_Total_Value"
      descricao="Energia ativa Total direta, mês atual"
      obis_completo="3-1.0.1.8.0.255-2" hex="0100010800FF"/>
```

- `codigo` (DLMS) e `abnt` viram **chaves de busca** da mesma tela; os demais atributos são informativos.
- `<telas modo="mesclar">` (padrão) mantém o mapa embutido no código e sobrescreve o que estiver no arquivo;
  `modo="substituir"` usa **somente** o arquivo.
- Código repetido dentro do arquivo: vale a **primeira** ocorrência (por isso as linhas de
  *Capture Time*, que repetem o código do valor, não sobrescrevem o valor).
- Também aceita JSON (`telas.json`): `{"1.8.0": "Nome", "03": "Nome"}`.

### Onde o arquivo é procurado

Nesta ordem: caminho passado em `--telas` → variável de ambiente `ZEUS_TELAS` →
`telas.xml`, `display_codes.xml`, `telas.json`, `display_codes.json` na pasta do script,
no bundle do PyInstaller, na pasta do `.exe` e no diretório atual.

**Se nenhum arquivo existir — ou se ele estiver corrompido — o parser continua funcionando
normalmente com o mapa embutido no código**, apenas exibindo um aviso.

### Comandos

```bash
python zeus_display_parser_v3.py --telas outro_arquivo.xml C4 01 C1 ...   # usa outro arquivo
python zeus_display_parser_v3.py --exportar-telas telas.xml               # gera o XML a partir do mapa atual
```

### Na API

```python
from zeus_display_parser_v3 import load_display_codes, get_screen_info, DISPLAY_CODES_SOURCE

load_display_codes("telas.xml", verbose=True)   # recarrega em runtime
get_screen_info("1.8.0")                        # {'descricao': ..., 'doc': '17', 'obis_completo': ..., 'hex': ...}
```

## Painel de configuração de tela

Depois de parsear o frame, o app mostra um painel que reformata o display sob outra
configuração — os campos de `Set_Display_Setup` (objeto DLMS `1|0.0.96.60.4.255`):

| Campo no painel | Campo da estrutura | Efeito |
|---|---|---|
| Família | — | energia (energia ativa/reativa e **UFER**) ou demanda (demanda acumulada, máxima, **DMCR**) |
| Casas inteiras | 1 / 3 `integer-places` | energia 5–8, demanda 4–8 |
| Casas decimais | 2 / 4 `decimal-places` | 0–3 (o LCD só tem 3 pontos) |
| Magnitude | 7 / 8 `unity` | k = 10³, M = 10⁶ |
| Primário / secundário | 10 `primary-secondary-type` | primário multiplica por TC × TP (campos RTC/RTP aparecem ao escolher) |
| Código exibido | 9 `obis-type` | alterna DLMS ↔ ABNT na linha superior; **não muda o valor** |
| Zeros à esquerda | 11 `use-left-zeros` | preenche até int + dec caracteres |

A conta usa aritmética inteira, na ordem certa (truncamento antes do módulo):

```
campo = (registrador × TC×TP × 10^dec) // escala      e depois     % 10^(int+dec)
```

**Restaurar do frame** volta todos os campos para a configuração detectada no frame.
O `DisplayBuffer` original nunca é alterado — `aplicar_setup()` devolve uma cópia.

### Limitações honestas

- O **registrador** é reconstruído a partir dos dígitos que o frame mostrou. Os dígitos
  que a virada de tela cortou (`mod`) e o que o truncamento descartou **não voltam** —
  por isso o campo é editável: se você souber o valor real, digite.
- O frame **não informa** `primary-secondary-type` nem os valores de TC/TP, então o
  padrão é secundário com TC × TP = 1.
- Telas não numéricas (data, hora, serial) mantêm o campo principal como veio; só
  magnitude e código são configuráveis.

### Validações (recusadas antes de virar configuração)

`decimais > 3` · `inteiros + decimais > 8` · `energia < 5 inteiros` · `demanda < 4 inteiros`.
Configuração inválida mostra o motivo e o display continua exibindo o frame original.

### Onde o painel existe

Nas **duas** interfaces, com a mesma lógica (`zeus_display_parser_v3.py`) por baixo:

- `app.py` — Streamlit (`streamlit run app.py` ou `python launcher.py`);
- `desktop_app.py` — pywebview, **é este que o `.exe` empacota**. Painel na coluna da direita.

Funcionalidade nova de UI precisa ser feita nos dois arquivos.

### Na API

```python
from zeus_display_parser_v3 import DisplaySetup, aplicar_setup, setup_do_frame, campo_do_display

setup = setup_do_frame(display)              # o que o frame aparenta usar
setup.magnitude, setup.integer_places = "M", 6
novo = aplicar_setup(display, setup)         # cópia reformatada, com .html novo
campo_do_display(99_999_900, familia="demanda", inteiros=4, decimais=2, magnitude="k")  # 999990
```
