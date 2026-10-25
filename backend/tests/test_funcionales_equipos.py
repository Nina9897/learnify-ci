"""Pruebas FUNCIONALES NUEVAS: flujos completos de un usuario sobre equipos."""


def registrar(client, nombre, email, rol):
    r = client.post("/api/registro", json={"nombre": nombre, "email": email,
                                           "password": "123456", "rol": rol})
    assert r.status_code == 200
    return r.get_json()["usuario_id"]


def test_flujo_alumno_se_une_y_luego_sale_del_equipo(client, db):
    maestro_id = registrar(client, "Maria Torres", "maria@correo.com", "maestro")
    equipo_id = client.post("/api/equipos/crear", json={
        "nombre": "Redes", "lider_id": maestro_id}).get_json()["equipo_id"]
    alumno_id = registrar(client, "Pedro Ruiz", "pedro@correo.com", "alumno")

    # Se une y ve el equipo
    client.post("/api/equipos/unirse", json={"equipo_id": equipo_id, "usuario_id": alumno_id})
    equipos = client.get(f"/api/equipos/{alumno_id}").get_json()["equipos"]
    assert [e["nombre"] for e in equipos] == ["Redes"]

    # Sale y ya no lo ve; el maestro lo ve con 0 miembros
    salir = client.delete(f"/api/equipos/salir/{equipo_id}", json={"usuario_id": alumno_id})
    assert salir.status_code == 200
    assert client.get(f"/api/equipos/{alumno_id}").get_json()["equipos"] == []
    del_maestro = client.get(f"/api/equipos/{maestro_id}").get_json()["equipos"]
    assert del_maestro[0]["total_miembros"] == 0


def test_flujo_maestro_elimina_el_equipo_y_desaparece_para_todos(client, db):
    maestro_id = registrar(client, "Maria Torres", "maria@correo.com", "maestro")
    equipo_id = client.post("/api/equipos/crear", json={
        "nombre": "Bases de Datos", "lider_id": maestro_id}).get_json()["equipo_id"]
    alumno_id = registrar(client, "Pedro Ruiz", "pedro@correo.com", "alumno")
    client.post("/api/equipos/unirse", json={"equipo_id": equipo_id, "usuario_id": alumno_id})

    eliminar = client.delete(f"/api/equipos/eliminar/{equipo_id}", json={"usuario_id": maestro_id})
    assert eliminar.status_code == 200

    assert client.get(f"/api/equipos/{maestro_id}").get_json()["equipos"] == []
    assert client.get(f"/api/equipos/{alumno_id}").get_json()["equipos"] == []
    assert client.get(f"/api/equipos/detalle/{equipo_id}").status_code == 404