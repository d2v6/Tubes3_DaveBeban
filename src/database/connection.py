import mysql.connector
from mysql.connector import Error
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()


class DatabaseConnection:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def connect(self) -> bool:
        """🔌 CONNECT: Membuka koneksi ke database"""
        try:
            self.connection = mysql.connector.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                user=os.getenv('DB_USER', 'root'),
                password=os.getenv('DB_PASSWORD', ''),
                database=os.getenv('DB_NAME', 'cv_ats'),
                port=int(os.getenv('DB_PORT', 3306)),
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
            )

            if self.connection.is_connected():
                self.cursor = self.connection.cursor(dictionary=True)
                print("Successfully connected to MySQL database")
                return True
                
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            return False

    def disconnect(self):
        """🔌 DISCONNECT: Menutup koneksi database"""
        try:
            if self.cursor:
                self.cursor.close()
                self.cursor = None
                
            if self.connection and self.connection.is_connected():
                self.connection.close()
                self.connection = None
                print("MySQL connection closed")
                
        except Error as e:
            print(f"Error closing connection: {e}")

    def execute_query(self, query: str, params: tuple = None, fetch: bool = True) -> Optional[List[Dict]]:
        """📊 SELECT: Mengambil data dari database"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            if fetch:
                return self.cursor.fetchall()  # Return data
            else:
                self.connection.commit()  # For non-SELECT queries
                return True
                
        except Error as e:
            print(f"Error executing query: {e}")
            if not fetch:
                self.connection.rollback()
            return None

    def execute_insert(self, query: str, params: tuple = None) -> Optional[int]:
        """INSERT: Menambah data baru, return ID yang baru dibuat"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
                
            self.connection.commit()
            return self.cursor.lastrowid  # Return new ID
            
        except Error as e:
            print(f"Error executing insert: {e}")
            self.connection.rollback()
            return None

    def execute_update(self, query: str, params: tuple = None) -> bool:
        """UPDATE/DELETE: Mengubah atau menghapus data"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
                
            self.connection.commit()
            return True
            
        except Error as e:
            print(f"Error executing update: {e}")
            self.connection.rollback()
            return False

    def is_connected(self) -> bool:
        """CHECK: Cek apakah masih terhubung"""
        try:
            return self.connection and self.connection.is_connected()
        except:
            return False

    def get_last_insert_id(self) -> Optional[int]:
        """GET ID: Ambil ID terakhir yang di-insert"""
        return self.cursor.lastrowid if self.cursor else None