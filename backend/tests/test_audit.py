from app.main import describe_audit


def test_creacion_de_orden():
    assert describe_audit("POST", "/api/ordenes") == ("CREAR", "orden", None, "Creó una orden")


def test_envio_a_cocina_es_edicion_de_orden():
    assert describe_audit("POST", "/api/ordenes/7/enviar-cocina") == ("EDITAR", "orden", 7, "Envió la orden #7 a cocina")


def test_pago_es_creacion():
    assert describe_audit("POST", "/api/ordenes/7/pagos") == ("CREAR", "pago", 7, "Registró un pago de la orden #7")


def test_cancelar_platillo_es_eliminacion():
    assert describe_audit("DELETE", "/api/ordenes/7/detalles/3") == ("ELIMINAR", "platillo", 3, "Canceló el platillo #3 de la orden #7")


def test_estado_de_platillo_en_cocina():
    assert describe_audit("PATCH", "/api/cocina/detalles/2/estado")[:3] == ("EDITAR", "platillo", 2)


def test_ruta_generica():
    assert describe_audit("DELETE", "/api/admin/usuarios/4") == ("ELIMINAR", "usuario", 4, "Eliminó usuario #4")
    assert describe_audit("POST", "/api/productos") == ("CREAR", "producto", None, "Creó producto")


def test_acceso():
    assert describe_audit("POST", "/api/auth/login")[0] == "ACCESO"
