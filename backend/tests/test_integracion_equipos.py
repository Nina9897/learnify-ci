"""Pruebas de INTEGRACIÓN NUEVAS: validaciones de registro, bloqueo de login
y gestión de equipos (detalle, salir, eliminar, listar)."""
import pytest

ID_INEXISTENTE = "64b7f0f0f0f0f0f0f0f0f0f0"


def registrar(client, nombre="Ana Lopez", email="ana@correo.com", rol="alumno", **extra):
    datos = {"nombre": nombre, "email": email, "password": "123456", "rol": rol, **extra}
    return client.post("/api/registro", json=datos)


def crear_equipo(client, lider_id, nombre="Equipo Alfa"):
    r = client.post("/api/equipos/crear", json={"nombre": nombre, "lider_id": lider_id})
    return r.get_json()["equipo_id"]


# ---------- Validaciones de registro (no necesitan guardar nada) ----------

@pytest.mark.parametrize("campo, valor, texto", [
    ("nombre", "Ana123", "Nombre no válido"),
    ("email", "correo-malo", "Correo no válido"),
    ("password", "123", "al menos 6 caracteres"),
    ("telefono", "12345", "10 dígitos"),
    ("nombre", "", "obligatorios"),
])
def test_registro_rechaza_datos_invalidos(client, campo, valor, texto):
    datos = {"nombre": "Ana Lopez", "email": "ana@correo.com",
             "password": "123456", "rol": "alumno", campo: valor}
    respuesta = client.post("/api/registro", json=datos)
    assert respuesta.status_code == 400
    assert texto in respuesta.get_json()["mensaje"]


# ---------- Registro y login con MongoDB ----------

def test_registro_guarda_el_correo_en_minusculas(client, db):
    registrar(client, email="ANA@Correo.COM")
    assert db.usuarios.find_one({"email": "ana@correo.com"}) is not None


def test_registro_guarda_telefono_valido(client, db):
    registrar(client, telefono="7221234567")
    assert db.usuarios.find_one({"email": "ana@correo.com"})["telefono"] == "7221234567"


def test_tres_logins_fallidos_bloquean_incluso_con_password_correcta(client, db):
    registrar(client)
    mala = {"email": "ana@correo.com", "password": "incorrecta"}

    primera = client.post("/api/iniciar-sesion", json=mala)
    assert primera.status_code == 401
    assert primera.get_json()["intentos_restantes"] == 2

    client.post("/api/iniciar-sesion", json=mala)
    tercera = client.post("/api/iniciar-sesion", json=mala)
    assert tercera.get_json()["bloqueado"] is True

    buena = client.post("/api/iniciar-sesion",
                        json={"email": "ana@correo.com", "password": "123456"})
    assert buena.status_code == 403
    assert buena.get_json()["bloqueado"] is True


# ---------- Equipos ----------

def test_detalle_equipo_muestra_lider_y_miembros(client, db):
    lider_id = registrar(client, nombre="Maria Torres", email="m@correo.com",
                         rol="maestro").get_json()["usuario_id"]
    alumno_id = registrar(client, nombre="Pedro Ruiz",
                          email="p@correo.com").get_json()["usuario_id"]
    equipo_id = crear_equipo(client, lider_id)
    client.post("/api/equipos/unirse", json={"equipo_id": equipo_id, "usuario_id": alumno_id})

    equipo = client.get(f"/api/equipos/detalle/{equipo_id}").get_json()["equipo"]
    assert equipo["lider_nombre"] == "Maria Torres"
    assert equipo["total_miembros"] == 1
    assert equipo["miembros"][0]["email"] == "p@correo.com"


def test_detalle_de_equipo_inexistente_devuelve_404(client, db):
    respuesta = client.get(f"/api/equipos/detalle/{ID_INEXISTENTE}")
    assert respuesta.status_code == 404


def test_listar_equipos_de_usuario_inexistente_devuelve_404(client, db):
    respuesta = client.get(f"/api/equipos/{ID_INEXISTENTE}")
    assert respuesta.status_code == 404


def test_crear_equipo_con_lider_inexistente_devuelve_404(client, db):
    respuesta = client.post("/api/equipos/crear",
                            json={"nombre": "Fantasma", "lider_id": ID_INEXISTENTE})
    assert respuesta.status_code == 404
    assert db.equipos.count_documents({}) == 0


def test_crear_equipo_sin_nombre_devuelve_400(client, db):
    respuesta = client.post("/api/equipos/crear", json={"lider_id": ID_INEXISTENTE})
    assert respuesta.status_code == 400


def test_solo_el_lider_puede_eliminar_el_equipo(client, db):
    lider_id = registrar(client, rol="maestro").get_json()["usuario_id"]
    otro_id = registrar(client, nombre="Luis Perez",
                        email="l@correo.com").get_json()["usuario_id"]
    equipo_id = crear_equipo(client, lider_id)

    rechazada = client.delete(f"/api/equipos/eliminar/{equipo_id}", json={"usuario_id": otro_id})
    assert rechazada.status_code == 403
    assert db.equipos.count_documents({}) == 1

    aceptada = client.delete(f"/api/equipos/eliminar/{equipo_id}", json={"usuario_id": lider_id})
    assert aceptada.status_code == 200
    assert db.equipos.count_documents({}) == 0


def test_el_lider_no_puede_salir_de_su_propio_equipo(client, db):
    lider_id = registrar(client, rol="maestro").get_json()["usuario_id"]
    equipo_id = crear_equipo(client, lider_id)
    respuesta = client.delete(f"/api/equipos/salir/{equipo_id}", json={"usuario_id": lider_id})
    assert respuesta.status_code == 403


def test_un_no_miembro_no_puede_salir_del_equipo(client, db):
    lider_id = registrar(client, rol="maestro").get_json()["usuario_id"]
    ajeno_id = registrar(client, nombre="Luis Perez",
                         email="l@correo.com").get_json()["usuario_id"]
    equipo_id = crear_equipo(client, lider_id)
    respuesta = client.delete(f"/api/equipos/salir/{equipo_id}", json={"usuario_id": ajeno_id})
    assert respuesta.status_code == 404