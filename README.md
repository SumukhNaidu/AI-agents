Description
The Smart Room Monitoring System is an AI-based automation project that continuously monitors room conditions such as temperature, humidity, light intensity, motion, and air quality. Based on these sensor readings, the system automatically controls devices like AC, heater, fan, and lights.

The project is developed using Python and demonstrates how autonomous systems can improve comfort, safety, and energy efficiency in smart homes and offices.


Features
  The system provides real-time monitoring of temperature, humidity, light, motion, and air quality. Based on these values, it automatically controls devices such    as AC, heater, fan, and lights. It also supports motion detection for occupancy tracking, air quality alerts for safety, and a live dashboard to display sensor     values and device status.



Technologies Used
 Python

 HTML

 CSS

 JavaScript

 HTTP Server

 Dataclasses

Rule-Based AI Logic


Dashboard Features
Live sensor cards — colour-coded status (good / warn / alert)
Device panel — AC, Heater, Fan, Lights toggle in real time
Temperature chart — scrolling history with threshold lines
Action log — every autonomous decision logged with timestamp
Scenario buttons — simulate Hot, Cold, Humid, Bad Air, Dark, Empty 

Demonstration Scenarios
1. Hot Room Condition
Temperature = 36°C

Output: AC turned ON

2. Cold Room Condition
Temperature = 15°C

Output: Heater turned ON

3. High Humidity Condition
Humidity = 82%

Output: Fan turned ON

4. Dark Room with Occupancy
Light = Low

Motion Detected = Yes

Output: Lights turned ON

5. Poor Air Quality
AQI = 180

Output: Alert Raised + Fan ON

6. Empty Room Condition
No motion detected for 10 seconds

Output: Lights turned OFF
