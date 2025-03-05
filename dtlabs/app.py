from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
import datetime
from typing import Optional
from dtlabs.database import get_db, Base, engine
from dtlabs.models import User, Server, SensorData
from dtlabs.auth import create_access_token, get_current_user
from dtlabs.schemas import UserCreate, ServerCreate, SensorDataCreate
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from datetime import datetime, timezone

app = FastAPI(
    title="IoT Backend API",
    description="API para gerenciamento de sensores IoT e servidores on-premise",
    version="1.0.0",
)

Base.metadata.create_all(bind=engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@app.get("/")
def root():
    return {"message": "API IoT Backend está rodando!"}

@app.post("/auth/register")
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Usuário já existe")
    hashed_password = pwd_context.hash(user_data.password)
    user = User(username=user_data.username, password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "Usuário criado com sucesso"}

@app.post("/auth/login")
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not pwd_context.verify(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="Credenciais inválidas")
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}


@app.post("/servers")
def register_server(server_data: ServerCreate, db: Session = Depends(get_db)):
    server = db.query(Server).filter(Server.server_name == server_data.server_name).first()
    if server :
        raise HTTPException(status_code=400, detail="Servidor já existe")
    server = Server(server_name=server_data.server_name)
    db.add(server)
    db.commit()
    db.refresh(server)
    return {"server_ulid": server.server_ulid, "server_name": server.server_name}

@app.post("/data")
def register_sensor_data(sensor_data: SensorDataCreate, db: Session = Depends(get_db)):
    server = db.query(Server).filter(Server.server_ulid == sensor_data.server_ulid).first()
    if not server:
        raise HTTPException(status_code=404, detail="Servidor não encontrado")
    new_data = SensorData(
        server_ulid=sensor_data.server_ulid,
        timestamp=sensor_data.timestamp,
        temperature=sensor_data.temperature,
        humidity=sensor_data.humidity,
        voltage=sensor_data.voltage,
        current=sensor_data.current
    )
    db.add(new_data)
    db.commit()
    return {"message": "Dados do sensor registrados"}

@app.get("/data")
def get_sensor_data(
    server_ulid: Optional[str] = Query(None, description="Filtrar por ULID do servidor"),
    start_time: Optional[str] = Query(None, description="Data de início no formato YYYY-MM-DD HH:MM:SS"),
    end_time: Optional[str] = Query(None, description="Data de fim no formato YYYY-MM-DD HH:MM:SS"),
    sensor_type: Optional[str] = Query(None, description="Tipo do sensor (temperature, humidity, voltage, current)"),
    aggregation: Optional[str] = Query(None, description="Agregação: minute, hour, day"),
    db: Session = Depends(get_db),
    user: str = Depends(get_current_user)
):
    try:
        if start_time:
            start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        if end_time:
            end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de data inválido. Use YYYY-MM-DD HH:MM:SS.")

    query = db.query(SensorData.timestamp)

    if server_ulid:
        query = query.filter(SensorData.server_ulid == server_ulid)
    if start_time and end_time:
        query = query.filter(SensorData.timestamp.between(start_time, end_time))

    sensor_column = None
    if sensor_type == "temperature":
        sensor_column = SensorData.temperature
    elif sensor_type == "humidity":
        sensor_column = SensorData.humidity
    elif sensor_type == "voltage":
        sensor_column = SensorData.voltage
    elif sensor_type == "current":
        sensor_column = SensorData.current
    else:
        raise HTTPException(status_code=400, detail="Sensor inválido. Escolha entre: temperature, humidity, voltage, current.")

    query = query.add_columns(sensor_column)

    if aggregation:
        if aggregation == "minute":
            time_group = func.date_trunc("minute", SensorData.timestamp)
        elif aggregation == "hour":
            time_group = func.date_trunc("hour", SensorData.timestamp)
        elif aggregation == "day":
            time_group = func.date_trunc("day", SensorData.timestamp)
        else:
            raise HTTPException(status_code=400, detail="Valor inválido para aggregation. Use: minute, hour, day.")

        query = (
            db.query(time_group.label("timestamp"), func.avg(sensor_column).label("avg_value"))
            .filter(sensor_column.isnot(None))
            .group_by(time_group)
            .order_by(time_group)
        )

    results = query.all()

    response = [{"timestamp": row.timestamp.isoformat(), sensor_type: row[1]} for row in results]

    return response

@app.get("/health/{server_id}")
def check_server_health(server_id: str, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    server = db.query(Server).filter(Server.server_ulid == server_id).first()
    last_entry = db.query(SensorData).filter(SensorData.server_ulid == server_id).order_by(SensorData.timestamp.desc()).first()
    if not server:
        raise HTTPException(status_code=404, detail="Servidor não encontrado")
    if not last_entry:
        return {"server_ulid": server_id, "status": "offline", "server_name": server.server_name}
    
    if last_entry.timestamp.tzinfo is None:
        last_entry.timestamp = last_entry.timestamp.replace(tzinfo=timezone.utc)
    
    time_diff = datetime.now(timezone.utc) - last_entry.timestamp
    status = "online" if time_diff.total_seconds() <= 100000 else "offline"
    
    return {"server_ulid": server_id, "status": status, "server_name": server.server_name}


@app.get("/health/all/")
def list_servers(db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    servers = db.query(Server).all()
    response = []
    for server in servers:
        last_entry = db.query(SensorData).filter(SensorData.server_ulid == server.server_ulid).order_by(SensorData.timestamp.desc()).first()

        if last_entry:

            if last_entry.timestamp.tzinfo is None:
                last_entry.timestamp = last_entry.timestamp.replace(tzinfo=timezone.utc)

            time_diff = datetime.now(timezone.utc) - last_entry.timestamp

            status = "online" if time_diff.total_seconds() <= 100000 else "offline"

        else:

            status = "offline"

        response.append({"server_ulid": server.server_ulid, "status": status, "server_name": server.server_name})

    return response
