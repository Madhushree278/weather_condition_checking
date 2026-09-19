"""
Himalayan Weather Monitoring System
------------------------------------
Fetches current weather for Manali, Himachal Pradesh, India from the
Open-Meteo API and emails a daily HTML weather report via Gmail SMTP.

Dependencies:
    pip install requests schedule

Run:
    python himalayan_weather_monitor.py
"""

import os
import time
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests
import schedule

# =====================================================================
# CONFIGURATION
# =====================================================================

# Automatically load .env file if present
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

SENDER_EMAIL = os.getenv("SENDER_EMAIL") or os.getenv("SMTP_EMAIL") or "your_email@gmail.com"
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD") or os.getenv("SMTP_APP_PASSWORD") or "your_app_password"
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL") or os.getenv("TO_EMAIL") or "recipient@gmail.com"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

LOCATION_NAME = "Manali, Himachal Pradesh, India"
LATITUDE = 32.2396
LONGITUDE = 77.1887

WEATHER_API_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude=32.2396&longitude=77.1887"
    "&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code"
    "&temperature_unit=celsius&wind_speed_unit=kmh"
)

REQUEST_TIMEOUT_SECONDS = 15
DAILY_REPORT_TIME = "09:00"

# =====================================================================
# WEATHER CODE MAPPING (WMO codes)
# =====================================================================

WEATHER_CODE_MAP = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def describe_weather_code(code):
    """Convert a WMO weather code into a human-readable description."""
    return WEATHER_CODE_MAP.get(code, "Weather condition unavailable")


# =====================================================================
# WEATHER RETRIEVAL
# =====================================================================

def get_weather():
    """
    Fetch current weather data from the Open-Meteo API.

    Returns a dict with time, temperature, humidity, wind_speed,
    weather_code, and weather_description on success, or None on failure.
    """
    try:
        response = requests.get(WEATHER_API_URL, timeout=REQUEST_TIMEOUT_SECONDS)
    except requests.exceptions.RequestException as exc:
        print(f"Error: Weather API request failed: {exc}")
        return None

    if response.status_code != 200:
        print(f"Error: Weather API returned HTTP status {response.status_code}")
        return None

    try:
        data = response.json()
    except ValueError as exc:
        print(f"Error: Could not parse weather API response as JSON: {exc}")
        return None

    current = data.get("current")
    if current is None:
        print("Error: 'current' field missing from weather API response.")
        return None

    required_fields = [
        "time",
        "temperature_2m",
        "relative_humidity_2m",
        "wind_speed_10m",
        "weather_code",
    ]
    missing_fields = [field for field in required_fields if field not in current]
    if missing_fields:
        print(f"Error: Missing required fields in API response: {missing_fields}")
        return None

    weather_code = current["weather_code"]

    return {
        "time": current["time"],
        "temperature": current["temperature_2m"],
        "humidity": current["relative_humidity_2m"],
        "wind_speed": current["wind_speed_10m"],
        "weather_code": weather_code,
        "weather_description": describe_weather_code(weather_code),
    }


# =====================================================================
# EMAIL CREATION
# =====================================================================

def create_html_email(weather):
    """Build a clean, centered HTML weather-report card."""
    html = f"""\
<html>
  <head>
    <style>
      body {{
        font-family: Arial, Helvetica, sans-serif;
        background-color: #f2f4f7;
        margin: 0;
        padding: 30px 0;
      }}
      .card {{
        max-width: 480px;
        margin: 0 auto;
        background-color: #ffffff;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
      }}
      .header {{
        background-color: #2c3e50;
        color: #ffffff;
        padding: 20px;
        text-align: center;
      }}
      .header h1 {{
        margin: 0;
        font-size: 20px;
        letter-spacing: 0.5px;
      }}
      .body {{
        padding: 24px;
      }}
      .row {{
        display: flex;
        justify-content: space-between;
        padding: 10px 0;
        border-bottom: 1px solid #eeeeee;
      }}
      .row:last-child {{
        border-bottom: none;
      }}
      .label {{
        color: #7f8c8d;
        font-size: 14px;
      }}
      .value {{
        color: #2c3e50;
        font-size: 14px;
        font-weight: bold;
        text-align: right;
      }}
      .footer {{
        background-color: #f7f9fa;
        color: #95a5a6;
        font-size: 11px;
        text-align: center;
        padding: 14px;
      }}
    </style>
  </head>
  <body>
    <div class="card">
      <div class="header">
        <h1>HIMALAYAN WEATHER UPDATE</h1>
      </div>
      <div class="body">
        <div class="row">
          <span class="label">Location</span>
          <span class="value">{LOCATION_NAME}</span>
        </div>
        <div class="row">
          <span class="label">Date &amp; Time</span>
          <span class="value">{weather['time']}</span>
        </div>
        <div class="row">
          <span class="label">Temperature</span>
          <span class="value">{weather['temperature']} &deg;C</span>
        </div>
        <div class="row">
          <span class="label">Humidity</span>
          <span class="value">{weather['humidity']} %</span>
        </div>
        <div class="row">
          <span class="label">Wind Speed</span>
          <span class="value">{weather['wind_speed']} km/h</span>
        </div>
        <div class="row">
          <span class="label">Weather Condition</span>
          <span class="value">{weather['weather_description']}</span>
        </div>
        <div class="row">
          <span class="label">Weather Code</span>
          <span class="value">{weather['weather_code']}</span>
        </div>
      </div>
      <div class="footer">
        This weather report was automatically generated using Python and the Open-Meteo Weather API.
      </div>
    </div>
  </body>
</html>
"""
    return html


# =====================================================================
# EMAIL SENDING
# =====================================================================

def send_email(subject, html_content):
    """Send an HTML email via Gmail SMTP using STARTTLS."""
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = SENDER_EMAIL
    message["To"] = RECIPIENT_EMAIL
    message.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=REQUEST_TIMEOUT_SECONDS) as server:
            server.starttls()
            try:
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
            except smtplib.SMTPAuthenticationError:
                print("Error: Gmail SMTP authentication failed. Check SENDER_EMAIL and the Gmail App Password.")
                return False
            server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, message.as_string())
    except smtplib.SMTPException as exc:
        print(f"Error: Failed to send email: {exc}")
        return False
    except OSError as exc:
        print(f"Error: Could not connect to SMTP server: {exc}")
        return False

    print("Weather report email sent successfully.")
    return True


# =====================================================================
# SCHEDULED JOB
# =====================================================================

def send_weather_report():
    """Fetch the current weather and email the report. No email is sent on failure."""
    print(f"[{datetime.now()}] Running scheduled weather report job...")

    weather = get_weather()
    if weather is None:
        print("Weather report not sent due to a data retrieval error.")
        return

    html_content = create_html_email(weather)
    subject = "Himalayan Weather Update — Manali"
    send_email(subject, html_content)


# =====================================================================
# MAIN
# =====================================================================

def main():
    print("Himalayan Weather Monitoring System Started")
    print(f"Location: {LOCATION_NAME}")
    print(f"Daily report time: {DAILY_REPORT_TIME} AM")

    # Send report immediately on startup
    print("Sending initial weather report...")
    send_weather_report()

    # If running in CI or GitHub Actions, exit cleanly without entering infinite loop
    if os.getenv("CI") or os.getenv("GITHUB_ACTIONS"):
        print("Completed report execution for CI/GitHub Actions.")
        return

    schedule.every().day.at(DAILY_REPORT_TIME).do(send_weather_report)

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()