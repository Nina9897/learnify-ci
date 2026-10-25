"""Pruebas UNITARIAS NUEVAS (no necesitan MongoDB).

Cubren funciones de app.py que antes no tenían pruebas:
  - bloqueo de login por intentos fallidos (seguridad)
  - convertir_objectid (utilidad para serializar documentos de MongoDB)
  - casos adicionales de calcular_estado_dual
"""
import os
import sys
from datetime import datetime, timedelta

import pytest
from bson import ObjectId

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import app as app_module  # noqa: E402
from app import (  # noqa: E402
    calcular_estado_dual,
    cargar_intentos,
    convertir_objectid,
    guardar_intentos,
    obtener_info_intentos,
    registrar_intento_fallido,
    reiniciar_intentos,
    verificar_bloqueo,
)

CLIENTE = "192.168.0.10"


@pytest.fixture(autouse=True)
def archivo_intentos_temporal(tmp_path, monkeypatch):
    """Cada prueba usa su propio archivo para no tocar intentos_fallidos.json real."""
    monkeypatch.setattr(app_module, "ARCHIVO_INTENTOS", str(tmp_path / "intentos.json"))


# ---------- Bloqueo por intentos fallidos ----------

def test_cliente_nuevo_no_esta_bloqueado():
    bloqueado, minutos, segundos = verificar_bloqueo(CLIENTE)
    assert bloqueado is False
    assert (minutos, segundos) == (0, 0)


def test_dos_intentos_fallidos_no_bloquean():
    registrar_intento_fallido(CLIENTE)
    resultado = registrar_intento_fallido(CLIENTE)
    assert resultado["bloqueado"] is False
    assert resultado["intentos"] == 2
    assert verificar_bloqueo(CLIENTE)[0] is False


def test_tres_intentos_fallidos_bloquean_al_cliente():
    registrar_intento_fallido(CLIENTE)
    registrar_intento_fallido(CLIENTE)
    resultado = registrar_intento_fallido(CLIENTE)
    assert resultado["bloqueado"] is True
    assert resultado["intentos"] == 3
    bloqueado, _minutos, segundos = verificar_bloqueo(CLIENTE)
    assert bloqueado is True
    assert 1 <= segundos <= 300  # el bloqueo dura como máximo 5 minutos


def test_reiniciar_intentos_borra_el_contador():
    registrar_intento_fallido(CLIENTE)
    reiniciar_intentos(CLIENTE)
    assert obtener_info_intentos(CLIENTE)["intentos"] == 0
    assert CLIENTE not in cargar_intentos()


def test_bloqueo_vencido_ya_no_bloquea():
    ayer = (datetime.now() - timedelta(days=1)).isoformat()
    guardar_intentos({CLIENTE: {"intentos": 3, "bloqueo_hasta": ayer}})
    assert verificar_bloqueo(CLIENTE)[0] is False
    assert obtener_info_intentos(CLIENTE)["bloqueado"] is False


def test_info_de_cliente_desconocido_es_vacia():
    assert obtener_info_intentos("10.0.0.99") == {
        "intentos": 0, "bloqueado": False, "segundos_restantes": 0,
    }


def test_archivo_de_intentos_corrupto_se_trata_como_vacio():
    with open(app_module.ARCHIVO_INTENTOS, "w", encoding="utf-8") as f:
        f.write("esto no es json")
    assert cargar_intentos() == {}


def test_los_clientes_se_bloquean_de_forma_independiente():
    for _ in range(3):
        registrar_intento_fallido(CLIENTE)
    assert verificar_bloqueo(CLIENTE)[0] is True
    assert verificar_bloqueo("192.168.0.11")[0] is False


# ---------- convertir_objectid ----------

def test_convertir_objectid_cambia_ids_a_texto():
    oid = ObjectId()
    resultado = convertir_objectid({"_id": oid, "nombre": "Equipo"})
    assert resultado == {"_id": str(oid), "nombre": "Equipo"}


def test_convertir_objectid_funciona_en_diccionarios_anidados():
    oid = ObjectId()
    resultado = convertir_objectid({"equipo": {"lider_id": oid}})
    assert resultado["equipo"]["lider_id"] == str(oid)


def test_convertir_objectid_acepta_listas_y_none():
    oid = ObjectId()
    assert convertir_objectid(None) is None
    assert convertir_objectid([{"_id": oid}]) == [{"_id": str(oid)}]


# ---------- calcular_estado_dual (casos nuevos) ----------

def test_dual_vencido_es_inactivo_aunque_falten_firmas():
    dual = {
        "asignaciones": [{"materia": "Redes", "firmado": False}],
        "fecha_fin": datetime.now() - timedelta(days=1),
    }
    assert calcular_estado_dual(dual) == "inactivo"


def test_dual_sin_fecha_fin_y_firmado_es_activo():
    dual = {"asignaciones": [{"materia": "Redes", "firmado": True}]}
    assert calcular_estado_dual(dual) == "activo"


def test_asignacion_sin_campo_firmado_cuenta_como_no_firmada():
    dual = {
        "asignaciones": [{"materia": "Redes"}],
        "fecha_fin": datetime.now() + timedelta(days=10),
    }
    assert calcular_estado_dual(dual) == "pendiente"