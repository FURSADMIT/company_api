"""
CompanyDB API для обучения тестировщиков
FastAPI + PostgreSQL + Swagger UI
Полный CRUD для обучения тестированию
"""

from fastapi import FastAPI, HTTPException, Depends, Query, status, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text, MetaData, Table, inspect
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
import os
from datetime import datetime
import logging
import time
import json
import traceback

# ========== КОНФИГУРАЦИЯ ЛОГГИРОВАНИЯ ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========== НАСТРОЙКА ПРИЛОЖЕНИЯ FASTAPI ==========
app = FastAPI(
    title="🏢 CompanyDB API - Обучение тестировщиков",
    description="""
    ## 🎯 Полнофункциональное REST API для практики тестирования
    
    ### 📚 Возможности API:
    - **Swagger UI** - автоматическая интерактивная документация
    - **Полный CRUD** - создание, чтение, обновление, удаление
    - **Пагинация и фильтрация** - удобная навигация по данным
    - **Готовые тест-кейсы** - эндпоинты для обучения
    - **Обработка ошибок** - примеры всех HTTP статусов
    
    ### 🎓 Для кого:
    - Начинающие тестировщики
    - Студенты IT-курсов  
    - Разработчики, изучающие API
    - Все, кто хочет практиковаться в тестировании REST API
    """,
    version="2.0.0",
    contact={
        "name": "Для обучения тестировщиков",
        "url": "https://render.com",
        "email": "learning@example.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_ui_parameters={
        "persistAuthorization": True,
        "displayRequestDuration": True,
        "filter": True,
        "tryItOutEnabled": True,
        "defaultModelsExpandDepth": 2,
        "defaultModelExpandDepth": 2,
        "defaultModelRendering": "example",
        "displayOperationId": False,
        "docExpansion": "list",
        "showExtensions": True,
        "showCommonExtensions": True,
        "syntaxHighlight": {
            "activate": True,
            "theme": "monokai"
        }
    },
    openapi_tags=[
        {
            "name": "📊 Мониторинг",
            "description": "Проверка работоспособности API и БД"
        },
        {
            "name": "👥 Сотрудники",
            "description": "Полный CRUD для сотрудников компании"
        },
        {
            "name": "🏢 Департаменты", 
            "description": "Работа с отделами компании"
        },
        {
            "name": "🚗 Автомобили",
            "description": "Данные об автомобилях"
        },
        {
            "name": "📺 Сериалы",
            "description": "Информация о сериалах"
        },
        {
            "name": "🔍 Поиск",
            "description": "Поиск и фильтрация данных"
        },
        {
            "name": "🧪 Тестирование",
            "description": "Эндпоинты для обучения тестированию"
        },
        {
            "name": "🎓 Обучение",
            "description": "Материалы для обучения тестировщиков"
        },
        {
            "name": "🔧 Диагностика",
            "description": "Диагностические эндпоинты"
        }
    ],
    servers=[
        {
            "url": "https://company-api-4pws.onrender.com",
            "description": "Текущий сервер на Render"
        },
        {
            "url": "http://localhost:8000", 
            "description": "Локальная разработка"
        }
    ]
)

# ========== CORS НАСТРОЙКИ ==========
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600
)

# ========== НАСТРОЙКА БАЗЫ ДАННЫХ ==========
PORT = int(os.getenv("PORT", 8000))

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user1:Qa_2025!@79.174.88.202:15539/WORK2025"
)

try:
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_recycle=300,
        pool_pre_ping=True,
        pool_timeout=30,
        echo=False,
        connect_args={
            "connect_timeout": 10,
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5
        }
    )
    
    # Тестируем подключение
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        logger.info("✅ Database connection successful")
        
except Exception as e:
    logger.error(f"❌ Database connection failed: {str(e)}")
    raise RuntimeError(f"Database connection failed: {e}")

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)

metadata = MetaData()

# ========== ЗАВИСИМОСТИ ==========
def get_db():
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error"
        )
    finally:
        db.close()

# ========== PYDANTIC МОДЕЛИ ==========

class EmployeeBase(BaseModel):
    first_name: str = Field(
        ...,
        min_length=2,
        max_length=50,
        example="Иван",
        description="Имя сотрудника (2-50 символов)"
    )
    last_name: str = Field(
        ...,
        min_length=2,
        max_length=50,
        example="Иванов",
        description="Фамилия сотрудника (2-50 символов)"
    )
    position: str = Field(
        ...,
        max_length=50,
        example="Тестировщик",
        description="Должность сотрудника"
    )
    department_id: int = Field(
        ...,
        gt=0,
        example=1,
        description="ID департамента (должен существовать)"
    )
    car_id: int = Field(
        ...,
        gt=0,
        example=1,
        description="ID автомобиля (должен существовать)"
    )
    
    @validator('first_name', 'last_name')
    def validate_name(cls, v):
        if any(char.isdigit() for char in v):
            raise ValueError('Имя не должно содержать цифры')
        return v.title()

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=50,
        example="Иван",
        description="Имя сотрудника (2-50 символов)"
    )
    last_name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=50,
        example="Иванов",
        description="Фамилия сотрудника (2-50 символов)"
    )
    position: Optional[str] = Field(
        None,
        max_length=50,
        example="Тестировщик",
        description="Должность сотрудника"
    )
    department_id: Optional[int] = Field(
        None,
        gt=0,
        example=1,
        description="ID департамента (должен существовать)"
    )
    car_id: Optional[int] = Field(
        None,
        gt=0,
        example=1,
        description="ID автомобиля (должен существовать)"
    )
    
    @validator('first_name', 'last_name')
    def validate_name(cls, v):
        if v and any(char.isdigit() for char in v):
            raise ValueError('Имя не должно содержать цифры')
        return v.title() if v else v

class EmployeeResponse(EmployeeBase):
    id: int
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class DepartmentBase(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=50,
        example="IT",
        description="Название департамента"
    )

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentResponse(DepartmentBase):
    id: int
    
    class Config:
        from_attributes = True

class CarBase(BaseModel):
    brand: str = Field(..., example="Toyota", description="Марка автомобиля")
    model: str = Field(..., example="Camry", description="Модель автомобиля")

class CarCreate(CarBase):
    pass

class CarResponse(CarBase):
    id: int
    
    class Config:
        from_attributes = True

class SeriesBase(BaseModel):
    title: str = Field(..., example="Игра престолов", description="Название сериала")
    rating: float = Field(..., ge=0, le=10, example=9.3, description="Рейтинг сериала (0-10)")

class SeriesCreate(SeriesBase):
    pass

class SeriesResponse(SeriesBase):
    id: int
    
    class Config:
        from_attributes = True

class HealthResponse(BaseModel):
    status: str
    database: Dict[str, Any]
    timestamp: str
    uptime: str
    version: str
    
    class Config:
        from_attributes = True

# ========== MIDDLEWARE ДЛЯ ЛОГГИРОВАНИЯ ==========
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        logger.info(
            f"Request completed: {request.method} {request.url.path} "
            f"Status: {response.status_code} Time: {process_time:.3f}s"
        )
        
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Request failed: {request.method} {request.url.path} "
            f"Error: {str(e)} Time: {process_time:.3f}s"
        )
        raise

# ========== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ДЛЯ МОНИТОРИНГА ==========
app_start_time = datetime.now()
request_count = 0

# ========== ОСНОВНЫЕ ЭНДПОИНТЫ ==========

@app.get("/", 
         tags=["📊 Мониторинг"],
         summary="Корневая страница API",
         description="Возвращает информацию о API и доступных эндпоинтах")
async def root():
    global request_count
    request_count += 1
    
    return {
        "application": "CompanyDB API для обучения тестировщиков",
        "version": "2.0.0",
        "status": "✅ Активно",
        "uptime": str(datetime.now() - app_start_time),
        "total_requests": request_count,
        "hosting": {
            "provider": "Render.com",
            "plan": "Free Tier",
            "url": "https://company-api-4pws.onrender.com"
        },
        "database": {
            "type": "PostgreSQL",
            "host": "79.174.88.202:15539",
            "name": "WORK2025"
        },
        "features": [
            "✅ Автоматическая документация Swagger UI",
            "✅ Полный CRUD для всех сущностей",
            "✅ Реальная PostgreSQL база данных",
            "✅ Готовые тест-кейсы для обучения",
            "✅ Обработка всех HTTP ошибок",
            "✅ CORS для всех доменов"
        ],
        "quick_start": {
            "employees": "GET /test/employees - тестовый список сотрудников",
            "health": "GET /health - проверка API",
            "diagnostics": "GET /debug/connection - диагностика БД"
        }
    }

@app.get("/health",
         response_model=HealthResponse,
         tags=["📊 Мониторинг"],
         summary="Проверка работоспособности")
async def health_check(db: Session = Depends(get_db)):
    health_data = {
        "status": "healthy",
        "database": {},
        "timestamp": datetime.now().isoformat(),
        "uptime": str(datetime.now() - app_start_time),
        "version": "2.0.0"
    }
    
    try:
        start_time = time.time()
        db.execute(text("SELECT 1"))
        db_connection_time = (time.time() - start_time) * 1000
        
        inspector = inspect(engine)
        tables = inspector.get_table_names(schema="public")
        
        stats = {}
        for table in tables[:10]:  # Проверяем первые 10 таблиц
            try:
                result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                stats[table] = count
            except:
                stats[table] = "error"
        
        health_data["database"] = {
            "status": "✅ CONNECTED",
            "response_time_ms": round(db_connection_time, 2),
            "tables_available": len(tables),
            "available_tables": tables,
            "sample_counts": stats
        }
        
        health_data.update({
            "status": "✅ HEALTHY",
            "api": {
                "status": "RUNNING",
                "port": PORT,
                "uptime_seconds": (datetime.now() - app_start_time).total_seconds(),
                "total_requests": request_count,
            }
        })
        
        logger.info(f"Health check passed. DB time: {db_connection_time:.2f}ms")
        
    except SQLAlchemyError as e:
        logger.error(f"Health check failed: {str(e)}")
        health_data["database"] = {
            "status": "❌ DISCONNECTED",
            "error": str(e),
        }
        health_data.update({
            "status": "❌ UNHEALTHY",
        })
    
    except Exception as e:
        logger.error(f"Unexpected error in health check: {str(e)}")
        health_data.update({
            "status": "❌ ERROR",
            "error": str(e),
        })
    
    return health_data

# ========== ДИАГНОСТИЧЕСКИЕ ЭНДПОИНТЫ ==========

@app.get("/debug/connection",
         tags=["🔧 Диагностика"],
         summary="Диагностика подключения к БД")
async def debug_connection(db: Session = Depends(get_db)):
    """Показывает подробную информацию о подключении к БД"""
    try:
        # Получаем информацию о текущей базе данных
        result = db.execute(text("""
            SELECT 
                current_database() as database,
                current_schema() as schema,
                current_user as user,
                inet_server_addr() as server_address,
                inet_server_port() as server_port,
                version() as postgres_version
        """))
        
        db_info = dict(zip(result.keys(), result.fetchone()))
        
        # Получаем все таблицы во всех схемах
        result = db.execute(text("""
            SELECT 
                table_schema,
                table_name,
                table_type
            FROM information_schema.tables 
            WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
            ORDER BY table_schema, table_name
        """))
        
        all_tables = []
        for row in result:
            all_tables.append({
                "schema": row[0],
                "table": row[1],
                "type": row[2]
            })
        
        # Ищем таблицы с сотрудниками в любых схемах
        employee_tables = []
        for table_info in all_tables:
            table_name_lower = table_info["table"].lower()
            if any(keyword in table_name_lower for keyword in ['employee', 'staff', 'worker', 'person']):
                employee_tables.append(table_info)
        
        # Проверяем существование наших таблиц
        our_tables_status = {}
        table_variants = ['Employees', 'employees', 'Employee', 'employee',
                         'Departments', 'departments', 'Department', 'department',
                         'Cars', 'cars', 'Car', 'car',
                         'Series', 'series', 'Serie', 'serie',
                         'Employee_Series', 'employee_series', 'EmployeeSeries', 'employeeseries']
        
        for table_name in table_variants:
            found = False
            for table_info in all_tables:
                if table_info["table"] == table_name:
                    our_tables_status[table_name] = {
                        "found": True,
                        "schema": table_info["schema"],
                        "type": table_info["type"]
                    }
                    found = True
                    break
            
            if not found:
                our_tables_status[table_name] = {
                    "found": False,
                    "schema": None,
                    "type": None
                }
        
        return {
            "database_connection": db_info,
            "total_tables_found": len(all_tables),
            "all_tables": all_tables,
            "employee_related_tables": employee_tables,
            "our_tables_status": {k: v for k, v in our_tables_status.items() if v["found"]},
            "connection_url": str(engine.url).replace('Qa_2025!', '***')
        }
        
    except Exception as e:
        logger.error(f"Connection info error: {str(e)}", exc_info=True)
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@app.get("/debug/query-table",
         tags=["🔧 Диагностика"],
         summary="Тестовый запрос к таблице")
async def test_table_query(
    table_name: str = Query(None, description="Имя таблицы для теста"),
    schema_name: str = Query("public", description="Схема таблицы"),
    limit: int = Query(5, ge=1, le=100, description="Лимит строк"),
    db: Session = Depends(get_db)
):
    """Тестовый запрос к указанной таблице"""
    try:
        # Если имя таблицы не указано, показываем все таблицы
        if not table_name:
            inspector = inspect(engine)
            tables = []
            for schema in inspector.get_schema_names():
                for table in inspector.get_table_names(schema=schema):
                    tables.append(f"{schema}.{table}")
            
            return {
                "available_tables": tables,
                "message": "Specify table_name parameter to test a specific table"
            }
        
        # Пробуем разные варианты запросов
        queries = []
        
        # Вариант 1: со схемой и кавычками
        queries.append(f'SELECT * FROM "{schema_name}"."{table_name}" LIMIT {limit}')
        
        # Вариант 2: со схемой без кавычек
        queries.append(f'SELECT * FROM {schema_name}.{table_name} LIMIT {limit}')
        
        # Вариант 3: без схемы с кавычками
        queries.append(f'SELECT * FROM "{table_name}" LIMIT {limit}')
        
        # Вариант 4: без схемы и кавычек
        queries.append(f'SELECT * FROM {table_name} LIMIT {limit}')
        
        # Вариант 5: ищем таблицу без учета регистра
        queries.append(f'SELECT * FROM information_schema.tables WHERE table_name ILIKE \'{table_name}\'')
        
        results = []
        for sql in queries:
            try:
                result = db.execute(text(sql))
                columns = result.keys()
                rows = []
                for row in result:
                    rows.append(dict(zip(columns, row)))
                
                results.append({
                    "query": sql,
                    "success": True,
                    "columns": list(columns),
                    "data": rows,
                    "count": len(rows)
                })
                
                # Если запрос успешен, возвращаем первый успешный результат
                if rows:
                    return results[-1]
                    
            except Exception as e:
                results.append({
                    "query": sql,
                    "success": False,
                    "error": str(e)
                })
        
        # Если все запросы не сработали
        return {
            "success": False,
            "message": f"All query attempts failed for table '{table_name}'",
            "attempted_queries": results,
            "suggestion": "Check /debug/connection to see available tables"
        }
        
    except Exception as e:
        logger.error(f"Test query error: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

# ========== ТЕСТОВЫЕ ЭНДПОИНТЫ ==========

@app.get("/test/employees",
         tags=["🧪 Тестирование", "👥 Сотрудники"],
         summary="Тестовый запрос сотрудников")
async def test_employees(db: Session = Depends(get_db)):
    """Тестовый запрос для проверки данных о сотрудниках"""
    try:
        # Сначала найдем таблицу с сотрудниками
        inspector = inspect(engine)
        tables = inspector.get_table_names(schema="public")
        
        employee_table = None
        for table in tables:
            if any(keyword in table.lower() for keyword in ['employee', 'staff', 'worker']):
                employee_table = table
                break
        
        if not employee_table:
            return {
                "status": "warning",
                "message": "No employee table found",
                "available_tables": tables,
                "data": []
            }
        
        # Пробуем простой запрос
        sql = f"SELECT * FROM {employee_table} LIMIT 5"
        result = db.execute(text(sql))
        
        employees = []
        columns = result.keys()
        for row in result:
            employees.append(dict(zip(columns, row)))
        
        return {
            "status": "success",
            "table_used": employee_table,
            "columns": list(columns),
            "data": employees,
            "count": len(employees)
        }
        
    except Exception as e:
        logger.error(f"Test employees error: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "data": []
        }

@app.get("/test/query",
         tags=["🧪 Тестирование"],
         summary="Пример сложного SQL запроса")
async def test_complex_query(db: Session = Depends(get_db)):
    """Пример сложного SQL запроса для обучения"""
    try:
        # Простой тестовый запрос
        sql = """
            SELECT 
                table_schema,
                table_name,
                table_type
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
            LIMIT 10
        """
        
        result = db.execute(text(sql))
        columns = result.keys()
        data = [dict(zip(columns, row)) for row in result]
        
        return {
            "query": "Показывает таблицы в схеме public",
            "description": "Пример SQL запроса к information_schema",
            "data": data,
            "count": len(data)
        }
        
    except Exception as e:
        logger.error(f"Test query error: {str(e)}", exc_info=True)
        return {
            "error": str(e),
            "query": sql if 'sql' in locals() else "N/A"
        }

# ========== УНИВЕРСАЛЬНЫЕ ЭНДПОИНТЫ ==========

@app.get("/data/{table_name}",
         tags=["🔍 Поиск"],
         summary="Получить данные из любой таблицы")
async def get_table_data(
    table_name: str,
    page: int = Query(1, ge=1, description="Номер страницы"),
    per_page: int = Query(20, ge=1, le=100, description="Количество записей на страницу"),
    db: Session = Depends(get_db)
):
    """Универсальный эндпоинт для получения данных из любой таблицы"""
    try:
        offset = (page - 1) * per_page
        
        # Пробуем получить данные из таблицы
        try:
            sql = f"SELECT * FROM {table_name} LIMIT :limit OFFSET :offset"
            result = db.execute(text(sql), {"limit": per_page, "offset": offset})
            columns = result.keys()
            data = [dict(zip(columns, row)) for row in result]
            
            # Получаем общее количество
            count_sql = f"SELECT COUNT(*) FROM {table_name}"
            total_count = db.execute(text(count_sql)).scalar() or 0
            
        except:
            # Пробуем с кавычками
            sql = f'SELECT * FROM "{table_name}" LIMIT :limit OFFSET :offset'
            result = db.execute(text(sql), {"limit": per_page, "offset": offset})
            columns = result.keys()
            data = [dict(zip(columns, row)) for row in result]
            
            # Получаем общее количество
            count_sql = f'SELECT COUNT(*) FROM "{table_name}"'
            total_count = db.execute(text(count_sql)).scalar() or 0
        
        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
        
        return {
            "meta": {
                "table": table_name,
                "page": page,
                "per_page": per_page,
                "total": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            },
            "columns": list(columns),
            "data": data
        }
        
    except Exception as e:
        logger.error(f"Error getting table data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Table not found or inaccessible",
                "table_name": table_name,
                "message": str(e),
                "suggestion": "Check available tables at /debug/connection"
            }
        )

# ========== ЭНДПОИНТЫ ДЛЯ ОБУЧЕНИЯ ==========

@app.get("/test-cors",
         tags=["🧪 Тестирование"],
         summary="Тест CORS настроек")
async def test_cors():
    return {
        "message": "CORS test endpoint",
        "cors_enabled": True,
        "timestamp": datetime.now().isoformat(),
        "cors_headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true"
        }
    }

@app.get("/learning/http-status",
         tags=["🎓 Обучение"],
         summary="Примеры HTTP статусов")
async def learning_http_status(
    status_code: int = Query(200, description="HTTP статус код для примера")
):
    status_examples = {
        200: {"message": "OK - Запрос успешно выполнен", "example": "Успешное получение данных"},
        201: {"message": "Created - Ресурс создан", "example": "Успешное создание сотрудника"},
        400: {"message": "Bad Request - Неверный запрос", "example": "Некорректные данные в запросе"},
        401: {"message": "Unauthorized - Не авторизован", "example": "Отсутствует токен авторизации"},
        403: {"message": "Forbidden - Доступ запрещен", "example": "Нет прав для выполнения операции"},
        404: {"message": "Not Found - Ресурс не найден", "example": "Сотрудник с указанным ID не существует"},
        500: {"message": "Internal Server Error - Ошибка сервера", "example": "Ошибка в базе данных"},
    }
    
    if status_code in status_examples:
        return {
            "status_code": status_code,
            "status_message": status_examples[status_code]["message"],
            "example": status_examples[status_code]["example"],
            "timestamp": datetime.now().isoformat()
        }
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown status code. Available: {', '.join(map(str, status_examples.keys()))}"
        )

@app.get("/learning/http-methods",
         tags=["🎓 Обучение"],
         summary="Примеры HTTP методов")
async def learning_http_methods():
    return {
        "title": "🎓 Изучение HTTP методов",
        "methods": {
            "GET": {
                "description": "Получение данных",
                "use_case": "Получение списка сотрудников, информации о сотруднике",
                "example": "GET /employees, GET /employees/1",
                "idempotent": True,
                "safe": True
            },
            "POST": {
                "description": "Создание новых данных",
                "use_case": "Создание нового сотрудника",
                "example": "POST /employees",
                "idempotent": False,
                "safe": False
            },
            "PUT": {
                "description": "Полное обновление данных",
                "use_case": "Полное обновление информации о сотруднике",
                "example": "PUT /employees/1",
                "idempotent": True,
                "safe": False
            },
            "PATCH": {
                "description": "Частичное обновление данных",
                "use_case": "Частичное обновление информации о сотруднике",
                "example": "PATCH /employees/1",
                "idempotent": False,
                "safe": False
            },
            "DELETE": {
                "description": "Удаление данных",
                "use_case": "Удаление сотрудника",
                "example": "DELETE /employees/1",
                "idempotent": True,
                "safe": False
            }
        }
    }

# ========== ОБРАБОТЧИК OPTIONS ==========

@app.options("/{path:path}")
async def options_handler(path: str):
    return JSONResponse(
        content={"status": "ok"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "600"
        }
    )

# ========== ОБРАБОТЧИКИ ОШИБОК ==========

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTPException: {exc.status_code} - {exc.detail}")
    
    error_response = {
        "error": True,
        "status_code": exc.status_code,
        "detail": exc.detail if isinstance(exc.detail, dict) else {"message": exc.detail},
        "path": request.url.path,
        "method": request.method,
        "timestamp": datetime.now().isoformat()
    }
    
    headers = dict(exc.headers) if exc.headers else {}
    headers.update({
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
        "Access-Control-Allow-Headers": "*",
        "Access-Control-Allow-Credentials": "true"
    })
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response,
        headers=headers
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    error_response = {
        "error": True,
        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "detail": {
            "message": "Internal server error",
            "error_type": type(exc).__name__,
        },
        "path": request.url.path,
        "method": request.method,
        "timestamp": datetime.now().isoformat()
    }
    
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
        "Access-Control-Allow-Headers": "*",
        "Access-Control-Allow-Credentials": "true"
    }
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response,
        headers=headers
    )

# ========== ЗАПУСК СЕРВЕРА ==========

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 70)
    print("🏢 COMPANYDB API ДЛЯ ОБУЧЕНИЯ ТЕСТИРОВЩИКОВ")
    print("=" * 70)
    print(f"🌐 Основной URL: https://company-api-4pws.onrender.com")
    print(f"📖 Swagger UI:   https://company-api-4pws.onrender.com/docs")
    print(f"📚 ReDoc:        https://company-api-4pws.onrender.com/redoc")
    print(f"🔧 Health:       https://company-api-4pws.onrender.com/health")
    print("-" * 70)
    print("🔍 ДИАГНОСТИЧЕСКИЕ ЭНДПОИНТЫ:")
    print("GET /health                    - Проверка работоспособности")
    print("GET /debug/connection          - Диагностика подключения к БД")
    print("GET /debug/query-table         - Тестовые запросы к таблицам")
    print("GET /data/{table_name}         - Данные из любой таблицы")
    print("-" * 70)
    print("🧪 ТЕСТОВЫЕ ЭНДПОИНТЫ:")
    print("GET /test/employees            - Тестовый запрос сотрудников")
    print("GET /test/query                - Пример SQL запроса")
    print("GET /test-cors                 - Тест CORS настроек")
    print("-" * 70)
    print("🎓 ОБУЧАЮЩИЕ ЭНДПОИНТЫ:")
    print("GET /learning/http-status      - Примеры HTTP статусов")
    print("GET /learning/http-methods     - Примеры HTTP методов")
    print("=" * 70)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level="info",
        access_log=True,
        reload=False
    )