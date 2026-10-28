from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text,
    UniqueConstraint, Table, JSON, func,
)
from sqlalchemy.orm import DeclarativeBase, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


rol_permiso = Table(
    "rol_permiso", Base.metadata,
    Column("rol_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permiso_id", ForeignKey("permisos.id", ondelete="CASCADE"), primary_key=True),
)

recetas = Table(
    "recetas", Base.metadata,
    Column("producto_id", ForeignKey("productos.id", ondelete="CASCADE"), primary_key=True),
    Column("insumo_id", ForeignKey("insumos.id", ondelete="CASCADE"), primary_key=True),
    Column("cantidad", Numeric(12, 3), nullable=False),
)


class Sucursal(Base):
    __tablename__ = "sucursales"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(120), nullable=False, unique=True)
    direccion = Column(String(240), nullable=False, default="")
    activa = Column(Boolean, nullable=False, default=True)
    usuarios = relationship("Usuario", back_populates="sucursal")


class Rol(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(40), nullable=False, unique=True)
    permisos = relationship("Permiso", secondary=rol_permiso, back_populates="roles")
    usuarios = relationship("Usuario", back_populates="rol")


class Permiso(Base):
    __tablename__ = "permisos"
    id = Column(Integer, primary_key=True)
    clave = Column(String(100), nullable=False, unique=True, index=True)
    descripcion = Column(String(240), nullable=False, default="")
    roles = relationship("Rol", secondary=rol_permiso, back_populates="permisos")


class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(140), nullable=False)
    correo = Column(String(180), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    rol_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    sucursal_id = Column(Integer, ForeignKey("sucursales.id"), nullable=False)
    activo = Column(Boolean, nullable=False, default=True)
    creado_en = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    rol = relationship("Rol", back_populates="usuarios")
    sucursal = relationship("Sucursal", back_populates="usuarios")
    refresh_tokens = relationship("RefreshToken", back_populates="usuario", cascade="all, delete-orphan")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    expira_en = Column(DateTime(timezone=True), nullable=False)
    revocado = Column(Boolean, nullable=False, default=False)
    creado_en = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    reemplaza_a = Column(String(64), nullable=True)
    usuario = relationship("Usuario", back_populates="refresh_tokens")


class Mesa(Base):
    __tablename__ = "mesas"
    __table_args__ = (UniqueConstraint("sucursal_id", "numero", name="uq_mesa_sucursal_numero"),)
    id = Column(Integer, primary_key=True)
    sucursal_id = Column(Integer, ForeignKey("sucursales.id", ondelete="CASCADE"), nullable=False, index=True)
    numero = Column(Integer, nullable=False)
    capacidad = Column(Integer, nullable=False, default=4)
    estado = Column(String(24), nullable=False, default="LIBRE")


class Categoria(Base):
    __tablename__ = "categorias"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False, unique=True)


class Producto(Base):
    __tablename__ = "productos"
    id = Column(Integer, primary_key=True)
    categoria_id = Column(Integer, ForeignKey("categorias.id", ondelete="RESTRICT"), nullable=False, index=True)
    nombre = Column(String(140), nullable=False)
    precio = Column(Numeric(10, 2), nullable=False)
    imagen_url = Column(String(500), nullable=False, default="")
    activo = Column(Boolean, nullable=False, default=True)
    categoria = relationship("Categoria")
    insumos = relationship("Insumo", secondary=recetas, back_populates="productos")


class Insumo(Base):
    __tablename__ = "insumos"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(140), nullable=False, unique=True)
    unidad_medida = Column(String(24), nullable=False, default="pieza")
    productos = relationship("Producto", secondary=recetas, back_populates="insumos")


class Inventario(Base):
    __tablename__ = "inventario"
    __table_args__ = (UniqueConstraint("sucursal_id", "insumo_id", name="uq_inventario_sucursal_insumo"),)
    id = Column(Integer, primary_key=True)
    sucursal_id = Column(Integer, ForeignKey("sucursales.id", ondelete="CASCADE"), nullable=False, index=True)
    insumo_id = Column(Integer, ForeignKey("insumos.id", ondelete="RESTRICT"), nullable=False, index=True)
    existencia = Column(Numeric(12, 3), nullable=False, default=0)
    stock_minimo = Column(Numeric(12, 3), nullable=False, default=0)
    insumo = relationship("Insumo")
    sucursal = relationship("Sucursal")


class MovimientoInventario(Base):
    __tablename__ = "movimientos_inventario"
    id = Column(Integer, primary_key=True)
    inventario_id = Column(Integer, ForeignKey("inventario.id", ondelete="RESTRICT"), nullable=False, index=True)
    tipo = Column(String(24), nullable=False)
    cantidad = Column(Numeric(12, 3), nullable=False)
    orden_id = Column(Integer, ForeignKey("ordenes.id", ondelete="SET NULL"), nullable=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    fecha = Column(DateTime(timezone=True), nullable=False, default=utcnow, index=True)
    nota = Column(String(300), nullable=False, default="")
    inventario = relationship("Inventario")


class Orden(Base):
    __tablename__ = "ordenes"
    id = Column(Integer, primary_key=True)
    sucursal_id = Column(Integer, ForeignKey("sucursales.id", ondelete="RESTRICT"), nullable=False, index=True)
    mesa_id = Column(Integer, ForeignKey("mesas.id", ondelete="RESTRICT"), nullable=False, index=True)
    mesero_id = Column(Integer, ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False, index=True)
    estado = Column(String(24), nullable=False, default="ABIERTA", index=True)
    total = Column(Numeric(10, 2), nullable=False, default=0)
    fecha = Column(DateTime(timezone=True), nullable=False, default=utcnow, index=True)
    detalles = relationship("DetalleOrden", back_populates="orden", cascade="all, delete-orphan")
    mesa = relationship("Mesa")


class DetalleOrden(Base):
    __tablename__ = "detalle_orden"
    id = Column(Integer, primary_key=True)
    orden_id = Column(Integer, ForeignKey("ordenes.id", ondelete="CASCADE"), nullable=False, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id", ondelete="RESTRICT"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Numeric(10, 2), nullable=False)
    notas = Column(String(300), nullable=False, default="")
    estado = Column(String(24), nullable=False, default="PENDIENTE", index=True)
    stock_reintegrado = Column(Boolean, nullable=False, default=False)
    producto = relationship("Producto")
    orden = relationship("Orden", back_populates="detalles")


class Pago(Base):
    __tablename__ = "pagos"
    id = Column(Integer, primary_key=True)
    orden_id = Column(Integer, ForeignKey("ordenes.id", ondelete="RESTRICT"), nullable=False, index=True)
    cajero_id = Column(Integer, ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False)
    metodo = Column(String(24), nullable=False)
    monto = Column(Numeric(10, 2), nullable=False)
    fecha = Column(DateTime(timezone=True), nullable=False, default=utcnow, index=True)


class Bitacora(Base):
    __tablename__ = "bitacora"
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True)
    accion = Column(String(24), nullable=False)
    entidad = Column(String(100), nullable=False)
    entidad_id = Column(String(80), nullable=True)
    datos_json = Column(JSON, nullable=False, default=dict)
    fecha = Column(DateTime(timezone=True), nullable=False, default=utcnow, index=True)
    usuario = relationship("Usuario")
