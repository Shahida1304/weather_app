import streamlit as st
import mysql.connector
from mysql.connector import Error
from datetime import datetime, time, timedelta

class WeatherDB:
    def __init__(self, host=None, user=None, password=None, database=None):
        # Load secrets if parameters are not provided
        host = host or st.secrets.get("DB_HOST")
        user = user or st.secrets.get("DB_USER")
        password = password or st.secrets.get("DB_PASSWORD")
        database = database or st.secrets.get("DB_NAME")

        self.conn = None
        self.cursor = None

        try:
            self.conn = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )
            self.cursor = self.conn.cursor(dictionary=True)
            st.success("Connected to MySQL Database")
        except Error as e:
            st.error(f"Could not connect to MySQL database: {e}")
            # Optional: raise RuntimeError(e) if you want the app to stop
            self.conn = None
            self.cursor = None


    self.create_table_if_not_exists()
        except Error as e:
            st.error(f"Could not connect to MySQL database: {e}")
            self.conn = None
            self.cursor = None

    def create_table_if_not_exists(self):
        if not self.cursor:
            return
        try:
            create_table_query = """
            CREATE TABLE IF NOT EXISTS history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                location VARCHAR(255),
                temperature VARCHAR(50),
                air_quality VARCHAR(50),
                record_time TIME,
                date DATETIME
            )
            """
            self.cursor.execute(create_table_query)
            self.conn.commit()
            st.info("Table 'history' ensured to exist")
        except Error as e:
            st.error(f"Error creating table: {e}")

    def add_record(self, location, weather, air_quality, record_time=None, date=None):
        if not self.cursor:
            return "Cannot add record: no database connection."
        try:
            record_time = record_time or datetime.now().strftime("%H:%M:%S")
            if isinstance(record_time, (datetime, time)):
                record_time = record_time.strftime("%H:%M:%S")
            date = date or datetime.now().date()

            sql = """
                INSERT INTO history (location, weather, air_quality, record_time, date)
                VALUES (%s, %s, %s, %s, %s)
            """
            self.cursor.execute(sql, (location, weather, air_quality, record_time, date))
            self.conn.commit()
            return "Record inserted successfully"
        except Error as e:
            return f"Error inserting record: {e}"

    def get_records(self, location=None, start_date=None, end_date=None):
        if not self.cursor:
            return []
        try:
            query = "SELECT * FROM history WHERE 1=1"
            params = []

            if location:
                query += " AND location=%s"
                params.append(location)
            if start_date:
                query += " AND date >= %s"
                params.append(start_date)
            if end_date:
                query += " AND date <= %s"
                params.append(end_date)

            query += " ORDER BY date DESC, record_time DESC"
            self.cursor.execute(query, tuple(params))
            rows = self.cursor.fetchall()

            for r in rows:
                if isinstance(r["record_time"], timedelta):
                    total_seconds = int(r["record_time"].total_seconds())
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    seconds = total_seconds % 60
                    r["record_time"] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

            return rows
        except Exception as e:
            st.error(f"Error reading records: {e}")
            return []

    def update_record(self, record_id, location=None, weather=None, air_quality=None, record_time=None, date=None):
        if not self.cursor:
            return "Cannot update record: no database connection."
        try:
            fields = []
            values = []

            if location:
                fields.append("location=%s")
                values.append(location)
            if weather:
                fields.append("weather=%s")
                values.append(weather)
            if air_quality:
                fields.append("air_quality=%s")
                values.append(air_quality)
            if record_time:
                if isinstance(record_time, (datetime, time)):
                    record_time = record_time.strftime("%H:%M:%S")
                fields.append("record_time=%s")
                values.append(record_time)
            if date:
                fields.append("date=%s")
                values.append(date)

            if not fields:
                return "Nothing to update"

            query = f"UPDATE history SET {', '.join(fields)} WHERE id=%s"
            values.append(record_id)
            self.cursor.execute(query, tuple(values))
            self.conn.commit()
            return f"Record {record_id} updated"
        except Exception as e:
            return f"Error updating record: {e}"

    def delete_record(self, record_id):
        if not self.cursor:
            return "Cannot delete record: no database connection."
        try:
            self.cursor.execute("DELETE FROM history WHERE id=%s", (record_id,))
            self.conn.commit()
            return f"Record {record_id} deleted"
        except Exception as e:
            return f"Error deleting record: {e}"

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        st.info("MySQL connection closed")

