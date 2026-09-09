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
import os
import sys

# AXDR tags used by ZEUS-NG DISP.CMD.7 according to the product spec.
AXDR_STRUCTURE = 0x02
AXDR_OCTET_STRING = 0x09
AXDR_VISIBLE_STRING = 0x0A
AXDR_DOUBLE_LONG_UNSIGNED = 0x06
AXDR_UNSIGNED = 0x11
AXDR_ENUM = 0x16

class SignalStrength(IntEnum):
    SIGNAL_NONE = 0x00  # signal total off
    SIGNAL_0 = 0x01     # no bar, only antenna
    SIGNAL_1 = 0x02     # one bar
    SIGNAL_2 = 0x03     # two bars
    SIGNAL_3 = 0x04     # three bars
    SIGNAL_4 = 0x05     # four bars

class NICType(IntEnum):
    NIC_NONE = 0x00
    NIC_RF = 0x01
    NIC_PLC = 0x02
    NIC_CELLULAR = 0x03

class Quadrant(IntEnum):
    QUADRANT_NONE = 0x00     # no quadrant is displayed
    QUADRANT_0 = 0x01        # only the axis is displayed
    QUADRANT_1 = 0x02
    QUADRANT_2 = 0x03
    QUADRANT_3 = 0x04
    QUADRANT_4 = 0x05
    QUADRANT_ALL = 0x06      # all quadrants displayed

class Unit(IntEnum):
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
    L1 = 0
    L2 = 1
    L3 = 2
    L1_OUT = 3
    L2_OUT = 4
    L3_OUT = 5
    L1_IN = 6
    L2_IN = 7
    L3_IN = 8
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
    Flag.L1: "L1", Flag.L2: "L2", Flag.L3: "L3", Flag.L1_OUT: "L1 Out",
    Flag.L2_OUT: "L2 Out", Flag.L3_OUT: "L3 Out", Flag.L1_IN: "L1 In",
    Flag.L2_IN: "L2 In", Flag.L3_IN: "L3 In", Flag.CAP: "Capacitive",
    Flag.IND: "Inductive", Flag.ALT: "Alternative", Flag.MAN: "Manual",
    Flag.RELAY_CLOSED: "Relay Closed", Flag.RELAY_OPEN: "Relay Open",
    Flag.COMMUNICATION: "Communication", Flag.LOW_BATTERY: "Low Battery",
    Flag.RTC_TEST: "RTC Test", Flag.DEM: "Demand", Flag.BLOCKING_HAND: "Blocking Hand",
    Flag.ALARM_1: "Alarm 1", Flag.ALARM_2: "Alarm 2", Flag.ALARM_3: "Alarm 3",
    Flag.ALARM_4: "Alarm 4", Flag.ALARM_5: "Alarm 5", Flag.ALARM_6: "Alarm 6",
    Flag.ALARM_EXCLAMATION: "Alarm Exclamation", Flag.ARROW_1_DST: "Arrow DST",
    Flag.ARROW_2_COV: "Arrow COV", Flag.ARROW_3_TER: "Arrow TER",
    Flag.ARROW_4_NIC: "Arrow NIC", Flag.ARROW_5_RESERVED: "Arrow Reserved",
}

FLAG2_NAMES = {
    Flag2.DATA_DECIMAL_1: "Data Decimal 1", Flag2.DATA_DECIMAL_2: "Data Decimal 2",
    Flag2.DATA_DECIMAL_3: "Data Decimal 3", Flag2.DATA_DECIMAL_4: "Data Decimal 4",
    Flag2.DATA_DECIMAL_2_UPPER: "Data Decimal 2 Upper", Flag2.DATA_DECIMAL_4_UPPER: "Data Decimal 4 Upper",
    Flag2.OBIS_DECIMAL_1: "OBIS Decimal 1", Flag2.OBIS_DECIMAL_2: "OBIS Decimal 2",
    Flag2.OBIS_DECIMAL_3: "OBIS Decimal 3", Flag2.OBIS_DECIMAL_4: "OBIS Decimal 4",
    Flag2.OBIS_DECIMAL_5: "OBIS Decimal 5",
}

# --- MERGE V1: MAPEAMENTO COMPLETO DOS CÓDIGOS OBIS ---
# Mapeamento unificado de códigos DLMS (OBIS) e ABNT para nomes das telas
DISPLAY_CODES = {
    # Data / Hora / Sistema / Serial
    "0.1.0": "Billing_Counter", "23": "Billing_Counter",
    "0.1.2.1": "Last_Billing_Close_Time", "2A": "Last_Billing_Close_Time",
    "0.2.0": "Short_Software_Version", "FC": "Short_Software_Version",
    "0.9.1": "Time", "02": "Time",
    "0.9.2": "Date", "01": "Date",
    "8.8.8.8.8.8": "Display_Test", "8.8.8.8.8.8": "Display_Test",
    "C.1.0": "Meter_Serial_Number", "33": "Meter_Serial_Number",
    "96.54.4": "BatteryStatus", "32": "BatteryStatus",
    "96.0": "RTP_Numerator", "96": "RTP_Numerator",
    "96.1": "RTP_Denominator", "196": "RTP_Denominator",
    "97.0": "RTC_Numerator", "97": "RTC_Numerator",
    "97.1": "RTC_Denominator", "197": "RTC_Denominator",

    # Grandezas Diretas (+) - Ativas
    "1.2.0": "Active_Direct_Energy_Accumulated_Demand_Total_Value", "54": "Active_Direct_Energy_Accumulated_Demand_Total_Value",
    "1.2.1": "Active_Direct_Energy_Accumulated_Demand_T1_Value", "17": "Active_Direct_Energy_Accumulated_Demand_T1_Value",
    "1.2.2": "Active_Direct_Energy_Accumulated_Demand_T2_Value", "21": "Active_Direct_Energy_Accumulated_Demand_T2_Value",
    "1.2.3": "Active_Direct_Energy_Accumulated_Demand_T3_Value", "19": "Active_Direct_Energy_Accumulated_Demand_T3_Value",
    "1.2.4": "Active_Direct_Energy_Accumulated_Demand_T4_Value", "22": "Active_Direct_Energy_Accumulated_Demand_T4_Value",
    "1.6.0": "Active_Direct_Energy_Maximum_Demand_Total_Value", "52": "Active_Direct_Energy_Maximum_Demand_Total_Value",
    "1.6.1": "Active_Direct_Energy_Maximum_Demand_T1_Value", "10": "Active_Direct_Energy_Maximum_Demand_T1_Value",
    "1.6.2": "Active_Direct_Energy_Maximum_Demand_T2_Value", "14": "Active_Direct_Energy_Maximum_Demand_T2_Value",
    "1.6.3": "Active_Direct_Energy_Maximum_Demand_T3_Value", "12": "Active_Direct_Energy_Maximum_Demand_T3_Value",
    "1.6.4": "Active_Direct_Energy_Maximum_Demand_T4_Value", "15": "Active_Direct_Energy_Maximum_Demand_T4_Value",
    "1.7.0": "Active_Power_Q1_Q4", "Pt": "Active_Power_Q1_Q4",
    "1.8.0": "Active_Direct_Energy_Total_Value", "03": "Active_Direct_Energy_Total_Value",
    "1.8.1": "Active_Direct_Energy_T1_Value", "04": "Active_Direct_Energy_T1_Value",
    "1.8.2": "Active_Direct_Energy_T2_Value", "08": "Active_Direct_Energy_T2_Value",
    "1.8.3": "Active_Direct_Energy_T3_Value", "06": "Active_Direct_Energy_T3_Value",
    "1.8.4": "Active_Direct_Energy_T4_Value", "09": "Active_Direct_Energy_T4_Value",
    "1.4.0": "Active_Direct_Energy_Demand_Total_Last_Value", "16": "Active_Direct_Energy_Demand_Total_Last_Value",

    # Grandezas Reversas (-) - Ativas
    "2.2.0": "Active_Reverse_Energy_Accumulated_Demand_Total_Value", "154": "Active_Reverse_Energy_Accumulated_Demand_Total_Value",
    "2.2.1": "Active_Reverse_Energy_Accumulated_Demand_T1_Value", "117": "Active_Reverse_Energy_Accumulated_Demand_T1_Value",
    "2.2.2": "Active_Reverse_Energy_Accumulated_Demand_T2_Value", "121": "Active_Reverse_Energy_Accumulated_Demand_T2_Value",
    "2.2.3": "Active_Reverse_Energy_Accumulated_Demand_T3_Value", "119": "Active_Reverse_Energy_Accumulated_Demand_T3_Value",
    "2.2.4": "Active_Reverse_Energy_Accumulated_Demand_T4_Value", "122": "Active_Reverse_Energy_Accumulated_Demand_T4_Value",
    "2.6.0": "Active_Reverse_Energy_Maximum_Demand_Total_Value", "152": "Active_Reverse_Energy_Maximum_Demand_Total_Value",
    "2.6.1": "Active_Reverse_Energy_Maximum_Demand_T1_Value", "110": "Active_Reverse_Energy_Maximum_Demand_T1_Value",
    "2.6.2": "Active_Reverse_Energy_Maximum_Demand_T2_Value", "114": "Active_Reverse_Energy_Maximum_Demand_T2_Value",
    "2.6.3": "Active_Reverse_Energy_Maximum_Demand_T3_Value", "112": "Active_Reverse_Energy_Maximum_Demand_T3_Value",
    "2.6.4": "Active_Reverse_Energy_Maximum_Demand_T4_Value", "115": "Active_Reverse_Energy_Maximum_Demand_T4_Value",
    "2.7.0": "Active_Power_Q2_Q3", "1Pt": "Active_Power_Q2_Q3",
    "2.8.0": "Active_Reverse_Energy_Total_Value", "103": "Active_Reverse_Energy_Total_Value",
    "2.8.1": "Active_Reverse_Energy_T1_Value", "104": "Active_Reverse_Energy_T1_Value",
    "2.8.2": "Active_Reverse_Energy_T2_Value", "108": "Active_Reverse_Energy_T2_Value",
    "2.8.3": "Active_Reverse_Energy_T3_Value", "106": "Active_Reverse_Energy_T3_Value",
    "2.8.4": "Active_Reverse_Energy_T4_Value", "109": "Active_Reverse_Energy_T4_Value",
    "2.4.0": "Active_Reverse_Energy_Demand_Total_Last_Value", "116": "Active_Reverse_Energy_Demand_Total_Last_Value",

    # Reativos Q1
    "3.7.0": "Reactive_Power_Q1_Q2", "rt": "Reactive_Power_Q1_Q2",
    "5.2.0": "Reactive_Q1_Energy_Accumulated_Demand_Total_Value", "64": "Reactive_Q1_Energy_Accumulated_Demand_Total_Value",
    "5.2.1": "Reactive_Q1_Energy_Accumulated_Demand_T1_Value", "41": "Reactive_Q1_Energy_Accumulated_Demand_T1_Value",
    "5.2.2": "Reactive_Q1_Energy_Accumulated_Demand_T2_Value", "45": "Reactive_Q1_Energy_Accumulated_Demand_T2_Value",
    "5.2.3": "Reactive_Q1_Energy_Accumulated_Demand_T3_Value", "43": "Reactive_Q1_Energy_Accumulated_Demand_T3_Value",
    "5.2.4": "Reactive_Q1_Energy_Accumulated_Demand_T4_Value", "46": "Reactive_Q1_Energy_Accumulated_Demand_T4_Value",
    "5.6.0": "Reactive_Q1_Energy_Maximum_Demand_Total_Value", "62": "Reactive_Q1_Energy_Maximum_Demand_Total_Value",
    "5.6.1": "Reactive_Q1_Energy_Maximum_Demand_T1_Value", "34": "Reactive_Q1_Energy_Maximum_Demand_T1_Value",
    "5.6.2": "Reactive_Q1_Energy_Maximum_Demand_T2_Value", "38": "Reactive_Q1_Energy_Maximum_Demand_T2_Value",
    "5.6.3": "Reactive_Q1_Energy_Maximum_Demand_T3_Value", "36": "Reactive_Q1_Energy_Maximum_Demand_T3_Value",
    "5.6.4": "Reactive_Q1_Energy_Maximum_Demand_T4_Value", "39": "Reactive_Q1_Energy_Maximum_Demand_T4_Value",
    "5.8.0": "Reactive_Q1_Energy_Total_Value", "24": "Reactive_Q1_Energy_Total_Value",
    "5.8.1": "Reactive_Q1_Energy_T1_Value", "25": "Reactive_Q1_Energy_T1_Value",
    "5.8.2": "Reactive_Q1_Energy_T2_Value", "29": "Reactive_Q1_Energy_T2_Value",
    "5.8.3": "Reactive_Q1_Energy_T3_Value", "27": "Reactive_Q1_Energy_T3_Value",
    "5.8.4": "Reactive_Q1_Energy_T4_Value", "30": "Reactive_Q1_Energy_T4_Value",
    "5.4.0": "Reactive_Q1_Energy_Demand_Total_Last_Value", "40": "Reactive_Q1_Energy_Demand_Total_Last_Value",

    # Reativos Q2
    "6.2.0": "Reactive_Q2_Energy_Accumulated_Demand_Total_Value", "37": "Reactive_Q2_Energy_Accumulated_Demand_Total_Value",
    "6.2.1": "Reactive_Q2_Energy_Accumulated_Demand_T1_Value", "3A": "Reactive_Q2_Energy_Accumulated_Demand_T1_Value",
    "6.2.2": "Reactive_Q2_Energy_Accumulated_Demand_T2_Value", "3b": "Reactive_Q2_Energy_Accumulated_Demand_T2_Value",
    "6.2.3": "Reactive_Q2_Energy_Accumulated_Demand_T3_Value", "3C": "Reactive_Q2_Energy_Accumulated_Demand_T3_Value",
    "6.2.4": "Reactive_Q2_Energy_Accumulated_Demand_T4_Value", "3d": "Reactive_Q2_Energy_Accumulated_Demand_T4_Value",
    "6.6.0": "Reactive_Q2_Energy_Maximum_Demand_Total_Value", "35": "Reactive_Q2_Energy_Maximum_Demand_Total_Value",
    "6.6.1": "Reactive_Q2_Energy_Maximum_Demand_T1_Value", "3E": "Reactive_Q2_Energy_Maximum_Demand_T1_Value",
    "6.6.2": "Reactive_Q2_Energy_Maximum_Demand_T2_Value", "3F": "Reactive_Q2_Energy_Maximum_Demand_T2_Value",
    "6.6.3": "Reactive_Q2_Energy_Maximum_Demand_T3_Value", "3H": "Reactive_Q2_Energy_Maximum_Demand_T3_Value",
    "6.6.4": "Reactive_Q2_Energy_Maximum_Demand_T4_Value", "3L": "Reactive_Q2_Energy_Maximum_Demand_T4_Value",
    "6.8.0": "Reactive_Q2_Energy_Total_Value", "131": "Reactive_Q2_Energy_Total_Value",
    "6.8.1": "Reactive_Q2_Energy_T1_Value", "185": "Reactive_Q2_Energy_T1_Value",
    "6.8.2": "Reactive_Q2_Energy_T2_Value", "187": "Reactive_Q2_Energy_T2_Value",
    "6.8.3": "Reactive_Q2_Energy_T3_Value", "186": "Reactive_Q2_Energy_T3_Value",
    "6.8.4": "Reactive_Q2_Energy_T4_Value", "189": "Reactive_Q2_Energy_T4_Value",

    # Reativos Q3
    "7.2.0": "Reactive_Q3_Energy_Accumulated_Demand_Total_Value", "164": "Reactive_Q3_Energy_Accumulated_Demand_Total_Value",
    "7.2.1": "Reactive_Q3_Energy_Accumulated_Demand_T1_Value", "141": "Reactive_Q3_Energy_Accumulated_Demand_T1_Value",
    "7.2.2": "Reactive_Q3_Energy_Accumulated_Demand_T2_Value", "145": "Reactive_Q3_Energy_Accumulated_Demand_T2_Value",
    "7.2.3": "Reactive_Q3_Energy_Accumulated_Demand_T3_Value", "143": "Reactive_Q3_Energy_Accumulated_Demand_T3_Value",
    "7.2.4": "Reactive_Q3_Energy_Accumulated_Demand_T4_Value", "146": "Reactive_Q3_Energy_Accumulated_Demand_T4_Value",
    "7.6.0": "Reactive_Q3_Energy_Maximum_Demand_Total_Value", "162": "Reactive_Q3_Energy_Maximum_Demand_Total_Value",
    "7.6.1": "Reactive_Q3_Energy_Maximum_Demand_T1_Value", "134": "Reactive_Q3_Energy_Maximum_Demand_T1_Value",
    "7.6.2": "Reactive_Q3_Energy_Maximum_Demand_T2_Value", "138": "Reactive_Q3_Energy_Maximum_Demand_T2_Value",
    "7.6.3": "Reactive_Q3_Energy_Maximum_Demand_T3_Value", "136": "Reactive_Q3_Energy_Maximum_Demand_T3_Value",
    "7.6.4": "Reactive_Q3_Energy_Maximum_Demand_T4_Value", "139": "Reactive_Q3_Energy_Maximum_Demand_T4_Value",
    "7.8.0": "Reactive_Q3_Energy_Total_Value", "124": "Reactive_Q3_Energy_Total_Value",
    "7.8.1": "Reactive_Q3_Energy_T1_Value", "125": "Reactive_Q3_Energy_T1_Value",
    "7.8.2": "Reactive_Q3_Energy_T2_Value", "129": "Reactive_Q3_Energy_T2_Value",
    "7.8.3": "Reactive_Q3_Energy_T3_Value", "127": "Reactive_Q3_Energy_T3_Value",
    "7.8.4": "Reactive_Q3_Energy_T4_Value", "130": "Reactive_Q3_Energy_T4_Value",
    "7.4.0": "Reactive_Q3_Energy_Demand_Total_Last_Value", "140": "Reactive_Q3_Energy_Demand_Total_Last_Value",

    # Reativos Q4
    "4.7.0": "Reactive_Power_Q3_Q4", "1rt": "Reactive_Power_Q3_Q4",
    "8.2.0": "Reactive_Q4_Energy_Accumulated_Demand_Total_Value", "137": "Reactive_Q4_Energy_Accumulated_Demand_Total_Value",
    "8.2.1": "Reactive_Q4_Energy_Accumulated_Demand_T1_Value", "13A": "Reactive_Q4_Energy_Accumulated_Demand_T1_Value",
    "8.2.2": "Reactive_Q4_Energy_Accumulated_Demand_T2_Value", "13b": "Reactive_Q4_Energy_Accumulated_Demand_T2_Value",
    "8.2.3": "Reactive_Q4_Energy_Accumulated_Demand_T3_Value", "13C": "Reactive_Q4_Energy_Accumulated_Demand_T3_Value",
    "8.2.4": "Reactive_Q4_Energy_Accumulated_Demand_T4_Value", "13d": "Reactive_Q4_Energy_Accumulated_Demand_T4_Value",
    "8.6.0": "Reactive_Q4_Energy_Maximum_Demand_Total_Value", "132": "Reactive_Q4_Energy_Maximum_Demand_Total_Value",
    "8.6.1": "Reactive_Q4_Energy_Maximum_Demand_T1_Value", "13E": "Reactive_Q4_Energy_Maximum_Demand_T1_Value",
    "8.6.2": "Reactive_Q4_Energy_Maximum_Demand_T2_Value", "13F": "Reactive_Q4_Energy_Maximum_Demand_T2_Value",
    "8.6.3": "Reactive_Q4_Energy_Maximum_Demand_T3_Value", "13H": "Reactive_Q4_Energy_Maximum_Demand_T3_Value",
    "8.6.4": "Reactive_Q4_Energy_Maximum_Demand_T4_Value", "13L": "Reactive_Q4_Energy_Maximum_Demand_T4_Value",
    "8.8.0": "Reactive_Q4_Energy_Total_Value", "31": "Reactive_Q4_Energy_Total_Value",
    "8.8.1": "Reactive_Q4_Energy_T1_Value", "85": "Reactive_Q4_Energy_T1_Value",
    "8.8.2": "Reactive_Q4_Energy_T2_Value", "87": "Reactive_Q4_Energy_T2_Value",
    "8.8.3": "Reactive_Q4_Energy_T3_Value", "86": "Reactive_Q4_Energy_T3_Value",
    "8.8.4": "Reactive_Q4_Energy_T4_Value", "89": "Reactive_Q4_Energy_T4_Value",

    # Instântaneas e Fases
    "9.7.0": "Apparent_Power_Q1_Q4", "At": "Apparent_Power_Q1_Q4",
    "10.7.0": "Apparent_Power_Q2_Q3", "1At": "Apparent_Power_Q2_Q3",
    "13.7.0": "Power_Factor", "ot": "Power_Factor",
    "13.160.0": "Power_Factor_Last_Interval", "93": "Power_Factor_Last_Interval",
    "14.7.0": "Frequency", "Fn": "Frequency",
    "91.7.0": "Current_N", "1n": "Current_N",
    
    # Fase A
    "21.7.0": "Active_Power_Q1_Q4_L1", "PA": "Active_Power_Q1_Q4_L1",
    "22.7.0": "Active_Power_Q2_Q3_L1", "1PA": "Active_Power_Q2_Q3_L1",
    "23.7.0": "Reactive_Power_Q1_Q2_L1", "rA": "Reactive_Power_Q1_Q2_L1",
    "24.7.0": "Reactive_Power_Q3_Q4_L1", "1rA": "Reactive_Power_Q3_Q4_L1",
    "29.7.0": "Apparent_Power_Q1_Q4_L1", "AA": "Apparent_Power_Q1_Q4_L1",
    "30.7.0": "Apparent_Power_Q2_Q3_L1", "1AA": "Apparent_Power_Q2_Q3_L1",
    "31.7.0": "Current_L1", "1A": "Current_L1",
    "32.7.0": "Voltage_L1", "UA": "Voltage_L1",
    "33.7.0": "Power_Factor_L1", "oA": "Power_Factor_L1",
    
    # Fase B
    "41.7.0": "Active_Power_Q1_Q4_L2", "Pb": "Active_Power_Q1_Q4_L2",
    "42.7.0": "Active_Power_Q2_Q3_L2", "1Pb": "Active_Power_Q2_Q3_L2",
    "43.7.0": "Reactive_Power_Q1_Q2_L2", "rb": "Reactive_Power_Q1_Q2_L2",
    "44.7.0": "Reactive_Power_Q3_Q4_L2", "1rb": "Reactive_Power_Q3_Q4_L2",
    "49.7.0": "Apparent_Power_Q1_Q4_L2", "Ab": "Apparent_Power_Q1_Q4_L2",
    "50.7.0": "Apparent_Power_Q2_Q3_L2", "1Ab": "Apparent_Power_Q2_Q3_L2",
    "51.7.0": "Current_L2", "1b": "Current_L2",
    "52.7.0": "Voltage_L2", "Ub": "Voltage_L2",
    "53.7.0": "Power_Factor_L2", "ob": "Power_Factor_L2",

    # Fase C
    "61.7.0": "Active_Power_Q1_Q4_L3", "PC": "Active_Power_Q1_Q4_L3",
    "62.7.0": "Active_Power_Q2_Q3_L3", "1PC": "Active_Power_Q2_Q3_L3",
    "63.7.0": "Reactive_Power_Q1_Q2_L3", "rC": "Reactive_Power_Q1_Q2_L3",
    "64.7.0": "Reactive_Power_Q3_Q4_L3", "1rC": "Reactive_Power_Q3_Q4_L3",
    "69.7.0": "Apparent_Power_Q1_Q4_L3", "AC": "Apparent_Power_Q1_Q4_L3",
    "70.7.0": "Apparent_Power_Q2_Q3_L3", "1AC": "Apparent_Power_Q2_Q3_L3",
    "71.7.0": "Current_L3", "1C": "Current_L3",
    "72.7.0": "Voltage_L3", "UC": "Voltage_L3",
    "73.7.0": "Power_Factor_L3", "oC": "Power_Factor_L3",

    # Ângulos e Qualidade
    "81.7.1": "Angle_L1_L2", "C0": "Angle_L1_L2",
    "81.7.2": "Angle_L1_L3", "C1": "Angle_L1_L3",
    "81.7.12": "Angle_L2_L3", "C2": "Angle_L2_L3",
    "81.7.40": "Angle_L1", "C3": "Angle_L1",
    "81.7.51": "Angle_L2", "C4": "Angle_L2",
    "81.7.62": "Angle_L3", "C5": "Angle_L3",

    "12.140.0": "DRPm", "dP": "DRPm",
    "12.140.1": "DRPm_Last_Month", "1dP": "DRPm_Last_Month",
    "12.141.0": "DRCm", "dC": "DRCm",
    "12.141.1": "DRCm_Last_Month", "1dC": "DRCm_Last_Month",
    
    # Históricos DRP / DRC (1 a 12)
    "12.152.1": "DRPa_Max", "1b1": "DRPa_Max",
    "12.152.2": "DRPa_Max_2", "1b2": "DRPa_Max_2",
    "12.152.3": "DRPa_Max_3", "1b3": "DRPa_Max_3",
    "12.152.4": "DRPa_Max_4", "1b4": "DRPa_Max_4",
    "12.152.5": "DRPa_Max_5", "1b5": "DRPa_Max_5",
    "12.152.6": "DRPa_Max_6", "1b6": "DRPa_Max_6",
    "12.152.7": "DRPa_Max_7", "1b7": "DRPa_Max_7",
    "12.152.8": "DRPa_Max_8", "1b8": "DRPa_Max_8",
    "12.152.9": "DRPa_Max_9", "1b9": "DRPa_Max_9",
    "12.152.A": "DRPa_Max_10", "1bA": "DRPa_Max_10",
    "12.152.b": "DRPa_Max_11", "1bb": "DRPa_Max_11",
    "12.152.C": "DRPa_Max_12", "1bC": "DRPa_Max_12",

    "12.153.1": "DRCa_Max", "1C1": "DRCa_Max",
    "12.153.2": "DRCa_Max_2", "1C2": "DRCa_Max_2",
    "12.153.3": "DRCa_Max_3", "1C3": "DRCa_Max_3",
    "12.153.4": "DRCa_Max_4", "1C4": "DRCa_Max_4",
    "12.153.5": "DRCa_Max_5", "1C5": "DRCa_Max_5",
    "12.153.6": "DRCa_Max_6", "1C6": "DRCa_Max_6",
    "12.153.7": "DRCa_Max_7", "1C7": "DRCa_Max_7",
    "12.153.8": "DRCa_Max_8", "1C8": "DRCa_Max_8",
    "12.153.9": "DRCa_Max_9", "1C9": "DRCa_Max_9",
    "12.153.A": "DRCa_Max_10", "1CA": "DRCa_Max_10",
    "12.153.b": "DRCa_Max_11", "1Cb": "DRCa_Max_11",
    "12.153.C": "DRCa_Max_12", "1CC": "DRCa_Max_12",

    "32.152.0": "DRPa_L1", "r1": "DRPa_L1",
    "52.152.0": "DRPa_L2", "r2": "DRPa_L2",
    "72.152.0": "DRPa_L3", "r3": "DRPa_L3",
    "32.153.0": "DRCa_L1", "r4": "DRCa_L1",
    "52.153.0": "DRCa_L2", "r5": "DRCa_L2",
    "72.153.0": "DRCa_L3", "r6": "DRCa_L3",

    "12.204.1": "DRP_DRC_Time_1/DRP_DRC_Date_1", "1t1": "DRP_DRC_Time_1/DRP_DRC_Date_1",
    "12.204.2": "DRP_DRC_Time_2/DRP_DRC_Date_2", "1t2": "DRP_DRC_Time_2/DRP_DRC_Date_2",
    "12.204.3": "DRP_DRC_Time_3/DRP_DRC_Date_3", "1t3": "DRP_DRC_Time_3/DRP_DRC_Date_3",
    "12.204.4": "DRP_DRC_Time_4/DRP_DRC_Date_4", "1t4": "DRP_DRC_Time_4/DRP_DRC_Date_4",
    "12.204.5": "DRP_DRC_Time_5/DRP_DRC_Date_5", "1t5": "DRP_DRC_Time_5/DRP_DRC_Date_5",
    "12.204.6": "DRP_DRC_Time_6/DRP_DRC_Date_6", "1t6": "DRP_DRC_Time_6/DRP_DRC_Date_6",
    "12.204.7": "DRP_DRC_Time_7/DRP_DRC_Date_7", "1t7": "DRP_DRC_Time_7/DRP_DRC_Date_7",
    "12.204.8": "DRP_DRC_Time_8/DRP_DRC_Date_8", "1t8": "DRP_DRC_Time_8/DRP_DRC_Date_8",
    "12.204.9": "DRP_DRC_Time_9/DRP_DRC_Date_9", "1t9": "DRP_DRC_Time_9/DRP_DRC_Date_9",
    "12.204.A": "DRP_DRC_Time_10/DRP_DRC_Date_10", "1tA": "DRP_DRC_Time_10/DRP_DRC_Date_10",
    "12.204.b": "DRP_DRC_Time_11/DRP_DRC_Date_11", "1tb": "DRP_DRC_Time_11/DRP_DRC_Date_11",
    "12.204.C": "DRP_DRC_Time_12/DRP_DRC_Date_12", "1tC": "DRP_DRC_Time_12/DRP_DRC_Date_12",

    "12.198.0": "DIC_Current_Month", "d1": "DIC_Current_Month",
    "12.199.0": "FIC_Current_Month", "F1": "FIC_Current_Month",
    "12.200.0": "DMIC_Current_Month", "dn": "DMIC_Current_Month",
    "12.198.1": "DIC_Last_Month", "1d1": "DIC_Last_Month",
    "12.199.1": "FIC_Last_Month", "1F1": "FIC_Last_Month",
    "12.200.1": "DMIC_Last_Month", "1dn": "DMIC_Last_Month",

    "132.8.0": "UFER_Total", "65": "UFER_Total",
    "132.8.1": "UFER_T1", "66": "UFER_T1",
    "132.8.2": "UFER_T2", "68": "UFER_T2",
    "132.8.3": "UFER_T3", "67": "UFER_T3",
    "132.8.4": "UFER_T4", "6A": "UFER_T4",

    "128.6.0": "DMCR_Total_Value", "78": "DMCR_Total_Value",
    "128.6.1": "DMCR_T1_Value", "69": "DMCR_T1_Value",
    "128.6.2": "DMCR_T2_Value", "71": "DMCR_T2_Value",
    "128.6.3": "DMCR_T3_Value", "70": "DMCR_T3_Value",
    "128.6.4": "DMCR_T4_Value", "7A": "DMCR_T4_Value",

    "128.2.0": "Accumulated_DMCR_Total", "80": "Accumulated_DMCR_Total",
    "128.2.1": "Accumulated_DMCR_T1", "73": "Accumulated_DMCR_T1",
    "128.2.2": "Accumulated_DMCR_T2", "75": "Accumulated_DMCR_T2",
    "128.2.3": "Accumulated_DMCR_T3", "74": "Accumulated_DMCR_T3",
    "128.2.4": "Accumulated_DMCR_T4", "7b": "Accumulated_DMCR_T4",

    "128.14.0": "DMCR_Last_Reactive_Interval", "72": "DMCR_Last_Reactive_Interval",
    "128.14.1": "DMCR_Last_Reactive_Interval_T1", "7C": "DMCR_Last_Reactive_Interval_T1",
    "128.14.2": "DMCR_Last_Reactive_Interval_T2", "7d": "DMCR_Last_Reactive_Interval_T2",
    "128.14.3": "DMCR_Last_Reactive_Interval_T3", "7E": "DMCR_Last_Reactive_Interval_T3",
    "128.14.4": "DMCR_Last_Reactive_Interval_T4", "7F": "DMCR_Last_Reactive_Interval_T4",

    # Captura de Data/Hora de Máximas (Demandas)
    "Active_Reverse_Energy_Maximum_Demand_T1_Capture_Time": "Active_Reverse_Energy_Maximum_Demand_T1_Capture_Time",
    "Active_Reverse_Energy_Maximum_Demand_T2_Capture_Time": "Active_Reverse_Energy_Maximum_Demand_T2_Capture_Time",
    "Active_Reverse_Energy_Maximum_Demand_T3_Capture_Time": "Active_Reverse_Energy_Maximum_Demand_T3_Capture_Time",
    "Active_Reverse_Energy_Maximum_Demand_T4_Capture_Time": "Active_Reverse_Energy_Maximum_Demand_T4_Capture_Time",
    "Active_Reverse_Energy_Maximum_Demand_Total_Capture_Time": "Active_Reverse_Energy_Maximum_Demand_Total_Capture_Time",
    "Active_Direct_Energy_Maximum_Demand_T1_Capture_Time": "Active_Direct_Energy_Maximum_Demand_T1_Capture_Time",
    "Active_Direct_Energy_Maximum_Demand_T2_Capture_Time": "Active_Direct_Energy_Maximum_Demand_T2_Capture_Time",
    "Active_Direct_Energy_Maximum_Demand_T3_Capture_Time": "Active_Direct_Energy_Maximum_Demand_T3_Capture_Time",
    "Active_Direct_Energy_Maximum_Demand_T4_Capture_Time": "Active_Direct_Energy_Maximum_Demand_T4_Capture_Time",
    "Active_Direct_Energy_Maximum_Demand_Total_Capture_Time": "Active_Direct_Energy_Maximum_Demand_Total_Capture_Time",
    "Reactive_Q1_Energy_Maximum_Demand_T1_Capture_Time": "Reactive_Q1_Energy_Maximum_Demand_T1_Capture_Time",
    "Reactive_Q1_Energy_Maximum_Demand_T2_Capture_Time": "Reactive_Q1_Energy_Maximum_Demand_T2_Capture_Time",
    "Reactive_Q1_Energy_Maximum_Demand_T3_Capture_Time": "Reactive_Q1_Energy_Maximum_Demand_T3_Capture_Time",
    "Reactive_Q1_Energy_Maximum_Demand_T4_Capture_Time": "Reactive_Q1_Energy_Maximum_Demand_T4_Capture_Time",
    "Reactive_Q1_Energy_Maximum_Demand_Total_Capture_Time": "Reactive_Q1_Energy_Maximum_Demand_Total_Capture_Time",
    "Reactive_Q2_Energy_Maximum_Demand_T1_Capture_Time": "Reactive_Q2_Energy_Maximum_Demand_T1_Capture_Time",
    "Reactive_Q2_Energy_Maximum_Demand_T2_Capture_Time": "Reactive_Q2_Energy_Maximum_Demand_T2_Capture_Time",
    "Reactive_Q2_Energy_Maximum_Demand_T3_Capture_Time": "Reactive_Q2_Energy_Maximum_Demand_T3_Capture_Time",
    "Reactive_Q2_Energy_Maximum_Demand_T4_Capture_Time": "Reactive_Q2_Energy_Maximum_Demand_T4_Capture_Time",
    "Reactive_Q2_Energy_Maximum_Demand_Total_Capture_Time": "Reactive_Q2_Energy_Maximum_Demand_Total_Capture_Time",
    "Reactive_Q3_Energy_Maximum_Demand_T1_Capture_Time": "Reactive_Q3_Energy_Maximum_Demand_T1_Capture_Time",
    "Reactive_Q3_Energy_Maximum_Demand_T2_Capture_Time": "Reactive_Q3_Energy_Maximum_Demand_T2_Capture_Time",
    "Reactive_Q3_Energy_Maximum_Demand_T3_Capture_Time": "Reactive_Q3_Energy_Maximum_Demand_T3_Capture_Time",
    "Reactive_Q3_Energy_Maximum_Demand_T4_Capture_Time": "Reactive_Q3_Energy_Maximum_Demand_T4_Capture_Time",
    "Reactive_Q3_Energy_Maximum_Demand_Total_Capture_Time": "Reactive_Q3_Energy_Maximum_Demand_Total_Capture_Time",
    "Reactive_Q4_Energy_Maximum_Demand_T1_Capture_Time": "Reactive_Q4_Energy_Maximum_Demand_T1_Capture_Time",
    "Reactive_Q4_Energy_Maximum_Demand_T2_Capture_Time": "Reactive_Q4_Energy_Maximum_Demand_T2_Capture_Time",
    "Reactive_Q4_Energy_Maximum_Demand_T3_Capture_Time": "Reactive_Q4_Energy_Maximum_Demand_T3_Capture_Time",
    "Reactive_Q4_Energy_Maximum_Demand_T4_Capture_Time": "Reactive_Q4_Energy_Maximum_Demand_T4_Capture_Time",
    "Reactive_Q4_Energy_Maximum_Demand_Total_Capture_Time": "Reactive_Q4_Energy_Maximum_Demand_Total_Capture_Time",
    "DMCR_T1_DateTime": "DMCR_T1_DateTime",
    "DMCR_T2_DateTime": "DMCR_T2_DateTime",
    "DMCR_T3_DateTime": "DMCR_T3_DateTime",
    "DMCR_T4_DateTime": "DMCR_T4_DateTime",
    "DMCR_Total_DateTime": "DMCR_Total_DateTime",
}

# ---------------------------------------------------------------------------
# CARREGAMENTO EXTERNO DAS TELAS (XML / JSON)
# ---------------------------------------------------------------------------
# O mapa acima e o padrao embutido (fallback). Se existir um arquivo de telas
# ao lado do script/executavel (ou apontado por --telas / variavel ZEUS_TELAS),
# ele e carregado por cima, permitindo atualizar as telas sem mexer no codigo.
#
# Formato XML aceito (qualquer uma das formas abaixo):
#
#   <telas modo="mesclar">                  <!-- modo: mesclar (padrao) | substituir -->
#       <tela codigo="1.8.0" nome="Active_Direct_Energy_Total_Value"/>
#       <tela codigo="03"    nome="Active_Direct_Energy_Total_Value"/>
#       <tela nome="Voltage_L1">
#           <codigo>32.7.0</codigo>
#           <codigo>UA</codigo>
#       </tela>
#   </telas>
#
# Atributos aceitos: codigo/code/obis/id e nome/name/descricao/description.
# Formato JSON aceito: {"1.8.0": "Nome", "03": "Nome"}
#                  ou  {"modo": "mesclar", "telas": {...}}
#
# Se o arquivo NAO existir (ou estiver invalido), o parser continua funcionando
# normalmente com o mapa embutido.
# ---------------------------------------------------------------------------

DISPLAY_CODES_BUILTIN: Dict[str, str] = dict(DISPLAY_CODES)  # copia do mapa embutido
DISPLAY_CODES_SOURCE: str = "built-in"                       # de onde veio o mapa atual

# Nomes procurados automaticamente, na ordem
DISPLAY_CODES_FILENAMES = (
    "telas.xml", "display_codes.xml",
    "telas.json", "display_codes.json",
)
DISPLAY_CODES_ENV_VAR = "ZEUS_TELAS"

# Atributos lidos como CODIGO (todos os presentes viram chave da mesma tela)
_CODE_KEYS = ("codigo", "code", "abnt", "obis", "id", "chave", "key")
# Atributos lidos como NOME, em ordem de prioridade
_NAME_KEYS = ("nome", "name", "tela", "valor", "value", "descricao", "description")
# Atributos apenas informativos (guardados em DISPLAY_INFO, nao viram codigo/nome)
_INFO_KEYS = ("descricao", "description", "doc", "obis_completo", "hex", "unidade", "obs")

# Informacoes extras de cada tela, indexadas pelo codigo: descricao em portugues,
# OBIS completo, hex, numero no documento. Preenchido por load_display_codes().
DISPLAY_INFO: Dict[str, Dict[str, str]] = {}


def _display_codes_search_dirs() -> List[Path]:
    """Diretorios onde o arquivo de telas e procurado (script, exe/_MEIPASS, cwd)."""
    dirs: List[Path] = []
    congelado = bool(getattr(sys, "frozen", False))

    # No .exe, a pasta do executavel vem PRIMEIRO: assim um telas.xml colocado
    # ao lado do .exe substitui o que foi embutido no build (atualizar sem recompilar).
    if congelado:
        try:
            dirs.append(Path(sys.executable).resolve().parent)
        except Exception:
            pass
    try:
        dirs.append(Path(__file__).resolve().parent)
    except Exception:
        pass
    meipass = getattr(sys, "_MEIPASS", None)          # PyInstaller (one-file)
    if meipass:
        dirs.append(Path(meipass))
    if not congelado:
        try:
            dirs.append(Path(sys.executable).resolve().parent)
        except Exception:
            pass
    try:
        dirs.append(Path.cwd())
    except Exception:
        pass

    unicos: List[Path] = []
    for d in dirs:
        if d not in unicos:
            unicos.append(d)
    return unicos


def find_display_codes_file(path: Optional[str] = None) -> Optional[Path]:
    """Localiza o arquivo de telas. Retorna None se nenhum existir."""
    candidatos: List[Path] = []
    if path:
        candidatos.append(Path(path))
    env_path = os.environ.get(DISPLAY_CODES_ENV_VAR)
    if env_path:
        candidatos.append(Path(env_path))
    for pasta in _display_codes_search_dirs():
        for nome in DISPLAY_CODES_FILENAMES:
            candidatos.append(pasta / nome)

    for cand in candidatos:
        try:
            if cand.is_file():
                return cand.resolve()
        except OSError:
            continue
    return None


def _first_attr(elem, chaves) -> Optional[str]:
    """Primeiro atributo presente, na ordem de prioridade de `chaves`."""
    baixo = {str(k).lower(): str(v).strip() for k, v in elem.attrib.items()}
    for chave in chaves:
        if baixo.get(chave):
            return baixo[chave]
    return None


def _all_attrs(elem, chaves) -> List[str]:
    """Todos os atributos presentes cujas chaves estao em `chaves`."""
    baixo = {str(k).lower(): str(v).strip() for k, v in elem.attrib.items()}
    return [baixo[c] for c in chaves if baixo.get(c) and baixo[c] != "-"]


def _parse_display_codes_xml(caminho: Path) -> Tuple[Dict[str, str], str, Dict[str, Dict[str, str]]]:
    """Le o XML de telas. Retorna (mapa, modo, info)."""
    import xml.etree.ElementTree as ET

    raiz = ET.parse(str(caminho)).getroot()
    modo = (_first_attr(raiz, ("modo", "mode")) or "mesclar").lower()
    mapa: Dict[str, str] = {}
    info: Dict[str, Dict[str, str]] = {}

    for elem in raiz.iter():
        if elem is raiz:
            continue

        nome = _first_attr(elem, _NAME_KEYS)
        codigos: List[str] = _all_attrs(elem, _CODE_KEYS)   # ex.: codigo="1.8.0" abnt="03"

        # filhos <codigo>/<code> e <nome>/<name>
        for filho in list(elem):
            tag = filho.tag.lower()
            texto = (filho.text or "").strip()
            if not texto or texto == "-":
                continue
            if tag in _CODE_KEYS:
                codigos.append(texto)
            elif tag in _NAME_KEYS and not nome:
                nome = texto

        # forma <tela codigo="1.8.0">Nome</tela>
        if not nome and codigos:
            texto = (elem.text or "").strip()
            if texto:
                nome = texto

        # forma <tela nome="X">1.8.0</tela>
        if nome and not codigos:
            texto = (elem.text or "").strip()
            if texto and texto != "-":
                codigos.append(texto)

        if not (nome and codigos):
            continue

        extras = {k: v for k, v in ((c, _first_attr(elem, (c,))) for c in _INFO_KEYS) if v}
        for cod in codigos:
            if cod and cod not in mapa:      # dentro do arquivo, vale a 1a ocorrencia
                mapa[cod] = nome
                if extras:
                    info[cod] = dict(extras)

    return mapa, modo, info


def _parse_display_codes_json(caminho: Path) -> Tuple[Dict[str, str], str, Dict[str, Dict[str, str]]]:
    """Le o JSON de telas. Retorna (mapa, modo)."""
    import json

    dados = json.loads(caminho.read_text(encoding="utf-8"))
    modo = "mesclar"
    if isinstance(dados, dict) and any(k in dados for k in ("telas", "screens", "display_codes")):
        modo = str(dados.get("modo") or dados.get("mode") or "mesclar").lower()
        dados = dados.get("telas") or dados.get("screens") or dados.get("display_codes") or {}

    mapa: Dict[str, str] = {}
    if isinstance(dados, dict):
        for cod, nome in dados.items():
            if str(cod).strip() and str(nome).strip():
                mapa[str(cod).strip()] = str(nome).strip()
    elif isinstance(dados, list):  # [{"codigo": "...", "nome": "..."}, ...]
        for item in dados:
            if not isinstance(item, dict):
                continue
            baixo = {str(k).lower(): v for k, v in item.items()}
            nome = next((str(baixo[k]).strip() for k in _NAME_KEYS if baixo.get(k)), None)
            cod = next((str(baixo[k]).strip() for k in _CODE_KEYS if baixo.get(k)), None)
            if cod and nome and cod not in mapa:
                mapa[cod] = nome
    return mapa, modo, {}


def _reset_display_codes(motivo: str = "", verbose: bool = False) -> Dict[str, str]:
    global DISPLAY_CODES_SOURCE
    DISPLAY_CODES.clear()
    DISPLAY_CODES.update(DISPLAY_CODES_BUILTIN)
    DISPLAY_INFO.clear()
    DISPLAY_CODES_SOURCE = "built-in"
    if motivo:
        print(motivo)
    elif verbose:
        print("[TELAS] Nenhum arquivo externo encontrado; usando mapa embutido.")
    return DISPLAY_CODES


def load_display_codes(path: Optional[str] = None, verbose: bool = False) -> Dict[str, str]:
    """
    Carrega o mapa de telas de um arquivo externo (XML ou JSON), se existir.

    Se o arquivo nao existir ou estiver invalido, mantem o mapa embutido
    (DISPLAY_CODES_BUILTIN) e o parser continua funcionando normalmente.
    Retorna o proprio dicionario DISPLAY_CODES (atualizado no lugar).
    """
    global DISPLAY_CODES_SOURCE

    arquivo = find_display_codes_file(path)
    if arquivo is None:
        return _reset_display_codes(verbose=verbose)

    try:
        if arquivo.suffix.lower() == ".json":
            mapa, modo, info = _parse_display_codes_json(arquivo)
        else:
            mapa, modo, info = _parse_display_codes_xml(arquivo)
    except Exception as e:
        return _reset_display_codes(f"[TELAS] Falha ao ler '{arquivo}': {e}. Usando mapa embutido.")

    if not mapa:
        return _reset_display_codes(f"[TELAS] Arquivo '{arquivo}' nao tem telas validas. Usando mapa embutido.")

    DISPLAY_CODES.clear()
    if modo not in ("substituir", "replace", "exclusivo"):
        DISPLAY_CODES.update(DISPLAY_CODES_BUILTIN)   # o externo tem prioridade
    DISPLAY_CODES.update(mapa)
    DISPLAY_INFO.clear()
    DISPLAY_INFO.update(info)
    DISPLAY_CODES_SOURCE = str(arquivo)
    if verbose:
        print(f"[TELAS] {len(mapa)} telas carregadas de: {arquivo} (modo={modo})")
    return DISPLAY_CODES


def get_screen_info(codigo: str) -> Dict[str, str]:
    """Informacoes extras da tela (descricao, doc, obis_completo, hex), se o arquivo trouxer."""
    return DISPLAY_INFO.get(codigo, {})


def export_display_codes(path: Optional[str] = None) -> Path:
    """Gera um XML com as telas atuais, para servir de base de edicao/atualizacao."""
    from xml.sax.saxutils import quoteattr

    destino = Path(path) if path else (Path(__file__).resolve().parent / "telas.xml")
    linhas = ['<?xml version="1.0" encoding="utf-8"?>', '<telas modo="mesclar">']
    for cod, nome in DISPLAY_CODES.items():
        attrs = [f"codigo={quoteattr(str(cod))}", f"nome={quoteattr(str(nome))}"]
        for chave, valor in DISPLAY_INFO.get(cod, {}).items():
            if chave != "nome":
                attrs.append(f"{chave}={quoteattr(str(valor))}")
        linhas.append("    <tela " + " ".join(attrs) + "/>")
    linhas.append("</telas>")
    destino.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return destino


# Carrega automaticamente na importacao; nunca deixa o modulo quebrar por causa disso.
try:
    load_display_codes()
except Exception as _e:  # pragma: no cover - seguranca extra
    print(f"[TELAS] Erro inesperado ao carregar telas externas: {_e}. Usando mapa embutido.")

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

    # --- MERGE V1: GET SCREEN NAME ---
    def get_screen_name(self) -> str:
        """Retorna o nome legível da tela baseado no código OBIS ou ABNT/CODI"""
        if not self.obis:
            return "Tela desconhecida"
            
        # 1. Tenta achar o código exatamente como chegou (ex: "1.8.0", "03", "2A")
        exact_match = DISPLAY_CODES.get(self.obis)
        if exact_match:
            return exact_match
            
        # 2. Em alguns firmwares o DLMS vem com .0 sobrando (ex: 1.0.8.0 vs 1.8.0)
        # Limpa formatações estranhas e zeros à esquerda caso precise
        clean_code = self.obis.replace(".0.", ".").lstrip("0")
        
        # 3. Retorna o nome limpo ou o padrão
        return DISPLAY_CODES.get(clean_code, f"Tela não mapeada ({self.obis})")

    def get_signal_strength_text(self) -> str:
        try: return SIGNAL_STRENGTH_MAP.get(self.nic_signal_strength, f"Unknown ({self.nic_signal_strength:#x})")
        except: return "Unknown"

    def get_nic_type_text(self) -> str:
        try: return NIC_TYPE_MAP.get(self.nic_type, f"Unknown ({self.nic_type:#x})")
        except: return "Unknown"

    def get_quadrant_text(self) -> str:
        try: return QUADRANT_MAP.get(self.quadrant, f"Unknown ({self.quadrant:#x})")
        except: return "Unknown"

    def get_unit_text(self) -> str:
        try: return UNIT_MAP.get(self.unit, f"Unknown ({self.unit:#x})")
        except: return "Unknown"

    def get_active_flags(self) -> list:
        active = []
        for i in range(32):
            if (self.flags >> i) & 1:
                active.append((i, FLAG_NAMES.get(i, f"Reserved Bit {i}")))
        return active

    def get_active_flags2(self) -> list:
        active = []
        for i in range(11):
            if (self.flags2 >> i) & 1:
                active.append((i, FLAG2_NAMES.get(i, f"Reserved Bit {i}")))
        return active

    def __str__(self) -> str:
        output = []
        output.append("=" * 70)
        output.append("DISPLAY BUFFER (DISP.CMD.7) - ZEUS-NG SMART METER")
        output.append("STATUS: PARSE CONCLUIDO COM SUCESSO (alertas abaixo sao apenas informativos)")
        output.append("=" * 70)
        # --- MERGE V1: ADICIONADO NOME DA TELA NO TERMINAL ---
        output.append(f"\nNOME DA TELA:           {self.get_screen_name()}")
        output.append(f"OBIS Code:              {self.obis}")
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

        if self.warnings:
            output.append("\n" + "!" * 70)
            output.append("⚠ ALERTA: BYTES INESPERADOS RECEBIDOS DO MEDIDOR")
            output.append("!" * 70)
            for w in self.warnings:
                output.append(f"  - {w}")

        output.append("=" * 70)
        return "\n".join(output)

class DLMSDisplayParser:
    """Parser DLMS para Display Buffer"""

    _LCD_NUMBER_MAP = {
        0x3F: "0", 0x06: "1", 0x5B: "2", 0x4F: "3", 0x66: "4", 0x6D: "5", 0x7D: "6", 
        0x07: "7", 0x7F: "8", 0x6F: "9", 0x00: " ", 0x40: "-", 0x7C: "b", 0x71: "F", 
        0x5C: "o", 0x77: "A", 0x39: "C", 0x5E: "d", 0x3E: "U", 0x50: "r", 0x78: "t", 
        0x79: "E", 0x54: "n", 0x04: "I", 0x38: "L", 0x73: "P", 0x2D: "S", 0x76: "H", 0x58: "c",
    }

    @staticmethod
    def _read_axdr_length(data: bytes, offset: int) -> Tuple[int, int]:
        first = data[offset]
        offset += 1
        if first < 0x80:
            return first, offset
        count = first & 0x7F
        if count == 0:
            raise ValueError("Comprimento AXDR indefinido nao suportado")
        value = int.from_bytes(data[offset:offset + count], byteorder='big', signed=False)
        return value, offset + count

    @classmethod
    def _unwrap_get_response_data(cls, raw_bytes: bytes) -> bytes:
        if len(raw_bytes) < 6 or raw_bytes[0] != 0xC4:
            return raw_bytes
        data_tag_index = 4 if raw_bytes[3] == 0x00 else 3
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
        return raw_bytes[content_offset:end]

    @classmethod
    def _unwrap_single_axdr_string(cls, data: bytes) -> bytes:
        if len(data) < 2 or data[0] not in (AXDR_OCTET_STRING, AXDR_VISIBLE_STRING):
            return data
        try:
            length, content_offset = cls._read_axdr_length(data, 1)
        except ValueError:
            return data
        return data[content_offset:content_offset + length]

    @staticmethod
    def _bit(value: int, bit: int) -> int:
        return (value >> bit) & 0x01

    _SEGMENT_DIAGRAM_TEMPLATE = (
        " _a_", "f|   |b", " |_g_|", "e|   |c", " |_d_|",
    )
    _SEGMENT_POSITIONS = {
        "a": (0, 2), "b": (1, 6), "c": (3, 6), "d": (4, 3), "e": (3, 0), "f": (1, 0), "g": (2, 3),
    }
    _SEGMENT_BIT = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6}

    @classmethod
    def render_segment_diagram(cls, value: int, off_char: str = ".") -> str:
        key = value & 0xFF
        rows = [list(row) for row in cls._SEGMENT_DIAGRAM_TEMPLATE]
        for seg, (row, col) in cls._SEGMENT_POSITIONS.items():
            bit = cls._SEGMENT_BIT[seg]
            is_on = ((key >> bit) & 1) == 1
            rows[row][col] = seg if is_on else off_char
        return "\n".join("".join(row) for row in rows)

    @classmethod
    def describe_lcd_byte(cls, value: int) -> str:
        key = value & 0xFF
        char = cls._LCD_NUMBER_MAP.get(key)
        bits_msb_first = format(key, "08b")
        lines = [
            f"Byte: 0x{key:02X}  ({key} decimal)  =  {bits_msb_first} (bit7..bit0)",
            "", cls.render_segment_diagram(key), ""
        ]
        if char is not None:
            lines.append(f"Caractere reconhecido: '{char}'")
        else:
            lines.append("⚠ ALERTA: nenhum caractere conhecido (invalido).")
        return "\n".join(lines)

    @classmethod
    def _char_detail_block(cls, field_name: str, position: int, value: int) -> str:
        key = value & 0xFF
        char = cls._LCD_NUMBER_MAP.get(key)
        diagram = cls.render_segment_diagram(key)
        label = f"'{char}'" if char is not None else "???"
        return f"[{field_name} pos{position}] byte=0x{key:02X}\n{diagram}\n=> {label}"

    _HTML_CSS = """
        body { background:#cfd2d6; font-family: Arial, Helvetica, sans-serif; padding:24px; color:#222; }
        h2 { margin-top:0; color:#333; }
        .lcd-panel { background:#eef0ea; border:10px solid #3a3f44; border-radius:8px; padding:22px 26px; display:inline-block; box-shadow:0 6px 20px rgba(0,0,0,.4); }
        .top-row { display:flex; align-items:center; gap:12px; margin-bottom:16px; }
        .row { display:flex; align-items:flex-end; }
        .digit { position:relative; margin:0 2px; }
        .digit.sm { width:26px; height:44px; }
        .digit.md { width:36px; height:62px; }
        .digit.lg { width:46px; height:80px; }
        .seg { position:absolute; background:#d3d5cd; border-radius:1px; }
        .seg.on { background:#161616; }
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
        .sep.md { width:9px; height:62px; }
        .sep.lg { width:10px; height:80px; }
        .sep-dot { position:absolute; left:1px; width:6px; height:6px; border-radius:50%; background:#d3d5cd; }
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
        .relay-icon.on .relay-svg .relay-line, .relay-icon.on .relay-svg .relay-blade { stroke:#161616; }
        .relay-icon.on .relay-svg .relay-dot { fill:#161616; }
        .quad-icon { width:26px; height:26px; border-radius:50%; border:2px solid #b9bcb4; position:relative; overflow:hidden; }
        .quad-q { position:absolute; width:50%; height:50%; background:#eef0ea; }
        .quad-q.on { background:#161616; }
        .quad-q.q1 { top:0; right:0; }
        .quad-q.q2 { top:0; left:0; }
        .quad-q.q3 { bottom:0; left:0; }
        .quad-q.q4 { bottom:0; right:0; }
        .unit-col { display:flex; flex-direction:column; justify-content:center; gap:6px; font:bold 16px Arial; color:#c7c9c2; margin-left:14px; }
        .unit-col span.on, .unit-col div.on { color:#161616; }
        .unit-modular { font:bold 15px Arial; letter-spacing:1px; }
        .bottom-icons { display:flex; align-items:center; gap:16px; margin-top:18px; }
        .tri-row { display:flex; gap:12px; align-items:flex-end; }
        .tri { width:0; height:0; border-left:7px solid transparent; border-right:7px solid transparent; border-top:10px solid #d3d5cd; }
        .tri.on { border-top-color:#161616; }
        .alarm-icon { display:flex; flex-direction:column; align-items:center; gap:2px; }
        .alarm-tri-svg .alarm-tri-shape { fill:none; stroke:#d3d5cd; stroke-width:1.6; stroke-linejoin:round; }
        .alarm-tri-svg .alarm-tri-mark { fill:#d3d5cd; }
        .alarm-tri.on .alarm-tri-svg .alarm-tri-shape { stroke:#161616; }
        .alarm-tri.on .alarm-tri-svg .alarm-tri-mark { fill:#161616; }
        .alarm-grid { display:grid; grid-template-columns:repeat(3, 9px); gap:1px; font:bold 8px Arial; color:#c7c9c2; text-align:center; }
        .alarm-grid div.on { color:#161616; }
        .cap-ind-col { display:flex; flex-direction:column; gap:2px; font:bold 10px Arial; color:#c7c9c2; margin-top:8px; text-align:center; }
        .cap-ind-col span.on { color:#161616; }
        .block-icon { width:22px; height:22px; border-radius:50%; border:2px solid #d3d5cd; position:relative; }
        .block-icon.on { border-color:#161616; }
        .block-icon::after { content:""; position:absolute; top:50%; left:-2px; right:-2px; height:2px; background:#d3d5cd; transform:rotate(45deg); }
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
        .battery-icon::after { content:""; position:absolute; top:3px; right:-5px; width:3px; height:6px; background:#d3d5cd; }
        .battery-icon.on::after { background:#161616; }
        .push-icon { width:20px; height:16px; border:2px solid #d3d5cd; position:relative; color:#d3d5cd; font:bold 12px Arial; display:flex; align-items:center; justify-content:center; }
        .push-icon.on { border-color:#161616; color:#161616; }
        .badges { display:flex; flex-wrap:wrap; gap:6px; margin-top:20px; max-width:640px; }
        .badge { padding:4px 10px; border-radius:12px; font:12px monospace; background:#dfe1db; color:#8a8d86; border:1px solid #c7c9c2; }
        .badge.on { background:#2e5e33; color:#d8ffd9; border-color:#1f4523; }
        .meta { font:13px monospace; color:#333; margin-top:14px; line-height:1.6; }
        .warn { margin-top:16px; padding:10px 14px; background:#fff2f0; border:1px solid #e6a29c; color:#9c2b1f; font:12px monospace; border-radius:8px; max-width:640px; }
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
        if kind == ":":
            dots = '<div class="sep-dot on" style="top:32%;"></div><div class="sep-dot on" style="top:58%;"></div>'
        elif kind == ".":
            dots = '<div class="sep-dot on" style="bottom:4px; top:auto;"></div>'
        else:
            dots = ""
        return f'<div class="sep {size}">{dots}</div>'

    @staticmethod
    def _render_badges_html(display: "DisplayBuffer") -> str:
        badge_defs = [
            ("L1", display.flags & (1 << 0)), ("L2", display.flags & (1 << 1)), ("L3", display.flags & (1 << 2)),
            ("CAP", display.flags & (1 << 9)), ("IND", display.flags & (1 << 10)), ("ALT", display.flags & (1 << 11)),
            ("MAN", display.flags & (1 << 12)), ("Relay Closed", display.flags & (1 << 13)),
            ("Relay Open", display.flags & (1 << 14)), ("Comm", display.flags & (1 << 15)),
            ("Low Batt", display.flags & (1 << 16)), ("RTC Test", display.flags & (1 << 17)),
            ("Alarm 1", display.flags & (1 << 20)), ("Alarm 2", display.flags & (1 << 21)),
            ("Alarm 3", display.flags & (1 << 22)), ("Alarm 4", display.flags & (1 << 23)),
            ("Alarm 5", display.flags & (1 << 24)), ("Alarm 6", display.flags & (1 << 25)),
            ("!", display.flags & (1 << 26)),
        ]
        return "".join(f'<div class="badge{" on" if val else ""}">{name}</div>' for name, val in badge_defs)

    @staticmethod
    def _render_meta_html(display: "DisplayBuffer") -> str:
        # --- MERGE V1: INCLUIDO GET SCREEN NAME NO HTML ---
        return (
            '<div class="meta">'
            f"<strong>NOME DA TELA: {display.get_screen_name()}</strong><br>"
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
        if not display.warnings: return ""
        items = "".join(f"<div>- {w}</div>" for w in display.warnings)
        return f'<div class="warn"><b>\u26a0 ALERTA: bytes fora do esperado</b>{items}</div>'

    @classmethod
    def _phase_col_html(cls, display: "DisplayBuffer") -> str:
        def phase_row(label: str, present_bit: int, out_bit: int, in_bit: int) -> str:
            present_on = bool(display.flags & (1 << present_bit))
            direct_on = bool(display.flags & (1 << out_bit))
            reverse_on = bool(display.flags & (1 << in_bit))
            label_css = "phase on" if present_on else "phase"
            reverse_css = "phase-arrow left" + (" on" if reverse_on else "")
            direct_css = "phase-arrow right" + (" on" if direct_on else "")
            return f'<div class="{label_css}"><div class="{reverse_css}"></div><span>{label}</span><div class="{direct_css}"></div></div>'
        rows = phase_row("L1", 0, 3, 6) + phase_row("L2", 1, 4, 7) + phase_row("L3", 2, 5, 8)
        return f'<div class="phase-col">{rows}{cls._cap_ind_alt_man_html(display)}</div>'

    @staticmethod
    def _cap_ind_alt_man_html(display: "DisplayBuffer") -> str:
        cap_on, ind_on, alt_on, man_on = [bool(display.flags & (1 << b)) for b in (9, 10, 11, 12)]
        def span(text: str, on: bool) -> str: return f'<span class="{"on" if on else ""}">{text}</span>'
        return f'<div class="cap-ind-col"><div>{span("CAP", cap_on)}</div><div>{span("IND", ind_on)}</div><div>{span("ALT", alt_on)} {span("MAN", man_on)}</div></div>'

    @staticmethod
    def _tariff_html(display: "DisplayBuffer") -> str:
        on = display.tariff_num > 0
        text = f"T{display.tariff_num}" if on else "T-"
        return f'<div class="tariff-label{" on" if on else ""}">{text}</div>'

    @staticmethod
    def _antenna_html(display: "DisplayBuffer") -> str:
        bars_lit = {
            int(SignalStrength.SIGNAL_NONE): 0, int(SignalStrength.SIGNAL_0): 0, int(SignalStrength.SIGNAL_1): 1,
            int(SignalStrength.SIGNAL_2): 2, int(SignalStrength.SIGNAL_3): 3, int(SignalStrength.SIGNAL_4): 4,
        }.get(display.nic_signal_strength, 0)
        bars_html = "".join(f'<div class="antenna-bar{" on" if i < bars_lit else ""}"></div>' for i in range(4))
        is_rf, is_plc, is_cell = [display.nic_type == t for t in (int(NICType.NIC_RF), int(NICType.NIC_PLC), int(NICType.NIC_CELLULAR))]
        top_label = f'<span class="{"on" if is_rf else ""}">RF</span>/<span class="{"on" if is_plc else ""}">PLC</span>'
        bottom_label = f'<span class="{"on" if is_cell else ""}">CELL</span>'
        return f'<div class="antenna"><div class="antenna-bars">{bars_html}</div><div>{top_label}</div><div>{bottom_label}</div></div>'

    @staticmethod
    def _relay_icon_svg(kind: str) -> str:
        blades = '<line x1="9" y1="3" x2="25" y2="3" class="relay-blade"/>' if kind == "closed" else '<line x1="9" y1="0" x2="25" y2="6" class="relay-blade"/>'
        return f'<svg class="relay-svg" width="34" height="26" viewBox="0 0 34 26"><line x1="0" y1="6" x2="9" y2="6" class="relay-line"/><circle cx="9" cy="6" r="2.4" class="relay-dot"/><line x1="25" y1="6" x2="34" y2="6" class="relay-line"/><circle cx="25" cy="6" r="2.4" class="relay-dot"/>{blades}</svg>'

    @classmethod
    def _relay_html(cls, display: "DisplayBuffer") -> str:
        closed, opened = bool(display.flags & (1 << 13)), bool(display.flags & (1 << 14))
        return f'<div class="relay-group"><div class="relay-icon {"on" if opened else ""}">{cls._relay_icon_svg("open")}</div><div class="relay-icon {"on" if closed else ""}">{cls._relay_icon_svg("closed")}</div></div>'

    @staticmethod
    def _quadrant_icon_html(display: "DisplayBuffer") -> str:
        q = display.quadrant
        q1_on, q2_on, q3_on, q4_on = [q in (i, int(Quadrant.QUADRANT_ALL)) for i in (int(Quadrant.QUADRANT_1), int(Quadrant.QUADRANT_2), int(Quadrant.QUADRANT_3), int(Quadrant.QUADRANT_4))]
        def q_div(css: str, on: bool) -> str: return f'<div class="quad-q {css}{" on" if on else ""}"></div>'
        return f'<div class="quad-icon">{q_div("q1", q1_on)}{q_div("q2", q2_on)}{q_div("q3", q3_on)}{q_div("q4", q4_on)}</div>'

    @staticmethod
    def _unit_bit_flags(display: "DisplayBuffer") -> dict:
        base = {"k": False, "M": False, "V": False, "W": False, "A": False, "r": False, "h": False, "Hz": False, "C": False, "pct": False}
        bits = display.unit_bits
        if bits:
            for k, bit in [("k",0),("M",1),("V",2),("W",3),("A",4),("r",5),("h",6),("Hz",10),("C",11),("pct",12)]: base[k] = bool(bits & (1<<bit))
            return base
        fallback = {
            int(Unit.CELSIUS): {"C": True}, int(Unit.HERTZ): {"Hz": True}, int(Unit.PERCENTAGE): {"pct": True},
            int(Unit.KW): {"k": True, "W": True}, int(Unit.KWH): {"k": True, "W": True, "h": True},
            int(Unit.MWH): {"M": True, "W": True, "h": True}, int(Unit.KVAR): {"k": True, "V": True, "A": True, "r": True},
            int(Unit.KVARH): {"k": True, "V": True, "A": True, "r": True, "h": True}, int(Unit.MVARH): {"M": True, "V": True, "A": True, "r": True, "h": True},
            int(Unit.VOLT): {"V": True}, int(Unit.AMPERE): {"A": True}, int(Unit.VA): {"V": True, "A": True}, int(Unit.DEGREES): {"C": True},
        }
        base.update(fallback.get(display.unit, {}))
        return base

    @classmethod
    def _units_col_html(cls, display: "DisplayBuffer") -> str:
        f = cls._unit_bit_flags(display)
        def span(key: str, text: str) -> str: return f'<span class="{"on" if f[key] else ""}">{text}</span>'
        return f'<div class="unit-col"><div>{span("C", "°C")}</div><div>{span("Hz", "Hz")} {span("pct", "%")}</div><div class="unit-modular">{span("M", "M")}{span("k", "k")} {span("V", "V")}{span("W", "W")}{span("A", "A")}{span("r", "r")} {span("h", "h")}</div></div>'

    @staticmethod
    def _arrow_triangles_html(display: "DisplayBuffer") -> str:
        tris = "".join(f'<div class="tri{" on" if display.flags & (1 << b) else ""}"></div>' for b in [27, 28, 29, 30, 31])
        return f'<div class="tri-row">{tris}</div>'

    @staticmethod
    def _alarm_icon_html(display: "DisplayBuffer") -> str:
        excl_on = bool(display.flags & (1 << 26))
        nums = "".join(f'<div class="{"on" if bool(display.flags & (1 << b)) else ""}">{i}</div>' for i, b in enumerate([20, 21, 22, 23, 24, 25], 1))
        triangle_svg = '<svg class="alarm-tri-svg" width="20" height="18" viewBox="0 0 20 18"><polygon points="10,1 19,16 1,16" class="alarm-tri-shape"/><rect x="9" y="6" width="2" height="6" class="alarm-tri-mark"/><rect x="9" y="13" width="2" height="2" class="alarm-tri-mark"/></svg>'
        return f'<div class="alarm-icon"><div class="alarm-tri{" on" if excl_on else ""}">{triangle_svg}</div><div class="alarm-grid">{nums}</div></div>'

    @staticmethod
    def _block_icon_html(display: "DisplayBuffer") -> str: return f'<div class="block-icon{" on" if bool(display.flags & (1 << 19)) else ""}"></div>'

    @staticmethod
    def _dem_label_html() -> str: return '<div class="dem-label">DEM</div>'

    @staticmethod
    def _clock_icon_html(display: "DisplayBuffer") -> str: return f'<div class="clock-icon{" on" if bool(display.flags & (1 << 17)) else ""}"><div class="hand h1"></div><div class="hand h2"></div></div>'

    @staticmethod
    def _battery_icon_html(display: "DisplayBuffer") -> str: return f'<div class="battery-icon{" on" if bool(display.flags & (1 << 16)) else ""}"></div>'

    @staticmethod
    def _push_icon_html(display: "DisplayBuffer") -> str: return f'<div class="push-icon{" on" if bool(display.flags & (1 << 15)) else ""}">→</div>'

    @classmethod
    def _html_document(cls, obis_row: str, data_row: str, display: "DisplayBuffer") -> str:
        top_row = f'<div class="top-row">{cls._phase_col_html(display)}<div class="row">{obis_row}</div>{cls._tariff_html(display)}{cls._antenna_html(display)}{cls._relay_html(display)}{cls._quadrant_icon_html(display)}</div>'
        middle_row = f'<div class="top-row" style="margin-bottom:0;"><div class="row">{data_row}</div>{cls._units_col_html(display)}</div>'
        bottom_row = f'<div class="bottom-icons">{cls._arrow_triangles_html(display)}{cls._alarm_icon_html(display)}{cls._block_icon_html(display)}{cls._dem_label_html()}{cls._clock_icon_html(display)}{cls._battery_icon_html(display)}{cls._push_icon_html(display)}</div>'
        return f'<!DOCTYPE html>\n<html lang="pt-br">\n<head>\n<meta charset="utf-8">\n<title>ZEUS-NG Display Buffer</title>\n<style>{cls._HTML_CSS}</style>\n</head>\n<body>\n  <div class="lcd-panel">\n    {top_row}\n    {middle_row}\n    {bottom_row}\n  </div>\n  <div class="badges">{cls._render_badges_html(display)}</div>\n  {cls._render_meta_html(display)}\n  {cls._render_warnings_html(display)}\n</body>\n</html>\n'

    @classmethod
    def _build_html(cls, seg: bytes, display: "DisplayBuffer") -> str:
        obis_bytes = [seg[6], seg[5], seg[4], seg[3], seg[2], seg[1]]
        obis_dot_after = [cls._bit(seg[0], i) for i in (4, 3, 2, 1, 0)]
        obis_parts = []
        for i, b in enumerate(obis_bytes):
            obis_parts.append(cls._digit_html(b, "md"))
            if i < len(obis_dot_after) and obis_dot_after[i]: obis_parts.append(cls._sep_html(".", "md"))
        
        data_bytes = [seg[15], seg[14], seg[13], seg[12], seg[11], seg[10], seg[9], seg[8]]
        p6, p7, p8, p9, p10, p11 = [cls._bit(seg[7], b) for b in (5, 3, 2, 4, 1, 0)]
        data_seps_after = ["", "", "", ":" if (p6 and p7) else ("." if p7 else ""), "." if p8 else "", ":" if (p9 and p10) else ("." if p10 else ""), "." if p11 else ""]
        
        data_parts = []
        for i, b in enumerate(data_bytes):
            data_parts.append(cls._digit_html(b, "lg"))
            if i < len(data_seps_after) and data_seps_after[i]: data_parts.append(cls._sep_html(data_seps_after[i], "lg"))
        
        return cls._html_document("".join(obis_parts), "".join(data_parts), display)

    @classmethod
    def _build_html_simple(cls, display: "DisplayBuffer") -> str:
        return cls._html_document(
            f'<div style="font:24px monospace; color:#ff3b30;">{display.obis or "&nbsp;"}</div>',
            f'<div style="font:48px monospace; color:#ff3b30;">{display.data or "&nbsp;"}</div>',
            display
        )

    @classmethod
    def _lcd_char(cls, value: int, position: int, field_name: str, warnings: List[str], char_details: Optional[List[str]] = None) -> str:
        key = value & 0xFF
        char = cls._LCD_NUMBER_MAP.get(key)
        if char_details is not None: char_details.append(cls._char_detail_block(field_name, position, key))
        if char is None:
            warnings.append(f"Campo '{field_name}' (pos {position} = 0x{key:02X}): invalido.")
            return "?"
        return char

    @classmethod
    def _build_obis_from_segment(cls, seg: bytes, warnings: List[str], char_details: Optional[List[str]] = None) -> str:
        text = ""
        for i, (byte_idx, bit_idx) in enumerate(zip([6, 5, 4, 3, 2, 1], [4, 3, 2, 1, 0, -1])):
            text += cls._lcd_char(seg[byte_idx], byte_idx, "OBIS", warnings, char_details)
            if bit_idx >= 0 and cls._bit(seg[0], bit_idx): text += "."
        return text.strip()

    @classmethod
    def _build_data_from_segment(cls, seg: bytes, warnings: List[str], char_details: Optional[List[str]] = None) -> str:
        text = ""
        for b in [15, 14, 13, 12]: text += cls._lcd_char(seg[b], b, "Data", warnings, char_details)
        p6, p7 = cls._bit(seg[7], 5), cls._bit(seg[7], 3)
        if p6 and p7: text += ":"
        elif not p6 and p7: text += "."
        text += cls._lcd_char(seg[11], 11, "Data", warnings, char_details)
        if cls._bit(seg[7], 2): text += "."
        text += cls._lcd_char(seg[10], 10, "Data", warnings, char_details)
        p9, p10 = cls._bit(seg[7], 4), cls._bit(seg[7], 1)
        if p9 and p10: text += ":"
        elif not p9 and p10: text += "."
        text += cls._lcd_char(seg[9], 9, "Data", warnings, char_details)
        if cls._bit(seg[7], 0): text += "."
        text += cls._lcd_char(seg[8], 8, "Data", warnings, char_details)
        return text.strip()

    @staticmethod
    def _tariff_from_segment(value: int, warnings: List[str]) -> int:
        known = {0x00: 0, 0x86: 1, 0xDB: 2, 0xCF: 3, 0xE6: 4, 0xFF: 8}
        if value not in known:
            warnings.append(f"Tarifa invalida (0x{value:02X})")
            return 0
        return known[value]

    @staticmethod
    def _unit_from_magnitude_bytes(value: int, warnings: List[str]) -> int:
        magnitude_map = {0x0009: Unit.KW, 0x000A: Unit.MWH, 0x0049: Unit.KWH, 0x004A: Unit.MWH, 0x0004: Unit.VOLT, 0x0010: Unit.AMPERE, 0x0400: Unit.HERTZ, 0x1000: Unit.PERCENTAGE, 0x0035: Unit.KVAR, 0x0075: Unit.KVARH, 0x0076: Unit.MVARH}
        if value == 0x0000: return int(Unit.NO_UNIT)
        if value not in magnitude_map:
            warnings.append(f"Magnitude desconhecida (0x{value:04X})")
            return int(Unit.NO_UNIT)
        return int(magnitude_map[value])

    @staticmethod
    def _quadrant_from_segment(value: int, warnings: List[str]) -> int:
        b = lambda bit: ((value >> bit) & 1) == 1
        axis = b(4)
        selected = sum([b(0), b(1), b(2), b(3)])
        if not axis: return int(Quadrant.QUADRANT_NONE)
        if selected == 4: return int(Quadrant.QUADRANT_ALL)
        if selected == 1: return [int(Quadrant.QUADRANT_1), int(Quadrant.QUADRANT_2), int(Quadrant.QUADRANT_3), int(Quadrant.QUADRANT_4)][[b(0), b(1), b(2), b(3)].index(True)]
        if selected == 0: return int(Quadrant.QUADRANT_0)
        warnings.append("Quadrantes invalidos.")
        return int(Quadrant.QUADRANT_NONE)

    @staticmethod
    def _signal_and_nic_from_segment(signal_byte: int, module_byte: int, warnings: List[str]) -> Tuple[int, int]:
        b = lambda bit: ((signal_byte >> bit) & 1) == 1
        antenna = b(4)
        bars = [b(0), b(1), b(2), b(3)]
        signal = SignalStrength.SIGNAL_NONE
        if antenna:
            if bars == [True, True, True, True]: signal = SignalStrength.SIGNAL_4
            elif bars == [True, True, True, False]: signal = SignalStrength.SIGNAL_3
            elif bars == [True, True, False, False]: signal = SignalStrength.SIGNAL_2
            elif bars == [True, False, False, False]: signal = SignalStrength.SIGNAL_1
            elif bars == [False, False, False, False]: signal = SignalStrength.SIGNAL_0
        nic_map = {0x00: NICType.NIC_NONE, 0x20: NICType.NIC_RF, 0x40: NICType.NIC_PLC, 0x80: NICType.NIC_CELLULAR}
        return int(signal), nic_map.get(module_byte, NICType.NIC_NONE)

    @classmethod
    def _parse_compact_display_buffer(cls, payload: bytes) -> DisplayBuffer:
        if len(payload) != 39: raise ValueError(f"Tamanho de payload compacto invalido: {len(payload)}")
        warnings, char_details = [], []
        obis = cls._build_obis_from_segment(payload, warnings, char_details)
        data = cls._build_data_from_segment(payload, warnings, char_details)
        tariff_num = cls._tariff_from_segment(payload[20], warnings)
        quadrant = cls._quadrant_from_segment(payload[22], warnings)
        nic_signal, nic_type = cls._signal_and_nic_from_segment(payload[21], payload[27], warnings)
        magnitude = ((payload[17] << 8) | payload[16]) & 0xFFFF
        unit = cls._unit_from_magnitude_bytes(magnitude, warnings)
        
        flags = 0
        flags |= cls._bit(payload[22], 5) << 0
        flags |= cls._bit(payload[22], 6) << 1
        flags |= cls._bit(payload[22], 7) << 2
        flags |= (1 if (cls._bit(payload[23], 3) and cls._bit(payload[24], 0)) else 0) << 3
        flags |= (1 if (cls._bit(payload[23], 4) and cls._bit(payload[24], 1)) else 0) << 4
        flags |= (1 if (cls._bit(payload[23], 5) and cls._bit(payload[24], 2)) else 0) << 5
        flags |= (1 if (cls._bit(payload[23], 0) and cls._bit(payload[24], 0)) else 0) << 6
        flags |= (1 if (cls._bit(payload[23], 1) and cls._bit(payload[24], 1)) else 0) << 7
        flags |= (1 if (cls._bit(payload[23], 2) and cls._bit(payload[24], 2)) else 0) << 8
        flags |= cls._bit(payload[18], 5) << 9
        flags |= cls._bit(payload[18], 6) << 10
        flags |= cls._bit(payload[25], 5) << 11
        flags |= cls._bit(payload[25], 7) << 12
        flags |= (1 if (cls._bit(payload[21], 5) and cls._bit(payload[21], 7)) else 0) << 13
        flags |= (1 if (cls._bit(payload[21], 6) and cls._bit(payload[21], 7)) else 0) << 14
        flags |= cls._bit(payload[25], 1) << 15
        flags |= cls._bit(payload[25], 0) << 16
        flags |= cls._bit(payload[28], 1) << 17
        flags |= cls._bit(payload[28], 0) << 19 
        flags |= cls._bit(payload[19], 2) << 20
        flags |= cls._bit(payload[19], 3) << 21
        flags |= cls._bit(payload[19], 4) << 22
        flags |= cls._bit(payload[19], 5) << 23
        flags |= cls._bit(payload[19], 6) << 24
        flags |= cls._bit(payload[19], 7) << 25
        flags |= cls._bit(payload[19], 1) << 26
        flags |= cls._bit(payload[18], 0) << 27
        flags |= cls._bit(payload[18], 1) << 28
        flags |= cls._bit(payload[18], 2) << 29
        flags |= cls._bit(payload[18], 3) << 30
        flags |= cls._bit(payload[18], 4) << 31

        flags2 = 0
        for i in range(6): flags2 |= cls._bit(payload[7], i) << i
        for i, bit in enumerate([4, 3, 2, 1, 0], 6): flags2 |= cls._bit(payload[0], bit) << i

        result = DisplayBuffer(obis, data, tariff_num, nic_signal, nic_type, quadrant, unit, flags, flags2, warnings, char_details, unit_bits=magnitude)
        result.html = cls._build_html(payload, result)
        return result

    @staticmethod
    def bytes_to_visible_string(data: bytes, length: int, offset: int) -> Tuple[str, int]:
        str_length, offset = DLMSDisplayParser._read_axdr_length(data, offset + 1)
        string_data = data[offset:offset + str_length]
        result = string_data.decode('ascii', errors='ignore').strip('\x00').strip()
        return result if result else string_data.hex(), offset + str_length

    @staticmethod
    def bytes_to_unsigned(data: bytes, offset: int) -> Tuple[int, int]: return data[offset + 1], offset + 2

    @staticmethod
    def bytes_to_enum(data: bytes, offset: int) -> Tuple[int, int]: return data[offset + 1], offset + 2

    @staticmethod
    def bytes_to_double_long_unsigned(data: bytes, offset: int) -> Tuple[int, int]: return int.from_bytes(data[offset + 1:offset + 5], byteorder='big', signed=False), offset + 5

    @staticmethod
    def skip_structure_tag(data: bytes, offset: int) -> int: return offset + 2

    @classmethod
    def print_hex_debug(cls, data: bytes, offset: int = 0, length: int = 32) -> None:
        print("\n[HEX DUMP]")
        for i in range(offset, min(offset + length, len(data))):
            if i % 16 == 0: print(f"  {i:04X}: ", end="")
            print(f"{data[i]:02X} ", end="")
            if (i + 1) % 16 == 0: print()
        if len(data) % 16 != 0: print()

    @classmethod
    def parse(cls, raw_bytes: bytes, verbose: bool = False) -> Optional[DisplayBuffer]:
        try:
            offset = 0
            payload = cls._unwrap_get_response_data(raw_bytes)
            payload = cls._unwrap_single_axdr_string(payload)
            if len(payload) == 39: return cls._parse_compact_display_buffer(payload)
            
            structure_pos = payload.find(bytes([AXDR_STRUCTURE, 0x08]))
            if structure_pos < 0: raise ValueError("Payload nao contem estrutura AXDR DISP.CMD.7 (02 08).")
            
            offset = cls.skip_structure_tag(payload, structure_pos)
            obis, offset = cls.bytes_to_visible_string(payload, 6, offset)
            data, offset = cls.bytes_to_visible_string(payload, 8, offset)
            tariff_num, offset = cls.bytes_to_unsigned(payload, offset)
            nic_signal_strength, offset = cls.bytes_to_enum(payload, offset)
            nic_type, offset = cls.bytes_to_enum(payload, offset)
            quadrant, offset = cls.bytes_to_enum(payload, offset)
            unit, offset = cls.bytes_to_enum(payload, offset)
            flags, offset = cls.bytes_to_double_long_unsigned(payload, offset)
            flags2, offset = cls.bytes_to_double_long_unsigned(payload, offset)
            
            result = DisplayBuffer(obis, data, tariff_num, nic_signal_strength, nic_type, quadrant, unit, flags, flags2)
            result.html = cls._build_html_simple(result)
            return result
        except Exception as e:
            print(f"[ERRO] Falha ao fazer parse: {e}")
            return None

def print_byte_diagram(raw_value: str) -> None:
    try: value = int(raw_value.strip().replace("0x", "").replace("0X", ""), 16)
    except ValueError: return print(f"[ERRO] Byte hex invalido: {raw_value!r}")
    print(DLMSDisplayParser.describe_lcd_byte(value))

def parse_frame_hex(frame_hex: str, verbose: bool = True, html_path: Optional[str] = None) -> Optional[DisplayBuffer]:
    cleaned = "".join(frame_hex.replace("0x", "").replace("0X", "").replace(",", " ").replace("\n", " ").replace("\r", " ").split())
    try: frame_bytes = bytes.fromhex(cleaned)
    except ValueError as e: return print(f"[ERRO] Frame hex invalido: {e}")
    
    print(f"Frame recebido ({len(frame_bytes)} bytes):")
    display_buffer = DLMSDisplayParser().parse(frame_bytes, verbose=verbose)
    if display_buffer:
        print(display_buffer)
        out_path = Path(html_path) if html_path else Path(__file__).resolve().parent / "zeus_display.html"
        try:
            out_path.write_text(display_buffer.html, encoding="utf-8")
            print(f"\n[HTML] Display gerado em: {out_path}")
        except OSError as e: print(f"\n[ERRO] Falha ao salvar HTML: {e}")
    else: print("[ERRO] Falha ao fazer parse do frame")
    return display_buffer

def main():
    args = sys.argv[1:]

    # --- TELAS EXTERNAS: --telas <arquivo.xml|.json> ---
    if args and args[0].lower() in ("--telas", "--screens", "-t"):
        if len(args) < 2:
            return print("Uso: python script.py --telas telas.xml [frame hex]")
        load_display_codes(args[1], verbose=True)
        args = args[2:]

    # --- TELAS EXTERNAS: --exportar-telas [arquivo.xml] ---
    if args and args[0].lower() in ("--exportar-telas", "--export-telas", "--export-screens"):
        destino = export_display_codes(args[1] if len(args) > 1 else None)
        return print(f"[TELAS] {len(DISPLAY_CODES)} telas exportadas para: {destino}")

    if args and args[0].lower() in ("--byte", "-b", "byte"):
        return print_byte_diagram(args[1]) if len(args) > 1 else print("Uso: python script.py --byte 0x7C")
        
    args_hex = " ".join(args).strip()
    if args_hex and not args_hex.startswith("--"):
        return parse_frame_hex(args_hex)
        
    # --- MERGE V1: CONTORNO PARA DEBUGGER DO VS CODE ---
    print("Cole o frame HEX recebido do medidor (ex: C4 01 C1 00 09 27 ...).")
    print("Ou digite 'teste' para rodar um exemplo automático.")
    print("Deixe em branco (Enter) ou digite 'sair' para encerrar.\n")
    
    while True:
        try:
            entry = input("Frame HEX > ").strip()
        except (KeyboardInterrupt, EOFError):
            break # Tratamento para caso o depurador do VS Code bloqueie o input()
            
        if not entry or entry.lower() in ("sair", "exit", "quit"):
            break
        elif entry.lower().startswith("byte "):
            print_byte_diagram(entry[5:].strip())
        else:
            parse_frame_hex(entry)
        print()

if __name__ == "__main__":
    main()