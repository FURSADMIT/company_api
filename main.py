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
    
    ### 🗄️ База данных: PostgreSQL
    - **Таблица Employees** - сотрудники компании
    - **Таблица Departments** - отделы компании
    - **Таблица Cars** - автомобили сотрудников  
    - **Таблица Series** - сериалы
    - **Таблица Employee_Series** - связь сотрудников и сериалов
    
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
            "employees": "GET /employees - список сотрудников",
            "departments": "GET /departments - список отделов",
            "cars": "GET /cars - список автомобилей",
            "series": "GET /series - список сериалов",
            "health": "GET /health - проверка API"
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
        for table in ['Employees', 'Departments', 'Cars', 'Series']:
            try:
                result = db.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
                count = result.scalar()
                stats[table] = count
            except:
                stats[table] = "not found"
        
        health_data["database"] = {
            "status": "✅ CONNECTED",
            "response_time_ms": round(db_connection_time, 2),
            "tables_available": len(tables),
            "available_tables": tables,
            "table_counts": stats
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

# ========== ЭНДПОИНТЫ ДЛЯ СОТРУДНИКОВ (CRUD) ==========

@app.get("/employees",
         response_model=Dict[str, Any],
         tags=["👥 Сотрудники"],
         summary="Получить список сотрудников",
         description="Получение списка сотрудников с пагинацией и фильтрацией")
async def get_employees(
    page: int = Query(1, ge=1, description="Номер страницы"),
    per_page: int = Query(20, ge=1, le=100, description="Количество записей на страницу"),
    department_id: Optional[int] = Query(None, description="Фильтр по ID департамента"),
    search: Optional[str] = Query(None, description="Поиск по имени или фамилии"),
    sort_by: str = Query("id", description="Поле для сортировки"),
    sort_order: str = Query("asc", description="Порядок сортировки (asc/desc)"),
    db: Session = Depends(get_db)
):
    try:
        # Валидация параметров сортировки
        valid_sort_fields = ["id", "first_name", "last_name", "position", "department_id", "car_id"]
        if sort_by not in valid_sort_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid sort field. Valid options: {', '.join(valid_sort_fields)}"
            )
        
        if sort_order not in ["asc", "desc"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid sort order. Use 'asc' or 'desc'"
            )
        
        offset = (page - 1) * per_page
        
        # Основной SQL запрос - используем правильные имена таблиц с кавычками
        sql = """
            SELECT 
                e.id,
                e.first_name,
                e.last_name,
                e.position,
                e.department_id,
                e.car_id,
                d.name as department_name,
                c.brand as car_brand,
                c.model as car_model
            FROM "Employees" e
            LEFT JOIN "Departments" d ON e.department_id = d.id
            LEFT JOIN "Cars" c ON e.car_id = c.id
        """
        
        params = {"limit": per_page, "offset": offset}
        conditions = []
        
        if department_id:
            conditions.append("e.department_id = :dept_id")
            params["dept_id"] = department_id
        
        if search:
            conditions.append("(e.first_name ILIKE :search OR e.last_name ILIKE :search)")
            params["search"] = f"%{search}%"
        
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        
        sql += f" ORDER BY e.{sort_by} {sort_order.upper()}"
        sql += " LIMIT :limit OFFSET :offset"
        
        logger.debug(f"Executing SQL: {sql}")
        result = db.execute(text(sql), params)
        columns = result.keys()
        employees = [dict(zip(columns, row)) for row in result]
        
        # Получаем общее количество
        count_sql = 'SELECT COUNT(*) FROM "Employees" e'
        if conditions:
            count_sql += " WHERE " + " AND ".join(conditions)
        
        total_count = db.execute(
            text(count_sql), 
            {k: v for k, v in params.items() if k in ["dept_id", "search"]}
        ).scalar() or 0
        
        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
        
        return {
            "meta": {
                "page": page,
                "per_page": per_page,
                "total": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
                "sorting": {
                    "by": sort_by,
                    "order": sort_order
                },
                "filters": {
                    "department_id": department_id,
                    "search": search
                }
            },
            "data": employees
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching employees: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while fetching employees: {str(e)}"
        )

@app.get("/employees/{employee_id}",
         response_model=Dict[str, Any],
         tags=["👥 Сотрудники"],
         summary="Получить сотрудника по ID",
         description="Полная информация о сотруднике включая связанные данные")
async def get_employee(
    employee_id: int,
    db: Session = Depends(get_db)
):
    try:
        result = db.execute(text("""
            SELECT 
                e.id,
                e.first_name,
                e.last_name,
                e.position,
                e.department_id,
                e.car_id,
                d.name as department_name,
                d.id as department_id,
                c.brand as car_brand,
                c.model as car_model,
                c.id as car_id,
                (
                    SELECT json_agg(json_build_object(
                        'id', s.id,
                        'title', s.title,
                        'rating', s.rating
                    ))
                    FROM "Employee_Series" es
                    JOIN "Series" s ON es.series_id = s.id
                    WHERE es.employee_id = e.id
                ) as favorite_series
            FROM "Employees" e
            LEFT JOIN "Departments" d ON e.department_id = d.id
            LEFT JOIN "Cars" c ON e.car_id = c.id
            WHERE e.id = :id
        """), {"id": employee_id})
        
        employee = result.fetchone()
        
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Employee not found",
                    "employee_id": employee_id,
                    "message": f"Сотрудник с ID {employee_id} не существует",
                    "suggestion": "Проверьте ID или получите список всех сотрудников: GET /employees"
                }
            )
        
        columns = result.keys()
        employee_dict = dict(zip(columns, employee))
        
        # Преобразуем JSON строку в объект если нужно
        if employee_dict.get('favorite_series') and isinstance(employee_dict['favorite_series'], str):
            try:
                employee_dict['favorite_series'] = json.loads(employee_dict['favorite_series'])
            except:
                employee_dict['favorite_series'] = []
        
        return {
            "data": employee_dict,
            "metadata": {
                "retrieved_at": datetime.now().isoformat(),
                "employee_id": employee_id,
                "has_favorite_series": bool(employee_dict.get('favorite_series'))
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching employee {employee_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.post("/employees",
          response_model=Dict[str, Any],
          status_code=status.HTTP_201_CREATED,
          tags=["👥 Сотрудники"],
          summary="Создать нового сотрудника")
async def create_employee(
    employee: EmployeeCreate,
    db: Session = Depends(get_db)
):
    try:
        # Проверяем существование департамента
        department_exists = db.execute(
            text('SELECT id, name FROM "Departments" WHERE id = :id'),
            {"id": employee.department_id}
        ).fetchone()
        
        if not department_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Department not found",
                    "department_id": employee.department_id,
                    "message": f"Департамент с ID {employee.department_id} не существует",
                    "available_departments": "GET /departments"
                }
            )
        
        # Проверяем существование автомобиля
        car_exists = db.execute(
            text('SELECT id, brand, model FROM "Cars" WHERE id = :id'),
            {"id": employee.car_id}
        ).fetchone()
        
        if not car_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Car not found",
                    "car_id": employee.car_id,
                    "message": f"Автомобиль с ID {employee.car_id} не существует",
                    "available_cars": "GET /cars"
                }
            )
        
        # Создаем сотрудника
        result = db.execute(text("""
            INSERT INTO "Employees" 
            (first_name, last_name, position, department_id, car_id)
            VALUES 
            (:first_name, :last_name, :position, :department_id, :car_id)
            RETURNING 
                id, 
                first_name, 
                last_name, 
                position, 
                department_id, 
                car_id
        """), employee.dict())
        
        db.commit()
        
        new_employee = result.fetchone()
        columns = result.keys()
        
        return {
            "status": "success",
            "message": "Сотрудник успешно создан",
            "data": dict(zip(columns, new_employee)),
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "department": department_exists[1],
                "car": f"{car_exists[1]} {car_exists[2]}"
            }
        }
        
    except HTTPException:
        raise
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error creating employee: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Data integrity error. Check foreign key constraints."
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error creating employee: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.put("/employees/{employee_id}",
         response_model=Dict[str, Any],
         tags=["👥 Сотрудники"],
         summary="Обновить сотрудника")
async def update_employee(
    employee_id: int,
    employee: EmployeeCreate,
    db: Session = Depends(get_db)
):
    try:
        # Проверяем существование департамента
        department_exists = db.execute(
            text('SELECT id, name FROM "Departments" WHERE id = :id'),
            {"id": employee.department_id}
        ).fetchone()
        
        if not department_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Department not found",
                    "department_id": employee.department_id,
                }
            )
        
        # Проверяем существование автомобиля
        car_exists = db.execute(
            text('SELECT id, brand, model FROM "Cars" WHERE id = :id'),
            {"id": employee.car_id}
        ).fetchone()
        
        if not car_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Car not found",
                    "car_id": employee.car_id,
                }
            )
        
        # Обновляем сотрудника
        result = db.execute(text("""
            UPDATE "Employees" 
            SET first_name = :first_name,
                last_name = :last_name,
                position = :position,
                department_id = :department_id,
                car_id = :car_id
            WHERE id = :id
            RETURNING 
                id, 
                first_name, 
                last_name, 
                position, 
                department_id, 
                car_id
        """), {**employee.dict(), "id": employee_id})
        
        updated_employee = result.fetchone()
        
        if not updated_employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Employee not found",
                    "employee_id": employee_id,
                }
            )
        
        db.commit()
        
        columns = result.keys()
        
        return {
            "status": "success",
            "message": "Сотрудник успешно обновлен",
            "data": dict(zip(columns, updated_employee)),
            "metadata": {
                "updated_at": datetime.now().isoformat(),
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating employee {employee_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.patch("/employees/{employee_id}",
           response_model=Dict[str, Any],
           tags=["👥 Сотрудники"],
           summary="Частично обновить сотрудника")
async def partial_update_employee(
    employee_id: int,
    employee_update: EmployeeUpdate,
    db: Session = Depends(get_db)
):
    try:
        update_data = employee_update.dict(exclude_unset=True)
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No data provided for update"
            )
        
        # Проверяем зависимости если они указаны
        if 'department_id' in update_data:
            department_exists = db.execute(
                text('SELECT id FROM "Departments" WHERE id = :id'),
                {"id": update_data['department_id']}
            ).fetchone()
            
            if not department_exists:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "Department not found",
                        "department_id": update_data['department_id'],
                    }
                )
        
        if 'car_id' in update_data:
            car_exists = db.execute(
                text('SELECT id FROM "Cars" WHERE id = :id'),
                {"id": update_data['car_id']}
            ).fetchone()
            
            if not car_exists:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "Car not found",
                        "car_id": update_data['car_id'],
                    }
                )
        
        # Формируем SQL запрос
        set_clauses = []
        params = {"id": employee_id}
        
        for key, value in update_data.items():
            if value is not None:
                set_clauses.append(f'{key} = :{key}')
                params[key] = value
        
        sql = f"""
            UPDATE "Employees" 
            SET {', '.join(set_clauses)}
            WHERE id = :id
            RETURNING 
                id, 
                first_name, 
                last_name, 
                position, 
                department_id, 
                car_id
        """
        
        result = db.execute(text(sql), params)
        updated_employee = result.fetchone()
        
        if not updated_employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Employee not found",
                    "employee_id": employee_id,
                }
            )
        
        db.commit()
        
        columns = result.keys()
        
        return {
            "status": "success",
            "message": "Сотрудник успешно обновлен",
            "data": dict(zip(columns, updated_employee)),
            "metadata": {
                "updated_at": datetime.now().isoformat(),
                "updated_fields": list(update_data.keys())
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error partially updating employee {employee_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.delete("/employees/{employee_id}",
           response_model=Dict[str, Any],
           tags=["👥 Сотрудники"],
           summary="Удалить сотрудника")
async def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db)
):
    try:
        # Получаем информацию о сотруднике перед удалением
        employee_info = db.execute(
            text("""
                SELECT e.first_name, e.last_name, e.position,
                       d.name as department_name
                FROM "Employees" e
                LEFT JOIN "Departments" d ON e.department_id = d.id
                WHERE e.id = :id
            """),
            {"id": employee_id}
        ).fetchone()
        
        if not employee_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Employee not found",
                    "employee_id": employee_id,
                    "message": f"Сотрудник с ID {employee_id} не найден",
                    "suggestion": "Проверьте ID или получите список сотрудников: GET /employees"
                }
            )
        
        # Удаляем связи с сериалами
        db.execute(
            text('DELETE FROM "Employee_Series" WHERE employee_id = :id'),
            {"id": employee_id}
        )
        
        # Удаляем сотрудника
        result = db.execute(
            text('DELETE FROM "Employees" WHERE id = :id RETURNING id'),
            {"id": employee_id}
        )
        
        db.commit()
        
        deleted_id = result.scalar()
        
        return {
            "status": "success",
            "message": "Сотрудник успешно удален",
            "deleted_employee": {
                "id": deleted_id,
                "name": f"{employee_info[0]} {employee_info[1]}",
                "position": employee_info[2],
                "department": employee_info[3]
            },
            "metadata": {
                "deleted_at": datetime.now().isoformat(),
                "employee_id": employee_id,
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting employee {employee_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

# ========== ЭНДПОИНТЫ ДЛЯ ДЕПАРТАМЕНТОВ ==========

@app.get("/departments",
         response_model=Dict[str, Any],
         tags=["🏢 Департаменты"],
         summary="Получить список департаментов")
async def get_departments(
    page: int = Query(1, ge=1, description="Номер страницы"),
    per_page: int = Query(20, ge=1, le=100, description="Количество записей на страницу"),
    db: Session = Depends(get_db)
):
    try:
        offset = (page - 1) * per_page
        
        sql = 'SELECT id, name FROM "Departments" ORDER BY id LIMIT :limit OFFSET :offset'
        result = db.execute(text(sql), {"limit": per_page, "offset": offset})
        
        departments = [{"id": row[0], "name": row[1]} for row in result]
        
        total_count = db.execute(text('SELECT COUNT(*) FROM "Departments"')).scalar() or 0
        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
        
        return {
            "meta": {
                "page": page,
                "per_page": per_page,
                "total": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            },
            "data": departments
        }
        
    except Exception as e:
        logger.error(f"Error fetching departments: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while fetching departments: {str(e)}"
        )

@app.get("/departments/{department_id}/employees",
         tags=["🏢 Департаменты"],
         summary="Получить сотрудников департамента")
async def get_department_employees(
    department_id: int,
    page: int = Query(1, ge=1, description="Номер страницы"),
    per_page: int = Query(20, ge=1, le=100, description="Количество записей на страницу"),
    db: Session = Depends(get_db)
):
    try:
        # Проверяем существование департамента
        department_exists = db.execute(
            text('SELECT name FROM "Departments" WHERE id = :id'),
            {"id": department_id}
        ).fetchone()
        
        if not department_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Department not found",
                    "department_id": department_id,
                }
            )
        
        offset = (page - 1) * per_page
        
        sql = """
            SELECT 
                e.id,
                e.first_name,
                e.last_name,
                e.position,
                e.car_id,
                c.brand as car_brand,
                c.model as car_model
            FROM "Employees" e
            LEFT JOIN "Cars" c ON e.car_id = c.id
            WHERE e.department_id = :dept_id
            ORDER BY e.id
            LIMIT :limit OFFSET :offset
        """
        
        result = db.execute(text(sql), {
            "dept_id": department_id,
            "limit": per_page,
            "offset": offset
        })
        
        employees = []
        columns = result.keys()
        for row in result:
            employees.append(dict(zip(columns, row)))
        
        total_count = db.execute(
            text('SELECT COUNT(*) FROM "Employees" WHERE department_id = :dept_id'),
            {"dept_id": department_id}
        ).scalar() or 0
        
        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
        
        return {
            "department": {
                "id": department_id,
                "name": department_exists[0]
            },
            "meta": {
                "page": page,
                "per_page": per_page,
                "total": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            },
            "data": employees
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching department employees: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

# ========== ЭНДПОИНТЫ ДЛЯ АВТОМОБИЛЕЙ ==========

@app.get("/cars",
         response_model=Dict[str, Any],
         tags=["🚗 Автомобили"],
         summary="Получить список автомобилей")
async def get_cars(
    page: int = Query(1, ge=1, description="Номер страницы"),
    per_page: int = Query(20, ge=1, le=100, description="Количество записей на страницу"),
    search: Optional[str] = Query(None, description="Поиск по марке или модели"),
    db: Session = Depends(get_db)
):
    try:
        offset = (page - 1) * per_page
        
        sql = 'SELECT id, brand, model FROM "Cars"'
        params = {"limit": per_page, "offset": offset}
        
        if search:
            sql += ' WHERE brand ILIKE :search OR model ILIKE :search'
            params["search"] = f"%{search}%"
        
        sql += ' ORDER BY id LIMIT :limit OFFSET :offset'
        
        result = db.execute(text(sql), params)
        cars = [{"id": row[0], "brand": row[1], "model": row[2]} for row in result]
        
        count_sql = 'SELECT COUNT(*) FROM "Cars"'
        if search:
            count_sql += ' WHERE brand ILIKE :search OR model ILIKE :search'
        
        total_count = db.execute(
            text(count_sql), 
            {"search": params.get("search")} if search else {}
        ).scalar() or 0
        
        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
        
        return {
            "meta": {
                "page": page,
                "per_page": per_page,
                "total": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
                "filters": {
                    "search": search
                }
            },
            "data": cars
        }
        
    except Exception as e:
        logger.error(f"Error fetching cars: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while fetching cars: {str(e)}"
        )

@app.get("/cars/{car_id}/employees",
         tags=["🚗 Автомобили"],
         summary="Получить сотрудников с автомобилем")
async def get_car_employees(
    car_id: int,
    db: Session = Depends(get_db)
):
    try:
        # Проверяем существование автомобиля
        car_exists = db.execute(
            text('SELECT brand, model FROM "Cars" WHERE id = :id'),
            {"id": car_id}
        ).fetchone()
        
        if not car_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Car not found",
                    "car_id": car_id,
                }
            )
        
        sql = """
            SELECT 
                e.id,
                e.first_name,
                e.last_name,
                e.position,
                e.department_id,
                d.name as department_name
            FROM "Employees" e
            LEFT JOIN "Departments" d ON e.department_id = d.id
            WHERE e.car_id = :car_id
            ORDER BY e.id
        """
        
        result = db.execute(text(sql), {"car_id": car_id})
        
        employees = []
        columns = result.keys()
        for row in result:
            employees.append(dict(zip(columns, row)))
        
        return {
            "car": {
                "id": car_id,
                "brand": car_exists[0],
                "model": car_exists[1]
            },
            "employees": employees,
            "count": len(employees)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching car employees: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

# ========== ЭНДПОИНТЫ ДЛЯ СЕРИАЛОВ ==========

@app.get("/series",
         response_model=Dict[str, Any],
         tags=["📺 Сериалы"],
         summary="Получить список сериалов")
async def get_series(
    page: int = Query(1, ge=1, description="Номер страницы"),
    per_page: int = Query(20, ge=1, le=100, description="Количество записей на страницу"),
    min_rating: Optional[float] = Query(None, ge=0, le=10, description="Минимальный рейтинг"),
    max_rating: Optional[float] = Query(None, ge=0, le=10, description="Максимальный рейтинг"),
    search: Optional[str] = Query(None, description="Поиск по названию"),
    db: Session = Depends(get_db)
):
    try:
        offset = (page - 1) * per_page
        
        sql = 'SELECT id, title, rating FROM "Series"'
        params = {"limit": per_page, "offset": offset}
        conditions = []
        
        if min_rating is not None:
            conditions.append("rating >= :min_rating")
            params["min_rating"] = min_rating
        
        if max_rating is not None:
            conditions.append("rating <= :max_rating")
            params["max_rating"] = max_rating
        
        if search:
            conditions.append("title ILIKE :search")
            params["search"] = f"%{search}%"
        
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        
        sql += ' ORDER BY rating DESC, title LIMIT :limit OFFSET :offset'
        
        result = db.execute(text(sql), params)
        series_list = [{"id": row[0], "title": row[1], "rating": float(row[2])} for row in result]
        
        count_sql = 'SELECT COUNT(*) FROM "Series"'
        if conditions:
            count_sql += " WHERE " + " AND ".join(conditions)
        
        total_count = db.execute(
            text(count_sql), 
            {k: v for k, v in params.items() if k in ["min_rating", "max_rating", "search"]}
        ).scalar() or 0
        
        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
        
        return {
            "meta": {
                "page": page,
                "per_page": per_page,
                "total": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
                "filters": {
                    "min_rating": min_rating,
                    "max_rating": max_rating,
                    "search": search
                }
            },
            "data": series_list
        }
        
    except Exception as e:
        logger.error(f"Error fetching series: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while fetching series: {str(e)}"
        )

@app.get("/series/{series_id}/employees",
         tags=["📺 Сериалы"],
         summary="Получить сотрудников которые смотрят сериал")
async def get_series_employees(
    series_id: int,
    db: Session = Depends(get_db)
):
    try:
        # Проверяем существование сериала
        series_exists = db.execute(
            text('SELECT title, rating FROM "Series" WHERE id = :id'),
            {"id": series_id}
        ).fetchone()
        
        if not series_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Series not found",
                    "series_id": series_id,
                }
            )
        
        sql = """
            SELECT 
                e.id,
                e.first_name,
                e.last_name,
                e.position,
                e.department_id,
                d.name as department_name,
                e.car_id,
                c.brand as car_brand,
                c.model as car_model
            FROM "Employees" e
            LEFT JOIN "Departments" d ON e.department_id = d.id
            LEFT JOIN "Cars" c ON e.car_id = c.id
            JOIN "Employee_Series" es ON e.id = es.employee_id
            WHERE es.series_id = :series_id
            ORDER BY e.id
        """
        
        result = db.execute(text(sql), {"series_id": series_id})
        
        employees = []
        columns = result.keys()
        for row in result:
            employees.append(dict(zip(columns, row)))
        
        return {
            "series": {
                "id": series_id,
                "title": series_exists[0],
                "rating": float(series_exists[1])
            },
            "employees": employees,
            "count": len(employees)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching series employees: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

# ========== ЭНДПОИНТЫ ДЛЯ ПОИСКА ==========

@app.get("/search",
         tags=["🔍 Поиск"],
         summary="Поиск по всем данным")
async def search_all(
    query: str = Query(..., description="Поисковый запрос"),
    limit: int = Query(20, ge=1, le=100, description="Количество результатов"),
    db: Session = Depends(get_db)
):
    try:
        results = {
            "employees": [],
            "departments": [],
            "cars": [],
            "series": []
        }
        
        # Поиск по сотрудникам
        try:
            sql = """
                SELECT 
                    e.id,
                    e.first_name,
                    e.last_name,
                    e.position,
                    e.department_id,
                    d.name as department_name,
                    e.car_id,
                    c.brand as car_brand,
                    c.model as car_model
                FROM "Employees" e
                LEFT JOIN "Departments" d ON e.department_id = d.id
                LEFT JOIN "Cars" c ON e.car_id = c.id
                WHERE e.first_name ILIKE :query 
                   OR e.last_name ILIKE :query 
                   OR e.position ILIKE :query
                LIMIT :limit
            """
            
            result = db.execute(text(sql), {"query": f"%{query}%", "limit": limit})
            columns = result.keys()
            for row in result:
                results["employees"].append(dict(zip(columns, row)))
        except Exception as e:
            logger.warning(f"Search employees error: {str(e)}")
        
        # Поиск по департаментам
        try:
            sql = 'SELECT id, name FROM "Departments" WHERE name ILIKE :query LIMIT :limit'
            result = db.execute(text(sql), {"query": f"%{query}%", "limit": limit})
            for row in result:
                results["departments"].append({"id": row[0], "name": row[1]})
        except Exception as e:
            logger.warning(f"Search departments error: {str(e)}")
        
        # Поиск по автомобилям
        try:
            sql = 'SELECT id, brand, model FROM "Cars" WHERE brand ILIKE :query OR model ILIKE :query LIMIT :limit'
            result = db.execute(text(sql), {"query": f"%{query}%", "limit": limit})
            for row in result:
                results["cars"].append({"id": row[0], "brand": row[1], "model": row[2]})
        except Exception as e:
            logger.warning(f"Search cars error: {str(e)}")
        
        # Поиск по сериалам
        try:
            sql = 'SELECT id, title, rating FROM "Series" WHERE title ILIKE :query LIMIT :limit'
            result = db.execute(text(sql), {"query": f"%{query}%", "limit": limit})
            for row in result:
                results["series"].append({"id": row[0], "title": row[1], "rating": float(row[2])})
        except Exception as e:
            logger.warning(f"Search series error: {str(e)}")
        
        total_results = sum(len(v) for v in results.values())
        
        return {
            "query": query,
            "total_results": total_results,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error in search: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search error: {str(e)}"
        )

# ========== ТЕСТОВЫЕ ЭНДПОИНТЫ ==========

@app.get("/test/query",
         tags=["🧪 Тестирование"],
         summary="Тестовый SQL запрос")
async def test_query(db: Session = Depends(get_db)):
    """Пример сложного SQL запроса для обучения"""
    try:
        sql = """
            SELECT 
                e.first_name, 
                e.last_name, 
                d.name AS department, 
                c.brand AS car_brand, 
                c.model AS car_model,
                s.title as favorite_series,
                s.rating
            FROM "Employees" e
            JOIN "Departments" d ON e.department_id = d.id
            JOIN "Cars" c ON e.car_id = c.id
            LEFT JOIN "Employee_Series" es ON e.id = es.employee_id
            LEFT JOIN "Series" s ON es.series_id = s.id
            WHERE s.title = 'Теория большого взрыва'
            OR s.title IS NULL
            ORDER BY e.id
            LIMIT 10
        """
        
        result = db.execute(text(sql))
        columns = result.keys()
        data = [dict(zip(columns, row)) for row in result]
        
        return {
            "query": "Пример сложного SQL запроса с JOIN",
            "description": "Находит сотрудников, которые смотрят 'Теорию большого взрыва'",
            "data": data,
            "count": len(data)
        }
        
    except Exception as e:
        logger.error(f"Error in test query: {str(e)}", exc_info=True)
        return {
            "error": str(e),
            "query": sql if 'sql' in locals() else "N/A"
        }

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

# ========== ДИАГНОСТИЧЕСКИЕ ЭНДПОИНТЫ ==========

@app.get("/debug/tables",
         tags=["🔧 Диагностика"],
         summary="Информация о таблицах в базе данных")
async def debug_tables(db: Session = Depends(get_db)):
    """Показывает все таблицы в базе данных"""
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names(schema="public")
        
        table_info = {}
        for table_name in tables:
            try:
                columns = inspector.get_columns(table_name)
                column_info = []
                
                for col in columns:
                    column_info.append({
                        "name": col['name'],
                        "type": str(col['type']),
                        "nullable": col.get('nullable', True)
                    })
                
                table_info[table_name] = {
                    "columns": column_info,
                    "row_count": db.execute(text(f'SELECT COUNT(*) FROM "{table_name}"')).scalar()
                }
                
            except Exception as e:
                table_info[table_name] = {
                    "error": str(e),
                    "columns": [],
                    "row_count": None
                }
        
        return {
            "database": engine.url.database,
            "total_tables": len(tables),
            "tables": tables,
            "table_details": table_info
        }
        
    except Exception as e:
        logger.error(f"Debug tables error: {str(e)}", exc_info=True)
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
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
    print("📊 ОСНОВНЫЕ ЭНДПОИНТЫ:")
    print("GET  /employees               - Список сотрудников")
    print("GET  /employees/{id}          - Сотрудник по ID")
    print("POST /employees               - Создать сотрудника")
    print("PUT  /employees/{id}          - Обновить сотрудника")
    print("GET  /departments             - Список отделов")
    print("GET  /cars                    - Список автомобилей")
    print("GET  /series                  - Список сериалов")
    print("GET  /search?query=текст      - Поиск по всем данным")
    print("GET  /test/query              - Пример сложного SQL запроса")
    print("GET  /debug/tables            - Диагностика таблиц БД")
    print("=" * 70)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level="info",
        access_log=True,
        reload=False
    )