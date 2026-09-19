# 🌦️ Automated Weather Monitoring & Email Reporting System

An automated Python-based weather monitoring system that fetches live weather conditions from the Open-Meteo API and sends formatted email updates via Gmail SMTP.

Includes **GitHub Actions automation** configured for **Indian Standard Time (IST)** to dispatch daily weather reports automatically.

---

## 📍 Locations Monitored
1. **Palani, Tamil Nadu, India** (`weather_email_simple.py`)
   - Current temperature, weather condition (rain, clouds, clear sky), humidity, and wind speed.
2. **Manali, Himachal Pradesh, India** (`himalayan_weather_monitor.py`)
   - Mountain weather updates with detailed HTML reporting and daily scheduling.

---

## 🚀 Features
- **No API Key Required**: Powered by the free and open [Open-Meteo](https://open-meteo.com/) API.
- **Gmail SMTP Integration**: Secure STARTTLS connection with Gmail App Password authentication.
- **Automated GitHub Actions Workflow**: Runs daily at **09:00 AM IST** (`30 3 * * *` UTC) or on-demand using manual dispatch.
- **Local `.env` Support**: Safely keeps credentials local without hardcoding sensitive passwords into git.

---

## ⚙️ Local Setup

### 1. Install Dependencies
```bash
pip install requests schedule
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your details:
```env
SMTP_EMAIL=your_gmail_address@gmail.com
SMTP_APP_PASSWORD=your_16_digit_app_password
TO_EMAIL=recipient_email@gmail.com
```

> **Note**: To create a Gmail App Password:
> 1. Turn on 2-Step Verification on your [Google Account](https://myaccount.google.com/).
> 2. Go to [Google App Passwords](https://myaccount.google.com/apppasswords).
> 3. Generate an App Password for "Mail" and paste the 16 characters into `SMTP_APP_PASSWORD`.

### 3. Run Locally
- **Palani Weather Report:**
  ```bash
  python weather_email_simple.py
  ```
- **Himalayan (Manali) Weather Report:**
  ```bash
  python himalayan_weather_monitor.py
  ```

---

## ⏰ GitHub Actions Automation (IST Schedule)

The workflow file is located at [`.github/workflows/weather_report.yml`](.github/workflows/weather_report.yml).

### Add GitHub Repository Secrets
In your GitHub repository, navigate to **Settings** > **Secrets and variables** > **Actions** and add:
- `SMTP_EMAIL`: Your sender Gmail address.
- `SMTP_APP_PASSWORD`: Your 16-character Gmail App Password.
- `TO_EMAIL`: The recipient's email address.

### Manual Trigger:
You can also trigger the report at any time from the **Actions** tab by selecting the workflow and clicking **Run workflow**.
