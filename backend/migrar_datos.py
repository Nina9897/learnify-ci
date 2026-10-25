# ============================================
# MIGRAR DATOS DE MYSQL A MONGODB
# ============================================

import mysql.connector
from mongo_config import get_mongo_connection
from config import obtener_conexion as get_mysql_connection
from bson import ObjectId
from datetime import datetime as dt
import datetime

def migrar_usuarios(mapping_ids):
    """Migrar tabla usuarios a MongoDB"""
    print("\n📋 Migrando usuarios...")
    
    mysql_conn = get_mysql_connection()
    mysql_cursor = mysql_conn.cursor(dictionary=True)
    mysql_cursor.execute("SELECT * FROM usuarios")
    usuarios = mysql_cursor.fetchall()
    
    mongo_db = get_mongo_connection()
    collection = mongo_db["usuarios"]
    
    for usuario in usuarios:
        doc = {
            "nombre": usuario["nombre"],
            "email": usuario["email"],
            "password": usuario["password"],
            "rol": usuario["rol"],
            "fecha_registro": usuario["fecha_registro"]
        }
        result = collection.insert_one(doc)
        mapping_ids[usuario["id"]] = result.inserted_id
        print(f"   ✅ Usuario: {usuario['nombre']} (ID MySQL: {usuario['id']})")
    
    mysql_cursor.close()
    mysql_conn.close()
    
    print(f"   📊 Total: {len(usuarios)} usuarios migrados")
    return mapping_ids

def migrar_equipos(mapping_ids):
    """Migrar tabla equipos a MongoDB"""
    print("\n📋 Migrando equipos...")
    
    mysql_conn = get_mysql_connection()
    mysql_cursor = mysql_conn.cursor(dictionary=True)
    mysql_cursor.execute("SELECT * FROM equipos")
    equipos = mysql_cursor.fetchall()
    
    mongo_db = get_mongo_connection()
    collection = mongo_db["equipos"]
    
    mapping_equipos = {}
    
    for equipo in equipos:
        doc = {
            "nombre": equipo["nombre"],
            "descripcion": equipo["descripcion"],
            "lider_id": mapping_ids.get(equipo["lider_id"]),
            "fecha_creacion": equipo["fecha_creacion"],
            "miembros": []
        }
        result = collection.insert_one(doc)
        mapping_equipos[equipo["id"]] = result.inserted_id
        print(f"   ✅ Equipo: {equipo['nombre']} (ID MySQL: {equipo['id']})")
    
    mysql_cursor.close()
    mysql_conn.close()
    
    print(f"   📊 Total: {len(equipos)} equipos migrados")
    return mapping_equipos

def migrar_miembros(mapping_ids, mapping_equipos):
    """Migrar miembros de equipos"""
    print("\n📋 Migrando miembros de equipos...")
    
    mysql_conn = get_mysql_connection()
    mysql_cursor = mysql_conn.cursor(dictionary=True)
    mysql_cursor.execute("SELECT * FROM equipo_miembros")
    miembros = mysql_cursor.fetchall()
    
    mongo_db = get_mongo_connection()
    equipos_col = mongo_db["equipos"]
    
    contador = 0
    for miembro in miembros:
        equipo_id = mapping_equipos.get(miembro["equipo_id"])
        usuario_id = mapping_ids.get(miembro["usuario_id"])
        
        if equipo_id and usuario_id:
            equipos_col.update_one(
                {"_id": equipo_id},
                {"$addToSet": {"miembros": usuario_id}}
            )
            contador += 1
    
    print(f"   ✅ {contador} membresías migradas")
    mysql_cursor.close()
    mysql_conn.close()

def migrar_tareas(mapping_ids, mapping_equipos):
    """Migrar tareas"""
    print("\n📋 Migrando tareas...")
    
    mysql_conn = get_mysql_connection()
    mysql_cursor = mysql_conn.cursor(dictionary=True)
    mysql_cursor.execute("SELECT * FROM tareas")
    tareas = mysql_cursor.fetchall()
    
    mongo_db = get_mongo_connection()
    collection = mongo_db["tareas"]
    
    mapping_tareas = {}
    
    for tarea in tareas:
        # Convertir fechas correctamente
        fecha_limite = None
        if tarea["fecha_limite"]:
            if isinstance(tarea["fecha_limite"], datetime.date):
                fecha_limite = datetime.datetime.combine(tarea["fecha_limite"], datetime.datetime.min.time())
            else:
                fecha_limite = tarea["fecha_limite"]
        
        fecha_creacion = tarea["fecha_creacion"]
        if isinstance(fecha_creacion, datetime.date) and not isinstance(fecha_creacion, datetime.datetime):
            fecha_creacion = datetime.datetime.combine(fecha_creacion, datetime.datetime.min.time())
        
        doc = {
            "titulo": tarea["titulo"],
            "descripcion": tarea["descripcion"],
            "equipo_id": mapping_equipos.get(tarea["equipo_id"]),
            "creador_id": mapping_ids.get(tarea["creador_id"]),
            "fecha_limite": fecha_limite,
            "fecha_creacion": fecha_creacion,
            "archivos_adjuntos": []
        }
        
        # Solo insertar si tiene equipo y creador válidos
        if doc["equipo_id"] and doc["creador_id"]:
            result = collection.insert_one(doc)
            mapping_tareas[tarea["id"]] = result.inserted_id
            print(f"   ✅ Tarea: {tarea['titulo']}")
        else:
            print(f"   ⚠️ Tarea omitida: {tarea['titulo']} (faltan referencias)")
    
    mysql_cursor.close()
    mysql_conn.close()
    
    print(f"   📊 Total: {len(mapping_tareas)} tareas migradas")
    return mapping_tareas

def migrar_entregas(mapping_ids, mapping_tareas):
    """Migrar entregas"""
    print("\n📋 Migrando entregas...")
    
    mysql_conn = get_mysql_connection()
    mysql_cursor = mysql_conn.cursor(dictionary=True)
    mysql_cursor.execute("SELECT * FROM entregas")
    entregas = mysql_cursor.fetchall()
    
    mongo_db = get_mongo_connection()
    collection = mongo_db["entregas"]
    
    contador = 0
    for entrega in entregas:
        # Convertir fecha
        fecha_entrega = entrega["fecha_entrega"]
        if isinstance(fecha_entrega, datetime.date) and not isinstance(fecha_entrega, datetime.datetime):
            fecha_entrega = datetime.datetime.combine(fecha_entrega, datetime.datetime.min.time())
        
        doc = {
            "tarea_id": mapping_tareas.get(entrega["tarea_id"]),
            "alumno_id": mapping_ids.get(entrega["alumno_id"]),
            "comentario": entrega["comentario"],
            "archivo": entrega.get("archivo"),
            "nombre_archivo": entrega.get("nombre_archivo"),
            "calificacion": entrega.get("calificacion"),
            "fecha_entrega": fecha_entrega
        }
        # Solo insertar si la tarea y alumno existen
        if doc["tarea_id"] and doc["alumno_id"]:
            collection.insert_one(doc)
            contador += 1
    
    print(f"   ✅ {contador} entregas migradas")
    mysql_cursor.close()
    mysql_conn.close()

def migrar_mensajes(mapping_ids, mapping_equipos):
    """Migrar mensajes del chat"""
    print("\n📋 Migrando mensajes del chat...")
    
    mysql_conn = get_mysql_connection()
    mysql_cursor = mysql_conn.cursor(dictionary=True)
    mysql_cursor.execute("SELECT * FROM mensajes_chat")
    mensajes = mysql_cursor.fetchall()
    
    mongo_db = get_mongo_connection()
    collection = mongo_db["mensajes_chat"]
    
    contador = 0
    for mensaje in mensajes:
        # Convertir fecha
        fecha_envio = mensaje["fecha_envio"]
        if isinstance(fecha_envio, datetime.date) and not isinstance(fecha_envio, datetime.datetime):
            fecha_envio = datetime.datetime.combine(fecha_envio, datetime.datetime.min.time())
        
        doc = {
            "equipo_id": mapping_equipos.get(mensaje["equipo_id"]),
            "usuario_id": mapping_ids.get(mensaje["usuario_id"]),
            "mensaje": mensaje["mensaje"],
            "fecha_envio": fecha_envio
        }
        if doc["equipo_id"] and doc["usuario_id"]:
            collection.insert_one(doc)
            contador += 1
    
    print(f"   ✅ {contador} mensajes migrados")
    mysql_cursor.close()
    mysql_conn.close()

def verificar_migracion():
    """Verificar que los datos se migraron correctamente"""
    print("\n" + "=" * 50)
    print("📊 VERIFICANDO MIGRACIÓN")
    print("=" * 50)
    
    mongo_db = get_mongo_connection()
    
    colecciones = ["usuarios", "equipos", "tareas", "entregas", "mensajes_chat"]
    
    for col_name in colecciones:
        count = mongo_db[col_name].count_documents({})
        print(f"   📁 {col_name}: {count} documentos")

if __name__ == "__main__":
    print("=" * 50)
    print("🔄 MIGRANDO DATOS DE MYSQL A MONGODB")
    print("=" * 50)
    
    # Diccionarios para mapear IDs de MySQL a ObjectId de MongoDB
    mapping_ids = {}      # usuarios
    mapping_equipos = {}  # equipos
    mapping_tareas = {}   # tareas
    
    # Ejecutar migración en orden (por las dependencias)
    migrar_usuarios(mapping_ids)
    mapping_equipos = migrar_equipos(mapping_ids)
    migrar_miembros(mapping_ids, mapping_equipos)
    mapping_tareas = migrar_tareas(mapping_ids, mapping_equipos)
    migrar_entregas(mapping_ids, mapping_tareas)
    migrar_mensajes(mapping_ids, mapping_equipos)
    
    # Verificar resultados
    verificar_migracion()
    
    print("\n" + "=" * 50)
    print("🎉 MIGRACIÓN COMPLETADA")
    print("=" * 50)