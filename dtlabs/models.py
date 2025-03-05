from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from dtlabs.database import Base
import datetime
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)

class Server(Base):
    __tablename__ = "servers"

    server_ulid = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    server_name = Column(String, nullable=False)

    sensor_data = relationship("SensorData", back_populates="server")

class SensorData(Base):
    __tablename__ = "sensor_data"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    server_ulid = Column(String, ForeignKey("servers.server_ulid"), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    temperature = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    voltage = Column(Float, nullable=True)
    current = Column(Float, nullable=True)

    server = relationship("Server", back_populates="sensor_data")
