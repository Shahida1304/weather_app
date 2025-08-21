****Weather Dashboard Project****

**Overview**

This project is a Weather Dashboard Application built using Python, Streamlit, and a weather API. The application allows users to check current weather, 5-day forecasts, and air pollution details for any city. It also stores and retrieves weather queries in a database, making it easy to track historical searches.

The goal of this project is to create a user-friendly, interactive platform for accessing real-time weather data, while also demonstrating integration of APIs, database handling, and visualization in a single project.

**Features**

-Real-time Weather Data

Displays current temperature, humidity, wind speed, and weather conditions.

-Weather Forecast

Shows a multi-day forecast with detailed weather information.

-Air Pollution Monitoring

Provides air quality index (AQI) data along with pollutant levels.

-Data Visualization

Generates charts and plots for weather and pollution trends.

-Database Integration

Saves user queries (city name, time, and results) into a database.

-Allows CRUD operations (Create, Read, Update, Delete) on weather history.

-Interactive Dashboard

Simple and intuitive interface using Streamlit.

Users can search for cities, visualize results, and view past history.

**project structure**

weather_app/
│

├── app.py          # Main Streamlit application (frontend)

├── weather.py      # Weather data fetching, forecasting, and visualization

├── database.py     # Database class with CRUD operations

├── requirements.txt# Python dependencies

└── README.md       # Project documentation

**Technologies Used**

Python 3.x

Streamlit (for dashboard UI)

Requests (for API calls)

Matplotlib (for data visualization)

MySQL (for database handling)


**How It Works**

-The user enters a city name in the dashboard.

-The app fetches current weather, forecast, and pollution data using APIs.

-Data is displayed in a clean and interactive format.

-Queries are stored in a database for history tracking.

-Users can view, edit, or delete stored weather queries.


**Future Enhancements**

-Add user authentication for personalized dashboards.
