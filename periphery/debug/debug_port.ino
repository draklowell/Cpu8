#define SPLIT_LINE "-------|----------|------|----"
#define COLUMNS "PORT   | BINARY   | HEX  | DEC"
#define DATA_ROW "DATA   | "
#define STATE_ROW "STATE  | "

// DATA[0] -> Pin 23 and DATA[7] -> Pin 37
const byte dataPins[] = {23, 25, 27, 29, 31, 33, 35, 37};
// STATE[8] -> Pin 38 and STATE[15] -> Pin 52
const byte statePins[] = {38, 40, 42, 44, 46, 48, 50, 52};

void printFormatted(byte val)
{
  for (int i = 7; i >= 0; i--)
  {
    Serial.print(bitRead(val, i));
  }

  Serial.print("  | 0x");
  if (val < 16)
  {
    Serial.print("0");
  }
  Serial.print(val, HEX);

  Serial.print(" | ");
  Serial.println(val, DEC);
}

void setup()
{
  Serial.begin(115200);

  for (int i = 0; i < 8; i++)
  {
    pinMode(dataPins[i], INPUT);
    pinMode(statePins[i], INPUT);
  }

  Serial.println(COLUMNS);
  Serial.println(SPLIT_LINE);
}

void loop()
{
  byte dataVal = 0;
  byte stateVal = 0;

  for (int i = 0; i < 8; i++)
  {
    if (digitalRead(dataPins[i]) == HIGH)
    {
      dataVal |= (1 << i);
    }

    if (digitalRead(statePins[i]) == HIGH)
    {
      stateVal |= (1 << i);
    }
  }

  Serial.print(DATA_ROW);
  printFormatted(dataVal);

  Serial.print(STATE_ROW);
  printFormatted(stateVal);

  Serial.println(SPLIT_LINE);
  delay(1000);
}
