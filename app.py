import streamlit as st
from weather import (
    get_weather,
    get_forecast,
    get_air_pollution,
    plot_weather,
    plot_pollution,
    generate_report,
    get_user_location,
    get_current_weather,
    get_weather_tips,
    parse_record_time,
)
from database import WeatherDB
from datetime import datetime, time, timedelta
import urllib.parse

st.markdown(
    "<h1 style='text-align: center; color: #2E86C1;'>🌍 Weather & Air Around You</h1>",
    unsafe_allow_html=True,
)
st.markdown("---")

col1 = st.columns(1)[0]
latitude, longitude = get_user_location()
with col1:
    if latitude and longitude:
        weather = get_current_weather(latitude, longitude)
        city = weather.get("city", "Your Location")  #
        st.subheader(f"Today's Weather in {city}")
        if "error" in weather:
            st.error(weather["error"])
        else:
            st.markdown(
                f"""
                <div style='display: flex; gap: 20px; justify-content: center;'>
                    <div style='background-color:#f0f8ff;padding:15px;border-radius:12px;box-shadow:2px 2px 10px #dcdcdc;width:30%;text-align:center;'>
                        <h3>🌡 Temp</h3>
                        <p style='font-size:22px;font-weight:bold;'>{weather["temperature"]} °C</p>
                    </div>
                    <div style='background-color:#eafaf1;padding:15px;border-radius:12px;box-shadow:2px 2px 10px #dcdcdc;width:30%;text-align:center;'>
                        <h3>💧 Humidity</h3>
                        <p style='font-size:22px;font-weight:bold;'>{weather["humidity"]}%</p>
                    </div>
                    <div style='background-color:#fef9e7;padding:15px;border-radius:12px;box-shadow:2px 2px 10px #dcdcdc;width:30%;text-align:center;'>
                        <h3>🌬️ Wind</h3>
                        <p style='font-size:22px;font-weight:bold;'>{weather["wind_speed"]} m/s</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            tips = get_weather_tips(weather["temperature"], weather["description"])
            st.markdown("### 🌤️ Today's Weather Tips for You:")
            for tip in tips:
                st.write(f"- {tip}")


now = datetime.now()
# Initialize database
db = WeatherDB()

st.title("Search (city/lat,lon/zipcode)")
# Input section
location_input = st.text_input("Enter City / Zip / Lat,Lon")

if st.button("Search"):
    lat_val, lon_val = None, None
    city, zipcode = None, None

    # Check if user entered lat,lon
    if "," in location_input:
        try:
            lat_val, lon_val = map(float, location_input.split(","))
        except:  # noqa: E722
            st.error("Invalid latitude/longitude format. Use: lat,lon")
    elif location_input.isdigit():
        zipcode = location_input
    else:
        city = location_input

    weather = get_weather(
        city=city if city else None,
        zipcode=zipcode if zipcode else None,
        lat=lat_val,
        lon=lon_val,
    )

    if weather:
        # Air Pollution
        pollution = get_air_pollution(weather["lat"], weather["lon"])
        air_quality_text = "N/A"
        if pollution is not None and not pollution.empty:
            # Take latest AQI value
            air_quality_text = f"AQI {pollution.iloc[0]['aqi']}"

        # ---------------- Save Search to Database ----------------
        try:
            db.add_record(
                location=weather["city"],
                weather=weather["weather"],
                air_quality=air_quality_text,
                record_time=now.strftime("%H:%M:%S"),
                date=now.date(),
            )
        except Exception as e:
            st.warning(f"⚠ Could not save to database: {e}")

        # Current weather
        st.subheader(f"🌤 Current Weather in {weather['city']}")
        st.write(f"**Temperature:** {weather['temp']} °C")
        search_query = f"{city} weather"
        youtube_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(search_query)}"

        st.markdown(
            f"[▶ Watch Weather Video for {city}]({youtube_url})", unsafe_allow_html=True
        )

        # Handle DB string vs API JSON
        if "weather" in weather:  # From API
            if isinstance(weather["weather"], list):
                st.write(
                    f"**Condition:** {weather['weather'][0]['main']} ({weather['weather'][0]['description']})"
                )
            else:
                st.write(f"**Condition:** {weather['weather']}")
        elif "description" in weather:
            st.write(f"**Condition:** {weather['description']}")
        elif "condition" in weather:
            st.write(f"**Condition:** {weather['condition']}")
        else:
            st.write(
                f"**Condition:** {weather['weather'] if 'weather' in weather else 'N/A'}"
            )

        if "next_3h_temp" in weather:
            st.write(f"🌡 Next 3h Temp: {weather['next_3h_temp']} °C")
            st.write(f"⏳ Next 3h Condition: {weather['next_3h_condition']}")

        # Forecast
        forecast = get_forecast(
            city=city if city else None,
            zipcode=zipcode if zipcode else None,
            lat=lat_val,
            lon=lon_val,
        )
        if forecast is not None:
            st.subheader("📊 6-Day Weather Forecast (Daily Averages)")
            st.dataframe(forecast)
            st.pyplot(plot_weather(forecast))

        if pollution is not None:
            st.subheader("💨 Air Quality Forecast (5 Days)")
            st.dataframe(pollution)
            st.pyplot(plot_pollution(pollution))

        # Report
        report = generate_report(weather["city"], weather, forecast, pollution)
        st.download_button(
            label="⬇️ Download Weather Report (PDF)",
            data=report,
            file_name=f"{weather['city']}_weather_report.pdf",
            mime="application/pdf",
        )

    else:
        st.error("Location not found. Try again!")

menu = ["Add Record", "View Records", "Update Record", "Delete Record"]
choice = st.sidebar.selectbox("Menu", menu)

# ➕ Add Record
if choice == "Add Record":
    st.subheader("Add New Weather Record")
    location = st.text_input("Location")
    weather_cond = st.text_input("Weather Condition")
    air_quality = st.text_input("Air Quality")
    time_val = st.time_input("Time")
    date_val = st.date_input("Date")

    if st.button("Add Record"):
        db.add_record(
            location=location,
            weather=weather_cond,
            air_quality=air_quality,
            record_time=time_val,
            date=date_val,
        )
        st.success("Record added successfully!")

# 📖 View Records
elif choice == "View Records":
    st.subheader("Weather History Records")
    records = db.get_records()
    if records:
        st.table(records)
    else:
        st.warning("⚠ No records found.")

# ✏️ Update Record
elif choice == "Update Record":
    st.subheader("Update Weather Record")
    records = db.get_records()
    record_dict = {f"{r['id']} - {r['location']} ({r['weather']})": r for r in records}

    if record_dict:
        selection = st.selectbox("Select record to update", list(record_dict.keys()))
        record = record_dict[selection]

        time_val = parse_record_time(record["record_time"])
        date_val = record["date"] if record["date"] else datetime.now().date()

        location_input = st.text_input("Location", record["location"])
        weather_input = st.text_input("Weather Condition", record["weather"])
        air_quality_input = st.text_input("Air Quality", record["air_quality"])
        time_input = st.time_input("Time", time_val)
        date_input = st.date_input("Date", date_val)

        if st.button("Update Record"):
            db.update_record(
                record["id"],
                location_input,
                weather_input,
                air_quality_input,
                record_time=time_input,
                date=date_input,
            )
            st.success("Record updated successfully!")

# 🗑️ Delete Record
elif choice == "Delete Record":
    st.subheader("Delete Weather Record")
    records = db.get_records()
    record_dict = {f"{r['id']} - {r['location']} ({r['weather']})": r for r in records}

    if record_dict:
        selection = st.selectbox("Select record to delete", list(record_dict.keys()))
        record = record_dict[selection]

        if st.button("Delete Record"):
            db.delete_record(record["id"])
            st.success("Record deleted successfully!")
# Initialize session state
if "show_info" not in st.session_state:
    st.session_state.show_info = False

# Button to toggle sidebar info
if st.button("Show Info"):
    st.session_state.show_info = not st.session_state.show_info  # toggle

# Conditionally show sidebar info
if st.session_state.show_info:
    st.success("👩‍💻 Name: Shaik Shahida")
    st.info(
        """📌 The Product Manager Accelerator Program is a career-growth platform that supports professionals at every stage, from students entering the field to Directors advancing into leadership roles. With structured training, real-world projects, and expert mentorship, the program has helped hundreds of ambitious individuals build strong PM and leadership skills, secure dream jobs, and accelerate their career growth in top organizations.
        [🔗 Visit LinkedIn Page](https://www.linkedin.com/school/pmaccelerator/)"""
    )
