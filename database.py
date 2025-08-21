import mysql.connector
from mysql.connector import Error
from datetime import datetime, time, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class WeatherDB:
    def __init__(
        self, host=st.secrets("DB_HOST", "localhost"), 
        user=st.secrets("DB_USER", "root"), 
        password=st.secrets("DB_PASSWORD", ""), 
        database=st.secrets("DB_NAME", "weatherdb")
    ):
        try:
            self.conn = mysql.connector.connect(
                host=host, user=user, password=password, database=database
            )
            self.cursor = self.conn.cursor(dictionary=True)
            print("Connected to MySQL Database")
        except Error as e:
            print("Error connecting to database:", e)

    def add_record(self, location, weather, air_quality, record_time=None, date=None):
        try:
            # Ensure record_time is string "HH:MM:SS"
            if record_time is None:
                record_time = datetime.now().strftime("%H:%M:%S")
            elif isinstance(record_time, (datetime, time)):
                record_time = record_time.strftime("%H:%M:%S")

            if date is None:
                date = datetime.now().date()

            sql = """
                INSERT INTO history (location, weather, air_quality, record_time, date)
                VALUES (%s, %s, %s, %s, %s)
            """
            self.cursor.execute(
                sql, (location, weather, air_quality, record_time, date)
            )
            self.conn.commit()
            print("Record inserted successfully")
        except Error as e:
            print("Error inserting record:", e)

    
    def get_records(self, location=None, start_date=None, end_date=None):
        try:
            query = "SELECT * FROM history WHERE 1=1"
            params = []

            if location:
                query += " AND location = %s"
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
            print(f"Error reading records: {e}")
            return []


    def update_record(
        self,
        record_id,
        location=None,
        weather=None,
        air_quality=None,
        record_time=None,
        date=None,
    ):
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
        print("MySQL connection closed")


