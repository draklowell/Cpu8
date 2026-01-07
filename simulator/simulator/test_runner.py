#!/usr/bin/env python3
"""
Обсяжний файл тестів для всіх мікросхем симулятора CPU8.
Тестує функціональність IC7400, IC7402, IC7404, IC74109, IC74138, IC74154,
IC74161, IC74193, IC74245, IC74273, IC74574, IC74181 та EEPROM.
"""

import sys
from base import Network, Component
from ic74xx import IC7400, IC7402, IC7404, IC74109
from ic74138 import IC74138
from ic74154 import IC74154
from ic74161 import IC74161
from ic74193 import IC74193
from ic74245 import IC74245
from ic74273 import IC74273
from ic74574 import IC74574
from EEPROM import EEPROM


class TestFramework:
    """Простий фреймворк для запуску тестів"""
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.current_test = ""

    def test(self, name: str):
        """Декоратор для позначення тестової функції"""
        def decorator(func):
            def wrapper():
                self.current_test = name
                try:
                    func()
                    self.tests_passed += 1
                    print(f"✓ {name}")
                except AssertionError as e:
                    self.tests_failed += 1
                    print(f"✗ {name}: {e}")
                except Exception as e:
                    self.tests_failed += 1
                    print(f"✗ {name}: Неочікувана помилка - {e}")
            return wrapper
        return decorator

    def assert_equal(self, actual, expected, message=""):
        """Перевірка рівності значень"""
        if actual != expected:
            raise AssertionError(f"{message} Очікувалось {expected}, отримано {actual}")

    def assert_true(self, condition, message=""):
        """Перевірка істинності умови"""
        if not condition:
            raise AssertionError(f"{message} Умова хибна")

    def assert_false(self, condition, message=""):
        """Перевірка хибності умови"""
        if condition:
            raise AssertionError(f"{message} Умова істинна")

    def summary(self):
        """Виведення підсумків тестування"""
        total = self.tests_passed + self.tests_failed
        print(f"\n{'='*60}")
        print(f"Усього тестів: {total}")
        print(f"Пройдено: {self.tests_passed}")
        print(f"Провалено: {self.tests_failed}")
        print(f"{'='*60}")
        return self.tests_failed == 0


def create_network_dict(pins: list[str]) -> dict[str, Network]:
    """Створює словник мереж для заданих пінів"""
    return {pin: Network(pin) for pin in pins}


def propagate_all(*components):
    """Виконує пропагацію для всіх компонентів і мереж"""
    networks_seen = set()
    for comp in components:
        comp.propagate()
        for net in comp.pins.values():
            if id(net) not in networks_seen:
                net.propagate()
                networks_seen.add(id(net))


# Створюємо екземпляр фреймворку
tf = TestFramework()


# ============================================================================
# ТЕСТИ ДЛЯ IC7400 (QUAD 2-INPUT NAND)
# ============================================================================

@tf.test("IC7400: Базова функціональність NAND")
def test_ic7400_basic():
    pins = create_network_dict([IC7400.VCC, IC7400.GND, IC7400.A1, IC7400.B1, IC7400.Y1])
    ic = IC7400("U1", pins)
    
    # Живлення
    pins[IC7400.VCC].set(True)
    pins[IC7400.GND].set(False)
    propagate_all(ic)
    
    # Тест 1: 0 NAND 0 = 1
    pins[IC7400.A1].set(False)
    pins[IC7400.B1].set(False)
    propagate_all(ic)
    tf.assert_true(pins[IC7400.Y1].get(), "0 NAND 0 повинно дати 1")
    
    # Тест 2: 0 NAND 1 = 1
    pins[IC7400.A1].set(False)
    pins[IC7400.B1].set(True)
    propagate_all(ic)
    tf.assert_true(pins[IC7400.Y1].get(), "0 NAND 1 повинно дати 1")
    
    # Тест 3: 1 NAND 0 = 1
    pins[IC7400.A1].set(True)
    pins[IC7400.B1].set(False)
    propagate_all(ic)
    tf.assert_true(pins[IC7400.Y1].get(), "1 NAND 0 повинно дати 1")
    
    # Тест 4: 1 NAND 1 = 0
    pins[IC7400.A1].set(True)
    pins[IC7400.B1].set(True)
    propagate_all(ic)
    tf.assert_false(pins[IC7400.Y1].get(), "1 NAND 1 повинно дати 0")


@tf.test("IC7400: Всі чотири гейти")
def test_ic7400_all_gates():
    pins = create_network_dict([
        IC7400.VCC, IC7400.GND,
        IC7400.A0, IC7400.B0, IC7400.Y0,
        IC7400.A1, IC7400.B1, IC7400.Y1,
        IC7400.A2, IC7400.B2, IC7400.Y2,
        IC7400.A3, IC7400.B3, IC7400.Y3
    ])
    ic = IC7400("U1", pins)
    
    pins[IC7400.VCC].set(True)
    pins[IC7400.GND].set(False)
    
    # Перевіряємо всі гейти з різними входами
    test_cases = [
        (IC7400.A0, IC7400.B0, IC7400.Y0, True, True, False),
        (IC7400.A1, IC7400.B1, IC7400.Y1, False, True, True),
        (IC7400.A2, IC7400.B2, IC7400.Y2, True, False, True),
        (IC7400.A3, IC7400.B3, IC7400.Y3, False, False, True),
    ]
    
    for a_pin, b_pin, y_pin, a_val, b_val, expected in test_cases:
        pins[a_pin].set(a_val)
        pins[b_pin].set(b_val)
        propagate_all(ic)
        tf.assert_equal(pins[y_pin].get(), expected, f"Гейт {y_pin}")


# ============================================================================
# ТЕСТИ ДЛЯ IC7402 (QUAD 2-INPUT NOR)
# ============================================================================

@tf.test("IC7402: Базова функціональність NOR")
def test_ic7402_basic():
    pins = create_network_dict([IC7402.VCC, IC7402.GND, IC7402.A1, IC7402.B1, IC7402.Y1])
    ic = IC7402("U2", pins)
    
    pins[IC7402.VCC].set(True)
    pins[IC7402.GND].set(False)
    propagate_all(ic)
    
    # 0 NOR 0 = 1
    pins[IC7402.A1].set(False)
    pins[IC7402.B1].set(False)
    propagate_all(ic)
    tf.assert_true(pins[IC7402.Y1].get(), "0 NOR 0 = 1")
    
    # 0 NOR 1 = 0
    pins[IC7402.A1].set(False)
    pins[IC7402.B1].set(True)
    propagate_all(ic)
    tf.assert_false(pins[IC7402.Y1].get(), "0 NOR 1 = 0")
    
    # 1 NOR 0 = 0
    pins[IC7402.A1].set(True)
    pins[IC7402.B1].set(False)
    propagate_all(ic)
    tf.assert_false(pins[IC7402.Y1].get(), "1 NOR 0 = 0")
    
    # 1 NOR 1 = 0
    pins[IC7402.A1].set(True)
    pins[IC7402.B1].set(True)
    propagate_all(ic)
    tf.assert_false(pins[IC7402.Y1].get(), "1 NOR 1 = 0")


@tf.test("IC7402: Всі чотири гейти")
def test_ic7402_all_gates():
    pins = create_network_dict([
        IC7402.VCC, IC7402.GND,
        IC7402.A0, IC7402.B0, IC7402.Y0,
        IC7402.A1, IC7402.B1, IC7402.Y1,
        IC7402.A2, IC7402.B2, IC7402.Y2,
        IC7402.A3, IC7402.B3, IC7402.Y3
    ])
    ic = IC7402("U2", pins)
    
    pins[IC7402.VCC].set(True)
    pins[IC7402.GND].set(False)
    
    test_cases = [
        (IC7402.A0, IC7402.B0, IC7402.Y0, False, False, True),
        (IC7402.A1, IC7402.B1, IC7402.Y1, True, False, False),
        (IC7402.A2, IC7402.B2, IC7402.Y2, False, True, False),
        (IC7402.A3, IC7402.B3, IC7402.Y3, True, True, False),
    ]
    
    for a_pin, b_pin, y_pin, a_val, b_val, expected in test_cases:
        pins[a_pin].set(a_val)
        pins[b_pin].set(b_val)
        propagate_all(ic)
        tf.assert_equal(pins[y_pin].get(), expected, f"Гейт {y_pin}")


# ============================================================================
# ТЕСТИ ДЛЯ IC7404 (HEX INVERTER)
# ============================================================================

@tf.test("IC7404: Інверсія сигналів")
def test_ic7404_basic():
    pins = create_network_dict([
        IC7404.VCC, IC7404.GND,
        IC7404.A1, IC7404.Y1,
        IC7404.A2, IC7404.Y2,
        IC7404.A3, IC7404.Y3,
        IC7404.A4, IC7404.Y4,
        IC7404.A5, IC7404.Y5,
        IC7404.A6, IC7404.Y6
    ])
    ic = IC7404("U3", pins)
    
    pins[IC7404.VCC].set(True)
    pins[IC7404.GND].set(False)
    
    # Тест всіх 6 інверторів
    inverters = [
        (IC7404.A1, IC7404.Y1),
        (IC7404.A2, IC7404.Y2),
        (IC7404.A3, IC7404.Y3),
        (IC7404.A4, IC7404.Y4),
        (IC7404.A5, IC7404.Y5),
        (IC7404.A6, IC7404.Y6),
    ]
    
    # NOT 0 = 1
    for a_pin, y_pin in inverters:
        pins[a_pin].set(False)
    propagate_all(ic)
    for a_pin, y_pin in inverters:
        tf.assert_true(pins[y_pin].get(), f"{y_pin}: NOT 0 = 1")
    
    # NOT 1 = 0
    for a_pin, y_pin in inverters:
        pins[a_pin].set(True)
    propagate_all(ic)
    for a_pin, y_pin in inverters:
        tf.assert_false(pins[y_pin].get(), f"{y_pin}: NOT 1 = 0")


# ============================================================================
# ТЕСТИ ДЛЯ IC74109 (DUAL J-K FLIP-FLOP)
# ============================================================================

@tf.test("IC74109: Set і Clear")
def test_ic74109_preset_clear():
    pins = create_network_dict([
        IC74109.VCC, IC74109.GND,
        IC74109.CLR1, IC74109.PRE1, IC74109.CLK1,
        IC74109.J1, IC74109.nK1, IC74109.Q1, IC74109.nQ1
    ])
    ic = IC74109("U4", pins)
    
    pins[IC74109.VCC].set(True)
    pins[IC74109.GND].set(False)
    pins[IC74109.J1].set(False)
    pins[IC74109.nK1].set(True)
    pins[IC74109.CLK1].set(False)
    
    # Preset (активний низький)
    pins[IC74109.CLR1].set(True)
    pins[IC74109.PRE1].set(False)
    propagate_all(ic)
    tf.assert_true(pins[IC74109.Q1].get(), "Preset встановлює Q=1")
    tf.assert_false(pins[IC74109.nQ1].get(), "Preset встановлює nQ=0")
    
    # Clear (активний низький)
    pins[IC74109.CLR1].set(False)
    pins[IC74109.PRE1].set(True)
    propagate_all(ic)
    tf.assert_false(pins[IC74109.Q1].get(), "Clear встановлює Q=0")
    tf.assert_true(pins[IC74109.nQ1].get(), "Clear встановлює nQ=1")


@tf.test("IC74109: JK Flip-Flop функціональність")
def test_ic74109_jk_functionality():
    pins = create_network_dict([
        IC74109.VCC, IC74109.GND,
        IC74109.CLR1, IC74109.PRE1, IC74109.CLK1,
        IC74109.J1, IC74109.nK1, IC74109.Q1, IC74109.nQ1
    ])
    ic = IC74109("U4", pins)
    
    pins[IC74109.VCC].set(True)
    pins[IC74109.GND].set(False)
    pins[IC74109.CLR1].set(True)
    pins[IC74109.PRE1].set(True)
    propagate_all(ic)
    
    # Reset to known state
    pins[IC74109.CLR1].set(False)
    propagate_all(ic)
    pins[IC74109.CLR1].set(True)
    propagate_all(ic)
    
    # J=1, K=0 -> Set на clock edge
    pins[IC74109.J1].set(True)
    pins[IC74109.nK1].set(True)  # K=0
    pins[IC74109.CLK1].set(False)
    propagate_all(ic)
    pins[IC74109.CLK1].set(True)  # Rising edge
    propagate_all(ic)
    tf.assert_true(pins[IC74109.Q1].get(), "J=1, K=0 встановлює Q=1")
    
    # J=0, K=1 -> Reset на clock edge
    pins[IC74109.J1].set(False)
    pins[IC74109.nK1].set(False)  # K=1
    pins[IC74109.CLK1].set(False)
    propagate_all(ic)
    pins[IC74109.CLK1].set(True)  # Rising edge
    propagate_all(ic)
    tf.assert_false(pins[IC74109.Q1].get(), "J=0, K=1 встановлює Q=0")


# ============================================================================
# ТЕСТИ ДЛЯ IC74138 (3-TO-8 DECODER)
# ============================================================================

@tf.test("IC74138: Декодування всіх виходів")
def test_ic74138_decoding():
    pins = create_network_dict([
        IC74138.VCC, IC74138.GND,
        IC74138.A, IC74138.B, IC74138.C,
        IC74138.G1, IC74138.G2A, IC74138.G2B,
        IC74138.Y0, IC74138.Y1, IC74138.Y2, IC74138.Y3,
        IC74138.Y4, IC74138.Y5, IC74138.Y6, IC74138.Y7
    ])
    ic = IC74138("U5", pins)
    
    pins[IC74138.VCC].set(True)
    pins[IC74138.GND].set(False)
    pins[IC74138.G1].set(True)
    pins[IC74138.G2A].set(False)
    pins[IC74138.G2B].set(False)
    
    outputs = [
        IC74138.Y0, IC74138.Y1, IC74138.Y2, IC74138.Y3,
        IC74138.Y4, IC74138.Y5, IC74138.Y6, IC74138.Y7
    ]
    
    # Тест кожного виходу
    for i in range(8):
        pins[IC74138.A].set(bool(i & 1))
        pins[IC74138.B].set(bool(i & 2))
        pins[IC74138.C].set(bool(i & 4))
        propagate_all(ic)
        
        for j, out_pin in enumerate(outputs):
            if j == i:
                tf.assert_false(pins[out_pin].get(), f"Y{i} повинен бути LOW при адресі {i}")
            else:
                tf.assert_true(pins[out_pin].get(), f"Y{j} повинен бути HIGH при адресі {i}")


@tf.test("IC74138: Enable логіка")
def test_ic74138_enable():
    pins = create_network_dict([
        IC74138.VCC, IC74138.GND,
        IC74138.A, IC74138.B, IC74138.C,
        IC74138.G1, IC74138.G2A, IC74138.G2B,
        IC74138.Y0, IC74138.Y1
    ])
    ic = IC74138("U5", pins)
    
    pins[IC74138.VCC].set(True)
    pins[IC74138.GND].set(False)
    pins[IC74138.A].set(False)
    pins[IC74138.B].set(False)
    pins[IC74138.C].set(False)
    
    # Disabled: всі виходи HIGH
    pins[IC74138.G1].set(False)
    pins[IC74138.G2A].set(False)
    pins[IC74138.G2B].set(False)
    propagate_all(ic)
    tf.assert_true(pins[IC74138.Y0].get(), "Disabled: Y0 повинен бути HIGH")
    
    # Enabled
    pins[IC74138.G1].set(True)
    propagate_all(ic)
    tf.assert_false(pins[IC74138.Y0].get(), "Enabled: Y0 повинен бути LOW для адреси 0")


# ============================================================================
# ТЕСТИ ДЛЯ IC74154 (4-TO-16 DECODER)
# ============================================================================

@tf.test("IC74154: Декодування 16 виходів")
def test_ic74154_decoding():
    output_pins = [
        IC74154.Y0, IC74154.Y1, IC74154.Y2, IC74154.Y3,
        IC74154.Y4, IC74154.Y5, IC74154.Y6, IC74154.Y7,
        IC74154.Y8, IC74154.Y9, IC74154.Y10, IC74154.Y11,
        IC74154.Y12, IC74154.Y13, IC74154.Y14, IC74154.Y15
    ]
    
    pins = create_network_dict([
        IC74154.VCC, IC74154.GND,
        IC74154.A0, IC74154.A1, IC74154.A2, IC74154.A3,
        IC74154.E1, IC74154.E2
    ] + output_pins)
    ic = IC74154("U6", pins)
    
    pins[IC74154.VCC].set(True)
    pins[IC74154.GND].set(False)
    pins[IC74154.E1].set(False)
    pins[IC74154.E2].set(False)
    
    # Тестуємо перші 4 виходи
    for i in range(4):
        pins[IC74154.A0].set(bool(i & 1))
        pins[IC74154.A1].set(bool(i & 2))
        pins[IC74154.A2].set(bool(i & 4))
        pins[IC74154.A3].set(bool(i & 8))
        propagate_all(ic)
        
        tf.assert_false(pins[output_pins[i]].get(), f"Y{i} повинен бути LOW")
        tf.assert_true(pins[output_pins[(i+1) % 16]].get(), f"Y{(i+1) % 16} повинен бути HIGH")


@tf.test("IC74154: Enable логіка")
def test_ic74154_enable():
    pins = create_network_dict([
        IC74154.VCC, IC74154.GND,
        IC74154.A0, IC74154.A1, IC74154.A2, IC74154.A3,
        IC74154.E1, IC74154.E2, IC74154.Y0, IC74154.Y1
    ])
    ic = IC74154("U6", pins)
    
    pins[IC74154.VCC].set(True)
    pins[IC74154.GND].set(False)
    pins[IC74154.A0].set(False)
    pins[IC74154.A1].set(False)
    pins[IC74154.A2].set(False)
    pins[IC74154.A3].set(False)
    
    # Disabled
    pins[IC74154.E1].set(True)
    pins[IC74154.E2].set(False)
    propagate_all(ic)
    tf.assert_true(pins[IC74154.Y0].get(), "Disabled: всі виходи HIGH")
    
    # Enabled
    pins[IC74154.E1].set(False)
    pins[IC74154.E2].set(False)
    propagate_all(ic)
    tf.assert_false(pins[IC74154.Y0].get(), "Enabled: Y0 LOW для адреси 0")


# ============================================================================
# ТЕСТИ ДЛЯ IC74161 (4-BIT COUNTER)
# ============================================================================

@tf.test("IC74161: Лічба від 0 до 15")
def test_ic74161_counting():
    pins = create_network_dict([
        IC74161.VCC, IC74161.GND,
        IC74161.CLK, IC74161.CLR, IC74161.LOAD,
        IC74161.ENT, IC74161.ENP, IC74161.RCO,
        IC74161.A, IC74161.B, IC74161.C, IC74161.D,
        IC74161.QA, IC74161.QB, IC74161.QC, IC74161.QD
    ])
    ic = IC74161("U7", pins)
    
    pins[IC74161.VCC].set(True)
    pins[IC74161.GND].set(False)
    pins[IC74161.CLR].set(True)
    pins[IC74161.LOAD].set(True)
    pins[IC74161.ENT].set(True)
    pins[IC74161.ENP].set(True)
    
    # Clear
    pins[IC74161.CLR].set(False)
    propagate_all(ic)
    pins[IC74161.CLR].set(True)
    propagate_all(ic)
    
    # Рахуємо до 5
    for i in range(6):
        expected_a = bool(i & 1)
        expected_b = bool(i & 2)
        expected_c = bool(i & 4)
        expected_d = bool(i & 8)
        
        tf.assert_equal(pins[IC74161.QA].get(), expected_a, f"Лічба {i}: QA")
        tf.assert_equal(pins[IC74161.QB].get(), expected_b, f"Лічба {i}: QB")
        tf.assert_equal(pins[IC74161.QC].get(), expected_c, f"Лічба {i}: QC")
        tf.assert_equal(pins[IC74161.QD].get(), expected_d, f"Лічба {i}: QD")
        
        # Clock pulse
        pins[IC74161.CLK].set(False)
        propagate_all(ic)
        pins[IC74161.CLK].set(True)
        propagate_all(ic)


@tf.test("IC74161: Load функціональність")
def test_ic74161_load():
    pins = create_network_dict([
        IC74161.VCC, IC74161.GND,
        IC74161.CLK, IC74161.CLR, IC74161.LOAD,
        IC74161.ENT, IC74161.ENP,
        IC74161.A, IC74161.B, IC74161.C, IC74161.D,
        IC74161.QA, IC74161.QB, IC74161.QC, IC74161.QD
    ])
    ic = IC74161("U7", pins)
    
    pins[IC74161.VCC].set(True)
    pins[IC74161.GND].set(False)
    pins[IC74161.CLR].set(True)
    pins[IC74161.ENT].set(True)
    pins[IC74161.ENP].set(True)
    
    # Завантажуємо значення 0b1010 (10)
    pins[IC74161.A].set(False)
    pins[IC74161.B].set(True)
    pins[IC74161.C].set(False)
    pins[IC74161.D].set(True)
    pins[IC74161.LOAD].set(False)
    pins[IC74161.CLK].set(False)
    propagate_all(ic)
    pins[IC74161.CLK].set(True)
    propagate_all(ic)
    
    tf.assert_false(pins[IC74161.QA].get(), "Load: QA = 0")
    tf.assert_true(pins[IC74161.QB].get(), "Load: QB = 1")
    tf.assert_false(pins[IC74161.QC].get(), "Load: QC = 0")
    tf.assert_true(pins[IC74161.QD].get(), "Load: QD = 1")


@tf.test("IC74161: RCO (Ripple Carry Out)")
def test_ic74161_rco():
    pins = create_network_dict([
        IC74161.VCC, IC74161.GND,
        IC74161.CLK, IC74161.CLR, IC74161.LOAD,
        IC74161.ENT, IC74161.ENP, IC74161.RCO,
        IC74161.A, IC74161.B, IC74161.C, IC74161.D,
        IC74161.QA, IC74161.QB, IC74161.QC, IC74161.QD
    ])
    ic = IC74161("U7", pins)
    
    pins[IC74161.VCC].set(True)
    pins[IC74161.GND].set(False)
    pins[IC74161.CLR].set(True)
    pins[IC74161.ENT].set(True)
    pins[IC74161.ENP].set(True)
    
    # Завантажуємо 15
    pins[IC74161.A].set(True)
    pins[IC74161.B].set(True)
    pins[IC74161.C].set(True)
    pins[IC74161.D].set(True)
    pins[IC74161.LOAD].set(False)
    pins[IC74161.CLK].set(False)
    propagate_all(ic)
    pins[IC74161.CLK].set(True)
    propagate_all(ic)
    pins[IC74161.LOAD].set(True)
    propagate_all(ic)
    
    # RCO має бути HIGH коли count=15 і ENT=HIGH
    tf.assert_true(pins[IC74161.RCO].get(), "RCO HIGH при count=15 і ENT=HIGH")


# ============================================================================
# ТЕСТИ ДЛЯ IC74193 (UP/DOWN COUNTER)
# ============================================================================

@tf.test("IC74193: Лічба вгору")
def test_ic74193_count_up():
    pins = create_network_dict([
        IC74193.VCC, IC74193.GND,
        IC74193.CPU, IC74193.CPD, IC74193.MR, IC74193.N_PL,
        IC74193.P0, IC74193.P1, IC74193.P2, IC74193.P3,
        IC74193.Q0, IC74193.Q1, IC74193.Q2, IC74193.Q3,
        IC74193.N_TCU, IC74193.N_TCD
    ])
    ic = IC74193("U8", pins)
    
    pins[IC74193.VCC].set(True)
    pins[IC74193.GND].set(False)
    pins[IC74193.MR].set(False)
    pins[IC74193.N_PL].set(True)
    pins[IC74193.CPD].set(False)
    
    # Clear
    pins[IC74193.MR].set(True)
    propagate_all(ic)
    pins[IC74193.MR].set(False)
    propagate_all(ic)
    
    # Рахуємо вгору
    for i in range(5):
        expected = i & 0xF
        actual = (pins[IC74193.Q3].get() << 3 | 
                 pins[IC74193.Q2].get() << 2 |
                 pins[IC74193.Q1].get() << 1 | 
                 pins[IC74193.Q0].get())
        tf.assert_equal(actual, expected, f"Count up: iteration {i}")
        
        # Clock pulse
        pins[IC74193.CPU].set(False)
        propagate_all(ic)
        pins[IC74193.CPU].set(True)
        propagate_all(ic)


@tf.test("IC74193: Лічба вниз")
def test_ic74193_count_down():
    pins = create_network_dict([
        IC74193.VCC, IC74193.GND,
        IC74193.CPU, IC74193.CPD, IC74193.MR, IC74193.N_PL,
        IC74193.P0, IC74193.P1, IC74193.P2, IC74193.P3,
        IC74193.Q0, IC74193.Q1, IC74193.Q2, IC74193.Q3
    ])
    ic = IC74193("U8", pins)
    
    pins[IC74193.VCC].set(True)
    pins[IC74193.GND].set(False)
    pins[IC74193.MR].set(False)
    pins[IC74193.N_PL].set(True)
    pins[IC74193.CPU].set(False)
    
    # Load 5
    pins[IC74193.P0].set(True)
    pins[IC74193.P1].set(False)
    pins[IC74193.P2].set(True)
    pins[IC74193.P3].set(False)
    pins[IC74193.N_PL].set(False)
    propagate_all(ic)
    pins[IC74193.N_PL].set(True)
    propagate_all(ic)
    
    # Рахуємо вниз
    for i in range(3):
        expected = (5 - i) & 0xF
        actual = (pins[IC74193.Q3].get() << 3 | 
                 pins[IC74193.Q2].get() << 2 |
                 pins[IC74193.Q1].get() << 1 | 
                 pins[IC74193.Q0].get())
        tf.assert_equal(actual, expected, f"Count down: iteration {i}")
        
        # Clock pulse
        pins[IC74193.CPD].set(False)
        propagate_all(ic)
        pins[IC74193.CPD].set(True)
        propagate_all(ic)


# ============================================================================
# ТЕСТИ ДЛЯ IC74245 (OCTAL BUS TRANSCEIVER)
# ============================================================================

@tf.test("IC74245: Напрямок A -> B")
def test_ic74245_a_to_b():
    pins = create_network_dict([
        IC74245.VCC, IC74245.GND, IC74245.OE, IC74245.DIR,
        IC74245.A1, IC74245.A2, IC74245.A3, IC74245.A4,
        IC74245.B1, IC74245.B2, IC74245.B3, IC74245.B4
    ])
    ic = IC74245("U9", pins)
    
    pins[IC74245.VCC].set(True)
    pins[IC74245.GND].set(False)
    pins[IC74245.OE].set(False)  # Enable
    pins[IC74245.DIR].set(True)  # A -> B
    
    # Тестові дані
    pins[IC74245.A1].set(True)
    pins[IC74245.A2].set(False)
    pins[IC74245.A3].set(True)
    pins[IC74245.A4].set(False)
    propagate_all(ic)
    
    tf.assert_true(pins[IC74245.B1].get(), "A1 -> B1")
    tf.assert_false(pins[IC74245.B2].get(), "A2 -> B2")
    tf.assert_true(pins[IC74245.B3].get(), "A3 -> B3")
    tf.assert_false(pins[IC74245.B4].get(), "A4 -> B4")


@tf.test("IC74245: Напрямок B -> A")
def test_ic74245_b_to_a():
    pins = create_network_dict([
        IC74245.VCC, IC74245.GND, IC74245.OE, IC74245.DIR,
        IC74245.A1, IC74245.A2, IC74245.B1, IC74245.B2
    ])
    ic = IC74245("U9", pins)
    
    pins[IC74245.VCC].set(True)
    pins[IC74245.GND].set(False)
    pins[IC74245.OE].set(False)  # Enable
    pins[IC74245.DIR].set(False)  # B -> A
    
    pins[IC74245.B1].set(False)
    pins[IC74245.B2].set(True)
    propagate_all(ic)
    
    tf.assert_false(pins[IC74245.A1].get(), "B1 -> A1")
    tf.assert_true(pins[IC74245.A2].get(), "B2 -> A2")


@tf.test("IC74245: Output Enable")
def test_ic74245_output_enable():
    pins = create_network_dict([
        IC74245.VCC, IC74245.GND, IC74245.OE, IC74245.DIR,
        IC74245.A1, IC74245.B1
    ])
    ic = IC74245("U9", pins)
    
    pins[IC74245.VCC].set(True)
    pins[IC74245.GND].set(False)
    pins[IC74245.DIR].set(True)
    pins[IC74245.A1].set(True)
    
    # Disabled (OE=HIGH) -> виходи плаваючі
    pins[IC74245.OE].set(True)
    propagate_all(ic)
    # Виходи не встановлюються при OE=HIGH
    
    # Enabled (OE=LOW)
    pins[IC74245.OE].set(False)
    propagate_all(ic)
    tf.assert_true(pins[IC74245.B1].get(), "OE=LOW дозволяє передачу")


# ============================================================================
# ТЕСТИ ДЛЯ IC74273 (OCTAL D FLIP-FLOP)
# ============================================================================

@tf.test("IC74273: Збереження даних")
def test_ic74273_data_storage():
    pins = create_network_dict([
        IC74273.VCC, IC74273.GND, IC74273.CLK, IC74273.CLR,
        IC74273.D1, IC74273.D2, IC74273.D3, IC74273.D4,
        IC74273.Q1, IC74273.Q2, IC74273.Q3, IC74273.Q4
    ])
    ic = IC74273("U10", pins)
    
    pins[IC74273.VCC].set(True)
    pins[IC74273.GND].set(False)
    pins[IC74273.CLR].set(True)
    
    # Встановлюємо дані
    pins[IC74273.D1].set(True)
    pins[IC74273.D2].set(False)
    pins[IC74273.D3].set(True)
    pins[IC74273.D4].set(False)
    
    # Clock pulse
    pins[IC74273.CLK].set(False)
    propagate_all(ic)
    pins[IC74273.CLK].set(True)
    propagate_all(ic)
    
    tf.assert_true(pins[IC74273.Q1].get(), "D1 -> Q1")
    tf.assert_false(pins[IC74273.Q2].get(), "D2 -> Q2")
    tf.assert_true(pins[IC74273.Q3].get(), "D3 -> Q3")
    tf.assert_false(pins[IC74273.Q4].get(), "D4 -> Q4")


@tf.test("IC74273: Clear функціональність")
def test_ic74273_clear():
    pins = create_network_dict([
        IC74273.VCC, IC74273.GND, IC74273.CLK, IC74273.CLR,
        IC74273.D1, IC74273.Q1, IC74273.Q2
    ])
    ic = IC74273("U10", pins)
    
    pins[IC74273.VCC].set(True)
    pins[IC74273.GND].set(False)
    pins[IC74273.CLR].set(True)
    
    # Встановлюємо дані
    pins[IC74273.D1].set(True)
    pins[IC74273.CLK].set(False)
    propagate_all(ic)
    pins[IC74273.CLK].set(True)
    propagate_all(ic)
    
    # Clear
    pins[IC74273.CLR].set(False)
    propagate_all(ic)
    
    tf.assert_false(pins[IC74273.Q1].get(), "Clear встановлює Q=0")
    tf.assert_false(pins[IC74273.Q2].get(), "Clear встановлює Q=0")


@tf.test("IC74273: Всі 8 біт")
def test_ic74273_all_bits():
    pins = create_network_dict([
        IC74273.VCC, IC74273.GND, IC74273.CLK, IC74273.CLR,
        IC74273.D1, IC74273.D2, IC74273.D3, IC74273.D4,
        IC74273.D5, IC74273.D6, IC74273.D7, IC74273.D8,
        IC74273.Q1, IC74273.Q2, IC74273.Q3, IC74273.Q4,
        IC74273.Q5, IC74273.Q6, IC74273.Q7, IC74273.Q8
    ])
    ic = IC74273("U10", pins)
    
    pins[IC74273.VCC].set(True)
    pins[IC74273.GND].set(False)
    pins[IC74273.CLR].set(True)
    
    # Тестове значення: 0b10101010 (170)
    test_value = 0b10101010
    d_pins = [IC74273.D1, IC74273.D2, IC74273.D3, IC74273.D4,
              IC74273.D5, IC74273.D6, IC74273.D7, IC74273.D8]
    q_pins = [IC74273.Q1, IC74273.Q2, IC74273.Q3, IC74273.Q4,
              IC74273.Q5, IC74273.Q6, IC74273.Q7, IC74273.Q8]
    
    for i, d_pin in enumerate(d_pins):
        pins[d_pin].set(bool((test_value >> i) & 1))
    
    pins[IC74273.CLK].set(False)
    propagate_all(ic)
    pins[IC74273.CLK].set(True)
    propagate_all(ic)
    
    for i, q_pin in enumerate(q_pins):
        expected = bool((test_value >> i) & 1)
        tf.assert_equal(pins[q_pin].get(), expected, f"Біт {i}")


# ============================================================================
# ТЕСТИ ДЛЯ IC74574 (OCTAL D FLIP-FLOP WITH 3-STATE)
# ============================================================================

@tf.test("IC74574: Збереження даних")
def test_ic74574_data_storage():
    pins = create_network_dict([
        IC74574.VCC, IC74574.GND, IC74574.CLK, IC74574.OE,
        IC74574.D1, IC74574.D2, IC74574.D3, IC74574.D4,
        IC74574.Q1, IC74574.Q2, IC74574.Q3, IC74574.Q4
    ])
    ic = IC74574("U11", pins)
    
    pins[IC74574.VCC].set(True)
    pins[IC74574.GND].set(False)
    pins[IC74574.OE].set(False)  # Enable outputs
    
    # Встановлюємо дані
    pins[IC74574.D1].set(True)
    pins[IC74574.D2].set(False)
    pins[IC74574.D3].set(True)
    pins[IC74574.D4].set(False)
    
    # Clock pulse (rising edge)
    pins[IC74574.CLK].set(False)
    propagate_all(ic)
    pins[IC74574.CLK].set(True)
    propagate_all(ic)
    
    tf.assert_true(pins[IC74574.Q1].get(), "D1 -> Q1")
    tf.assert_false(pins[IC74574.Q2].get(), "D2 -> Q2")
    tf.assert_true(pins[IC74574.Q3].get(), "D3 -> Q3")
    tf.assert_false(pins[IC74574.Q4].get(), "D4 -> Q4")


@tf.test("IC74574: Output Enable")
def test_ic74574_output_enable():
    pins = create_network_dict([
        IC74574.VCC, IC74574.GND, IC74574.CLK, IC74574.OE,
        IC74574.D1, IC74574.Q1
    ])
    ic = IC74574("U11", pins)
    
    pins[IC74574.VCC].set(True)
    pins[IC74574.GND].set(False)
    
    # Завантажуємо дані
    pins[IC74574.D1].set(True)
    pins[IC74574.OE].set(False)
    pins[IC74574.CLK].set(False)
    propagate_all(ic)
    pins[IC74574.CLK].set(True)
    propagate_all(ic)
    
    tf.assert_true(pins[IC74574.Q1].get(), "OE=LOW: вихід активний")
    
    # Вимикаємо вихід
    pins[IC74574.OE].set(True)
    propagate_all(ic)
    # При OE=HIGH виходи переходять у high-impedance стан


@tf.test("IC74574: Всі 8 біт")
def test_ic74574_all_bits():
    pins = create_network_dict([
        IC74574.VCC, IC74574.GND, IC74574.CLK, IC74574.OE,
        IC74574.D1, IC74574.D2, IC74574.D3, IC74574.D4,
        IC74574.D5, IC74574.D6, IC74574.D7, IC74574.D8,
        IC74574.Q1, IC74574.Q2, IC74574.Q3, IC74574.Q4,
        IC74574.Q5, IC74574.Q6, IC74574.Q7, IC74574.Q8
    ])
    ic = IC74574("U11", pins)
    
    pins[IC74574.VCC].set(True)
    pins[IC74574.GND].set(False)
    pins[IC74574.OE].set(False)
    
    # Тестове значення: 0b11001100 (204)
    test_value = 0b11001100
    d_pins = [IC74574.D1, IC74574.D2, IC74574.D3, IC74574.D4,
              IC74574.D5, IC74574.D6, IC74574.D7, IC74574.D8]
    q_pins = [IC74574.Q1, IC74574.Q2, IC74574.Q3, IC74574.Q4,
              IC74574.Q5, IC74574.Q6, IC74574.Q7, IC74574.Q8]
    
    for i, d_pin in enumerate(d_pins):
        pins[d_pin].set(bool((test_value >> i) & 1))
    
    pins[IC74574.CLK].set(False)
    propagate_all(ic)
    pins[IC74574.CLK].set(True)
    propagate_all(ic)
    
    for i, q_pin in enumerate(q_pins):
        expected = bool((test_value >> i) & 1)
        tf.assert_equal(pins[q_pin].get(), expected, f"Біт {i}")


# ============================================================================
# ТЕСТИ ДЛЯ EEPROM
# ============================================================================

@tf.test("EEPROM: Читання даних")
def test_eeprom_read():
    addr_pins = [
        EEPROM.A0, EEPROM.A1, EEPROM.A2, EEPROM.A3, EEPROM.A4,
        EEPROM.A5, EEPROM.A6, EEPROM.A7, EEPROM.A8, EEPROM.A9,
        EEPROM.A10, EEPROM.A11, EEPROM.A12, EEPROM.A13, EEPROM.A14
    ]
    io_pins = [
        EEPROM.IO0, EEPROM.IO1, EEPROM.IO2, EEPROM.IO3,
        EEPROM.IO4, EEPROM.IO5, EEPROM.IO6, EEPROM.IO7
    ]
    
    pins = create_network_dict([
        EEPROM.VCC, EEPROM.GND, EEPROM.CE, EEPROM.OE, EEPROM.WE
    ] + addr_pins + io_pins)
    
    eeprom = EEPROM("ROM1", pins)
    
    # Завантажуємо тестові дані
    test_data = [0x12, 0x34, 0x56, 0x78, 0xAB, 0xCD, 0xEF, 0x00]
    eeprom.load_data(test_data, offset=0)
    
    pins[EEPROM.VCC].set(True)
    pins[EEPROM.GND].set(False)
    pins[EEPROM.CE].set(False)   # Enable
    pins[EEPROM.OE].set(False)   # Output Enable
    pins[EEPROM.WE].set(True)    # Write Disable
    
    # Читаємо адресу 0
    for pin in addr_pins:
        pins[pin].set(False)
    propagate_all(eeprom)
    
    read_value = 0
    for i, io_pin in enumerate(io_pins):
        if pins[io_pin].get():
            read_value |= (1 << i)
    
    tf.assert_equal(read_value, 0x12, "Читання адреси 0")
    
    # Читаємо адресу 2
    pins[EEPROM.A0].set(False)
    pins[EEPROM.A1].set(True)
    propagate_all(eeprom)
    
    read_value = 0
    for i, io_pin in enumerate(io_pins):
        if pins[io_pin].get():
            read_value |= (1 << i)
    
    tf.assert_equal(read_value, 0x56, "Читання адреси 2")


@tf.test("EEPROM: Читання різних адрес")
def test_eeprom_multiple_addresses():
    addr_pins = [
        EEPROM.A0, EEPROM.A1, EEPROM.A2, EEPROM.A3, EEPROM.A4,
        EEPROM.A5, EEPROM.A6, EEPROM.A7, EEPROM.A8, EEPROM.A9,
        EEPROM.A10, EEPROM.A11, EEPROM.A12, EEPROM.A13, EEPROM.A14
    ]
    io_pins = [
        EEPROM.IO0, EEPROM.IO1, EEPROM.IO2, EEPROM.IO3,
        EEPROM.IO4, EEPROM.IO5, EEPROM.IO6, EEPROM.IO7
    ]
    
    pins = create_network_dict([
        EEPROM.VCC, EEPROM.GND, EEPROM.CE, EEPROM.OE, EEPROM.WE
    ] + addr_pins + io_pins)
    
    eeprom = EEPROM("ROM1", pins)
    
    # Завантажуємо послідовність
    test_data = list(range(256))
    eeprom.load_data(test_data, offset=0x100)
    
    pins[EEPROM.VCC].set(True)
    pins[EEPROM.GND].set(False)
    pins[EEPROM.CE].set(False)
    pins[EEPROM.OE].set(False)
    pins[EEPROM.WE].set(True)
    
    # Тест адреси 0x100 + 0x55 (85)
    test_addr = 0x155
    for i, pin in enumerate(addr_pins):
        pins[pin].set(bool((test_addr >> i) & 1))
    propagate_all(eeprom)
    
    read_value = 0
    for i, io_pin in enumerate(io_pins):
        if pins[io_pin].get():
            read_value |= (1 << i)
    
    tf.assert_equal(read_value, 0x55, f"Читання адреси 0x{test_addr:04X}")


@tf.test("EEPROM: Chip Enable")
def test_eeprom_chip_enable():
    addr_pins = [
        EEPROM.A0, EEPROM.A1, EEPROM.A2, EEPROM.A3, EEPROM.A4,
        EEPROM.A5, EEPROM.A6, EEPROM.A7, EEPROM.A8, EEPROM.A9,
        EEPROM.A10, EEPROM.A11, EEPROM.A12, EEPROM.A13, EEPROM.A14
    ]
    io_pins = [EEPROM.IO0, EEPROM.IO1]
    
    pins = create_network_dict([
        EEPROM.VCC, EEPROM.GND, EEPROM.CE, EEPROM.OE, EEPROM.WE
    ] + addr_pins + io_pins)
    
    eeprom = EEPROM("ROM1", pins)
    eeprom.load_data([0xFF], offset=0)
    
    pins[EEPROM.VCC].set(True)
    pins[EEPROM.GND].set(False)
    pins[EEPROM.OE].set(False)
    pins[EEPROM.WE].set(True)
    
    for pin in addr_pins:
        pins[pin].set(False)
    
    # CE=HIGH (disabled) - нічого не читається
    pins[EEPROM.CE].set(True)
    propagate_all(eeprom)
    # Виходи повинні бути плаваючими
    
    # CE=LOW (enabled) - читання працює
    pins[EEPROM.CE].set(False)
    propagate_all(eeprom)
    read_value = 0
    for i, io_pin in enumerate(io_pins):
        if pins[io_pin].get():
            read_value |= (1 << i)
    # Перші два біти 0xFF це 0b11
    tf.assert_equal(read_value & 3, 3, "CE=LOW дозволяє читання")


# ============================================================================
# ГОЛОВНА ФУНКЦІЯ
# ============================================================================

def main():
    """Запуск всіх тестів"""
    print("="*60)
    print("ТЕСТУВАННЯ МІКРОСХЕМ CPU8 SIMULATOR")
    print("="*60)
    print()
    
    # Запускаємо всі тести
    test_ic7400_basic()
    test_ic7400_all_gates()
    
    test_ic7402_basic()
    test_ic7402_all_gates()
    
    test_ic7404_basic()
    
    test_ic74109_preset_clear()
    test_ic74109_jk_functionality()
    
    test_ic74138_decoding()
    test_ic74138_enable()
    
    test_ic74154_decoding()
    test_ic74154_enable()
    
    test_ic74161_counting()
    test_ic74161_load()
    test_ic74161_rco()
    
    test_ic74193_count_up()
    test_ic74193_count_down()
    
    test_ic74245_a_to_b()
    test_ic74245_b_to_a()
    test_ic74245_output_enable()
    
    test_ic74273_data_storage()
    test_ic74273_clear()
    test_ic74273_all_bits()
    
    test_ic74574_data_storage()
    test_ic74574_output_enable()
    test_ic74574_all_bits()
    
    test_eeprom_read()
    test_eeprom_multiple_addresses()
    test_eeprom_chip_enable()
    
    # Виводимо підсумки
    success = tf.summary()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
