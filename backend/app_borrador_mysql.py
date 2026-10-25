# ============================================
# ARCHIVO 4/10: SERVIDOR PRINCIPAL (PARTE 1)
# ============================================
# Este archivo es el corazón del backend
# Por ahora solo configuraremos el servidor y rutas básicas
# ============================================

# ============================================
# IMPORTAR LIBRERÍAS NECESARIAS
# ============================================
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import hashlib  # Para encriptar contraseñas
from config import obtener_conexion  # Nuestro archivo de conexión
import os
from werkzeug.utils import secure_filename

# ============================================
# CONFIGURACIÓN DEL SERVIDOR
# ============================================
app = Flask(__name__, 
            static_folder='../frontend',  # Carpeta con nuestros HTML
            static_url_path='')            # Sirve archivos desde la raíz

# Permitir conexiones desde el frontend (importante para fetch)
CORS(app)

# ============================================
# RUTA DE PRUEBA (para verificar que el servidor funciona)
# ============================================
@app.route('/api/test', methods=['GET'])
def test():
    """
    Ruta simple para probar que el servidor responde
    """
    return jsonify({
        "mensaje": "Servidor funcionando correctamente",
        "estado": "ok"
    })


# ============================================
# ARCHIVO 5/10: SERVIDOR PRINCIPAL (PARTE 2)
# ============================================
# AGREGAR ESTE CÓDIGO DESPUÉS DE LA RUTA DE PRUEBA (/api/test)
# ============================================

# ============================================
# API: REGISTRO DE USUARIOS
# ============================================
@app.route('/api/registro', methods=['POST'])
def registrar_usuario():
    """
    Recibe datos del formulario de registro y guarda en BD
    """
    try:
        # 1. Obtener datos que envía el frontend (en formato JSON)
        datos = request.json
        nombre = datos['nombre']
        email = datos['email']
        password = datos['password']
        rol = datos['rol']
        
        # 2. Encriptar la contraseña (SHA256)
        #    Nunca guardamos contraseñas en texto plano
        password_encriptada = password
        
        # 3. Conectar a la base de datos
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        
        # 4. Insertar el nuevo usuario
        sql = "INSERT INTO usuarios (nombre, email, password, rol) VALUES (%s, %s, %s, %s)"
        valores = (nombre, email, password_encriptada, rol)
        
        cursor.execute(sql, valores)
        conexion.commit()
        
        # 5. Respuesta exitosa (el frontend recibirá esto)
        return jsonify({
            "exito": True,
            "mensaje": "Usuario registrado correctamente"
        })
        
    except Exception as error:
        # 6. Si hay error, lo devolvemos al frontend
        return jsonify({
            "exito": False,
            "mensaje": f"Error: {str(error)}"
        }), 400
        
    finally:
        # 7. Siempre cerrar la conexión (aunque haya error)
        if 'cursor' in locals():
            cursor.close()
        if 'conexion' in locals():
            conexion.close()

# ============================================
# API: INICIAR SESIÓN
# ============================================
@app.route('/api/iniciar-sesion', methods=['POST'])
def iniciar_sesion():
    try:
        datos = request.json
        email = datos['email']
        password = datos['password']

        # Encriptar la contraseña para comparar
        password_encriptada = password

        # Buscar usuario en BD
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)

        sql = "SELECT * FROM usuarios WHERE email = %s"
        cursor.execute(sql, (email,))
        usuario = cursor.fetchone()

        if usuario and usuario['password'] == password_encriptada:
            # No enviar la contraseña al frontend
            del usuario['password']

            return jsonify({
                "exito": True,
                "mensaje": "Login exitoso",
                "usuario": usuario
            })
        else:
            return jsonify({
                "exito": False,
                "mensaje": "Email o contraseña incorrectos"
            }), 401

    except Exception as error:
        return jsonify({
            "exito": False,
            "mensaje": str(error)
        }), 400
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conexion' in locals():
            conexion.close()

# ============================================
# ARCHIVO 12/20: API DE EQUIPOS
# ============================================

# ============================================
# API: CREAR EQUIPO (solo maestros)
# ============================================
@app.route('/api/equipos/crear', methods=['POST'])
def crear_equipo():
    """
    Crea un nuevo equipo
    Solo maestros pueden crear equipos
    Recibe: nombre, descripcion, lider_id (el maestro que lo crea)
    """
    try:
        datos = request.json
        nombre = datos.get('nombre')
        descripcion = datos.get('descripcion', '')
        lider_id = datos.get('lider_id')
        
        # Validar campos obligatorios
        if not nombre or not lider_id:
            return jsonify({
                "exito": False,
                "mensaje": "Nombre y líder son obligatorios"
            }), 400
        
        # Conectar a BD
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        
        # Insertar el equipo
        sql = "INSERT INTO equipos (nombre, descripcion, lider_id) VALUES (%s, %s, %s)"
        valores = (nombre, descripcion, lider_id)
        
        cursor.execute(sql, valores)
        conexion.commit()
        
        equipo_id = cursor.lastrowid  # Obtener el ID del equipo creado
        
        return jsonify({
            "exito": True,
            "mensaje": "Equipo creado correctamente",
            "equipo_id": equipo_id
        })
        
    except Exception as error:
        return jsonify({
            "exito": False,
            "mensaje": f"Error: {str(error)}"
        }), 400
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conexion' in locals():
            conexion.close()


# ============================================
# API: LISTAR EQUIPOS (según rol del usuario)
# ============================================
@app.route('/api/equipos/<int:usuario_id>', methods=['GET'])
def listar_equipos(usuario_id):
    """
    Devuelve los equipos según el rol:
    - Si es maestro: sus equipos creados
    - Si es alumno: los equipos donde es miembro O líder
    """
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        
        # Primero verificar el rol del usuario
        cursor.execute("SELECT rol FROM usuarios WHERE id = %s", (usuario_id,))
        usuario = cursor.fetchone()
        
        if not usuario:
            return jsonify({"exito": False, "mensaje": "Usuario no encontrado"}), 404
        
        equipos = []
        
        if usuario['rol'] == 'maestro':
            # Maestro: ver equipos que ha creado
            sql = """
                SELECT e.*, 
                       (SELECT COUNT(*) FROM equipo_miembros WHERE equipo_id = e.id) as total_miembros,
                       u.nombre as lider_nombre
                FROM equipos e
                JOIN usuarios u ON e.lider_id = u.id
                WHERE e.lider_id = %s 
                ORDER BY e.fecha_creacion DESC
            """
            cursor.execute(sql, (usuario_id,))
            equipos = cursor.fetchall()
            
        else:  # Alumno
            # Alumno: ver equipos donde es miembro O donde es líder (él lo creó)
            sql = """
                SELECT e.*, 
                       (SELECT COUNT(*) FROM equipo_miembros WHERE equipo_id = e.id) as total_miembros,
                       (SELECT nombre FROM usuarios WHERE id = e.lider_id) as lider_nombre
                FROM equipos e 
                WHERE e.id IN (
                    SELECT equipo_id FROM equipo_miembros WHERE usuario_id = %s
                    UNION
                    SELECT id FROM equipos WHERE lider_id = %s
                )
                ORDER BY e.fecha_creacion DESC
            """
            cursor.execute(sql, (usuario_id, usuario_id))
            equipos = cursor.fetchall()
        
        # Asegurar que total_miembros sea un número
        for equipo in equipos:
            if equipo.get('total_miembros') is None:
                equipo['total_miembros'] = 0
        
        return jsonify({
            "exito": True,
            "equipos": equipos
        })
        
    except Exception as error:
        print(f"Error en listar_equipos: {error}")
        return jsonify({
            "exito": False,
            "mensaje": str(error)
        }), 400
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conexion' in locals():
            conexion.close()

# ============================================
# API: UNIRSE A EQUIPO (solo alumnos)
# ============================================
@app.route('/api/equipos/unirse', methods=['POST'])
def unirse_equipo():
    """
    Un alumno se une a un equipo
    Recibe: equipo_id, usuario_id
    """
    try:
        datos = request.json
        equipo_id = datos.get('equipo_id')
        usuario_id = datos.get('usuario_id')
        
        if not equipo_id or not usuario_id:
            return jsonify({
                "exito": False,
                "mensaje": "Equipo y usuario son obligatorios"
            }), 400
        
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        
        # Verificar si ya es miembro
        cursor.execute(
            "SELECT * FROM equipo_miembros WHERE equipo_id = %s AND usuario_id = %s",
            (equipo_id, usuario_id)
        )
        if cursor.fetchone():
            return jsonify({
                "exito": False,
                "mensaje": "Ya eres miembro de este equipo"
            }), 400
        
        # Unirse al equipo
        sql = "INSERT INTO equipo_miembros (equipo_id, usuario_id) VALUES (%s, %s)"
        cursor.execute(sql, (equipo_id, usuario_id))
        conexion.commit()
        
        return jsonify({
            "exito": True,
            "mensaje": "Te has unido al equipo correctamente"
        })
        
    except Exception as error:
        return jsonify({
            "exito": False,
            "mensaje": f"Error: {str(error)}"
        }), 400
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conexion' in locals():
            conexion.close()


# ============================================
# API: VER DETALLE DE UN EQUIPO
# ============================================
@app.route('/api/equipos/detalle/<int:equipo_id>', methods=['GET'])
def detalle_equipo(equipo_id):
    """
    Devuelve la información completa de un equipo:
    - Datos del equipo
    - Lista de miembros
    - Información del líder
    """
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        
        # Obtener datos del equipo
        cursor.execute("""
            SELECT e.*, u.nombre as lider_nombre, u.email as lider_email
            FROM equipos e
            JOIN usuarios u ON e.lider_id = u.id
            WHERE e.id = %s
        """, (equipo_id,))
        equipo = cursor.fetchone()
        
        if not equipo:
            return jsonify({"exito": False, "mensaje": "Equipo no encontrado"}), 404
        
        # Obtener miembros del equipo
        cursor.execute("""
            SELECT u.id, u.nombre, u.email, em.fecha_union
            FROM equipo_miembros em
            JOIN usuarios u ON em.usuario_id = u.id
            WHERE em.equipo_id = %s
            ORDER BY em.fecha_union ASC
        """, (equipo_id,))
        miembros = cursor.fetchall()
        
        equipo['miembros'] = miembros
        equipo['total_miembros'] = len(miembros)
        
        return jsonify({
            "exito": True,
            "equipo": equipo
        })
        
    except Exception as error:
        return jsonify({
            "exito": False,
            "mensaje": str(error)
        }), 400
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conexion' in locals():
            conexion.close()


# ============================================
# API: ELIMINAR EQUIPO
# Solo el líder del equipo puede eliminarlo
# ============================================
@app.route('/api/equipos/eliminar/<int:equipo_id>', methods=['DELETE'])
def eliminar_equipo(equipo_id):
    """
    Elimina un equipo y todos sus miembros
    Solo el líder del equipo puede hacerlo
    """
    try:
        # Obtener el ID del usuario desde la petición (lo enviamos en el body)
        datos = request.json
        usuario_id = datos.get('usuario_id')
        
        if not usuario_id:
            return jsonify({
                "exito": False,
                "mensaje": "Usuario no identificado"
            }), 400
        
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        
        # Verificar que el usuario es el líder del equipo
        cursor.execute(
            "SELECT lider_id FROM equipos WHERE id = %s",
            (equipo_id,)
        )
        equipo = cursor.fetchone()
        
        if not equipo:
            return jsonify({
                "exito": False,
                "mensaje": "El equipo no existe"
            }), 404
        
        if equipo['lider_id'] != usuario_id:
            return jsonify({
                "exito": False,
                "mensaje": "No tienes permiso para eliminar este equipo"
            }), 403
        
        # Eliminar el equipo (los miembros se eliminan automáticamente por ON DELETE CASCADE)
        cursor.execute("DELETE FROM equipos WHERE id = %s", (equipo_id,))
        conexion.commit()
        
        return jsonify({
            "exito": True,
            "mensaje": "Equipo eliminado correctamente"
        })
        
    except Exception as error:
        return jsonify({
            "exito": False,
            "mensaje": f"Error: {str(error)}"
        }), 400
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conexion' in locals():
            conexion.close()


# ============================================
# API: SALIR DEL EQUIPO (solo para alumnos no líderes)
# ============================================
@app.route('/api/equipos/salir/<int:equipo_id>', methods=['DELETE'])
def salir_del_equipo(equipo_id):
    """
    Permite a un alumno salir de un equipo
    No puede salir si es el líder
    """
    try:
        datos = request.json
        usuario_id = datos.get('usuario_id')
        
        if not usuario_id:
            return jsonify({
                "exito": False,
                "mensaje": "Usuario no identificado"
            }), 400
        
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        
        # Verificar que el usuario es miembro del equipo
        cursor.execute(
            "SELECT * FROM equipo_miembros WHERE equipo_id = %s AND usuario_id = %s",
            (equipo_id, usuario_id)
        )
        membresia = cursor.fetchone()
        
        if not membresia:
            return jsonify({
                "exito": False,
                "mensaje": "No eres miembro de este equipo"
            }), 404
        
        # Verificar que no es el líder
        cursor.execute(
            "SELECT lider_id FROM equipos WHERE id = %s",
            (equipo_id,)
        )
        equipo = cursor.fetchone()
        
        if equipo and equipo['lider_id'] == usuario_id:
            return jsonify({
                "exito": False,
                "mensaje": "Eres el líder del equipo. No puedes salir, solo eliminarlo."
            }), 403
        
        # Eliminar al usuario de la tabla de miembros
        cursor.execute(
            "DELETE FROM equipo_miembros WHERE equipo_id = %s AND usuario_id = %s",
            (equipo_id, usuario_id)
        )
        conexion.commit()
        
        return jsonify({
            "exito": True,
            "mensaje": "Has salido del equipo correctamente"
        })
        
    except Exception as error:
        return jsonify({
            "exito": False,
            "mensaje": f"Error: {str(error)}"
        }), 400
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conexion' in locals():
            conexion.close()


# ============================================
# ARCHIVO 19/30: API DE TAREAS
# ============================================

# ============================================
# API: CREAR TAREA
# ============================================
@app.route('/api/tareas/crear', methods=['POST'])
def crear_tarea():
    """
    Crea una nueva tarea en un equipo
    Solo el líder del equipo puede crear tareas
    """
    try:
        datos = request.json
        titulo = datos.get('titulo')
        descripcion = datos.get('descripcion', '')
        equipo_id = datos.get('equipo_id')
        creador_id = datos.get('creador_id')
        fecha_limite = datos.get('fecha_limite')
        
        if not titulo or not equipo_id or not creador_id:
            return jsonify({
                "exito": False,
                "mensaje": "Título, equipo y creador son obligatorios"
            }), 400
        
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        
        # Verificar que el creador es el líder del equipo
        cursor.execute(
            "SELECT lider_id FROM equipos WHERE id = %s",
            (equipo_id,)
        )
        equipo = cursor.fetchone()
        
        if not equipo:
            return jsonify({
                "exito": False,
                "mensaje": "El equipo no existe"
            }), 404
        
        if equipo[0] != creador_id:
            return jsonify({
                "exito": False,
                "mensaje": "Solo el líder del equipo puede crear tareas"
            }), 403
        
        # Insertar tarea
        sql = """
            INSERT INTO tareas (titulo, descripcion, equipo_id, creador_id, fecha_limite)
            VALUES (%s, %s, %s, %s, %s)
        """
        valores = (titulo, descripcion, equipo_id, creador_id, fecha_limite)
        
        cursor.execute(sql, valores)
        conexion.commit()
        
        tarea_id = cursor.lastrowid
        
        return jsonify({
            "exito": True,
            "mensaje": "Tarea creada correctamente",
            "tarea_id": tarea_id
        })
        
    except Exception as error:
        return jsonify({
            "exito": False,
            "mensaje": f"Error: {str(error)}"
        }), 400
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conexion' in locals():
            conexion.close()


# ============================================
# API: LISTAR TAREAS DE UN EQUIPO
# ============================================
@app.route('/api/tareas/equipo/<int:equipo_id>', methods=['GET'])
def listar_tareas_equipo(equipo_id):
    """
    Devuelve todas las tareas de un equipo
    """
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        
        sql = """
            SELECT t.*, u.nombre as creador_nombre,
                   (SELECT COUNT(*) FROM entregas WHERE tarea_id = t.id) as total_entregas
            FROM tareas t
            JOIN usuarios u ON t.creador_id = u.id
            WHERE t.equipo_id = %s
            ORDER BY t.fecha_limite ASC, t.fecha_creacion DESC
        """
        cursor.execute(sql, (equipo_id,))
        tareas = cursor.fetchall()
        
        return jsonify({
            "exito": True,
            "tareas": tareas
        })
        
    except Exception as error:
        return jsonify({
            "exito": False,
            "mensaje": str(error)
        }), 400
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conexion' in locals():
            conexion.close()


# ============================================
# API: DETALLE DE UNA TAREA
# ============================================
@app.route('/api/tareas/detalle/<int:tarea_id>', methods=['GET'])
def detalle_tarea(tarea_id):
    """
    Devuelve información completa de una tarea y sus entregas
    """
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        
        # Obtener datos de la tarea
        sql = """
            SELECT t.*, u.nombre as creador_nombre, e.nombre as equipo_nombre
            FROM tareas t
            JOIN usuarios u ON t.creador_id = u.id
            JOIN equipos e ON t.equipo_id = e.id
            WHERE t.id = %s
        """
        cursor.execute(sql, (tarea_id,))
        tarea = cursor.fetchone()
        
        if not tarea:
            return jsonify({
                "exito": False,
                "mensaje": "Tarea no encontrada"
            }), 404
        
        # Obtener entregas de la tarea
        cursor.execute("""
            SELECT e.*, u.nombre as alumno_nombre
            FROM entregas e
            JOIN usuarios u ON e.alumno_id = u.id
            WHERE e.tarea_id = %s
            ORDER BY e.fecha_entrega DESC
        """, (tarea_id,))
        entregas = cursor.fetchall()
        
        tarea['entregas'] = entregas
        
        return jsonify({
            "exito": True,
            "tarea": tarea
        })
        
    except Exception as error:
        return jsonify({
            "exito": False,
            "mensaje": str(error)
        }), 400
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conexion' in locals():
            conexion.close()


# ============================================
# API: CREAR ENTREGA (alumno)
# ============================================
@app.route('/api/entregas/crear', methods=['POST'])
def crear_entrega():
    """
    Permite a un alumno entregar una tarea
    """
    try:
        datos = request.json
        tarea_id = datos.get('tarea_id')
        alumno_id = datos.get('alumno_id')
        comentario = datos.get('comentario', '')
        
        if not tarea_id or not alumno_id:
            return jsonify({
                "exito": False,
                "mensaje": "Tarea y alumno son obligatorios"
            }), 400
        
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        
        # Verificar si ya entregó
        cursor.execute(
            "SELECT * FROM entregas WHERE tarea_id = %s AND alumno_id = %s",
            (tarea_id, alumno_id)
        )
        if cursor.fetchone():
            return jsonify({
                "exito": False,
                "mensaje": "Ya has entregado esta tarea"
            }), 400
        
        # Insertar entrega
        sql = """
            INSERT INTO entregas (tarea_id, alumno_id, comentario)
            VALUES (%s, %s, %s)
        """
        cursor.execute(sql, (tarea_id, alumno_id, comentario))
        conexion.commit()
        
        return jsonify({
            "exito": True,
            "mensaje": "Tarea entregada correctamente"
        })
        
    except Exception as error:
        return jsonify({
            "exito": False,
            "mensaje": f"Error: {str(error)}"
        }), 400
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conexion' in locals():
            conexion.close()


# ============================================
# API: CALIFICAR ENTREGA
# ============================================
@app.route('/api/entregas/calificar', methods=['PUT'])
def calificar_entrega():
    """
    Permite al líder del equipo calificar una entrega
    """
    try:
        datos = request.json
        entrega_id = datos.get('entrega_id')
        calificacion = datos.get('calificacion')
        
        if not entrega_id or calificacion is None:
            return jsonify({
                "exito": False,
                "mensaje": "ID de entrega y calificación son obligatorios"
            }), 400
        
        if calificacion < 0 or calificacion > 100:
            return jsonify({
                "exito": False,
                "mensaje": "La calificación debe estar entre 0 y 100"
            }), 400
        
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        
        # Actualizar calificación
        sql = "UPDATE entregas SET calificacion = %s WHERE id = %s"
        cursor.execute(sql, (calificacion, entrega_id))
        conexion.commit()
        
        return jsonify({
            "exito": True,
            "mensaje": "Calificación guardada"
        })
        
    except Exception as error:
        return jsonify({
            "exito": False,
            "mensaje": f"Error: {str(error)}"
        }), 400
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conexion' in locals():
            conexion.close()


# ============================================
# API: TAREAS PENDIENTES DEL ALUMNO (para dashboard)
# ============================================
@app.route('/api/tareas/alumno/<int:alumno_id>', methods=['GET'])
def tareas_alumno(alumno_id):
    """
    Devuelve las tareas pendientes de un alumno
    (tareas de equipos donde es miembro y que no ha entregado)
    """
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        
        # Primero, obtener los equipos donde el alumno es miembro
        cursor.execute("""
            SELECT equipo_id FROM equipo_miembros WHERE usuario_id = %s
            UNION
            SELECT id FROM equipos WHERE lider_id = %s
        """, (alumno_id, alumno_id))
        equipos = cursor.fetchall()
        
        if not equipos:
            return jsonify({
                "exito": True,
                "tareas": []
            })
        
        # Crear lista de IDs de equipos
        equipos_ids = [str(e['equipo_id']) for e in equipos]
        equipos_str = ','.join(equipos_ids)
        
        # Obtener tareas de esos equipos que el alumno no ha entregado
        sql = f"""
            SELECT t.*, e.nombre as equipo_nombre,
                   CASE 
                       WHEN t.fecha_limite < CURDATE() THEN 'vencida'
                       ELSE 'pendiente'
                   END as estado_tarea
            FROM tareas t
            JOIN equipos e ON t.equipo_id = e.id
            WHERE t.equipo_id IN ({equipos_str})
            AND t.id NOT IN (
                SELECT tarea_id FROM entregas WHERE alumno_id = %s
            )
            ORDER BY t.fecha_limite ASC, t.fecha_creacion DESC
        """
        cursor.execute(sql, (alumno_id,))
        tareas = cursor.fetchall()
        
        return jsonify({
            "exito": True,
            "tareas": tareas
        })
        
    except Exception as error:
        print(f"Error en tareas_alumno: {error}")
        return jsonify({
            "exito": False,
            "mensaje": str(error)
        }), 400
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conexion' in locals():
            conexion.close()
            

# ============================================
# API: TAREAS RECIENTES DEL EQUIPO (para líder en dashboard)
# ============================================
@app.route('/api/tareas/lider/<int:lider_id>', methods=['GET'])
def tareas_lider(lider_id):
    """
    Devuelve las tareas de los equipos que lidera un usuario
    """
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        
        sql = """
            SELECT t.*, e.nombre as equipo_nombre,
                   (SELECT COUNT(*) FROM entregas WHERE tarea_id = t.id) as total_entregas
            FROM tareas t
            JOIN equipos e ON t.equipo_id = e.id
            WHERE e.lider_id = %s
            ORDER BY t.fecha_creacion DESC
            LIMIT 10
        """
        cursor.execute(sql, (lider_id,))
        tareas = cursor.fetchall()
        
        return jsonify({
            "exito": True,
            "tareas": tareas
        })
        
    except Exception as error:
        print(f"Error en tareas_lider: {error}")
        return jsonify({
            "exito": False,
            "mensaje": str(error)
        }), 400
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conexion' in locals():
            conexion.close()


# ============================================
# API: CHAT DEL EQUIPO
# ============================================

# Obtener mensajes de un equipo
@app.route('/api/chat/<int:equipo_id>', methods=['GET'])
def obtener_mensajes(equipo_id):
    """Devuelve todos los mensajes de un equipo"""
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        
        sql = """
            SELECT m.*, u.nombre as usuario_nombre, u.rol
            FROM mensajes_chat m
            JOIN usuarios u ON m.usuario_id = u.id
            WHERE m.equipo_id = %s
            ORDER BY m.fecha_envio ASC
            LIMIT 100
        """
        cursor.execute(sql, (equipo_id,))
        mensajes = cursor.fetchall()
        
        return jsonify({
            "exito": True,
            "mensajes": mensajes
        })
        
    except Exception as error:
        return jsonify({"exito": False, "mensaje": str(error)}), 400
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conexion' in locals(): conexion.close()


# Enviar mensaje a un equipo
@app.route('/api/chat/enviar', methods=['POST'])
def enviar_mensaje():
    """Guarda un mensaje en el chat del equipo"""
    try:
        datos = request.json
        equipo_id = datos.get('equipo_id')
        usuario_id = datos.get('usuario_id')
        mensaje = datos.get('mensaje', '').strip()
        
        if not mensaje:
            return jsonify({"exito": False, "mensaje": "El mensaje no puede estar vacío"}), 400
        
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        
        sql = "INSERT INTO mensajes_chat (equipo_id, usuario_id, mensaje) VALUES (%s, %s, %s)"
        cursor.execute(sql, (equipo_id, usuario_id, mensaje))
        conexion.commit()
        
        return jsonify({
            "exito": True,
            "mensaje": "Mensaje enviado"
        })
        
    except Exception as error:
        return jsonify({"exito": False, "mensaje": str(error)}), 400
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conexion' in locals(): conexion.close()


# ============================================
# API: SUBIR ARCHIVO (entrega de tarea)
# ============================================
import os
from werkzeug.utils import secure_filename

# Configurar carpeta de uploads
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx', 'txt'}

# Crear carpeta si no existe
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/entregas/subir', methods=['POST'])
def subir_archivo_entrega():
    """Sube un archivo para una entrega"""
    try:
        tarea_id = request.form.get('tarea_id')
        alumno_id = request.form.get('alumno_id')
        comentario = request.form.get('comentario', '')
        
        if not tarea_id or not alumno_id:
            return jsonify({"exito": False, "mensaje": "Faltan datos"}), 400
        
        # Procesar archivo
        archivo = request.files.get('archivo')
        nombre_archivo = None
        ruta_archivo = None
        
        if archivo and allowed_file(archivo.filename):
            nombre_archivo = secure_filename(archivo.filename)
            # Renombrar para evitar duplicados
            import time
            nombre_unico = f"{int(time.time())}_{nombre_archivo}"
            ruta_archivo = os.path.join(UPLOAD_FOLDER, nombre_unico)
            archivo.save(ruta_archivo)
        
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        
        # Verificar si ya entregó
        cursor.execute(
            "SELECT id FROM entregas WHERE tarea_id = %s AND alumno_id = %s",
            (tarea_id, alumno_id)
        )
        if cursor.fetchone():
            return jsonify({"exito": False, "mensaje": "Ya entregaste esta tarea"}), 400
        
        # Insertar entrega con archivo
        sql = """
            INSERT INTO entregas (tarea_id, alumno_id, comentario, archivo, nombre_archivo)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (tarea_id, alumno_id, comentario, ruta_archivo, nombre_archivo))
        conexion.commit()
        
        return jsonify({
            "exito": True,
            "mensaje": "Tarea entregada con éxito"
        })
        
    except Exception as error:
        return jsonify({"exito": False, "mensaje": str(error)}), 400
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conexion' in locals(): conexion.close()


# ============================================
# RUTA PARA SERVIR ARCHIVOS SUBIDOS
# ============================================
@app.route('/uploads/<path:nombre_archivo>')
def servir_archivo(nombre_archivo):
    """Sirve archivos subidos por los alumnos"""
    return send_from_directory('uploads', nombre_archivo)


# ============================================
# NOTA: El servidor se reinicia automáticamente
# cuando guardas el archivo (por el debug=True)
# ============================================

# ============================================
# INICIAR SERVIDOR (solo cuando ejecutamos este archivo)
# ============================================
if __name__ == '__main__':
    print("\n" + "="*50)
    print("SERVIDOR INICIADO")
    print("="*50)
    print("Rutas disponibles:")
    print("   • http://localhost:5000/api/test  (para probar)")
    print("\n Presiona CTRL+C para detener el servidor")
    print("="*50 + "\n")
    
    app.run(debug=True, port=5000)