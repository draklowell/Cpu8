#define SPLIT_LINE "-------|----------|------|----"
#define COLUMNS "PORT   | BINARY   | HEX  | DEC"
#define DATA_ROW "DATA   | "
#define STATE_ROW "STATE  | "

// DATA[0] -> Pin 37 and DATA[7] -> Pin 23
const byte dataPins[] = {37, 35, 33, 31, 29, 27, 25, 23};
// STATE[0] -> Pin 52 and STATE[7] -> Pin 38
const byte statePins[] = {52, 50, 48, 46, 44, 42, 40, 38};

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

void printFormatted(byte val)
{
  for (int i = 7; i >= 0; i--)
  {
    Serial.print(bitRead(val, i));
  }

  Serial.print(" | 0x");
  if (val < 16)
  {
    Serial.print("0");
  }
  Serial.print(val, HEX);

  Serial.print(" | ");
  Serial.println(val, DEC);
}