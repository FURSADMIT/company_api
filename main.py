"""
CompanyDB API для обучения тестировщиков
FastAPI + PostgreSQL + Swagger UI
Развертывание на Render.com
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
    - **Реальная БД** - PostgreSQL с тестовыми данными
    - **Готовые тест-кейсы** - эндпоинты для обучения
    - **Обработка ошибок** - примеры всех HTTP статусов
    
    ### 🎓 Для кого:
    - Начинающие тестировщики
    - Студенты IT-курсов  
    - Разработчики, изучающие API
    - Все, кто хочет практиковаться в тестировании REST API
    
    ### 🗄️ Структура базы данных:
    1. **employees** - сотрудники компании
    2. **departments** - отделы компании
    3. **cars** - автомобили сотрудников  
    4. **series** - сериалы
    5. **employee_series** - связь сотрудников и сериалов
    
    ### 🔗 Технологии:
    - **Backend**: FastAPI (Python 3.10)
    - **Database**: PostgreSQL
    - **Hosting**: Render.com (бесплатный тариф)
    - **Documentation**: Swagger UI, ReDoc
    
    ### ⚠️ Особенности бесплатного хостинга:
    - API может "засыпать" после 15 минут неактивности
    - Первый запрос после простоя: 30-60 секунд
    - Автоматический деплой из GitHub
    
    ### 🛡️ Безопасность:
    - CORS разрешен для всех доменов
    - Полная валидация данных
    - Защита от SQL-инъекций
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
        },
        "requestSnippetsEnabled": True,
        "requestSnippets": {
            "generators": {
                "curl_bash": {
                    "title": "cURL (bash)",
                    "syntax": "bash"
                }
            },
            "defaultExpanded": True
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
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],  # Все методы
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600
)

# ========== ДОПОЛНИТЕЛЬНЫЙ MIDDLEWARE ДЛЯ CORS ==========
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    """
    Middleware для добавления CORS заголовков к каждому ответу.
    """
    if request.method == "OPTIONS":
        response = JSONResponse(content={"status": "ok"})
    else:
        response = await call_next(request)
    
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
    response.headers["Access-Control-Allow-Headers"] = "Origin, X-Requested-With, Content-Type, Accept, Authorization, X-API-Key"
    response.headers["Access-Control-Expose-Headers"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Max-Age"] = "600"
    
    return response

# ========== НАСТРОЙКА БАЗЫ ДАННЫХ ==========
PORT = int(os.getenv("PORT", 8000))

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user1:Qa_2025!@79.174.88.202:15539/WORK2025"
)

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

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)

metadata = MetaData()

# ========== ЗАВИСИМОСТИ ==========
def get_db():
    """
    Зависимость для получения сессии БД.
    """
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
    """Базовая модель сотрудника"""
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
        """Проверка, что имя/фамилия не содержат цифр"""
        if any(char.isdigit() for char in v):
            raise ValueError('Имя не должно содержать цифры')
        return v.title()

class EmployeeCreate(EmployeeBase):
    """Модель для создания сотрудника"""
    pass

class EmployeeUpdate(BaseModel):
    """Модель для обновления сотрудника"""
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
        """Проверка, что имя/фамилия не содержат цифр"""
        if v and any(char.isdigit() for char in v):
            raise ValueError('Имя не должно содержать цифры')
        return v.title() if v else v

class EmployeeResponse(EmployeeBase):
    """Модель ответа для сотрудника"""
    id: int
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class DepartmentResponse(BaseModel):
    """Модель ответа для департамента"""
    id: int
    name: str
    
    class Config:
        from_attributes = True

class CarResponse(BaseModel):
    """Модель ответа для автомобиля"""
    id: int
    brand: str
    model: str
    
    class Config:
        from_attributes = True

class SeriesResponse(BaseModel):
    """Модель ответа для сериала"""
    id: int
    title: str
    rating: Optional[float] = None
    
    class Config:
        from_attributes = True

class HealthResponse(BaseModel):
    """Модель ответа для health check"""
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
    """Middleware для логирования всех запросов"""
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
    """
    Корневой эндпоинт API.
    """
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
        "api_methods": {
            "GET": "Чтение данных",
            "POST": "Создание новых записей",
            "PUT": "Полное обновление записей",
            "DELETE": "Удаление записей"
        }
    }

@app.get("/health",
         response_model=HealthResponse,
         tags=["📊 Мониторинг"],
         summary="Проверка работоспособности",
         description="Полная диагностика состояния API и подключения к БД")
async def health_check(db: Session = Depends(get_db)):
    """
    Comprehensive health check endpoint.
    """
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
        for table in tables[:5]:
            try:
                result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                stats[table] = count
            except:
                stats[table] = "error"
        
        largest_table = None
        largest_count = 0
        for table, count in stats.items():
            if isinstance(count, int) and count > largest_count:
                largest_count = count
                largest_table = table
        
        health_data["database"] = {
            "status": "CONNECTED",
            "response_time_ms": round(db_connection_time, 2),
            "tables_available": len(tables),
            "available_tables": tables,
            "sample_counts": stats,
            "largest_table": {
                "name": largest_table,
                "records": largest_count
            } if largest_table else None
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
            "status": "DISCONNECTED",
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
    per_page: int = Query(20, ge=1, le=100, description="Количество записей на странице"),
    department_id: Optional[int] = Query(None, description="Фильтр по ID департамента"),
    search: Optional[str] = Query(None, description="Поиск по имени или фамилии"),
    sort_by: str = Query("id", description="Поле для сортировки"),
    sort_order: str = Query("asc", description="Порядок сортировки"),
    db: Session = Depends(get_db)
):
    """
    Полный эндпоинт для работы с сотрудниками.
    """
    try:
        valid_sort_fields = ["id", "first_name", "last_name", "position", "department_id"]
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
            FROM employees e
            LEFT JOIN departments d ON e.department_id = d.id
            LEFT JOIN cars c ON e.car_id = c.id
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
        
        result = db.execute(text(sql), params)
        columns = result.keys()
        employees = [dict(zip(columns, row)) for row in result]
        
        count_sql = "SELECT COUNT(*) FROM employees e"
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
        logger.error(f"Error fetching employees: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while fetching employees"
        )

@app.get("/employees/{employee_id}",
         response_model=Dict[str, Any],
         tags=["👥 Сотрудники"],
         summary="Получить сотрудника по ID",
         description="Полная информация о сотруднике включая связанные данные",
         responses={
             200: {"description": "Сотрудник найден"},
             404: {"description": "Сотрудник не найден"},
             422: {"description": "Неверный ID сотрудника"}
         })
async def get_employee(
    employee_id: int,
    db: Session = Depends(get_db)
):
    """
    Получение полной информации о конкретном сотруднике.
    """
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
                    FROM employee_series es
                    JOIN series s ON es.series_id = s.id
                    WHERE es.employee_id = e.id
                ) as favorite_series
            FROM employees e
            LEFT JOIN departments d ON e.department_id = d.id
            LEFT JOIN cars c ON e.car_id = c.id
            WHERE e.id = :id
        """), {"id": employee_id})
        
        employee = result.fetchone()
        
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Employee not found",
                    "employee_id": employee_id,
                    "message": f"Сотрудник с ID {employee_id} не существует в базе данных",
                    "suggestion": "Проверьте ID или получите список всех сотрудников: GET /employees"
                }
            )
        
        columns = result.keys()
        employee_dict = dict(zip(columns, employee))
        
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
        logger.error(f"Error fetching employee {employee_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.post("/employees",
          response_model=Dict[str, Any],
          status_code=status.HTTP_201_CREATED,
          tags=["👥 Сотрудники"],
          summary="Создать нового сотрудника",
          description="Создание нового сотрудника с валидацией данных",
          responses={
              201: {"description": "Сотрудник успешно создан"},
              400: {"description": "Некорректные данные или зависимости не существуют"},
              422: {"description": "Ошибка валидации данных"}
          })
async def create_employee(
    employee: EmployeeCreate,
    db: Session = Depends(get_db)
):
    """
    Создание нового сотрудника.
    """
    try:
        department_exists = db.execute(
            text("SELECT id, name FROM departments WHERE id = :id"),
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
        
        car_exists = db.execute(
            text("SELECT id, brand, model FROM cars WHERE id = :id"),
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
        
        result = db.execute(text("""
            INSERT INTO employees 
            (first_name, last_name, position, department_id, car_id)
            VALUES 
            (:first_name, :last_name, :position, :department_id, :car_id)
            RETURNING 
                id, 
                first_name, 
                last_name, 
                position, 
                department_id, 
                car_id,
                CURRENT_TIMESTAMP as created_at
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
                "car": f"{car_exists[1]} {car_exists[2]}",
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
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error creating employee: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while creating employee"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error creating employee: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.put("/employees/{employee_id}",
         response_model=Dict[str, Any],
         tags=["👥 Сотрудники"],
         summary="Обновить сотрудника",
         description="Полное обновление данных сотрудника",
         responses={
             200: {"description": "Сотрудник успешно обновлен"},
             404: {"description": "Сотрудник не найден"},
             400: {"description": "Некорректные данные"},
             422: {"description": "Ошибка валидации данных"}
         })
async def update_employee(
    employee_id: int,
    employee: EmployeeCreate,
    db: Session = Depends(get_db)
):
    """
    Полное обновление сотрудника.
    """
    try:
        department_exists = db.execute(
            text("SELECT id, name FROM departments WHERE id = :id"),
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
        
        car_exists = db.execute(
            text("SELECT id, brand, model FROM cars WHERE id = :id"),
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
        
        result = db.execute(text("""
            UPDATE employees 
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
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error updating employee {employee_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while updating employee"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error updating employee {employee_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.patch("/employees/{employee_id}",
           response_model=Dict[str, Any],
           tags=["👥 Сотрудники"],
           summary="Частично обновить сотрудника",
           description="Частичное обновление данных сотрудника",
           responses={
               200: {"description": "Сотрудник успешно обновлен"},
               404: {"description": "Сотрудник не найден"},
               400: {"description": "Некорректные данные"},
               422: {"description": "Ошибка валидации данных"}
           })
async def partial_update_employee(
    employee_id: int,
    employee_update: EmployeeUpdate,
    db: Session = Depends(get_db)
):
    """
    Частичное обновление сотрудника.
    """
    try:
        update_data = employee_update.dict(exclude_unset=True)
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No data provided for update"
            )
        
        if 'department_id' in update_data:
            department_exists = db.execute(
                text("SELECT id FROM departments WHERE id = :id"),
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
                text("SELECT id FROM cars WHERE id = :id"),
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
        
        set_clauses = []
        params = {"id": employee_id}
        
        for key, value in update_data.items():
            if value is not None:
                set_clauses.append(f"{key} = :{key}")
                params[key] = value
        
        if not set_clauses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid data to update"
            )
        
        sql = f"""
            UPDATE employees 
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
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error partially updating employee {employee_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while updating employee"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error partially updating employee {employee_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.delete("/employees/{employee_id}",
           response_model=Dict[str, Any],
           tags=["👥 Сотрудники"],
           summary="Удалить сотрудника",
           description="Удаление сотрудника по ID",
           responses={
               200: {"description": "Сотрудник успешно удален"},
               404: {"description": "Сотрудник не найден"}
           })
async def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db)
):
    """
    Удаление сотрудника по ID.
    """
    try:
        employee_info = db.execute(
            text("""
                SELECT e.first_name, e.last_name, e.position,
                       d.name as department_name
                FROM employees e
                LEFT JOIN departments d ON e.department_id = d.id
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
        
        db.execute(
            text("DELETE FROM employee_series WHERE employee_id = :id"),
            {"id": employee_id}
        )
        
        result = db.execute(
            text("DELETE FROM employees WHERE id = :id RETURNING id"),
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
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error deleting employee {employee_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while deleting employee"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error deleting employee {employee_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# ========== ЭНДПОИНТ ДЛЯ ТЕСТИРОВАНИЯ CORS ==========

@app.get("/test-cors",
         tags=["🧪 Тестирование"],
         summary="Тест CORS настроек",
         description="Простой эндпоинт для проверки CORS настроек")
async def test_cors():
    """
    Простой эндпоинт для проверки CORS.
    """
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

# ========== ОБРАБОТЧИК OPTIONS ДЛЯ CORS ==========

@app.options("/{path:path}")
async def options_handler(path: str):
    """
    Обработчик OPTIONS запросов для CORS.
    """
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
    """Кастомный обработчик HTTP исключений"""
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
    """Обработчик неожиданных исключений"""
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
    
    if os.getenv("ENVIRONMENT") == "production":
        error_response["detail"]["message"] = "Internal server error"
    
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
    print(f"📄 OpenAPI Spec: https://company-api-4pws.onrender.com/openapi.json")
    print(f"🔧 Health:       https://company-api-4pws.onrender.com/health")
    print("-" * 70)
    print(f"🗄️  Database:     PostgreSQL")
    print(f"🔗 CORS:         Enabled for all domains")
    print(f"⚡ Methods:      GET, POST, PUT, PATCH, DELETE")
    print("=" * 70)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level="info",
        access_log=True,
        reload=False
    )