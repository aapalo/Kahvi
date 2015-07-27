/*
 Aloitettu 20.05.2015, Päivitetty 4.7.
 http://www.instructables.com/id/Charlieplexing-LEDs--The-theory/?ALLSTEPS
 3kpl 300 ohmin vastuksia, 6 lediä
 
 nappi: http://www.arduino.cc/en/Tutorial/Button
 tilanne 3.6.2015: http://pastebin.com/ihcyH2F6
 
 */
/*
 Lämpötila yli rajan -> ledi 5 päälle
 Nappia painamalla laskuri rullaa ylöspäin
 pc:n terminaaliin "tail -f < /dev/ttyUSB0"
 tail pois päältä uploadauksen ajaksi
 */
#define ONEWIRE_SEARCH 1
#define ONEWIRE_CRC 1
#include <OneWire.h> //ds18b20

#define L2 7
#define L1 6
#define L0 5
#define buttonPin 4
#define tempPin 3

//Kahvi tippumassa
#define tempRaja 65.0

int buttonState = 0;
int laskuri = 4;
unsigned long drop1 = 0;  //timestamp in milliseconds
int tippuu = 0; //tippuuko kahvi

//Ledi päälle
void funktio(int plus, int miinus, int nolla1) {
  //setup();
  pinMode(plus, OUTPUT);
  pinMode(miinus, OUTPUT);
  pinMode(nolla1, INPUT);
  digitalWrite(plus, HIGH);
  digitalWrite(miinus, LOW);
}

//Tietty ledi päälle
void ledi(int i){
  if (i == 1)
    funktio(L1,L0,L2); // 1
  else if (i == 2)
    funktio(L0,L1,L2); // 2
  else if (i == 3)
    funktio(L1,L2,L0); // 3	
  else if (i == 4)
    funktio(L2,L1,L0); // 4  
  else if (i == 5)
    funktio(L0,L2,L1); // 5
  else if (i == 6)
    funktio(L2,L0,L1); // 
}

void nappula(){
  //nappi painettu
  buttonState = digitalRead(buttonPin);
  if (buttonState == HIGH) {
    laskuri += 1;
  }
  if(laskuri > 4)
    laskuri = 1;   
  ledi(laskuri);
  delay(10);

}

//ds18b20
OneWire ds(tempPin);

void setup() {                
  pinMode(buttonPin, INPUT);
  pinMode(L0, OUTPUT);
  pinMode(L1, OUTPUT);
  pinMode(L2, OUTPUT);
  digitalWrite(L0, LOW);
  digitalWrite(L1, LOW);
  digitalWrite(L2, LOW);

  Serial.begin(9600);
}

//examples->OneWire->DS18x20_Temperature
void ykswire(void) {
  byte i;
  byte present = 0;
  byte type_s;
  byte data[12];
  byte addr[8];
  float celsius;

  if ( !ds.search(addr)) {
    ds.reset_search();
    delay(20); //250
    return;
  }

  if (OneWire::crc8(addr, 7) != addr[7]) {
    Serial.println("CRC is not valid!");
    return;
  }

  ds.reset();
  ds.select(addr);
  ds.write(0x44,1);         // start conversion, with parasite power on at the end

  delay(1000);     // maybe 750ms is enough, maybe not
  // we might do a ds.depower() here, but the reset will take care of it.

  present = ds.reset();
  ds.select(addr);    
  ds.write(0xBE);         // Read Scratchpad

  for ( i = 0; i < 9; i++) {           // we need 9 bytes
    data[i] = ds.read();
  }


  // convert the data to actual temperature

  unsigned int raw = (data[1] << 8) | data[0];
  if (type_s) {
    raw = raw << 3; // 'raw << 3', 9 bit resolution default
    if (data[7] == 0x10) {
      // count remain gives full 12 bit resolution
      raw = (raw & 0xFFF0) + 12 - data[6];
    }
  } 
  else {
    byte cfg = (data[4] & 0x60); //0x60
    if (cfg == 0x00) raw = raw << 3;  // 9 bit resolution, 93.75 ms
    else if (cfg == 0x20) raw = raw << 2; // 10 bit res, 187.5 ms
    else if (cfg == 0x40) raw = raw << 1; // 11 bit res, 375 ms
    // default is 12 bit resolution, 750 ms conversion time
  }
  celsius = (float)raw / 16.0;
  Serial.print(celsius);
  Serial.print(",");
  if(celsius > tempRaja) {
    laskuri = 5;
    drop1 = millis();
    tippuu = 1;
    ledi(laskuri);
  }
  if(tippuu){
    if(celsius < (tempRaja - 1) ) {
      tippuu = 0;
      laskuri = 1; //täysi
      if( (millis() - drop1 ) < 280000UL)
       laskuri = 2; //puolikas
      if( (millis() - drop1) < 160000UL)
       laskuri = 3; //tippa
    }
  }
  else 
    nappula();
  Serial.println(laskuri);
}

void loop() {
  ykswire();
}
