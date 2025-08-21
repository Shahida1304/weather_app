import os
import requests
import pandas as pd
from dotenv import load_dotenv
import matplotlib.pyplot as plt
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime, time, timedelta

# Load API key
load_dotenv()
OPENWEATHER_API = os.getenv("OPENWEATHER_API")

# Current Weather
def get_weather(city=None, zipcode=None, lat=None, lon=None):
    # Build query
    if city:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API}&units=metric"
        url_fc = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={OPENWEATHER_API}&units=metric"
    elif zipcode:
        url = f"http://api.openweathermap.org/data/2.5/weather?zip={zipcode},IN&appid={OPENWEATHER_API}&units=metric"
        url_fc = f"http://api.openweathermap.org/data/2.5/forecast?zip={zipcode},IN&appid={OPENWEATHER_API}&units=metric"
    elif lat and lon:
        url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API}&units=metric"
        url_fc = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={OPENWEATHER_API}&units=metric"
    else:
        return None

    # Current Weather
    r = requests.get(url)
    if r.status_code != 200:
        return None
    data = r.json()

    weather = {
        "city": data["name"],
        "temp": data["main"]["temp"],
        "weather": data["weather"][0]["description"],  # ✅ consistent key
        "lat": data["coord"]["lat"],
        "lon": data["coord"]["lon"],
    }

    # Next 3-hour forecast
    r_fc = requests.get(url_fc)
    if r_fc.status_code == 200:
        data_fc = r_fc.json()
        if len(data_fc["list"]) > 0:
            next_fc = data_fc["list"][0]  # next 3 hours
            weather["next_3h_temp"] = next_fc["main"]["temp"]
            weather["next_3h_condition"] = next_fc["weather"][0]["description"]

    return weather



# 6-day Daily Forecast
def get_forecast(city=None, zipcode=None, lat=None, lon=None):
    if city:
        url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={OPENWEATHER_API}&units=metric"
    elif zipcode:
        url = f"http://api.openweathermap.org/data/2.5/forecast?zip={zipcode},IN&appid={OPENWEATHER_API}&units=metric"
    elif lat and lon:
        url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={OPENWEATHER_API}&units=metric"
    else:
        return None

    r = requests.get(url)
    if r.status_code != 200:
        return None

    data = r.json()
    forecast_list = []

    for f in data["list"]:
        forecast_list.append(
            {
                "date": pd.to_datetime(f["dt_txt"]).date(),
                "temp": f["main"]["temp"],
                "condition": f["weather"][0]["description"],
            }
        )

    df = pd.DataFrame(forecast_list)

    df_daily = (
        df.groupby("date")
        .agg(
            temp=("temp", "mean"),
            condition=("condition", lambda x: x.value_counts().idxmax()),
        )
        .reset_index()
    )

    return df_daily


# Air Pollution (Current + 5 days)

def get_air_pollution(lat, lon):
    url = f"http://api.openweathermap.org/data/2.5/air_pollution/forecast?lat={lat}&lon={lon}&appid={OPENWEATHER_API}"
    r = requests.get(url)
    if r.status_code != 200:
        return None

    data = r.json()
    pollution_list = []

    aqi_map = {
        1: "Good",
        2: "Fair",
        3: "Moderate",
        4: "Poor",
        5: "Very Poor",
    }

    for f in data["list"]:
        dt = pd.to_datetime(f["dt"], unit="s")
        pollution_list.append(
            {
                "datetime": dt,
                "date": dt.date(),
                "aqi": f["main"]["aqi"],  # numeric AQI
                "aqi_label": aqi_map[f["main"]["aqi"]],  # mapped AQI text
                "pm2_5": f["components"]["pm2_5"],
                "pm10": f["components"]["pm10"],
                "no2": f["components"]["no2"],
                "so2": f["components"]["so2"],
                "o3": f["components"]["o3"],
                "co": f["components"]["co"],
            }
        )

    df = pd.DataFrame(pollution_list)

    df = df.groupby("date", as_index=False).mean(numeric_only=True)

    df["aqi"] = df["aqi"].round().astype(int)
    df["aqi_label"] = df["aqi"].map(aqi_map)

    return df


def plot_weather(forecast_df):
    fig, ax = plt.subplots()
    ax.plot(forecast_df["date"], forecast_df["temp"], marker="o")
    ax.set_xlabel("Date")
    ax.set_ylabel("Temperature (°C)")
    ax.set_title("6-Day Weather Forecast")
    plt.xticks(rotation=45)
    plt.tight_layout()
    return fig


def plot_pollution(pollution_df):
    fig, ax = plt.subplots()

    # Plot AQI values (1-5)
    ax.plot(
        pollution_df["date"],
        pollution_df["aqi"],
        marker="o",
        color="purple",
        label="AQI",
    )

    # Annotate with AQI labels (Good, Fair, etc.)
    for i, row in pollution_df.iterrows():
        ax.text(
            row["date"], row["aqi"] + 0.1, row["aqi_label"], ha="center", fontsize=8
        )

    ax.set_xlabel("Date")
    ax.set_ylabel("AQI (1=Good, 5=Very Poor)")
    ax.set_title("Air Quality Index Forecast (5 Days)")
    ax.set_ylim(0, 6)
    ax.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    return fig
# Report Generator (PDF)
def generate_report(city, weather, forecast, pollution):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph(f"Weather Report for {city}", styles["Title"]))
    story.append(Spacer(1, 12))

    # Current weather
    story.append(Paragraph("🌤 Current Weather", styles["Heading2"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"Temperature: {weather['temp']} °C", styles["Normal"]))
    story.append(Paragraph(f"Condition: {weather['weather']}", styles["Normal"]))
    story.append(
        Paragraph(f"Coordinates: {weather['lat']}, {weather['lon']}", styles["Normal"])
    )
    story.append(Spacer(1, 12))

    # 5-day forecast
    if forecast is not None:
        story.append(Paragraph("📊 5-Day Forecast", styles["Heading2"]))
        story.append(Spacer(1, 6))
        story.append(Table([forecast.columns.tolist()] + forecast.values.tolist()))

    story.append(Spacer(1, 12))

    # Air Pollution (with AQI categories)
    if pollution is not None:
        story.append(
            Paragraph("💨 Air Pollution Forecast (5 Days)", styles["Heading2"])
        )
        story.append(Spacer(1, 6))

        # Ensuring AQI and category columns exist
        if "aqi" not in pollution.columns:
            # Example fallback: use pm2_5 levels to estimate
            def estimate_aqi(pm2_5):
                if pm2_5 <= 12:
                    return 1
                if pm2_5 <= 35:
                    return 2
                if pm2_5 <= 55:
                    return 3
                if pm2_5 <= 150:
                    return 4
                return 5

            pollution["aqi"] = pollution["pm2_5"].apply(estimate_aqi)

        def label(aqi):
            return {1: "Good", 2: "Fair", 3: "Moderate", 4: "Poor", 5: "Very Poor"}.get(
                aqi, "Unknown"
            )

        pollution["AQI_Category"] = pollution["aqi"].apply(label)

        story.append(Table([pollution.columns.tolist()] + pollution.values.tolist()))

    doc.build(story)
    buffer.seek(0)
    return buffer


def get_user_location():
    """Get user's approximate location using IP address"""
    try:
        response = requests.get("http://ip-api.com/json/")
        data = response.json()
        return data["lat"], data["lon"]
    except:
        return None, None


def get_current_weather(lat, lon):
    """
    Fetches the current weather for given latitude and longitude using OpenWeatherMap API.
    """
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API}&units=metric"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        return {
            "city": data["name"],
            "temperature": data["main"]["temp"],
            "description": data["weather"][0]["description"].capitalize(),
            "humidity": data["main"]["humidity"],
            "wind_speed": data["wind"]["speed"],
        }
    else:
        return {"error": f"Failed to fetch weather: {response.status_code}"}


def get_weather_tips(temp_c, description):
    tips = []
    if temp_c >= 40:
        tips.append(
            "🥵 Extreme heat! Stay indoors during peak hours, hydrate with electrolyte drinks, use SPF 30+, and wear loose, breathable layers."
        )
    elif temp_c >= 30:
        tips.append(
            "🌞 Hot weather—choose lightweight, moisture-wicking fabrics and stay hydrated."
        )
    elif temp_c <= 0:
        tips.append(
            "🥶 Cold weather—layer up: base, insulating mid-layer, and waterproof shell. Cover head, hands, feet to stay warm."
        )
    elif 10 <= temp_c < 20:
        tips.append(
            "🧥 Mild but cool—layer light sweater or jacket, especially in the morning/evening."
        )
    else:
        tips.append("🙂 Comfortable weather—light layers are enough.")

    if "rain" in description.lower():
        tips.append("☔ Carry an umbrella or wear waterproof outer layer.")
    if "snow" in description.lower():
        tips.append(
            "❄ Be cautious—wear boots with good grip and watch for icy surfaces."
        )
    if "clear" in description.lower() and temp_c > 25:
        tips.append("🕶 Sunny and clear—use sunglasses and apply sunscreen.")

    return tips


def parse_record_time(rt):
    if isinstance(rt, str):
        try:
            return datetime.strptime(rt, "%H:%M:%S").time()
        except:
            return datetime.now().time()
    elif isinstance(rt, time):
        return rt
    else:
        return datetime.now().time()

