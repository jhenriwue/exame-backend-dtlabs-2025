from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    username: str = Field(..., example="usuario123")
    password: str = Field(..., example="senha_segura")

class ServerCreate(BaseModel):
    server_name: str = Field(..., example="Servidor IoT 1")

class SensorDataCreate(BaseModel):
    server_ulid: str = Field(..., example="01JMG0J6BH9JV08PKJD5GSRM84")
    timestamp: datetime = Field(..., example="2024-02-19T12:34:56Z")
    temperature: Optional[float] = Field(None, example=25.5)
    humidity: Optional[float] = Field(None, example=60.2)
    voltage: Optional[float] = Field(None, example=220.0)
    current: Optional[float] = Field(None, example=1.5)

class SensorDataResponse(SensorDataCreate):
    id: str
