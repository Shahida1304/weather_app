import streamlit as st
import mysql.connector
from mysql.connector import Error
from datetime import datetime, time, timedelta
import os

class WeatherDB:
    def __init__(self, host=None, user=None, password=None, database=None):

        # Local-first configuration
        host = host or os.getenv("DB_HOST", "localhost")
        user = user or os.getenv("DB_USER", "root")
        password = password or os.getenv("DB_PASSWORD", "")
        database = database or os.getenv("DB_NAME", "weather_db")

        self.conn = None
        self.cursor = None

        try:
            self.conn = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database,
                port=3306
            )
            self.cursor = self.conn.cursor(dictionary=True)
            st.success("✅ Connected to local MySQL database")

            self.create_table_if_not_exists()

        except Error as e:
            st.error(f"❌ Could not connect to MySQL: {e}")

    def create_table_if_not_exists(self):
        query = """
        CREATE TABLE IF NOT EXISTS history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            location VARCHAR(255),
            weather VARCHAR(100),
            air_quality VARCHAR(50),
            record_time TIME,
            date DATETIME
        )
        """
        self.cursor.execute(query)
        self.conn.commit()

    def add_record(self, location, weather, air_quality, record_time=None, date=None):
        record_time = record_time or datetime.now().strftime("%H:%M:%S")
        if isinstance(record_time, (datetime, time)):
            record_time = record_time.strftime("%H:%M:%S")

        date = date or datetime.now()

        query = """
        INSERT INTO history (location, weather, air_quality, record_time, date)
        VALUES (%s, %s, %s, %s, %s)
        """
        self.cursor.execute(query, (location, weather, air_quality, record_time, date))
        self.conn.commit()

    def get_records(self):
        self.cursor.execute(
            "SELECT * FROM history ORDER BY date DESC, record_time DESC"
        )
        rows = self.cursor.fetchall()

        for r in rows:
            if isinstance(r["record_time"], timedelta):
                total_seconds = int(r["record_time"].total_seconds())
                h = total_seconds // 3600
                m = (total_seconds % 3600) // 60
                s = total_seconds % 60
                r["record_time"] = f"{h:02d}:{m:02d}:{s:02d}"

        return rows

    def update_record(self, record_id, location, weather, air_quality, record_time, date):
        if isinstance(record_time, (datetime, time)):
            record_time = record_time.strftime("%H:%M:%S")

        query = """
        UPDATE history
        SET location=%s, weather=%s, air_quality=%s, record_time=%s, date=%s
        WHERE id=%s
        """
        self.cursor.execute(
            query,
            (location, weather, air_quality, record_time, date, record_id)
        )
        self.conn.commit()

    def delete_record(self, record_id):
        self.cursor.execute("DELETE FROM history WHERE id=%s", (record_id,))
        self.conn.commit()
