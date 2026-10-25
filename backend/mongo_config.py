# ============================================
# CONFIGURACIÓN DE MONGODB
# ============================================

from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env (en la raíz del proyecto)
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

# Obtener variables
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "learnify_db")

def get_mongo_connection():
    """Devuelve la base de datos de MongoDB"""
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB_NAME]
    return db

def test_connection():
    """Prueba la conexión a MongoDB"""
    try:
        db = get_mongo_connection()
        db.list_collection_names()
        print("Conexión a MongoDB exitosa")
        print(f"Base de datos: {MONGO_DB_NAME}")
        return True
    except Exception as e:
        print(f"Error de conexión: {e}")
        return False

if __name__ == "__main__":
    test_connection()