from pydantic import BaseModel
from typing import List


class Detail(BaseModel):
    actividad: str
    horas: int
    tarifa: int
    subtotal: int


class InvestmentTime(BaseModel):
    detalle: List[Detail]
    total_horas: int
    total_cop: int


class CommercialConditions(BaseModel):
    pago: str
    garantia: str
    metodologia: str


class Quotation(BaseModel):
    nombre_requerimiento: str
    numero_oferta: str
    fecha_cotizacion: str
    autores: List[str]
    objetivo: str
    antecedentes: str
    alcance: List[str]
    tiempo_inversion: InvestmentTime
    tiempo_desarrollo: str
    exclusiones: List[str]
    condiciones_comerciales: CommercialConditions
