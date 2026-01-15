#define HEADER F("time,data,state,pcinc,scclear,clk")

// DATA[0] -> Pin 23 and DATA[7] -> Pin 37
const byte dataPins[] = {23, 25, 27, 29, 31, 33, 35, 37};
// STATE[8] -> Pin 38 and STATE[15] -> Pin 52
const byte statePins[] = {38, 40, 42, 44, 46, 48, 50, 52};
const byte pcinc = 53;
const byte scclear = 55;
const byte clk = 57;

void setup()
{
  Serial.begin(115200);

  for (int i = 0; i < 8; i++)
  {
    pinMode(dataPins[i], INPUT);
    pinMode(statePins[i], INPUT);
  }
  pinMode(pcinc, INPUT);
  pinMode(scclear, INPUT);
  pinMode(clk, INPUT);
  Serial.println(HEADER);
}

void loop()
{
  byte dataVal = 0;
  byte stateVal = 0;

  for (int i = 0; i < 8; i++)
  {
    dataVal |= (digitalRead(dataPins[i]) << i);
    stateVal |= (digitalRead(statePins[i]) << i);
  }

  Serial.print(millis());
  Serial.print(',');
  Serial.print(dataVal);
  Serial.print(',');
  Serial.print(stateVal);
  Serial.print(',');
  Serial.print(digitalRead(pcinc));
  Serial.print(',');
  Serial.print(digitalRead(scclear));
  Serial.print(',');
  Serial.println(digitalRead(clk));
}
