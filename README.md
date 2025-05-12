# EXO CSV to QQ CSV Converter

### EXO CSV Files Input

* EXO CSV Data is expected to be UTF-16 encoded.
* All Heading Lines are currently ignored.
* **Date (MM/DD/YYYY)** and **Time (HH:mm:ss)**

Date (MM/DD/YYYY),Time (HH:mm:ss),Time (Fract. Sec),Site Name,Cond µS/cm,nLF Cond µS/cm,Sal psu,SpCond µS/cm,TDS mg/L,Wiper Position volt,Temp °C,Battery V,Cable Pwr V

***

### QQ CSV Files Output

* QQ CSV outputs with UTF-8 encoding
* Heading lines before CSV are just placeholders and auto-generated
* Windows style newlines (\r\n) are used.
* Only the following fields are output with data (with the rest being placeholders):
  * **DateTime** from EXO fields **Date (MM/DD/YYYY)** and **Time (HH:mm:ss)**
  * **EC(uS/cm)** from EXO field **Cond µS/cm**
  * **Temp(oC)** from EXO field **Temp °C**
  * **EC.T(uS/cm)** from EXO field **SpCond µS/cm**


***

Christopher Lafferty - [@chrislafferty.bsky.social](https://bsky.app/profile/chrislafferty.bsky.social)

Project Link: [https://github.com/ChristopherLafferty/exo2qq](https://github.com/ChristopherLafferty/exo2qq)