#pragma GCC diagnostic ignored "-Wunused-parameter"
// #include <LiquidCrystal.h>
#include "ROMData.h"

#define BAUD_RATE 9600

#define PIN_DATA_DIR 2
#define PIN_DATA_EN 3
#define DATA_DIRECTION_INPUT HIGH
#define DATA_DIRECTION_OUTPUT LOW
const uint8_t PIN_DATA[8] = {22, 23, 24, 25, 26, 27, 28, 29};
const uint8_t PIN_ADDRESS[16] = {32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47};

#define PIN_CTL_NREAD  7
#define PIN_CTL_NWRITE 6

#define PIN_BTN1 A3
#define PIN_BTN2 A4

#define PIN_CLK A5
#define PIN_CLK_OUT A6

#define EDGE_RISING 0x01
#define EDGE_FALLING 0xff
#define EDGE_TRIGGER EDGE_RISING

#define PIN_DISPLAY_RS     8
#define PIN_DISPLAY_ENABLE 9
#define PIN_DISPLAY_D4     10
#define PIN_DISPLAY_D5     11
#define PIN_DISPLAY_D6     12
#define PIN_DISPLAY_D7     13

#define OPERATION_NOP 0
#define OPERATION_READ 1
#define OPERATION_WRITE 2

#define DISPLAY_COLS 16
#define DISPLAY_ROWS 2
#define DISPLAY_CHARSIZE LCD_5x8DOTS
#define DISPLAY_SIZE DISPLAY_COLS * DISPLAY_ROWS

volatile uint8_t memoryRW[6144];
volatile uint8_t memoryStack[1024];

/*** CONTROL BUS ***/
uint8_t controlGetOperation() {
  if(!digitalRead(PIN_CTL_NREAD) && !digitalRead(PIN_CTL_NWRITE)) {
    return OPERATION_NOP;
  }

  if(!digitalRead(PIN_CTL_NREAD)) {
    return OPERATION_READ;
  }

  if(!digitalRead(PIN_CTL_NWRITE)) {
    return OPERATION_WRITE;
  }

  return OPERATION_NOP;
}

/*** ADDRESS BUS ***/
uint16_t addressRead() {
  uint16_t result = 0;
  uint8_t i;

  for (i = 0; i < 16; i++) {
    result |= digitalRead(PIN_ADDRESS[i]) << i;
  }
  return result;
}

void addressSetup() {
  uint8_t i;

  for (i = 0; i < 16; i++) {
    pinMode(PIN_ADDRESS[i], INPUT_PULLUP);
  }
}


/*** DATA BUS ***/
bool dataIsInput = false;

inline void dataSetInput(bool isInput) {
  uint8_t i;

  if (dataIsInput == isInput)
    return;

  digitalWrite(PIN_DATA_EN, HIGH);
  delayMicroseconds(1);

  if (isInput)
    digitalWrite(PIN_DATA_DIR, DATA_DIRECTION_INPUT);
  else
    digitalWrite(PIN_DATA_DIR, DATA_DIRECTION_OUTPUT);
  delayMicroseconds(1);

  for (i = 0; i < 8; i++) {
    if (isInput)
      pinMode(PIN_DATA[i], INPUT);
    else
      pinMode(PIN_DATA[i], OUTPUT);
  }

  digitalWrite(PIN_DATA_EN, LOW);

  dataIsInput = isInput;
}

void dataWrite(uint8_t value) {
  dataSetInput(false);

  uint8_t i;

  for (i = 0; i < 8; ++i) {
    digitalWrite(PIN_DATA[i], (value >> i) & 1);
  }
}

uint8_t dataRead() {
  uint8_t value = 0;
  uint8_t i;

  dataSetInput(true);

  for (i = 0; i < 8; ++i) {
    value |= digitalRead(PIN_DATA[i]) << i;
  }

  return value;
}

void dataSetup() {
  dataSetInput(true);
}

/*** BUTTONS ***/
// uint8_t buttonsGet() {
//   return digitalRead(PIN_BTN1) | (digitalRead(PIN_BTN2) << 1);
// }

// void buttonsSetup() {
//   pinMode(PIN_BTN1, INPUT);
//   pinMode(PIN_BTN2, INPUT);
// }

/*** SERIAL COM ***/
void serialSetup();

void serialSetup() {
  Serial.begin(BAUD_RATE);
}

/*** DISPLAY ***/
// LiquidCrystal display(
//   PIN_DISPLAY_RS, PIN_DISPLAY_ENABLE,
//   PIN_DISPLAY_D4, PIN_DISPLAY_D5,
//   PIN_DISPLAY_D6, PIN_DISPLAY_D7
// );
// void displaySet(uint8_t position);
// void displaySetup();

// void displaySet(uint8_t position, uint8_t value) {
//   display.setCursor(position % DISPLAY_COLS, position / DISPLAY_COLS);
//   display.write(value);
// }

// void displaySetup() {
//   display.begin(DISPLAY_COLS, DISPLAY_ROWS, DISPLAY_CHARSIZE);
// }

/*** MEMORY ***/
uint8_t memoryRead(uint16_t address);
void memoryWrite(uint16_t address, uint8_t value);

uint8_t memoryRead(uint16_t address) {
  Serial.print(F("OP: READ("));
  Serial.print(address, HEX);
  Serial.print(F(") -> "));
  // 0x0000 -- 0x27FF
  if (address < 0x2800) {
    Serial.println(pgm_read_byte(&memoryRO[address]), HEX);
    // to ROM: 0x0000 -- 0x27FF
    return pgm_read_byte(&memoryRO[address]);
  }

  // 0x4000 -- 0x57FF
  if (address >= 0x4000 && address < 0x5800) {
    Serial.println(memoryRW[address], HEX);
    // to RAM: 0x0000 -- 0x27FF
    return memoryRW[address-0x4000];
  }

  // 0xFC00 -- 0xFFFF
  if (address >= 0xFC00 && address < 0xFFFF) {
    Serial.println(memoryStack[address], HEX);
    // to STACK: 0x0000 -- 0x03FF
    return memoryStack[address-0xFC00];
  }

  // 0x8000 -- 0x801F
  if (address >= 0x8000 && address <= 0x801F) {
    // to DISPLAY: 0x0000 -- 0x001F
    return 0x00;
  }

  // 0x9000
  if (address == 0x9000) {
    // to BUTTONS
    // return buttonsGet();
    return 0x00;
  }

  return 0xff;
}

void memoryWrite(uint16_t address, uint8_t value) {
  Serial.print(F("OP: WRITE("));
  Serial.print(address, HEX);
  Serial.print(F(", "));
  Serial.print(value, HEX);
  Serial.println(F(")"));
  // 0x0000 -- 0x27FF
  if (address < 0x2800) {
    // to ROM: 0x0000 -- 0x27FF
    return;
  }

  // 0x4000 -- 0x57FF
  if (address >= 0x4000 && address < 0x5800) {
    // to RAM: 0x0000 -- 0x27FF
    memoryRW[address-0x4000] = value;
  }

  // 0xFC00 -- 0xFFFF
  if (address >= 0xFC00 && address < 0xFFFF) {
    // to STACK: 0x0000 -- 0x03FF
    memoryStack[address-0xFC00] = value;
  }

  // 0x8000 -- 0x801F
  if (address >= 0x8000 && address <= 0x801F) {
    // to DISPLAY: 0x0000 -- 0x001F
    return;
  }

  // 0x9000
  if (address == 0x9000) {
    // to BUTTONS
    return;
  }

  return;
}

/*** MAIN ***/
void setup() {
  addressSetup();
  dataSetup();
  serialSetup();
  //displaySetup();
  // buttonsSetup();
  pinMode(PIN_CLK, INPUT);
  pinMode(PIN_CLK_OUT, OUTPUT);
}

void loop() {
  uint16_t address = 0;
  uint8_t operation;

  uint8_t value = memoryRead(address);
  // dataWrite(value);
  dataSetInput(true);

  uint8_t prevClkValue = digitalRead(PIN_CLK);
  uint8_t clkValue = prevClkValue;
  for(;;) {
    clkValue = digitalRead(PIN_CLK);
    digitalWrite(PIN_CLK_OUT, clkValue);
    if (clkValue - prevClkValue != EDGE_TRIGGER) {
      prevClkValue = clkValue;
      continue;
    } else {
      prevClkValue = clkValue;
    }

    operation = controlGetOperation();

    if (operation == OPERATION_NOP) {
      Serial.println(F("OP: NOP"));
      continue;
    }

    address = addressRead();
    if (operation == OPERATION_READ) {
      value = memoryRead(address);
      dataWrite(value);
      continue;
    }

    if (operation == OPERATION_WRITE) {
      value = dataRead();
      memoryWrite(address, value);
      continue;
    }

    continue;
  }
}