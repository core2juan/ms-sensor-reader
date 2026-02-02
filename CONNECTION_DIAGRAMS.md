## Floating sensor (NC) with led indicator

### 1~2m
```
(Pi GPIO input)----[ 1kΩ ]--+---[ 330Ω ]---|> LED|---(Pi GND)
                            |
                            +---(cable signal)---(Float switch NC)---(Pi GND)
```

### 2~5m

```
(Pi GPIO input)---------+
                        |
(Pi 3.3V)---[ 4.7kΩ ]---+
                        |
                        +----[ 330Ω ]----|> LED|----(Pi GND)
                        |
                        +--[ 1kΩ ]--(cable signal)--(Float switch NC)---(Pi GND)
```

### 5~10m (Default recommended even for shorter cables)

```
(Pi GND)--[100nF]--+
                   +----+----[ 4.7kΩ ]------(Pi 3.3V)
(Pi GPIO input)----+    |
                        |
                        +----[ 330Ω ]----|> LED|----(Pi GND)
                        |
                        +---[ 1kΩ ]--(cable signal)--(Float switch NC)---(Pi GND)
```

## Pressure sensor
```
(Pi 3.3V pin 1)-------------------------------(ADS1115 VDD)

(Pi GND pin 6)----------------+--------------(ADS1115 GND)
                              |
                              +--------------(Pressure Sensor GND)
                              |
                              +----[ 33kΩ ]--+  # Voltage divider. This transforms: 4.5V become ~3.28V at A0 (safe) and 0.5V become ~0.36V at A0
                                             |
(Pressure Sensor SIGNAL)----[ 10kΩ ]---------+----------------(ADS1115 A0)

(Pi SDA / GPIO2 pin 3)-----------------------(ADS1115 SDA)

(Pi SCL / GPIO3 pin 5)-----------------------(ADS1115 SCL)

(Pi 5V pin 2)--------------------------------(Pressure Sensor VCC 5V)

(ADS1115 ADDR)--------------------------------(ADS1115 GND)
```