

import random
import time
import datetime
import os
import webbrowser
import http.server
import threading
from dataclasses import dataclass, field
from typing import Optional


# ╔══════════════════════════════════════════════════════╗
# ║              SECTION 1 — DATA MODELS                ║
# ╚══════════════════════════════════════════════════════╝

@dataclass
class SensorReading:
   
    timestamp:        datetime.datetime
    temperature:      float   # °C  — range: 15 to 40
    humidity:         float   # %   — range: 20 to 90
    light_level:      float   # lux — range: 0 to 1000
    motion_detected:  bool
    aqi:              float   # Air Quality Index — range: 0 to 300


@dataclass
class RoomState:
    
    ac_on:          bool = False
    heater_on:      bool = False
    fan_on:         bool = False
    lights_on:      bool = False
    alert_active:   bool = False
    alert_message:  str  = ""
    occupancy:      bool = False
    last_motion:    Optional[datetime.datetime] = None
    action_log:     list = field(default_factory=list)

    def log_action(self, message: str):
       
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}"
        self.action_log.append(entry)
        print(f"   >> {message}")


# ╔══════════════════════════════════════════════════════╗
# ║           SECTION 2 — SENSOR SIMULATOR              ║
# ╚══════════════════════════════════════════════════════╝

class SensorSimulator:
    

    def __init__(self):
        # Starting values (realistic room defaults)
        self._temp     = 24.0
        self._humidity = 50.0
        self._light    = 300.0
        self._aqi      = 45.0
        self._motion_prob = 0.65   # 65% chance of detecting motion each cycle

    # ── Public Methods ────────────────────────────────────

    def read(self) -> SensorReading:
       
        self._drift()
        return SensorReading(
            timestamp       = datetime.datetime.now(),
            temperature     = round(self._temp,    1),
            humidity        = round(self._humidity, 1),
            light_level     = round(self._light,   1),
            motion_detected = random.random() < self._motion_prob,
            aqi             = round(self._aqi,     1),
        )

    def set_scenario(self, scenario: str):
        
        scenarios = {
            "hot":      lambda: setattr(self, '_temp',     36.0),
            "cold":     lambda: setattr(self, '_temp',     15.0),
            "humid":    lambda: setattr(self, '_humidity', 82.0),
            "bad_air":  lambda: setattr(self, '_aqi',     180.0),
            "dark":     lambda: setattr(self, '_light',     5.0),
            "empty":    lambda: setattr(self, '_motion_prob', 0.02),
            "occupied": lambda: setattr(self, '_motion_prob', 0.92),
            "normal":   self._reset,
        }
        if scenario in scenarios:
            scenarios[scenario]()
            print(f"\n   [SCENARIO → {scenario.upper()}]")

    # ── Private Methods ───────────────────────────────────

    def _drift(self):

        self._temp     = self._clamp(self._temp     + random.uniform(-0.8, 0.8),  15, 40)
        self._humidity = self._clamp(self._humidity + random.uniform(-2.0, 2.0),  20, 90)
        self._light    = self._clamp(self._light    + random.uniform(-30, 30),     0, 1000)
        self._aqi      = self._clamp(self._aqi      + random.uniform(-5,  5),      0, 300)

    def _reset(self):
        self._temp, self._humidity = 23.0, 50.0
        self._light, self._aqi    = 350.0, 40.0
        self._motion_prob         = 0.65

    @staticmethod
    def _clamp(value, lo, hi):
        return max(lo, min(hi, value))


# ╔══════════════════════════════════════════════════════╗
# ║        SECTION 3 — AUTONOMOUS CONTROL LOGIC         ║
# ╚══════════════════════════════════════════════════════╝

class RoomController:

    # Decision thresholds (easy to tune)
    TEMP_HOT          = 28.0
    TEMP_COLD         = 19.0
    HUMIDITY_HIGH     = 65.0
    HUMIDITY_OK       = 55.0
    LIGHT_DIM         = 100.0
    LIGHT_OK          = 200.0
    AQI_POOR          = 100.0
    AQI_HAZARDOUS     = 150.0
    VACANCY_SECONDS   = 10

    def __init__(self):
        self.state = RoomState()

    def process(self, reading: SensorReading) -> RoomState:
       
        s = self.state
        r = reading

        self._check_occupancy(s, r)
        self._check_temperature(s, r)
        self._check_humidity(s, r)
        self._check_lighting(s, r)
        self._check_air_quality(s, r)

        return s

    # ── Private Rule Methods ──────────────────────────────

    def _check_occupancy(self, s: RoomState, r: SensorReading):
        if r.motion_detected:
            s.last_motion = r.timestamp
            if not s.occupancy:
                s.occupancy = True
                s.log_action("Motion detected — room marked OCCUPIED")
        else:
            if s.last_motion:
                idle_sec = (r.timestamp - s.last_motion).total_seconds()
                if idle_sec > self.VACANCY_SECONDS and s.occupancy:
                    s.occupancy = False
                    s.log_action(f"No motion for {self.VACANCY_SECONDS}s — room marked VACANT")

    def _check_temperature(self, s: RoomState, r: SensorReading):
        if r.temperature >= self.TEMP_HOT:
            if not s.ac_on:
                s.ac_on = True
                s.heater_on = False
                s.log_action(f"Temp {r.temperature}°C ≥ {self.TEMP_HOT}°C — AC turned ON")
        elif r.temperature <= self.TEMP_COLD:
            if not s.heater_on:
                s.heater_on = True
                s.ac_on = False
                s.log_action(f"Temp {r.temperature}°C ≤ {self.TEMP_COLD}°C — Heater turned ON")
        elif self.TEMP_COLD < r.temperature < self.TEMP_HOT:
            if s.ac_on or s.heater_on:
                s.ac_on = False
                s.heater_on = False
                s.log_action(f"Temp {r.temperature}°C comfortable — AC/Heater turned OFF")

    def _check_humidity(self, s: RoomState, r: SensorReading):
        if r.humidity >= self.HUMIDITY_HIGH and not s.fan_on:
            s.fan_on = True
            s.log_action(f"Humidity {r.humidity}% ≥ {self.HUMIDITY_HIGH}% — Fan turned ON")
        elif r.humidity <= self.HUMIDITY_OK and s.fan_on and r.aqi < self.AQI_POOR:
            s.fan_on = False
            s.log_action(f"Humidity {r.humidity}% normal — Fan turned OFF")

    def _check_lighting(self, s: RoomState, r: SensorReading):
        if s.occupancy:
            if r.light_level < self.LIGHT_DIM and not s.lights_on:
                s.lights_on = True
                s.log_action(f"Light {r.light_level} lux — too dim, Lights turned ON")
            elif r.light_level >= self.LIGHT_OK and s.lights_on:
                s.lights_on = False
                s.log_action(f"Light {r.light_level} lux — adequate, Lights turned OFF")
        elif s.lights_on:
            s.lights_on = False
            s.log_action("Room vacant — Lights turned OFF automatically")

    def _check_air_quality(self, s: RoomState, r: SensorReading):
        if r.aqi >= self.AQI_HAZARDOUS:
            s.alert_active = True
            s.alert_message = f"HAZARDOUS AIR (AQI={r.aqi}) — Open windows immediately!"
            if not s.fan_on:
                s.fan_on = True
                s.log_action(f"AQI={r.aqi} HAZARDOUS — Emergency ventilation ON + Alert raised")
        elif r.aqi >= self.AQI_POOR:
            s.alert_active = True
            s.alert_message = f"Poor air quality (AQI={r.aqi}) — Ventilating..."
            if not s.fan_on:
                s.fan_on = True
                s.log_action(f"AQI={r.aqi} poor — Fan ON for ventilation")
        elif s.alert_active:
            s.alert_active = False
            s.alert_message = ""
            s.log_action("Air quality restored — Alert cleared")


# ╔══════════════════════════════════════════════════════╗
# ║         SECTION 4 — CONSOLE DISPLAY (OPTIONAL)      ║
# ╚══════════════════════════════════════════════════════╝

def print_dashboard(reading: SensorReading, state: RoomState, cycle: int):
    """Print a formatted terminal dashboard for each cycle."""
    w = "═" * 52
    print(f"\n{w}")
    print(f"  SMART ROOM MONITOR  |  Cycle #{cycle}  |  {reading.timestamp.strftime('%H:%M:%S')}")
    print(w)
    print(f"  SENSORS")
    print(f"    Temperature  : {reading.temperature:>6.1f} °C")
    print(f"    Humidity     : {reading.humidity:>6.1f} %")
    print(f"    Light        : {reading.light_level:>6.1f} lux")
    print(f"    Air Quality  : {reading.aqi:>6.1f} AQI")
    print(f"    Motion       : {'Detected' if reading.motion_detected else 'None'}")
    print(f"\n  DEVICES")
    print(f"    AC           : {'ON' if state.ac_on     else 'OFF'}")
    print(f"    Heater       : {'ON' if state.heater_on else 'OFF'}")
    print(f"    Fan          : {'ON' if state.fan_on    else 'OFF'}")
    print(f"    Lights       : {'ON' if state.lights_on else 'OFF'}")
    print(f"    Occupancy    : {'OCCUPIED' if state.occupancy else 'VACANT'}")
    if state.alert_active:
        print(f"\n  ⚠  ALERT: {state.alert_message}")
    print("─" * 52)


# ╔══════════════════════════════════════════════════════╗
# ║          SECTION 5 — UI LAUNCHER (MAIN)             ║
# ╚══════════════════════════════════════════════════════╝

def find_ui_file() -> Optional[str]:
    """Locate the HTML dashboard in the same folder as this script."""
    base = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base, "smart_room_monitor_ui.html")
    return path if os.path.exists(path) else None


def start_local_server(directory: str, port: int = 8765) -> http.server.HTTPServer:
    """Spin up a minimal HTTP server to serve the dashboard."""
    os.chdir(directory)

    class SilentHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass  # suppress request logs

    server = http.server.HTTPServer(("localhost", port), SilentHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def run_console_demo(cycles: int = 15, interval: float = 1.5):
    """
    Optional: run a console-only demo (no browser).
    Demonstrates the autonomous logic with scenario injection.
    """
    sensor     = SensorSimulator()
    controller = RoomController()

    demo_scenarios = {4: "hot", 7: "humid", 10: "bad_air", 12: "cold", 14: "normal"}

    for cycle in range(1, cycles + 1):
        if cycle in demo_scenarios:
            sensor.set_scenario(demo_scenarios[cycle])
        reading = sensor.read()
        state   = controller.process(reading)
        print_dashboard(reading, state, cycle)
        time.sleep(interval)

    print("\n" + "═" * 52)
    print("  AUTONOMOUS ACTION LOG")
    print("═" * 52)
    for entry in controller.state.action_log:
        print(f"  {entry}")
    print("═" * 52)


def main():
    print("\n" + "=" * 52)
    print("  SMART ROOM MONITORING SYSTEM")
    print("  Autonomous Agent — Mini Project")
    print("=" * 52)

    ui_path = find_ui_file()

    if ui_path:
        print("\n  Opening dashboard in browser...")
        port = 8765
        server = start_local_server(os.path.dirname(ui_path), port)
        time.sleep(0.4)
        url = f"http://localhost:{port}/smart_room_monitor_ui.html"
        webbrowser.open(url)
        print(f"  Dashboard : {url}")
        print("  Press Ctrl+C to quit.\n")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n  Shutting down. Goodbye!\n")
            server.shutdown()
    else:
        print("\n  UI file not found — running console demo instead.")
        print("  (Place smart_room_monitor_ui.html in the same folder for the GUI)\n")
        run_console_demo()


if __name__ == "__main__":
    main()