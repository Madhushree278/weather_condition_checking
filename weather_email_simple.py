"""
weather_email_simple.py
------------------------
Gets the current weather for Palani, Tamil Nadu, India from the free
Open-Meteo API (no API key needed) and emails a formatted weather report
using Gmail SMTP (smtp.gmail.com, port 587, STARTTLS).

Install the only required package:
    pip install requests

Run it:
    python weather_email_simple.py
"""

import os
import sys
import smtplib
import requests
from datetime import datetime
from email.mime.text import MIMEText

# =============================================================================
# SMTP CONFIGURATION  --  EDIT THESE THREE VALUES BEFORE RUNNING
# =============================================================================
# IMPORTANT: SMTP_APP_PASSWORD must be a Gmail "App Password", NOT your normal
# Gmail login password. Gmail blocks normal passwords for SMTP login.
#
# How to create a Gmail App Password:
#   1. Go to your Google Account -> Security.
#   2. Turn on 2-Step Verification (required for App Passwords to appear).
#   3. Search for "App passwords" in your Google Account settings.
#   4. Choose app "Mail", device "Other" (name it e.g. "Weather Script"),
#      then click Generate.
#   5. Copy the 16-character password Google gives you (remove any spaces)
#      and paste it below as SMTP_APP_PASSWORD.
# =============================================================================

# Automatically load .env file if present
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

SMTP_EMAIL = os.getenv("SMTP_EMAIL") or "your_email@gmail.com"
SMTP_APP_PASSWORD = os.getenv("SMTP_APP_PASSWORD") or "your_app_password"
TO_EMAIL = os.getenv("TO_EMAIL") or "recipient@gmail.com"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587  # STARTTLS port

# =============================================================================
# LOCATION CONFIGURATION -- Palani, Tamil Nadu, India
# =============================================================================

LOCATION_NAME = "Palani, Tamil Nadu, India"
LATITUDE = 10.4500
LONGITUDE = 77.5167


# =============================================================================
# WEATHER CODE TRANSLATION
# =============================================================================

def get_weather_condition(code: int) -> str:
    """Converts Open-Meteo's numeric weather code into a readable string."""
    weather_codes = {
        0: "Clear Sky",
        1: "Mainly Clear",
        2: "Partly Cloudy",
        3: "Cloudy",
        45: "Fog",
        48: "Fog",
        51: "Rain", 53: "Rain", 55: "Rain",
        56: "Rain", 57: "Rain",
        61: "Rain", 63: "Rain", 65: "Rain",
        66: "Rain", 67: "Rain",
        71: "Snow", 73: "Snow", 75: "Snow", 77: "Snow",
        80: "Rain", 81: "Rain", 82: "Rain",
        85: "Snow", 86: "Snow",
        95: "Thunderstorm",
        96: "Thunderstorm",
        99: "Thunderstorm",
    }
    return weather_codes.get(code, "Unknown")


# =============================================================================
# STEP 1: GET CURRENT WEATHER FROM OPEN-METEO
# =============================================================================

def fetch_weather_data() -> dict:
    """Requests current weather data (and humidity) from Open-Meteo and
    returns the parsed fields as a dictionary. No API key required."""

    current_weather_url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={LATITUDE}&longitude={LONGITUDE}"
        f"&current_weather=true&timezone=Asia%2FKolkata"
    )

    # --- Request current weather (temperature, wind, weather code, time) ---
    try:
        response = requests.get(current_weather_url, timeout=10)
        response.raise_for_status()  # Raises an error for bad HTTP status codes
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to the internet. Please check your connection.")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("ERROR: The weather API request timed out. Please try again.")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"ERROR: Weather API returned an error: {e}")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"ERROR: An unexpected network error occurred: {e}")
        sys.exit(1)

    try:
        data = response.json()
        current = data["current_weather"]
        temperature = current["temperature"]
        wind_speed = current["windspeed"]
        weather_code = current["weathercode"]
        observed_time = current["time"]
    except (KeyError, ValueError) as e:
        print(f"ERROR: Invalid or unexpected API response format: {e}")
        sys.exit(1)

    # --- Request humidity separately (not included in current_weather) ---
    humidity = fetch_humidity(observed_time)

    return {
        "location": LOCATION_NAME,
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "temperature": temperature,
        "condition": get_weather_condition(weather_code),
        "humidity": humidity,
        "wind_speed": wind_speed,
        "observed_time": observed_time,
    }


def fetch_humidity(observed_time: str):
    """Fetches relative humidity for the current hour from Open-Meteo's
    hourly data and matches it to the observed timestamp."""
    hourly_url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={LATITUDE}&longitude={LONGITUDE}"
        f"&hourly=relative_humidity_2m&timezone=Asia%2FKolkata"
    )
    try:
        response = requests.get(hourly_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        times = data["hourly"]["time"]
        humidity_values = data["hourly"]["relative_humidity_2m"]
        hour_prefix = observed_time[:13]
        for idx, t in enumerate(times):
            if t.startswith(hour_prefix):
                return humidity_values[idx]
        if observed_time in times:
            index = times.index(observed_time)
            return humidity_values[index]
        return "N/A"
    except (requests.exceptions.RequestException, KeyError, ValueError):
        # Humidity is a secondary field; don't stop the whole program if it fails.
        return "N/A"


# =============================================================================
# STEP 2: FORMAT THE EMAIL BODY
# =============================================================================

def format_email_body(weather: dict) -> str:
    """Builds the professional, readable plain-text email body using
    dynamic values returned by the Open-Meteo API."""
    dt = datetime.fromisoformat(weather["observed_time"])
    formatted_date = dt.strftime("%d %B %Y, %I:%M %p")

    body = f"""Current Weather Update - Palani

Location: {weather['location']}
Latitude: {weather['latitude']}
Longitude: {weather['longitude']}

Weather Conditions:
Condition: {weather['condition']}
Temperature: {weather['temperature']} °C
Humidity: {weather['humidity']}%
Wind Speed: {weather['wind_speed']} km/h

Date & Time:
{formatted_date}

This is an automated weather report generated using Python.
"""
    return body


# =============================================================================
# STEP 3: SEND THE EMAIL VIA GMAIL SMTP
# =============================================================================

def send_email(body: str):
    """Connects to Gmail SMTP (smtp.gmail.com:587) using STARTTLS and
    sends the weather report email. The App Password is never printed."""

    if SMTP_EMAIL == "yourgmail@gmail.com" or SMTP_APP_PASSWORD == "your_16_digit_app_password":
        print("ERROR: Please edit the SMTP CONFIGURATION section at the top of this")
        print("script and replace SMTP_EMAIL, SMTP_APP_PASSWORD, and TO_EMAIL with")
        print("your real values before running.")
        sys.exit(1)

    message = MIMEText(body, "plain", "utf-8")
    message["Subject"] = "Current Weather Update - Palani"
    message["From"] = SMTP_EMAIL
    message["To"] = TO_EMAIL

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            server.starttls()  # Upgrade the connection to a secure TLS connection
            server.login(SMTP_EMAIL, SMTP_APP_PASSWORD)
            server.sendmail(SMTP_EMAIL, TO_EMAIL, message.as_string())
    except smtplib.SMTPAuthenticationError:
        # Note: we deliberately do not print SMTP_APP_PASSWORD anywhere.
        print("ERROR: SMTP authentication failed. Check your Gmail address and App Password.")
        sys.exit(1)
    except smtplib.SMTPConnectError:
        print("ERROR: Could not connect to Gmail's SMTP server.")
        sys.exit(1)
    except smtplib.SMTPException as e:
        print(f"ERROR: Failed to send email: {e}")
        sys.exit(1)


# =============================================================================
# MAIN WORKFLOW
# =============================================================================

def main():
    print("Fetching current weather data for Palani...")
    weather = fetch_weather_data()

    print("Formatting email...")
    email_body = format_email_body(weather)

    print("Connecting to Gmail SMTP and sending email...")
    send_email(email_body)

    print("SUCCESS: Weather report email sent successfully!")


if __name__ == "__main__":
    main()
