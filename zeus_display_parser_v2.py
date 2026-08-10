#!/usr/bin/env python3
"""
Parser DLMS para Display Buffer (DISP.CMD.7) - ZEUS-NG Smart Meter
Segue a especificação: SMART METER ZEUS-NG FAMILY: Product Specification (Rev 2.6 - March 2023)
Identification: 1 |0.0.96.55.9.255
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from enum import IntEnum
from pathlib import Path
import sys


# AXDR tags used by ZEUS-NG DISP.CMD.7 according to the product spec.
AXDR_STRUCTURE = 0x02
AXDR_OCTET_STRING = 0x09
AXDR_VISIBLE_STRING = 0x0A
AXDR_DOUBLE_LONG_UNSIGNED = 0x06
AXDR_UNSIGNED = 0x11
AXDR_ENUM = 0x16


class SignalStrength(IntEnum):
    """Enumeração para nic_signal_strength"""
    SIGNAL_NONE = 0x00  # signal total off
    SIGNAL_0 = 0x01     # no bar, only antenna
    SIGNAL_1 = 0x02     # one bar
    SIGNAL_2 = 0x03     # two bars
    SIGNAL_3 = 0x04     # three bars
    SIGNAL_4 = 0x05     # four bars


class NICType(IntEnum):
    """Enumeração para nic_type"""
    NIC_NONE = 0x00
    NIC_RF = 0x01
    NIC_PLC = 0x02
    NIC_CELLULAR = 0x03


class Quadrant(IntEnum):
    """Enumeração para quadrant"""
    QUADRANT_NONE = 0x00     # no quadrant is displayed
    QUADRANT_0 = 0x01        # only the axis is displayed
    QUADRANT_1 = 0x02
    QUADRANT_2 = 0x03
    QUADRANT_3 = 0x04
    QUADRANT_4 = 0x05
    QUADRANT_ALL = 0x06      # all quadrants displayed


class Unit(IntEnum):
    """Enumeração para unit"""
    NO_UNIT = 0x00
    CELSIUS = 0x01
    HERTZ = 0x02
    PERCENTAGE = 0x03
    KW = 0x04
    KWH = 0x05
    MWH = 0x06
    KVAR = 0x07
    KVARH = 0x08
    MVARH = 0x09
    VOLT = 0x10
    AMPERE = 0x11
    VA = 0x12
    DEGREES = 0x13


class Flag(IntEnum):
    """Bits da flag principal (flags)"""
    L1 = 0
    L2 = 1
    L3 = 2
    L1_OUT = 3          # -> (L1)
    L2_OUT = 4          # -> (L2)
    L3_OUT = 5          # -> (L3)
    L1_IN = 6           # <- (L1)
    L2_IN = 7           # <- (L2)
    L3_IN = 8           # <- (L3)
    CAP = 9
    IND = 10
    ALT = 11
    MAN = 12
    RELAY_CLOSED = 13
    RELAY_OPEN = 14
    COMMUNICATION = 15
    LOW_BATTERY = 16
    RTC_TEST = 17
    DEM = 18
    BLOCKING_HAND = 19
    ALARM_1 = 20
    ALARM_2 = 21
    ALARM_3 = 22
    ALARM_4 = 23
    ALARM_5 = 24
    ALARM_6 = 25
    ALARM_EXCLAMATION = 26
    ARROW_1_DST = 27
    ARROW_2_COV = 28
    ARROW_3_TER = 29
    ARROW_4_NIC = 30
    ARROW_5_RESERVED = 31


class Flag2(IntEnum):
    """Bits da flag secundária (flags2)"""
    DATA_DECIMAL_1 = 0
    DATA_DECIMAL_2 = 1
    DATA_DECIMAL_3 = 2
    DATA_DECIMAL_4 = 3
    DATA_DECIMAL_2_UPPER = 4
    DATA_DECIMAL_4_UPPER = 5
    OBIS_DECIMAL_1 = 6
    OBIS_DECIMAL_2 = 7
    OBIS_DECIMAL_3 = 8
    OBIS_DECIMAL_4 = 9
    OBIS_DECIMAL_5 = 10


# Mapeamentos para interpretação amigável
SIGNAL_STRENGTH_MAP = {
    SignalStrength.SIGNAL_NONE: "Signal OFF",
    SignalStrength.SIGNAL_0: "No bar (antenna only)",
    SignalStrength.SIGNAL_1: "1 bar",
    SignalStrength.SIGNAL_2: "2 bars",
    SignalStrength.SIGNAL_3: "3 bars",
    SignalStrength.SIGNAL_4: "4 bars",
}

NIC_TYPE_MAP = {
    NICType.NIC_NONE: "None",
    NICType.NIC_RF: "RF",
    NICType.NIC_PLC: "PLC",
    NICType.NIC_CELLULAR: "Cellular",
}

QUADRANT_MAP = {
    Quadrant.QUADRANT_NONE: "No quadrant",
    Quadrant.QUADRANT_0: "Axis only",
    Quadrant.QUADRANT_1: "Quadrant 1",
    Quadrant.QUADRANT_2: "Quadrant 2",
    Quadrant.QUADRANT_3: "Quadrant 3",
    Quadrant.QUADRANT_4: "Quadrant 4",
    Quadrant.QUADRANT_ALL: "All quadrants",
}

UNIT_MAP = {
    Unit.NO_UNIT: "No unit",
    Unit.CELSIUS: "°C",
    Unit.HERTZ: "Hz",
    Unit.PERCENTAGE: "%",
    Unit.KW: "kW",
    Unit.KWH: "kWh",
    Unit.MWH: "MWh",
    Unit.KVAR: "kvar",
    Unit.KVARH: "kvarh",
    Unit.MVARH: "Mvarh",
    Unit.VOLT: "V",
    Unit.AMPERE: "A",
    Unit.VA: "VA",
    Unit.DEGREES: "°",
}

FLAG_NAMES = {
    Flag.L1: "L1",
    Flag.L2: "L2",
    Flag.L3: "L3",
    Flag.L1_OUT: "L1 Out",
    Flag.L2_OUT: "L2 Out",
    Flag.L3_OUT: "L3 Out",
    Flag.L1_IN: "L1 In",
    Flag.L2_IN: "L2 In",
    Flag.L3_IN: "L3 In",
    Flag.CAP: "Capacitive",
    Flag.IND: "Inductive",
    Flag.ALT: "Alternative",
    Flag.MAN: "Manual",
    Flag.RELAY_CLOSED: "Relay Closed",
    Flag.RELAY_OPEN: "Relay Open",
    Flag.COMMUNICATION: "Communication",
    Flag.LOW_BATTERY: "Low Battery",
    Flag.RTC_TEST: "RTC Test",
    Flag.DEM: "Demand",
    Flag.BLOCKING_HAND: "Blocking Hand",
    Flag.ALARM_1: "Alarm 1",
    Flag.ALARM_2: "Alarm 2",
    Flag.ALARM_3: "Alarm 3",
    Flag.ALARM_4: "Alarm 4",
    Flag.ALARM_5: "Alarm 5",
    Flag.ALARM_6: "Alarm 6",
    Flag.ALARM_EXCLAMATION: "Alarm Exclamation",
    Flag.ARROW_1_DST: "Arrow DST",
    Flag.ARROW_2_COV: "Arrow COV",
    Flag.ARROW_3_TER: "Arrow TER",
    Flag.ARROW_4_NIC: "Arrow NIC",
    Flag.ARROW_5_RESERVED: "Arrow Reserved",
}

FLAG2_NAMES = {
    Flag2.DATA_DECIMAL_1: "Data Decimal 1",
    Flag2.DATA_DECIMAL_2: "Data Decimal 2",
    Flag2.DATA_DECIMAL_3: "Data Decimal 3",
    Flag2.DATA_DECIMAL_4: "Data Decimal 4",
    Flag2.DATA_DECIMAL_2_UPPER: "Data Decimal 2 Upper",
    Flag2.DATA_DECIMAL_4_UPPER: "Data Decimal 4 Upper",
    Flag2.OBIS_DECIMAL_1: "OBIS Decimal 1",
    Flag2.OBIS_DECIMAL_2: "OBIS Decimal 2",
    Flag2.OBIS_DECIMAL_3: "OBIS Decimal 3",
    Flag2.OBIS_DECIMAL_4: "OBIS Decimal 4",
    Flag2.OBIS_DECIMAL_5: "OBIS Decimal 5",
}


@dataclass
class DisplayBuffer:
    """Estrutura de dados do Display Buffer"""
    obis: str                       # visible-string[6]
    data: str                       # visible-string[8]
    tariff_num: int                 # unsigned
    nic_signal_strength: int        # enum
    nic_type: int                   # enum
    quadrant: int                   # enum
    unit: int                       # enum
    flags: int                      # double-long-unsigned (32-bit)
    flags2: int                     # double-long-unsigned (32-bit)
    warnings: List[str] = field(default_factory=list)  # bytes/valores fora do esperado (possível erro do medidor)
    char_details: List[str] = field(default_factory=list)  # desenho de 7 segmentos de cada caractere de OBIS/Data
    html: str = ""  # pagina HTML com o display desenhado (7 segmentos) nas posicoes corretas
    unit_bits: int = 0  # bits crus de magnitude (payload[16..17]): unidade e MODULAR (k/M + V/W/A/r + h)

    def get_signal_strength_text(self) -> str:
        """Retorna descrição legível do sinal NIC"""
        try:
            return SIGNAL_STRENGTH_MAP.get(
                self.nic_signal_strength,
                f"Unknown ({self.nic_signal_strength:#x})"
            )
        except:
            return "Unknown"

    def get_nic_type_text(self) -> str:
        """Retorna descrição legível do tipo NIC"""
        try:
            return NIC_TYPE_MAP.get(self.nic_type, f"Unknown ({self.nic_type:#x})")
        except:
            return "Unknown"

    def get_quadrant_text(self) -> str:
        """Retorna descrição legível do quadrante"""
        try:
            return QUADRANT_MAP.get(self.quadrant, f"Unknown ({self.quadrant:#x})")
        except:
            return "Unknown"

    def get_unit_text(self) -> str:
        """Retorna descrição legível da unidade"""
        try:
            return UNIT_MAP.get(self.unit, f"Unknown ({self.unit:#x})")
        except:
            return "Unknown"

    def get_active_flags(self) -> list:
        """Retorna lista de flags ativas"""
        active = []
        for i in range(32):
            if (self.flags >> i) & 1:
                flag_name = FLAG_NAMES.get(i, f"Reserved Bit {i}")
                active.append((i, flag_name))
        return active

    def get_active_flags2(self) -> list:
        """Retorna lista de flags2 ativas"""
        active = []
        for i in range(11):
            if (self.flags2 >> i) & 1:
                flag_name = FLAG2_NAMES.get(i, f"Reserved Bit {i}")
                active.append((i, flag_name))
        return active

    def __str__(self) -> str:
        """Retorna representação legível do Display Buffer"""
        output = []
        output.append("=" * 70)
        output.append("DISPLAY BUFFER (DISP.CMD.7) - ZEUS-NG SMART METER")
        output.append("STATUS: PARSE CONCLUIDO COM SUCESSO (alertas abaixo sao apenas informativos)")
        output.append("=" * 70)
        output.append(f"\nOBIS Code:              {self.obis}")
        output.append(f"Display Data:           {self.data}")
        output.append(f"Tariff Number:          {self.tariff_num}")
        output.append(f"\nNIC Signal Strength:    {self.get_signal_strength_text()} ({self.nic_signal_strength:#x})")
        output.append(f"NIC Type:               {self.get_nic_type_text()} ({self.nic_type:#x})")
        output.append(f"Quadrant:               {self.get_quadrant_text()} ({self.quadrant:#x})")
        output.append(f"Unit:                   {self.get_unit_text()} ({self.unit:#x})")
        output.append(f"\nFlags (0x{self.flags:08X}):")
        
        active_flags = self.get_active_flags()
        if active_flags:
            for bit, name in active_flags:
                output.append(f"  - Bit {bit:2d}: {name}")
        else:
            output.append("  (No flags set)")

        output.append(f"\nFlags2 (0x{self.flags2:08X}):")
        active_flags2 = self.get_active_flags2()
        if active_flags2:
            for bit, name in active_flags2:
                output.append(f"  - Bit {bit:2d}: {name}")
        else:
            output.append("  (No flags2 set)")

        if self.char_details:
            output.append("\n" + "-" * 70)
            output.append("DESENHO DE CADA CARACTERE (OBIS + DATA)")
            output.append("-" * 70)
            for block in self.char_details:
                output.append(block)
                output.append("")

        if self.warnings:
            output.append("\n" + "!" * 70)
            output.append("⚠ ALERTA: BYTES INESPERADOS RECEBIDOS DO MEDIDOR")
            output.append("!" * 70)
            output.append(
                "Os itens abaixo NAO correspondem a nenhum valor valido conhecido.\n"
                "Isso indica que o proprio medidor enviou um byte incorreto/fora do\n"
                "padrao esperado (nao e um problema do parser)."
            )
            for w in self.warnings:
                output.append(f"  - {w}")

        output.append("=" * 70)
        return "\n".join(output)


class DLMSDisplayParser:
    """Parser DLMS para Display Buffer"""

    # Mapping do display de 7 segmentos (mesmo usado no parser C# do projeto).
    _LCD_NUMBER_MAP = {
        0x3F: "0",
        0x06: "1",
        0x5B: "2",
        0x4F: "3",
        0x66: "4",
        0x6D: "5",
        0x7D: "6",
        0x07: "7",
        0x7F: "8",
        0x6F: "9",
        0x00: " ",
        0x40: "-",
        0x7C: "b",
        0x71: "F",
        0x5C: "o",
        0x77: "A",
        0x39: "C",
        0x5E: "d",
        0x3E: "U",
        0x50: "r",
        0x78: "t",
        0x79: "E",
        0x54: "n",
        0x04: "I",
        0x38: "L",
        0x73: "P",
        0x2D: "S",
        0x76: "H",
        0x58: "c",
    }

    @staticmethod
    def _read_axdr_length(data: bytes, offset: int) -> Tuple[int, int]:
        """Lê comprimento AXDR em formato curto ou longo."""
        if offset >= len(data):
            raise ValueError("Offset fora do buffer ao ler comprimento AXDR")

        first = data[offset]
        offset += 1

        # Short form: bit 7 = 0
        if first < 0x80:
            return first, offset

        # Long form: lower 7 bits informam quantos bytes compõem o length.
        count = first & 0x7F
        if count == 0:
            raise ValueError("Comprimento AXDR indefinido nao suportado")
        if offset + count > len(data):
            raise ValueError("Comprimento AXDR invalido")

        value = int.from_bytes(data[offset:offset + count], byteorder='big', signed=False)
        offset += count
        return value, offset

    @classmethod
    def _unwrap_get_response_data(cls, raw_bytes: bytes) -> bytes:
        """Extrai o conteúdo de um GET-Response normal com Data-Result (C4 ...)."""
        if len(raw_bytes) < 6 or raw_bytes[0] != 0xC4:
            return raw_bytes

        # C4 <choice> <invoke-id-priority> <result>
        # Para Data-Result, result costuma ser 0x00 e em seguida vem o Data tag.
        data_tag_index = 4
        if raw_bytes[3] == 0x00:
            data_tag_index = 4
        else:
            # Em variações de stack, já pode vir direto após invoke-id.
            data_tag_index = 3

        if data_tag_index >= len(raw_bytes):
            return raw_bytes

        data_tag = raw_bytes[data_tag_index]
        if data_tag not in (AXDR_OCTET_STRING, AXDR_VISIBLE_STRING):
            return raw_bytes

        try:
            length, content_offset = cls._read_axdr_length(raw_bytes, data_tag_index + 1)
        except ValueError:
            return raw_bytes

        end = content_offset + length
        if end > len(raw_bytes):
            return raw_bytes

        return raw_bytes[content_offset:end]

    @classmethod
    def _unwrap_single_axdr_string(cls, data: bytes) -> bytes:
        """Se buffer inteiro for um único 09/0A len data, retorna apenas o conteúdo."""
        if len(data) < 2 or data[0] not in (AXDR_OCTET_STRING, AXDR_VISIBLE_STRING):
            return data

        try:
            length, content_offset = cls._read_axdr_length(data, 1)
        except ValueError:
            return data

        end = content_offset + length
        if end != len(data):
            return data

        return data[content_offset:end]

    @staticmethod
    def _bit(value: int, bit: int) -> int:
        return (value >> bit) & 0x01

    @classmethod
    def _lcd_char(cls, value: int, position: int, field_name: str, warnings: List[str]) -> str:
        """Converte byte de segmento LCD em caractere. Registra alerta se o byte
        nao corresponder a nenhum caractere/digito conhecido (indica que o
        medidor enviou um segmento LCD invalido)."""
        key = value & 0xFF
        char = cls._LCD_NUMBER_MAP.get(key)
        if char is None:
            warnings.append(
                f"Campo '{field_name}' (payload[{position}] = 0x{key:02X}): padrao de "
                f"segmento LCD desconhecido. O medidor enviou um byte que nao existe "
                f"na tabela de caracteres do display."
            )
            return "?"
        return char

    # Layout do display de 7 segmentos, no mesmo formato usado no guia:
    #      _a_
    #    f|   |b
    #     |_g_|
    #    e|   |c
    #     |_d_|
    # Cada tupla (linha, coluna) diz onde a letra do segmento fica dentro do
    # "desenho" abaixo, para podermos apagar (trocar por '.') o que estiver
    # desligado.
    _SEGMENT_DIAGRAM_TEMPLATE = (
        " _a_",
        "f|   |b",
        " |_g_|",
        "e|   |c",
        " |_d_|",
    )
    _SEGMENT_POSITIONS = {
        "a": (0, 2),
        "b": (1, 6),
        "c": (3, 6),
        "d": (4, 3),
        "e": (3, 0),
        "f": (1, 0),
        "g": (2, 3),
    }
    _SEGMENT_BIT = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6}

    @classmethod
    def render_segment_diagram(cls, value: int, off_char: str = ".") -> str:
        """Desenha o display de 7 segmentos mostrando quais letras (a-g) estao
        acesas para o byte informado. Segmentos apagados aparecem como '.'.
        """
        key = value & 0xFF
        rows = [list(row) for row in cls._SEGMENT_DIAGRAM_TEMPLATE]
        for seg, (row, col) in cls._SEGMENT_POSITIONS.items():
            bit = cls._SEGMENT_BIT[seg]
            is_on = ((key >> bit) & 1) == 1
            rows[row][col] = seg if is_on else off_char
        return "\n".join("".join(row) for row in rows)

    @classmethod
    def describe_lcd_byte(cls, value: int) -> str:
        """Retorna hex/decimal/bits, o desenho de 7 segmentos e o caractere
        reconhecido (ou alerta se o byte nao existir na tabela)."""
        key = value & 0xFF
        char = cls._LCD_NUMBER_MAP.get(key)
        bits_msb_first = format(key, "08b")

        lines = []
        lines.append(f"Byte: 0x{key:02X}  ({key} decimal)  =  {bits_msb_first} (bit7..bit0)")
        lines.append("")
        lines.append(cls.render_segment_diagram(key))
        lines.append("")
        if char is not None:
            lines.append(f"Caractere reconhecido: '{char}'")
        else:
            lines.append(
                "\u26a0 ALERTA: nenhum caractere conhecido corresponde a este byte "
                "(padrao de segmento invalido)."
            )
        return "\n".join(lines)

    @classmethod
    def _char_detail_block(cls, field_name: str, position: int, value: int) -> str:
        """Bloco compacto (usado no parse do frame completo) com o desenho de 7
        segmentos de UM caractere de OBIS/Data, igual ao modo --byte."""
        key = value & 0xFF
        char = cls._LCD_NUMBER_MAP.get(key)
        diagram = cls.render_segment_diagram(key)
        label = f"'{char}'" if char is not None else "??? (sem caractere correspondente)"
        header = f"[{field_name} pos{position}] byte=0x{key:02X}"
        return f"{header}\n{diagram}\n=> {label}"

    # ------------------------------------------------------------------
    # Geracao de HTML: desenha o display de 7 segmentos (OBIS + Data) nas
    # posicoes corretas (mesma ordem visual esquerda->direita usada no parse),
    # junto com badges para as flags e um resumo dos demais campos.
    # ------------------------------------------------------------------
    _HTML_CSS = """
        body { background:#cfd2d6; font-family: Arial, Helvetica, sans-serif; padding:24px; color:#222; }
        h2 { margin-top:0; color:#333; }
        .lcd-panel { background:#eef0ea; border:10px solid #3a3f44; border-radius:8px;
                     padding:22px 26px; display:inline-block; box-shadow:0 6px 20px rgba(0,0,0,.4); }
        .top-row { display:flex; align-items:center; gap:12px; margin-bottom:16px; }
        .row { display:flex; align-items:flex-end; }
        .digit { position:relative; margin:0 2px; }
        .digit.sm { width:26px; height:44px; }
        .digit.md { width:36px; height:62px; }
        .digit.lg { width:46px; height:80px; }
        .seg { position:absolute; background:#d3d5cd; border-radius:1px; }
        .seg.on { background:#161616; }
        .digit.sm .seg-a { top:0;    left:3px;  width:20px; height:5px; }
        .digit.sm .seg-b { top:3px;  left:21px; width:5px;  height:18px; }
        .digit.sm .seg-c { top:23px; left:21px; width:5px;  height:18px; }
        .digit.sm .seg-d { top:39px; left:3px;  width:20px; height:5px; }
        .digit.sm .seg-e { top:23px; left:0;    width:5px;  height:18px; }
        .digit.sm .seg-f { top:3px;  left:0;    width:5px;  height:18px; }
        .digit.sm .seg-g { top:20px; left:3px;  width:20px; height:5px; }
        .digit.md .seg-a { top:0;    left:5px;  width:26px; height:6px; }
        .digit.md .seg-b { top:5px;  left:30px; width:6px;  height:24px; }
        .digit.md .seg-c { top:32px; left:30px; width:6px;  height:24px; }
        .digit.md .seg-d { top:56px; left:5px;  width:26px; height:6px; }
        .digit.md .seg-e { top:32px; left:0;    width:6px;  height:24px; }
        .digit.md .seg-f { top:5px;  left:0;    width:6px;  height:24px; }
        .digit.md .seg-g { top:28px; left:5px;  width:26px; height:6px; }
        .digit.lg .seg-a { top:0;    left:6px;  width:34px; height:8px; }
        .digit.lg .seg-b { top:6px;  left:38px; width:8px;  height:32px; }
        .digit.lg .seg-c { top:42px; left:38px; width:8px;  height:32px; }
        .digit.lg .seg-d { top:72px; left:6px;  width:34px; height:8px; }
        .digit.lg .seg-e { top:42px; left:0;    width:8px;  height:32px; }
        .digit.lg .seg-f { top:6px;  left:0;    width:8px;  height:32px; }
        .digit.lg .seg-g { top:36px; left:6px;  width:34px; height:8px; }
        .sep { position:relative; align-self:flex-end; }
        .sep.sm { width:8px; height:44px; }
        .sep.md { width:9px; height:62px; }
        .sep.lg { width:10px; height:80px; }
        .sep-dot { position:absolute; left:1px; width:6px; height:6px; border-radius:50%;
                   background:#d3d5cd; }
        .sep-dot.on { background:#161616; }

        .phase-col { display:flex; flex-direction:column; gap:4px; margin-right:6px; }
        .phase { display:flex; align-items:center; gap:4px; font:bold 12px Arial; color:#c7c9c2; }
        .phase.on { color:#161616; }
        .phase-arrow { width:0; height:0; border-top:4px solid transparent; border-bottom:4px solid transparent; }
        .phase-arrow.right { border-left:6px solid #dcded8; }
        .phase-arrow.right.on { border-left-color:#161616; }
        .phase-arrow.left { border-right:6px solid #dcded8; }
        .phase-arrow.left.on { border-right-color:#161616; }

        .tariff-label { font:bold 22px Arial; color:#c7c9c2; margin:0 4px; }
        .tariff-label.on { color:#161616; }

        .antenna { display:flex; flex-direction:column; align-items:center; font:bold 10px Arial; color:#c7c9c2; }
        .antenna span.on { color:#161616; }
        .antenna-bars { display:flex; align-items:flex-end; gap:2px; height:18px; margin-bottom:2px; }
        .antenna-bar { width:4px; background:#d3d5cd; }
        .antenna-bar.on { background:#161616; }
        .antenna-bar:nth-child(1){ height:30%; }
        .antenna-bar:nth-child(2){ height:55%; }
        .antenna-bar:nth-child(3){ height:80%; }
        .antenna-bar:nth-child(4){ height:100%; }

        .relay-icon { display:flex; align-items:center; }
        .relay-group { display:flex; align-items:center; gap:6px; }
        .relay-svg .relay-line, .relay-svg .relay-blade { stroke:#d3d5cd; stroke-width:2.2; fill:none; stroke-linecap:round; }
        .relay-svg .relay-dot { fill:#d3d5cd; }
        .relay-icon.on .relay-svg .relay-line,
        .relay-icon.on .relay-svg .relay-blade { stroke:#161616; }
        .relay-icon.on .relay-svg .relay-dot { fill:#161616; }

        .quad-icon { width:26px; height:26px; border-radius:50%; border:2px solid #b9bcb4; position:relative; overflow:hidden; }
        .quad-q { position:absolute; width:50%; height:50%; background:#eef0ea; }
        .quad-q.on { background:#161616; }
        .quad-q.q1 { top:0; right:0; }
        .quad-q.q2 { top:0; left:0; }
        .quad-q.q3 { bottom:0; left:0; }
        .quad-q.q4 { bottom:0; right:0; }

        .unit-col { display:flex; flex-direction:column; justify-content:center; gap:6px;
                    font:bold 16px Arial; color:#c7c9c2; margin-left:14px; }
        .unit-col span.on, .unit-col div.on { color:#161616; }
        .unit-modular { font:bold 15px Arial; letter-spacing:1px; }

        .bottom-icons { display:flex; align-items:center; gap:16px; margin-top:18px; }
        .tri-row { display:flex; gap:12px; align-items:flex-end; }
        .tri { width:0; height:0; border-left:7px solid transparent; border-right:7px solid transparent;
               border-top:10px solid #d3d5cd; }
        .tri.on { border-top-color:#161616; }

        .alarm-icon { display:flex; flex-direction:column; align-items:center; gap:2px; }
        .alarm-tri-svg .alarm-tri-shape { fill:none; stroke:#d3d5cd; stroke-width:1.6; stroke-linejoin:round; }
        .alarm-tri-svg .alarm-tri-mark { fill:#d3d5cd; }
        .alarm-tri.on .alarm-tri-svg .alarm-tri-shape { stroke:#161616; }
        .alarm-tri.on .alarm-tri-svg .alarm-tri-mark { fill:#161616; }
        .alarm-grid { display:grid; grid-template-columns:repeat(3, 9px); gap:1px; font:bold 8px Arial; color:#c7c9c2; text-align:center; }
        .alarm-grid div.on { color:#161616; }

        .cap-ind-col { display:flex; flex-direction:column; gap:2px; font:bold 10px Arial;
                       color:#c7c9c2; margin-top:8px; text-align:center; }
        .cap-ind-col span.on { color:#161616; }

        .block-icon { width:22px; height:22px; border-radius:50%; border:2px solid #d3d5cd; position:relative; }
        .block-icon.on { border-color:#161616; }
        .block-icon::after { content:""; position:absolute; top:50%; left:-2px; right:-2px; height:2px;
                              background:#d3d5cd; transform:rotate(45deg); }
        .block-icon.on::after { background:#161616; }

        .dem-label { font:bold 13px Arial; color:#c7c9c2; }
        .dem-label.on { color:#161616; }

        .clock-icon { width:22px; height:22px; border-radius:50%; border:2px solid #d3d5cd; position:relative; }
        .clock-icon.on { border-color:#161616; }
        .clock-icon .hand { position:absolute; background:#d3d5cd; }
        .clock-icon.on .hand { background:#161616; }
        .clock-icon .hand.h1 { width:2px; height:7px; top:4px; left:9px; }
        .clock-icon .hand.h2 { width:6px; height:2px; top:9px; left:10px; }

        .battery-icon { width:26px; height:14px; border:2px solid #d3d5cd; border-radius:2px; position:relative; }
        .battery-icon.on { border-color:#161616; background:#161616; }
        .battery-icon::after { content:""; position:absolute; top:3px; right:-5px; width:3px; height:6px;
                                background:#d3d5cd; }
        .battery-icon.on::after { background:#161616; }

        .push-icon { width:20px; height:16px; border:2px solid #d3d5cd; position:relative; color:#d3d5cd;
                     font:bold 12px Arial; display:flex; align-items:center; justify-content:center; }
        .push-icon.on { border-color:#161616; color:#161616; }

        .badges { display:flex; flex-wrap:wrap; gap:6px; margin-top:20px; max-width:640px; }
        .badge { padding:4px 10px; border-radius:12px; font:12px monospace; background:#dfe1db;
                 color:#8a8d86; border:1px solid #c7c9c2; }
        .badge.on { background:#2e5e33; color:#d8ffd9; border-color:#1f4523; }
        .meta { font:13px monospace; color:#333; margin-top:14px; line-height:1.6; }
        .warn { margin-top:16px; padding:10px 14px; background:#fff2f0; border:1px solid #e6a29c;
                color:#9c2b1f; font:12px monospace; border-radius:8px; max-width:640px; }
    """

    @classmethod
    def _digit_html(cls, byte_value: int, size: str) -> str:
        key = byte_value & 0xFF
        segs = []
        for seg_name, bit in cls._SEGMENT_BIT.items():
            is_on = ((key >> bit) & 1) == 1
            css_class = f"seg seg-{seg_name}" + (" on" if is_on else "")
            segs.append(f'<div class="{css_class}"></div>')
        return f'<div class="digit {size}">{"".join(segs)}</div>'

    @classmethod
    def _sep_html(cls, kind: str, size: str) -> str:
        """kind: '' (nada), '.' (um ponto) ou ':' (dois pontos, tipo dois-pontos)."""
        if kind == ":":
            dots = (
                '<div class="sep-dot on" style="top:32%;"></div>'
                '<div class="sep-dot on" style="top:58%;"></div>'
            )
        elif kind == ".":
            dots = '<div class="sep-dot on" style="bottom:4px; top:auto;"></div>'
        else:
            dots = ""
        return f'<div class="sep {size}">{dots}</div>'

    @staticmethod
    def _render_badges_html(display: "DisplayBuffer") -> str:
        badge_defs = [
            ("L1", display.flags & (1 << 0)),
            ("L2", display.flags & (1 << 1)),
            ("L3", display.flags & (1 << 2)),
            ("CAP", display.flags & (1 << 9)),
            ("IND", display.flags & (1 << 10)),
            ("ALT", display.flags & (1 << 11)),
            ("MAN", display.flags & (1 << 12)),
            ("Relay Closed", display.flags & (1 << 13)),
            ("Relay Open", display.flags & (1 << 14)),
            ("Comm", display.flags & (1 << 15)),
            ("Low Batt", display.flags & (1 << 16)),
            ("RTC Test", display.flags & (1 << 17)),
            ("Alarm 1", display.flags & (1 << 20)),
            ("Alarm 2", display.flags & (1 << 21)),
            ("Alarm 3", display.flags & (1 << 22)),
            ("Alarm 4", display.flags & (1 << 23)),
            ("Alarm 5", display.flags & (1 << 24)),
            ("Alarm 6", display.flags & (1 << 25)),
            ("!", display.flags & (1 << 26)),
        ]
        return "".join(
            f'<div class="badge{" on" if val else ""}">{name}</div>' for name, val in badge_defs
        )

    @staticmethod
    def _render_meta_html(display: "DisplayBuffer") -> str:
        return (
            '<div class="meta">'
            f"OBIS: {display.obis or '(vazio)'}<br>"
            f"Data: {display.data or '(vazio)'}<br>"
            f"Tariff: {display.tariff_num}<br>"
            f"Quadrant: {display.get_quadrant_text()}<br>"
            f"Signal: {display.get_signal_strength_text()}<br>"
            f"NIC Type: {display.get_nic_type_text()}<br>"
            f"Unit: {display.get_unit_text()}"
            "</div>"
        )

    @staticmethod
    def _render_warnings_html(display: "DisplayBuffer") -> str:
        if not display.warnings:
            return ""
        items = "".join(f"<div>- {w}</div>" for w in display.warnings)
        return f'<div class="warn"><b>\u26a0 ALERTA: bytes fora do esperado</b>{items}</div>'

    # -- Icones do painel, no estilo do vidro de LCD da foto de referencia --

    @classmethod
    def _phase_col_html(cls, display: "DisplayBuffer") -> str:
        def phase_row(label: str, present_bit: int, out_bit: int, in_bit: int) -> str:
            present_on = bool(display.flags & (1 << present_bit))
            direct_on = bool(display.flags & (1 << out_bit))    # corrente direta (->)
            reverse_on = bool(display.flags & (1 << in_bit))    # corrente reversa (<-)

            label_css = "phase on" if present_on else "phase"
            reverse_css = "phase-arrow left" + (" on" if reverse_on else "")
            direct_css = "phase-arrow right" + (" on" if direct_on else "")

            return (
                f'<div class="{label_css}">'
                f'<div class="{reverse_css}" title="Corrente reversa {label}"></div>'
                f'<span>{label}</span>'
                f'<div class="{direct_css}" title="Corrente direta {label}"></div>'
                '</div>'
            )

        rows = phase_row("L1", 0, 3, 6) + phase_row("L2", 1, 4, 7) + phase_row("L3", 2, 5, 8)
        return f'<div class="phase-col">{rows}{cls._cap_ind_alt_man_html(display)}</div>'

    @staticmethod
    def _cap_ind_alt_man_html(display: "DisplayBuffer") -> str:
        cap_on = bool(display.flags & (1 << 9))
        ind_on = bool(display.flags & (1 << 10))
        alt_on = bool(display.flags & (1 << 11))
        man_on = bool(display.flags & (1 << 12))

        def span(text: str, on: bool) -> str:
            return f'<span class="{"on" if on else ""}">{text}</span>'

        return (
            '<div class="cap-ind-col">'
            f'<div>{span("CAP", cap_on)}</div>'
            f'<div>{span("IND", ind_on)}</div>'
            f'<div>{span("ALT", alt_on)} {span("MAN", man_on)}</div>'
            '</div>'
        )

    @staticmethod
    def _tariff_html(display: "DisplayBuffer") -> str:
        on = display.tariff_num > 0
        text = f"T{display.tariff_num}" if on else "T-"
        return f'<div class="tariff-label{" on" if on else ""}">{text}</div>'

    @staticmethod
    def _antenna_html(display: "DisplayBuffer") -> str:
        bars_lit = {
            int(SignalStrength.SIGNAL_NONE): 0,
            int(SignalStrength.SIGNAL_0): 0,
            int(SignalStrength.SIGNAL_1): 1,
            int(SignalStrength.SIGNAL_2): 2,
            int(SignalStrength.SIGNAL_3): 3,
            int(SignalStrength.SIGNAL_4): 4,
        }.get(display.nic_signal_strength, 0)
        bars_html = "".join(
            f'<div class="antenna-bar{" on" if i < bars_lit else ""}"></div>' for i in range(4)
        )
        is_rf = display.nic_type == int(NICType.NIC_RF)
        is_plc = display.nic_type == int(NICType.NIC_PLC)
        is_cell = display.nic_type == int(NICType.NIC_CELLULAR)
        top_label = (
            f'<span class="{"on" if is_rf else ""}">RF</span>/'
            f'<span class="{"on" if is_plc else ""}">PLC</span>'
        )
        bottom_label = f'<span class="{"on" if is_cell else ""}">CELL</span>'
        return (
            '<div class="antenna">'
            f'<div class="antenna-bars">{bars_html}</div>'
            f'<div>{top_label}</div>'
            f'<div>{bottom_label}</div>'
            '</div>'
        )

    @staticmethod
    def _relay_icon_svg(kind: str) -> str:
        if kind == "closed":
            # Lamina reta ligando os dois contatos (rele fechado).
            blades = (
                '<line x1="9" y1="3" x2="25" y2="3" class="relay-blade"/>'
            )
        else:
            # Lamina na diagonal, contato aberto (mesmo desenho da chave seccionadora da foto).
            blades = '<line x1="9" y1="0" x2="25" y2="6" class="relay-blade"/>'

        return (
            '<svg class="relay-svg" width="34" height="26" viewBox="0 0 34 26">'
            '<line x1="0" y1="6" x2="9" y2="6" class="relay-line"/>'
            '<circle cx="9" cy="6" r="2.4" class="relay-dot"/>'
            '<line x1="25" y1="6" x2="34" y2="6" class="relay-line"/>'
            '<circle cx="25" cy="6" r="2.4" class="relay-dot"/>'
            + blades +
            '</svg>'
        )

    @classmethod
    def _relay_html(cls, display: "DisplayBuffer") -> str:
        closed = bool(display.flags & (1 << 13))
        opened = bool(display.flags & (1 << 14))

        open_css = "on" if opened else ""
        closed_css = "on" if closed else ""

        return (
            '<div class="relay-group">'
            f'<div class="relay-icon {open_css}" title="Rele Aberto">{cls._relay_icon_svg("open")}</div>'
            f'<div class="relay-icon {closed_css}" title="Rele Fechado">{cls._relay_icon_svg("closed")}</div>'
            '</div>'
        )

    @staticmethod
    def _quadrant_icon_html(display: "DisplayBuffer") -> str:
        q = display.quadrant
        q1_on = q in (int(Quadrant.QUADRANT_1), int(Quadrant.QUADRANT_ALL))
        q2_on = q in (int(Quadrant.QUADRANT_2), int(Quadrant.QUADRANT_ALL))
        q3_on = q in (int(Quadrant.QUADRANT_3), int(Quadrant.QUADRANT_ALL))
        q4_on = q in (int(Quadrant.QUADRANT_4), int(Quadrant.QUADRANT_ALL))

        def q_div(css: str, on: bool) -> str:
            return f'<div class="quad-q {css}{" on" if on else ""}"></div>'

        return (
            '<div class="quad-icon" title="Quadrante">'
            + q_div("q1", q1_on) + q_div("q2", q2_on) + q_div("q3", q3_on) + q_div("q4", q4_on)
            + '</div>'
        )

    @staticmethod
    def _unit_bit_flags(display: "DisplayBuffer") -> dict:
        """A area de unidade do LCD e MODULAR: prefixos (k, M), base (V, W, A, r)
        e sufixo (h) sao glifos independentes que se combinam (kWh, MWh, kVArh,
        Ah, kVA, etc.). Usa os bits crus de payload[16..17] quando disponiveis
        (formato compacto); no formato AXDR (sem bits crus) aproxima a partir
        do enum Unit resolvido."""
        base = {
            "k": False, "M": False, "V": False, "W": False, "A": False,
            "r": False, "h": False, "Hz": False, "C": False, "pct": False,
        }
        bits = display.unit_bits
        if bits:
            base["k"] = bool(bits & (1 << 0))
            base["M"] = bool(bits & (1 << 1))
            base["V"] = bool(bits & (1 << 2))
            base["W"] = bool(bits & (1 << 3))
            base["A"] = bool(bits & (1 << 4))
            base["r"] = bool(bits & (1 << 5))
            base["h"] = bool(bits & (1 << 6))
            base["Hz"] = bool(bits & (1 << 10))
            base["C"] = bool(bits & (1 << 11))
            base["pct"] = bool(bits & (1 << 12))
            return base

        fallback = {
            int(Unit.CELSIUS): {"C": True},
            int(Unit.HERTZ): {"Hz": True},
            int(Unit.PERCENTAGE): {"pct": True},
            int(Unit.KW): {"k": True, "W": True},
            int(Unit.KWH): {"k": True, "W": True, "h": True},
            int(Unit.MWH): {"M": True, "W": True, "h": True},
            int(Unit.KVAR): {"k": True, "V": True, "A": True, "r": True},
            int(Unit.KVARH): {"k": True, "V": True, "A": True, "r": True, "h": True},
            int(Unit.MVARH): {"M": True, "V": True, "A": True, "r": True, "h": True},
            int(Unit.VOLT): {"V": True},
            int(Unit.AMPERE): {"A": True},
            int(Unit.VA): {"V": True, "A": True},
            int(Unit.DEGREES): {"C": True},
        }
        base.update(fallback.get(display.unit, {}))
        return base

    @classmethod
    def _units_col_html(cls, display: "DisplayBuffer") -> str:
        f = cls._unit_bit_flags(display)

        def span(key: str, text: str) -> str:
            return f'<span class="{"on" if f[key] else ""}">{text}</span>'

        return (
            '<div class="unit-col">'
            f'<div>{span("C", "\u00b0C")}</div>'
            f'<div>{span("Hz", "Hz")} {span("pct", "%")}</div>'
            '<div class="unit-modular">'
            f'{span("M", "M")}{span("k", "k")} '
            f'{span("V", "V")}{span("W", "W")}{span("A", "A")}{span("r", "r")} '
            f'{span("h", "h")}'
            '</div>'
            '</div>'
        )

    @staticmethod
    def _arrow_triangles_html(display: "DisplayBuffer") -> str:
        bits = [27, 28, 29, 30, 31]
        tris = "".join(
            f'<div class="tri{" on" if display.flags & (1 << b) else ""}"></div>' for b in bits
        )
        return f'<div class="tri-row" title="Setas 1-5">{tris}</div>'

    @staticmethod
    def _alarm_icon_html(display: "DisplayBuffer") -> str:
        excl_on = bool(display.flags & (1 << 26))
        nums = []
        for i, bit in enumerate([20, 21, 22, 23, 24, 25], start=1):
            on = bool(display.flags & (1 << bit))
            nums.append(f'<div class="{"on" if on else ""}">{i}</div>')
        triangle_svg = (
            '<svg class="alarm-tri-svg" width="20" height="18" viewBox="0 0 20 18">'
            '<polygon points="10,1 19,16 1,16" class="alarm-tri-shape"/>'
            '<rect x="9" y="6" width="2" height="6" class="alarm-tri-mark"/>'
            '<rect x="9" y="13" width="2" height="2" class="alarm-tri-mark"/>'
            '</svg>'
        )
        return (
            '<div class="alarm-icon" title="Alarmes 1-6">'
            f'<div class="alarm-tri{" on" if excl_on else ""}">{triangle_svg}</div>'
            f'<div class="alarm-grid">{"".join(nums)}</div>'
            '</div>'
        )

    @staticmethod
    def _block_icon_html(display: "DisplayBuffer") -> str:
        # Flag.BLOCKING_HAND (bit19) = Billing_Protection (payload[28] bit0) no parser C#.
        on = bool(display.flags & (1 << 19))
        return f'<div class="block-icon{" on" if on else ""}" title="Protecao de faturamento"></div>'

    @staticmethod
    def _dem_label_html() -> str:
        # Nao ha bit conhecido para "DEM" neste formato compacto; mostrado sempre apagado.
        return '<div class="dem-label" title="Nao mapeado neste formato de frame">DEM</div>'

    @staticmethod
    def _clock_icon_html(display: "DisplayBuffer") -> str:
        on = bool(display.flags & (1 << 17))  # RTC_TEST
        css = "clock-icon" + (" on" if on else "")
        return f'<div class="{css}" title="Teste RTC"><div class="hand h1"></div><div class="hand h2"></div></div>'

    @staticmethod
    def _battery_icon_html(display: "DisplayBuffer") -> str:
        on = bool(display.flags & (1 << 16))  # LOW_BATTERY
        return f'<div class="battery-icon{" on" if on else ""}" title="Bateria fraca"></div>'

    @staticmethod
    def _push_icon_html(display: "DisplayBuffer") -> str:
        on = bool(display.flags & (1 << 15))  # Communication
        arrow = "\u2192"
        return f'<div class="push-icon{" on" if on else ""}" title="Comunicacao">{arrow}</div>'

    @classmethod
    def _html_document(cls, obis_row: str, data_row: str, display: "DisplayBuffer") -> str:
        top_row = (
            '<div class="top-row">'
            + cls._phase_col_html(display)
            + f'<div class="row">{obis_row}</div>'
            + cls._tariff_html(display)
            + cls._antenna_html(display)
            + cls._relay_html(display)
            + cls._quadrant_icon_html(display)
            + '</div>'
        )
        middle_row = (
            '<div class="top-row" style="margin-bottom:0;">'
            + f'<div class="row">{data_row}</div>'
            + cls._units_col_html(display)
            + '</div>'
        )
        bottom_row = (
            '<div class="bottom-icons">'
            + cls._arrow_triangles_html(display)
            + cls._alarm_icon_html(display)
            + cls._block_icon_html(display)
            + cls._dem_label_html()
            + cls._clock_icon_html(display)
            + cls._battery_icon_html(display)
            + cls._push_icon_html(display)
            + '</div>'
        )
        return f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<title>ZEUS-NG Display Buffer</title>
<style>{cls._HTML_CSS}</style>
</head>
<body>
  <h2>ZEUS-NG - Display Buffer</h2>
  <div class="lcd-panel">
    {top_row}
    {middle_row}
    {bottom_row}
  </div>
  <div class="badges">{cls._render_badges_html(display)}</div>
  {cls._render_meta_html(display)}
  {cls._render_warnings_html(display)}
</body>
</html>
"""

    @classmethod
    def _build_html(cls, seg: bytes, display: "DisplayBuffer") -> str:
        """Monta o HTML do formato compacto, usando os bytes reais de cada
        digito (posicoes corretas e ordem visual esquerda->direita)."""
        obis_bytes = [seg[6], seg[5], seg[4], seg[3], seg[2], seg[1]]
        obis_dot_after = [
            cls._bit(seg[0], 4),
            cls._bit(seg[0], 3),
            cls._bit(seg[0], 2),
            cls._bit(seg[0], 1),
            cls._bit(seg[0], 0),
        ]
        obis_parts = []
        for i, b in enumerate(obis_bytes):
            obis_parts.append(cls._digit_html(b, "md"))
            if i < len(obis_dot_after) and obis_dot_after[i]:
                obis_parts.append(cls._sep_html(".", "md"))
        obis_row = "".join(obis_parts)

        data_bytes = [seg[15], seg[14], seg[13], seg[12], seg[11], seg[10], seg[9], seg[8]]
        p6, p7 = cls._bit(seg[7], 5), cls._bit(seg[7], 3)
        p8 = cls._bit(seg[7], 2)
        p9, p10 = cls._bit(seg[7], 4), cls._bit(seg[7], 1)
        p11 = cls._bit(seg[7], 0)

        sep1 = ":" if (p6 and p7) else ("." if p7 else "")
        sep2 = "." if p8 else ""
        sep3 = ":" if (p9 and p10) else ("." if p10 else "")
        sep4 = "." if p11 else ""
        # Slot APOS cada digito (indices 0..6 para 8 digitos); so os 4 ultimos usam separador.
        data_seps_after = ["", "", "", sep1, sep2, sep3, sep4]

        data_parts = []
        for i, b in enumerate(data_bytes):
            data_parts.append(cls._digit_html(b, "lg"))
            if i < len(data_seps_after) and data_seps_after[i]:
                data_parts.append(cls._sep_html(data_seps_after[i], "lg"))
        data_row = "".join(data_parts)

        return cls._html_document(obis_row, data_row, display)

    @classmethod
    def _build_html_simple(cls, display: "DisplayBuffer") -> str:
        """Fallback para o formato AXDR estruturado: nao temos os bytes de
        segmento originais (o atributo ja vem como texto), entao mostramos o
        texto decodificado dentro do mesmo painel, sem desenhar segmentos."""
        obis_text = display.obis or "&nbsp;"
        data_text = display.data or "&nbsp;"
        obis_row = f'<div style="font:24px monospace; color:#ff3b30;">{obis_text}</div>'
        data_row = f'<div style="font:48px monospace; color:#ff3b30;">{data_text}</div>'
        return cls._html_document(obis_row, data_row, display)

    @classmethod
    def _lcd_char(cls, value: int, position: int, field_name: str, warnings: List[str], char_details: Optional[List[str]] = None) -> str:
        """Converte byte de segmento LCD em caractere. Registra alerta se o byte
        nao corresponder a nenhum caractere/digito conhecido (indica que o
        medidor enviou um segmento LCD invalido)."""
        key = value & 0xFF
        char = cls._LCD_NUMBER_MAP.get(key)
        if char_details is not None:
            char_details.append(cls._char_detail_block(field_name, position, key))
        if char is None:
            warnings.append(
                f"Campo '{field_name}' (payload[{position}] = 0x{key:02X}): padrao de "
                f"segmento LCD desconhecido. O medidor enviou um byte que nao existe "
                f"na tabela de caracteres do display."
            )
            return "?"
        return char

    @classmethod
    def _build_obis_from_segment(cls, seg: bytes, warnings: List[str], char_details: Optional[List[str]] = None) -> str:
        # Equivalente ao assemblyObisLcdPattern do parser C#.
        text = ""
        text += cls._lcd_char(seg[6], 6, "OBIS", warnings, char_details)
        if cls._bit(seg[0], 4):
            text += "."
        text += cls._lcd_char(seg[5], 5, "OBIS", warnings, char_details)
        if cls._bit(seg[0], 3):
            text += "."
        text += cls._lcd_char(seg[4], 4, "OBIS", warnings, char_details)
        if cls._bit(seg[0], 2):
            text += "."
        text += cls._lcd_char(seg[3], 3, "OBIS", warnings, char_details)
        if cls._bit(seg[0], 1):
            text += "."
        text += cls._lcd_char(seg[2], 2, "OBIS", warnings, char_details)
        if cls._bit(seg[0], 0):
            text += "."
        text += cls._lcd_char(seg[1], 1, "OBIS", warnings, char_details)
        return text.strip()

    @classmethod
    def _build_data_from_segment(cls, seg: bytes, warnings: List[str], char_details: Optional[List[str]] = None) -> str:
        # Equivalente ao assemblyMainLcdPattern do parser C#.
        text = ""
        text += cls._lcd_char(seg[15], 15, "Data", warnings, char_details)
        text += cls._lcd_char(seg[14], 14, "Data", warnings, char_details)
        text += cls._lcd_char(seg[13], 13, "Data", warnings, char_details)
        text += cls._lcd_char(seg[12], 12, "Data", warnings, char_details)

        # P6/P7
        p6 = cls._bit(seg[7], 5)
        p7 = cls._bit(seg[7], 3)
        if p6 and p7:
            text += ":"
        elif (not p6) and p7:
            text += "."

        text += cls._lcd_char(seg[11], 11, "Data", warnings, char_details)

        # P8
        if cls._bit(seg[7], 2):
            text += "."

        text += cls._lcd_char(seg[10], 10, "Data", warnings, char_details)

        # P9/P10
        p9 = cls._bit(seg[7], 4)
        p10 = cls._bit(seg[7], 1)
        if p9 and p10:
            text += ":"
        elif (not p9) and p10:
            text += "."

        text += cls._lcd_char(seg[9], 9, "Data", warnings, char_details)

        # P11
        if cls._bit(seg[7], 0):
            text += "."

        text += cls._lcd_char(seg[8], 8, "Data", warnings, char_details)
        return text.strip()

    @staticmethod
    def _tariff_from_segment(value: int, warnings: List[str]) -> int:
        known = {
            0x86: 1,
            0xDB: 2,
            0xCF: 3,
            0xE6: 4,
            0xFF: 8,
        }
        if value == 0x00:
            return 0
        if value not in known:
            warnings.append(
                f"Campo 'Tariff' (payload[20] = 0x{value:02X}): valor de tarifa nao "
                f"reconhecido (esperado 0x00, 0x86, 0xDB, 0xCF, 0xE6 ou 0xFF). "
                f"O medidor enviou um codigo de tarifa fora do padrao."
            )
            return 0
        return known[value]

    @staticmethod
    def _unit_from_magnitude_bytes(value: int, warnings: List[str]) -> int:
        # Conversao parcial de magnitudes do parser C# para enum do PDF.
        magnitude_map = {
            0x0009: Unit.KW,
            0x000A: Unit.MWH,   # MW nao existe no enum Unit do DISP.CMD.7; mantemos MWh como fallback visual.
            0x0049: Unit.KWH,
            0x004A: Unit.MWH,
            0x0004: Unit.VOLT,
            0x0010: Unit.AMPERE,
            0x0400: Unit.HERTZ,
            0x1000: Unit.PERCENTAGE,
            0x0035: Unit.KVAR,
            0x0075: Unit.KVARH,
            0x0076: Unit.MVARH,
        }
        if value == 0x0000:
            return int(Unit.NO_UNIT)
        if value not in magnitude_map:
            warnings.append(
                f"Campo 'Magnitude/Unit' (payload[16..17] = 0x{value:04X}): combinacao "
                f"de bytes de magnitude nao reconhecida. O medidor enviou uma unidade "
                f"fora da tabela conhecida."
            )
            return int(Unit.NO_UNIT)
        return int(magnitude_map[value])

    @staticmethod
    def _quadrant_from_segment(value: int, warnings: List[str]) -> int:
        # payload[22] tambem carrega L1/L2/L3 nos bits 5,6,7 (ver flags), entao
        # aqui so os bits 0-4 dizem respeito ao quadrante, igual assemblyQuadrant do C#.
        # bit4 = "eixo ativo"; bits 0-3 = qual quadrante (um por vez) ou todos (All).
        b = lambda bit: ((value >> bit) & 1) == 1
        axis = b(4)
        q1, q2, q3, q4 = b(0), b(1), b(2), b(3)
        selected = sum([q1, q2, q3, q4])

        if not axis:
            if selected > 0:
                warnings.append(
                    f"Campo 'Quadrant' (payload[22] = 0x{value:02X}): bit de quadrante "
                    f"selecionado sem o bit de eixo ativo (bit4=0). Combinacao inconsistente."
                )
            return int(Quadrant.QUADRANT_NONE)

        if selected == 4:
            return int(Quadrant.QUADRANT_ALL)
        if selected == 1:
            if q1:
                return int(Quadrant.QUADRANT_1)
            if q2:
                return int(Quadrant.QUADRANT_2)
            if q3:
                return int(Quadrant.QUADRANT_3)
            return int(Quadrant.QUADRANT_4)
        if selected == 0:
            # Eixo ativo mas nenhum quadrante especifico selecionado: "apenas o eixo".
            return int(Quadrant.QUADRANT_0)

        # 2 ou 3 quadrantes simultaneos (nem "um so" nem "todos") nao faz sentido fisico.
        warnings.append(
            f"Campo 'Quadrant' (payload[22] = 0x{value:02X}): {selected} quadrantes "
            f"marcados ao mesmo tempo (esperado 0, 1 ou os 4). Combinacao inconsistente."
        )
        return int(Quadrant.QUADRANT_NONE)

    @staticmethod
    def _signal_and_nic_from_segment(signal_byte: int, module_byte: int, warnings: List[str]) -> Tuple[int, int]:
        # signal_byte usa os mesmos bits do parser C# assemblySignalLevel: bit4 = antena
        # ativa; bits 0-3 formam um "termometro" (cada bar adicional liga o proximo bit).
        b = lambda bit: ((signal_byte >> bit) & 1) == 1
        antenna = b(4)
        bars = [b(0), b(1), b(2), b(3)]

        if not antenna:
            if any(bars):
                warnings.append(
                    f"Campo 'Signal Level' (payload[21] = 0x{signal_byte:02X}): bits de "
                    f"barra marcados sem a antena ativa (bit4=0). Combinacao inconsistente."
                )
            signal = SignalStrength.SIGNAL_NONE
        elif bars == [True, True, True, True]:
            signal = SignalStrength.SIGNAL_4
        elif bars == [True, True, True, False]:
            signal = SignalStrength.SIGNAL_3
        elif bars == [True, True, False, False]:
            signal = SignalStrength.SIGNAL_2
        elif bars == [True, False, False, False]:
            signal = SignalStrength.SIGNAL_1
        elif bars == [False, False, False, False]:
            # Antena ativa mas sem nenhuma barra: sinal minimo (so antena aparece).
            signal = SignalStrength.SIGNAL_0
        else:
            warnings.append(
                f"Campo 'Signal Level' (payload[21] = 0x{signal_byte:02X}): padrao de "
                f"barras nao segue a sequencia esperada (0,1,2,3 barras em ordem)."
            )
            signal = SignalStrength.SIGNAL_NONE

        nic_map = {
            0x20: NICType.NIC_RF,
            0x40: NICType.NIC_PLC,
            0x80: NICType.NIC_CELLULAR,
        }
        if module_byte == 0x00:
            nic = NICType.NIC_NONE
        elif module_byte not in nic_map:
            warnings.append(
                f"Campo 'Module' (payload[27] = 0x{module_byte:02X}): valor nao "
                f"corresponde a nenhum modulo de comunicacao conhecido (RF/PLC/CELL)."
            )
            nic = NICType.NIC_NONE
        else:
            nic = nic_map[module_byte]

        return int(signal), int(nic)

    @classmethod
    def _parse_compact_display_buffer(cls, payload: bytes) -> DisplayBuffer:
        """Parse do formato compacto de 39 bytes usado em ZeusNG Display_MAP."""
        if len(payload) != 39:
            raise ValueError(f"Tamanho inesperado para Display_MAP compacto: {len(payload)} bytes (esperado 39)")

        seg = payload
        warnings: List[str] = []
        char_details: List[str] = []

        obis = cls._build_obis_from_segment(seg, warnings, char_details)
        data = cls._build_data_from_segment(seg, warnings, char_details)

        tariff_num = cls._tariff_from_segment(seg[20], warnings)
        quadrant = cls._quadrant_from_segment(seg[22], warnings)
        nic_signal_strength, nic_type = cls._signal_and_nic_from_segment(seg[21], seg[27], warnings)

        magnitude = ((seg[17] << 8) | seg[16]) & 0xFFFF
        unit = cls._unit_from_magnitude_bytes(magnitude, warnings)

        # Constrói flags no mapeamento do PDF com base nos bits usados no parser C#.
        flags = 0
        flags |= cls._bit(seg[22], 5) << 0
        flags |= cls._bit(seg[22], 6) << 1
        flags |= cls._bit(seg[22], 7) << 2
        flags |= (1 if (cls._bit(seg[23], 3) and cls._bit(seg[24], 0)) else 0) << 3
        flags |= (1 if (cls._bit(seg[23], 4) and cls._bit(seg[24], 1)) else 0) << 4
        flags |= (1 if (cls._bit(seg[23], 5) and cls._bit(seg[24], 2)) else 0) << 5
        flags |= (1 if (cls._bit(seg[23], 0) and cls._bit(seg[24], 0)) else 0) << 6
        flags |= (1 if (cls._bit(seg[23], 1) and cls._bit(seg[24], 1)) else 0) << 7
        flags |= (1 if (cls._bit(seg[23], 2) and cls._bit(seg[24], 2)) else 0) << 8
        flags |= cls._bit(seg[18], 5) << 9
        flags |= cls._bit(seg[18], 6) << 10
        flags |= cls._bit(seg[25], 5) << 11
        flags |= cls._bit(seg[25], 7) << 12
        flags |= (1 if (cls._bit(seg[21], 5) and cls._bit(seg[21], 7)) else 0) << 13
        flags |= (1 if (cls._bit(seg[21], 6) and cls._bit(seg[21], 7)) else 0) << 14
        flags |= cls._bit(seg[25], 1) << 15
        flags |= cls._bit(seg[25], 0) << 16
        flags |= cls._bit(seg[28], 1) << 17
        flags |= cls._bit(seg[28], 0) << 19  # Billing_Protection -> icone de bloqueio (Flag.BLOCKING_HAND)
        flags |= cls._bit(seg[19], 2) << 20
        flags |= cls._bit(seg[19], 3) << 21
        flags |= cls._bit(seg[19], 4) << 22
        flags |= cls._bit(seg[19], 5) << 23
        flags |= cls._bit(seg[19], 6) << 24
        flags |= cls._bit(seg[19], 7) << 25
        flags |= cls._bit(seg[19], 1) << 26
        flags |= cls._bit(seg[18], 0) << 27
        flags |= cls._bit(seg[18], 1) << 28
        flags |= cls._bit(seg[18], 2) << 29
        flags |= cls._bit(seg[18], 3) << 30
        flags |= cls._bit(seg[18], 4) << 31

        flags2 = 0
        # Decimais do dado (conforme bits MAIN_LCD_Px no parser C#).
        flags2 |= cls._bit(seg[7], 0) << 0
        flags2 |= cls._bit(seg[7], 1) << 1
        flags2 |= cls._bit(seg[7], 2) << 2
        flags2 |= cls._bit(seg[7], 3) << 3
        flags2 |= cls._bit(seg[7], 4) << 4
        flags2 |= cls._bit(seg[7], 5) << 5
        # Decimais do OBIS.
        flags2 |= cls._bit(seg[0], 4) << 6
        flags2 |= cls._bit(seg[0], 3) << 7
        flags2 |= cls._bit(seg[0], 2) << 8
        flags2 |= cls._bit(seg[0], 1) << 9
        flags2 |= cls._bit(seg[0], 0) << 10

        result = DisplayBuffer(
            obis=obis,
            data=data,
            tariff_num=tariff_num,
            nic_signal_strength=nic_signal_strength,
            nic_type=nic_type,
            quadrant=quadrant,
            unit=unit,
            flags=flags,
            flags2=flags2,
            warnings=warnings,
            char_details=char_details,
            unit_bits=magnitude,
        )
        result.html = cls._build_html(seg, result)
        return result

    @staticmethod
    def bytes_to_visible_string(data: bytes, length: int, offset: int) -> Tuple[str, int]:
        """
        Extrai visible-string do buffer DLMS.
        Formato: 0x0A <length> <data...> ou 0x09 <length> <data...>
        """
        if offset >= len(data):
            return "", offset

        tag = data[offset]
        if tag not in (AXDR_VISIBLE_STRING, AXDR_OCTET_STRING):
            raise ValueError(f"Tag invalida para visible-string em {offset}: 0x{tag:02X}")

        str_length, offset = DLMSDisplayParser._read_axdr_length(data, offset + 1)
        if offset + str_length > len(data):
            raise ValueError("Visible-string ultrapassa tamanho do buffer")

        string_data = data[offset:offset + str_length]
        offset += str_length

        # Converte para string, ignorando caracteres não-ASCII.
        result = string_data.decode('ascii', errors='ignore').strip()
        if not result or all(c == ' ' for c in result):
            return string_data.hex(), offset
        return result, offset

    @staticmethod
    def bytes_to_unsigned(data: bytes, offset: int) -> Tuple[int, int]:
        """Extrai unsigned (1 byte) do buffer DLMS"""
        if offset + 1 >= len(data):
            raise ValueError("Buffer insuficiente para unsigned")

        tag = data[offset]
        if tag != AXDR_UNSIGNED:
            raise ValueError(f"Tag invalida para unsigned em {offset}: 0x{tag:02X}")

        return data[offset + 1], offset + 2

    @staticmethod
    def bytes_to_enum(data: bytes, offset: int) -> Tuple[int, int]:
        """Extrai enum (1 byte) do buffer DLMS"""
        if offset + 1 >= len(data):
            raise ValueError("Buffer insuficiente para enum")

        tag = data[offset]
        if tag != AXDR_ENUM:
            raise ValueError(f"Tag invalida para enum em {offset}: 0x{tag:02X}")

        return data[offset + 1], offset + 2

    @staticmethod
    def bytes_to_double_long_unsigned(data: bytes, offset: int) -> Tuple[int, int]:
        """Extrai double-long-unsigned (4 bytes, big-endian) do buffer DLMS"""
        if offset + 5 > len(data):
            raise ValueError("Buffer insuficiente para double-long-unsigned")

        tag = data[offset]
        if tag != AXDR_DOUBLE_LONG_UNSIGNED:
            raise ValueError(f"Tag invalida para double-long-unsigned em {offset}: 0x{tag:02X}")

        value = int.from_bytes(data[offset + 1:offset + 5], byteorder='big', signed=False)
        return value, offset + 5

    @staticmethod
    def skip_structure_tag(data: bytes, offset: int) -> int:
        """Pula a tag de estrutura e seu tamanho"""
        if offset + 1 >= len(data):
            raise ValueError("Buffer insuficiente para estrutura AXDR")

        if data[offset] != AXDR_STRUCTURE:
            raise ValueError(f"Tag invalida de estrutura em {offset}: 0x{data[offset]:02X}")

        # Para DISP.CMD.7 esperamos exatamente 8 elementos.
        elements = data[offset + 1]
        if elements != 0x08:
            raise ValueError(f"Estrutura inesperada: quantidade de elementos = {elements}, esperado 8")

        return offset + 2

    @classmethod
    def print_hex_debug(cls, data: bytes, offset: int = 0, length: int = 32) -> None:
        """Imprime dados em hex com offset para debug"""
        print("\n[HEX DUMP]")
        for i in range(offset, min(offset + length, len(data))):
            if i % 16 == 0:
                print(f"  {i:04X}: ", end="")
            print(f"{data[i]:02X} ", end="")
            if (i + 1) % 16 == 0:
                print()
        if len(data) % 16 != 0:
            print()

    @classmethod
    def parse(cls, raw_bytes: bytes, verbose: bool = False) -> Optional[DisplayBuffer]:
        """
        Faz parse do frame DLMS bruto para DisplayBuffer.
        
        Estrutura esperada (DLMS):
        - 0x02: Structure tag
        - 0x08: Number of elements (8)
        - visible-string[6]: OBIS
        - visible-string[8]: Data
        - unsigned: tariff_num
        - enum: nic_signal_strength
        - enum: nic_type
        - enum: quadrant
        - enum: unit
        - double-long-unsigned: flags
        - double-long-unsigned: flags2
        """
        try:
            offset = 0

            if verbose:
                print("[DEBUG] Raw frame:")
                cls.print_hex_debug(raw_bytes, 0)

            payload = cls._unwrap_get_response_data(raw_bytes)
            payload = cls._unwrap_single_axdr_string(payload)

            if verbose:
                print("[DEBUG] Payload após unwrap do GET response:")
                cls.print_hex_debug(payload, 0)

            # Fallback: alguns firmwares retornam Display Buffer como mapa compacto (39 bytes)
            # em octet-string, sem estrutura AXDR 02 08.
            if len(payload) == 39:
                if verbose:
                    print("[DEBUG] Detectado formato compacto de 39 bytes (Display_MAP)")
                return cls._parse_compact_display_buffer(payload)

            # DISP.CMD.7 AXDR completo precisa começar com estrutura 0x02 0x08.
            structure_pos = payload.find(bytes([AXDR_STRUCTURE, 0x08]))
            if structure_pos < 0:
                raise ValueError(
                    "Payload nao contem estrutura AXDR DISP.CMD.7 (02 08). "
                    "Verifique se o OBIS lido e 0.0.96.55.9.255 atributo 2."
                )

            offset = structure_pos
            if verbose:
                print(f"[DEBUG] Estrutura DISP.CMD.7 encontrada na posicao {offset}")

            offset = cls.skip_structure_tag(payload, offset)

            if verbose:
                print(f"[DEBUG] Após skip structure tag, offset = {offset}")
                cls.print_hex_debug(payload, offset, 24)
            
            # Parse de cada field
            obis, offset = cls.bytes_to_visible_string(payload, 6, offset)
            if verbose:
                print(f"[DEBUG] OBIS: '{obis}', offset = {offset}")
            
            data, offset = cls.bytes_to_visible_string(payload, 8, offset)
            if verbose:
                print(f"[DEBUG] DATA: '{data}', offset = {offset}")
            
            tariff_num, offset = cls.bytes_to_unsigned(payload, offset)
            if verbose:
                print(f"[DEBUG] Tariff: {tariff_num}, offset = {offset}")
            
            nic_signal_strength, offset = cls.bytes_to_enum(payload, offset)
            if verbose:
                print(f"[DEBUG] NIC Signal: {nic_signal_strength:#x}, offset = {offset}")
            
            nic_type, offset = cls.bytes_to_enum(payload, offset)
            if verbose:
                print(f"[DEBUG] NIC Type: {nic_type:#x}, offset = {offset}")
            
            quadrant, offset = cls.bytes_to_enum(payload, offset)
            if verbose:
                print(f"[DEBUG] Quadrant: {quadrant:#x}, offset = {offset}")
            
            unit, offset = cls.bytes_to_enum(payload, offset)
            if verbose:
                print(f"[DEBUG] Unit: {unit:#x}, offset = {offset}")
            
            flags, offset = cls.bytes_to_double_long_unsigned(payload, offset)
            if verbose:
                print(f"[DEBUG] Flags: {flags:#010x}, offset = {offset}")
            
            flags2, offset = cls.bytes_to_double_long_unsigned(payload, offset)
            if verbose:
                print(f"[DEBUG] Flags2: {flags2:#010x}, offset = {offset}")
            
            result = DisplayBuffer(
                obis=obis,
                data=data,
                tariff_num=tariff_num,
                nic_signal_strength=nic_signal_strength,
                nic_type=nic_type,
                quadrant=quadrant,
                unit=unit,
                flags=flags,
                flags2=flags2,
            )
            result.html = cls._build_html_simple(result)
            return result
        
        except Exception as e:
            print(f"[ERRO] Falha ao fazer parse: {e}")
            if verbose:
                import traceback
                traceback.print_exc()
            return None


def main():
    """Permite parsear um frame hex informado pelo usuario (via argumento de
    linha de comando ou digitado/colado interativamente), ou visualizar o
    desenho de 7 segmentos de um unico byte.

    Uso:
      python zeus_display_parser.py                -> modo interativo (pede o frame)
      python zeus_display_parser.py C4 01 C1 ...    -> parseia direto o frame informado
      python zeus_display_parser.py --byte 0x7C     -> mostra o desenho de 7 segmentos do byte
    """
    args = sys.argv[1:]

    if args and args[0].lower() in ("--byte", "-b", "byte"):
        if len(args) < 2:
            print("Uso: python zeus_display_parser.py --byte 0x7C")
            return
        print_byte_diagram(args[1])
        return

    args_hex = " ".join(args).strip()
    if args_hex:
        parse_frame_hex(args_hex)
        return

    print("Cole o frame HEX recebido do medidor (ex: C4 01 C1 00 09 27 ...).")
    print("Ou digite 'byte 0x7C' para ver o desenho de 7 segmentos de um byte isolado.")
    print("Deixe em branco (Enter) ou digite 'sair' para encerrar.\n")

    while True:
        entry = input("Frame HEX / byte> ").strip()
        if not entry or entry.lower() in ("sair", "exit", "quit"):
            break
        if entry.lower().startswith("byte "):
            print_byte_diagram(entry[5:].strip())
        else:
            parse_frame_hex(entry)
        print()


def print_byte_diagram(raw_value: str) -> None:
    """Imprime hex/decimal/bits + o desenho de 7 segmentos + o caractere
    reconhecido (ou alerta) para um unico byte informado pelo usuario."""
    cleaned = raw_value.strip().replace("0x", "").replace("0X", "")
    try:
        value = int(cleaned, 16)
    except ValueError:
        print(f"[ERRO] Byte hex invalido: {raw_value!r}")
        return
    print(DLMSDisplayParser.describe_lcd_byte(value))


def parse_frame_hex(frame_hex: str, verbose: bool = True, html_path: Optional[str] = None) -> Optional[DisplayBuffer]:
    """Converte a string hex informada (com ou sem espacos/prefixo 0x) em bytes,
    faz o parse do Display Buffer, imprime o resultado na tela e gera um HTML
    com o display desenhado (7 segmentos) nas posicoes corretas."""
    cleaned = (
        frame_hex.replace("0x", "")
        .replace("0X", "")
        .replace(",", " ")
        .replace("\n", " ")
        .replace("\r", " ")
    )
    cleaned = "".join(cleaned.split())

    try:
        frame_bytes = bytes.fromhex(cleaned)
    except ValueError as e:
        print(f"[ERRO] Frame hex invalido: {e}")
        return None

    print(f"Frame recebido ({len(frame_bytes)} bytes):")
    print(f"HEX: {frame_bytes.hex().upper()}")
    print()

    parser = DLMSDisplayParser()
    display_buffer = parser.parse(frame_bytes, verbose=verbose)

    if display_buffer:
        print(display_buffer)

        print("\n[DEBUG]")
        print(f"OBIS (raw):  {display_buffer.obis.encode().hex() if display_buffer.obis else 'N/A'}")
        print(f"Data (raw):  {display_buffer.data.encode().hex() if display_buffer.data else 'N/A'}")
        print(f"Flags (raw): 0x{display_buffer.flags:08X} = {display_buffer.flags:032b}")
        print(f"Flags2 (raw): 0x{display_buffer.flags2:08X} = {display_buffer.flags2:032b}")

        out_path = Path(html_path) if html_path else Path(__file__).resolve().parent / "zeus_display.html"
        try:
            out_path.write_text(display_buffer.html, encoding="utf-8")
            print(f"\n[HTML] Display gerado em: {out_path}")
        except OSError as e:
            print(f"\n[ERRO] Falha ao salvar HTML: {e}")
    else:
        print("[ERRO] Falha ao fazer parse do frame")

    return display_buffer


def test_with_manual_data():
    """Teste com dados inseridos manualmente (útil para testes)"""
    print("\n" + "=" * 70)
    print("TESTE COM DADOS MANUAIS")
    print("=" * 70 + "\n")
    
    # Cria um DisplayBuffer com dados de teste
    display = DisplayBuffer(
        obis="1.0.0.9.255",
        data="12,345",
        tariff_num=1,
        nic_signal_strength=SignalStrength.SIGNAL_3,
        nic_type=NICType.NIC_PLC,
        quadrant=Quadrant.QUADRANT_1,
        unit=Unit.KWH,
        flags=0x0600000000,  # Exemplo com algumas flags
        flags2=0x0600000003,  # Exemplo com algumas flags2
    )
    
    print(display)
    
    # Mostra especificamente os flags ativos
    print("\nFlags Ativos Detalhados:")
    for bit, name in display.get_active_flags():
        print(f"  Bit {bit:2d} ({name})")
    
    print("\nFlags2 Ativos Detalhados:")
    for bit, name in display.get_active_flags2():
        print(f"  Bit {bit:2d} ({name})")


def parse_from_dict(**kwargs) -> DisplayBuffer:
    """Factory para criar DisplayBuffer a partir de dicionário"""
    defaults = {
        'obis': '',
        'data': '',
        'tariff_num': 0,
        'nic_signal_strength': 0,
        'nic_type': 0,
        'quadrant': 0,
        'unit': 0,
        'flags': 0,
        'flags2': 0,
    }
    defaults.update(kwargs)
    return DisplayBuffer(**defaults)


if __name__ == "__main__":
    main()
