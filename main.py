"""
CompanyDB API для обучения тестировщиков
FastAPI + PostgreSQL + Swagger UI
Развертывание на Render.com
"""

from fastapi import FastAPI, HTTPException, Depends, Query, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text, MetaData, Table, inspect
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
import os
from datetime import datetime, timedelta
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
    """,
    version="1.0.0",
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
    openapi_tags=[
        {
            "name": "👥 Сотрудники",
            "description": "Операции с сотрудниками компании"
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
            "name": "📊 Мониторинг",
            "description": "Проверка работоспособности"
        },
        {
            "name": "🎓 Обучение",
            "description": "Материалы для обучения"
        }
    ],
    servers=[
        {
            "url": "https://company-api.onrender.com",
            "description": "Production server"
        },
        {
            "url": "http://localhost:8000", 
            "description": "Local development server"
        }
    ]
)

# ========== CORS НАСТРОЙКИ ==========
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем все домены для обучения
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем все HTTP методы
    allow_headers=["*"],  # Разрешаем все заголовки
)

# ========== НАСТРОЙКА БАЗЫ ДАННЫХ ==========

# Автоматическое определение порта для Render
PORT = int(os.getenv("PORT", 8000))

# Строка подключения к PostgreSQL на Reg.ru
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user1:Qa_2025!@79.174.88.202:15539/WORK2025"
)

# Оптимизированный движок SQLAlchemy для облачного хостинга
engine = create_engine(
    DATABASE_URL,
    pool_size=5,           # Базовый размер пула соединений
    max_overflow=10,       # Максимальное количество соединений
    pool_recycle=300,      # Переподключение каждые 5 минут
    pool_pre_ping=True,    # Проверка соединения перед использованием
    pool_timeout=30,       # Таймаут ожидания соединения
    echo=False,            # Логирование SQL (False в продакшене)
    connect_args={
        "connect_timeout": 10,      # Таймаут подключения
        "keepalives": 1,            # Включить keepalive
        "keepalives_idle": 30,      # Keepalive idle время
        "keepalives_interval": 10,  # Интервал keepalive
        "keepalives_count": 5       # Количество попыток keepalive
    }
)

# Создаем фабрику сессий
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)

# Метаданные базы данных
metadata = MetaData()

# ========== ЗАВИСИМОСТИ ==========
def get_db():
    """
    Зависимость для получения сессии БД.
    Гарантирует закрытие сессии после использования.
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
        return v.title()  # Приводим к формату "Иван"

class EmployeeCreate(EmployeeBase):
    """Модель для создания сотрудника"""
    pass

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
    rating: float
    
    class Config:
        from_attributes = True

class QueryRequest(BaseModel):
    """Модель для кастомных SQL запросов"""
    sql: str = Field(
        ...,
        example="SELECT * FROM employees LIMIT 5",
        description="SQL запрос (разрешены только SELECT)"
    )

class HealthResponse(BaseModel):
    """Модель ответа для health check"""
    status: str
    database: str
    timestamp: str
    uptime: str
    version: str

class StatsResponse(BaseModel):
    """Модель ответа для статистики"""
    tables: Dict[str, int]
    departments: List[Dict[str, Any]]
    timestamp: str
    api_info: Dict[str, Any]

# ========== MIDDLEWARE ДЛЯ ЛОГГИРОВАНИЯ ==========
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware для логирования всех запросов"""
    start_time = time.time()
    
    # Логируем входящий запрос
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Логируем ответ
        logger.info(
            f"Request completed: {request.method} {request.url.path} "
            f"Status: {response.status_code} Time: {process_time:.3f}s"
        )
        
        # Добавляем время обработки в заголовки
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
    
    Возвращает полную информацию о доступных возможностях,
    эндпоинтах и инструкции для начала работы.
    """
    global request_count
    request_count += 1
    
    return {
        "application": "CompanyDB API для обучения тестировщиков",
        "version": "1.0.0",
        "status": "✅ Активно",
        "uptime": str(datetime.now() - app_start_time),
        "total_requests": request_count,
        
        "hosting": {
            "provider": "Render.com",
            "plan": "Free Tier",
            "region": "Frankfurt, EU",
            "url": "https://company-api.onrender.com"
        },
        
        "database": {
            "type": "PostgreSQL",
            "host": "79.174.88.202:15539",
            "name": "WORK2025",
            "tables": 5
        },
        
        "features": [
            "✅ Автоматическая документация Swagger UI",
            "✅ Поддержка 10+ одновременных пользователей",
            "✅ Реальная PostgreSQL база данных",
            "✅ Полный CRUD для всех сущностей",
            "✅ Готовые тест-кейсы для обучения",
            "✅ Обработка всех HTTP ошибок",
            "✅ Мониторинг и статистика",
            "✅ CORS для всех доменов"
        ],
        
        "quick_start_guide": {
            "step_1": "Откройте Swagger UI: /docs",
            "step_2": "Изучите документацию каждого эндпоинта",
            "step_3": "Попробуйте 'Try it out' для GET запросов",
            "step_4": "Протестируйте создание ресурсов (POST)",
            "step_5": "Проверьте обработку ошибок: /test/error/404"
        },
        
        "useful_endpoints": {
            "documentation": {
                "swagger_ui": "/docs",
                "redoc": "/redoc",
                "openapi_spec": "/openapi.json"
            },
            "monitoring": {
                "health_check": "/health",
                "statistics": "/stats",
                "database_info": "/db/tables"
            },
            "testing": {
                "error_testing": "/test/error/{code}",
                "validation_testing": "/test/validation",
                "learning_tasks": "/learning/tasks"
            },
            "data": {
                "employees": "/employees",
                "departments": "/departments", 
                "cars": "/cars",
                "series": "/series"
            }
        },
        
        "learning_path": {
            "beginner": {
                "duration": "5-6 часов",
                "topics": ["HTTP методы", "Статус коды", "JSON структуры"]
            },
            "intermediate": {
                "duration": "6-7 часов", 
                "topics": ["Валидация", "Пагинация", "Фильтрация", "Ошибки"]
            },
            "advanced": {
                "duration": "4-6 часов",
                "topics": ["Интеграционное тестирование", "Нагрузочное тестирование", "Безопасность"]
            }
        },
        
        "api_limits": {
            "concurrent_users": "10-15",
            "rate_limits": "Нет (для обучения)",
            "request_timeout": "30 секунд",
            "max_payload_size": "10MB"
        },
        
        "support": {
            "issues": "Используйте Swagger UI для тестирования",
            "contact": "Для вопросов по обучению",
            "note": "Это учебный проект для практики тестирования"
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
    
    Проверяет:
    1. Работу самого API
    2. Подключение к PostgreSQL
    3. Доступность всех таблиц
    4. Время ответа БД
    
    Возвращает подробный отчет о состоянии системы.
    """
    health_data = {
        "status": "healthy",
        "database": "connected",
        "timestamp": datetime.now().isoformat(),
        "uptime": str(datetime.now() - app_start_time),
        "version": "1.0.0"
    }
    
    # Проверка подключения к базе данных
    try:
        start_time = time.time()
        
        # 1. Проверяем базовое подключение
        db.execute(text("SELECT 1"))
        db_connection_time = (time.time() - start_time) * 1000  # в мс
        
        # 2. Проверяем доступность таблиц
        inspector = inspect(engine)
        tables = inspector.get_table_names(schema="public")
        
        # 3. Получаем статистику по данным
        stats = {}
        for table in tables[:5]:  # Проверяем первые 5 таблиц
            try:
                result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                stats[table] = count
            except:
                stats[table] = "error"
        
        # 4. Получаем информацию о самой большой таблице
        largest_table = None
        largest_count = 0
        for table, count in stats.items():
            if isinstance(count, int) and count > largest_count:
                largest_count = count
                largest_table = table
        
        health_data.update({
            "status": "✅ HEALTHY",
            "database": {
                "status": "CONNECTED",
                "response_time_ms": round(db_connection_time, 2),
                "tables_available": len(tables),
                "available_tables": tables,
                "sample_counts": stats,
                "largest_table": {
                    "name": largest_table,
                    "records": largest_count
                } if largest_table else None
            },
            "api": {
                "status": "RUNNING",
                "port": PORT,
                "uptime_seconds": (datetime.now() - app_start_time).total_seconds(),
                "total_requests": request_count,
                "concurrent_capacity": "15+ users"
            },
            "hosting": {
                "provider": "Render.com",
                "plan": "Free Tier",
                "cold_start": "Да (после 15 мин простоя)",
                "region": "Frankfurt, EU"
            }
        })
        
        logger.info(f"Health check passed. DB time: {db_connection_time:.2f}ms")
        
    except SQLAlchemyError as e:
        logger.error(f"Health check failed: {str(e)}")
        health_data.update({
            "status": "❌ UNHEALTHY",
            "database": {
                "status": "DISCONNECTED",
                "error": str(e),
                "connection_string": DATABASE_URL.split('@')[0] + "@***"  # Маскируем пароль
            },
            "api": {
                "status": "RUNNING",
                "port": PORT,
                "error": "Database connection failed"
            },
            "troubleshooting": [
                "1. Проверьте доступность сервера PostgreSQL",
                "2. Проверьте правильность учетных данных",
                "3. Проверьте настройки брандмауэра",
                "4. Проверьте, запущена ли база данных"
            ]
        })
    
    except Exception as e:
        logger.error(f"Unexpected error in health check: {str(e)}")
        health_data.update({
            "status": "❌ ERROR",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })
    
    return health_data

# ========== ЭНДПОИНТЫ ДЛЯ СОТРУДНИКОВ ==========

@app.get("/employees",
         response_model=Dict[str, Any],
         tags=["👥 Сотрудники"],
         summary="Получить список сотрудников",
         description="""
         Получение списка сотрудников с поддержкой:
         - Пагинации (page, per_page)
         - Фильтрации по департаменту
         - Сортировки
         - Поиска по имени
         """)
async def get_employees(
    page: int = Query(
        1,
        ge=1,
        description="Номер страницы (начиная с 1)",
        example=1
    ),
    per_page: int = Query(
        20,
        ge=1,
        le=100,
        description="Количество записей на странице (1-100)",
        example=20
    ),
    department_id: Optional[int] = Query(
        None,
        description="Фильтр по ID департамента",
        example=1
    ),
    search: Optional[str] = Query(
        None,
        description="Поиск по имени или фамилии",
        example="Иван"
    ),
    sort_by: str = Query(
        "id",
        description="Поле для сортировки (id, first_name, last_name, position)",
        example="last_name"
    ),
    sort_order: str = Query(
        "asc",
        description="Порядок сортировки (asc, desc)",
        example="asc"
    ),
    db: Session = Depends(get_db)
):
    """
    Полный эндпоинт для работы с сотрудниками.
    
    Поддерживает все возможности для комплексного тестирования:
    - Пагинация с валидацией
    - Фильтрация по разным критериям
    - Поиск текста
    - Сортировка по разным полям
    - Подробная мета-информация
    
    Идеально для обучения тестированию API с различными параметрами.
    """
    # Валидация параметров сортировки
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
    
    # Вычисляем offset для пагинации
    offset = (page - 1) * per_page
    
    # Строим SQL запрос динамически
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
    
    # Добавляем условия фильтрации
    if department_id:
        conditions.append("e.department_id = :dept_id")
        params["dept_id"] = department_id
    
    if search:
        conditions.append("(e.first_name ILIKE :search OR e.last_name ILIKE :search)")
        params["search"] = f"%{search}%"
    
    # Добавляем WHERE если есть условия
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    
    # Добавляем сортировку
    sql += f" ORDER BY e.{sort_by} {sort_order.upper()}"
    
    # Добавляем лимит и offset
    sql += " LIMIT :limit OFFSET :offset"
    
    try:
        # Выполняем основной запрос
        result = db.execute(text(sql), params)
        columns = result.keys()
        employees = [dict(zip(columns, row)) for row in result]
        
        # Получаем общее количество для пагинации
        count_sql = "SELECT COUNT(*) FROM employees e"
        if conditions:
            count_sql += " WHERE " + " AND ".join(conditions)
        
        total_count = db.execute(
            text(count_sql), 
            {k: v for k, v in params.items() if k in ["dept_id", "search"]}
        ).scalar() or 0
        
        # Вычисляем общее количество страниц
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
            "data": employees,
            "testing_guidance": {
                "positive_tests": [
                    "Проверьте пагинацию с разными значениями page/per_page",
                    "Протестируйте фильтрацию по department_id",
                    "Проверьте поиск по имени/фамилии",
                    "Протестируйте разные варианты сортировки"
                ],
                "negative_tests": [
                    "page=0, page=-1, page=999999",
                    "per_page=0, per_page=101, per_page=-5",
                    "department_id=999999 (несуществующий)",
                    "sort_by=invalid_field, sort_order=invalid_order"
                ],
                "boundary_tests": [
                    "per_page=1 (минимальное значение)",
                    "per_page=100 (максимальное значение)",
                    "page=1 (первая страница)",
                    f"page={total_pages} (последняя страница)"
                ]
            }
        }
        
    except SQLAlchemyError as e:
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
    employee_id: int = Query(..., ge=1, description="ID сотрудника"),
    db: Session = Depends(get_db)
):
    """
    Получение полной информации о конкретном сотруднике.
    
    Возвращает:
    - Основные данные сотрудника
    - Информацию о департаменте
    - Информацию об автомобиле
    - Список любимых сериалов
    
    Идеально для тестирования:
    - Получение существующего ресурса
    - Обработка несуществующего ID
    - Валидация входных параметров
    - Проверка структуры сложного ответа
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
        
        # Преобразуем JSON строку в объект Python если нужно
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
            },
            "related_endpoints": {
                "department": f"/departments/{employee_dict['department_id']}",
                "car": f"/cars/{employee_dict['car_id']}",
                "all_employees": "/employees"
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
    
    Полная валидация:
    1. Проверка формата имени/фамилии
    2. Проверка существования департамента
    3. Проверка существования автомобиля
    4. Проверка уникальности данных (опционально)
    
    Возвращает созданного сотрудника с присвоенным ID.
    """
    try:
        # 1. Проверяем существование департамента
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
        
        # 2. Проверяем существование автомобиля
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
        
        # 3. Создаем сотрудника
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
                "next_steps": [
                    f"Просмотреть созданного сотрудника: GET /employees/{new_employee[0]}",
                    "Обновить данные сотрудника: PUT /employees/{id}",
                    "Получить список всех сотрудников: GET /employees"
                ]
            },
            "testing_scenarios": {
                "success": "Корректные данные → 201 Created",
                "validation_error": "Неполные/некорректные данные → 422",
                "foreign_key_error": "Несуществующий department_id/car_id → 400",
                "duplicate_data": "Повторное создание одинакового сотрудника"
            }
        }
        
    except HTTPException:
        raise
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
    
    Важные аспекты для тестирования:
    1. Удаление существующего сотрудника → 200 OK
    2. Повторное удаление → 404 Not Found  
    3. Удаление несуществующего ID → 404 Not Found
    4. Проверка каскадного удаления (если настроено)
    """
    try:
        # Сначала получаем информацию о сотруднике
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
        
        # Удаляем связи из employee_series (если есть)
        db.execute(
            text("DELETE FROM employee_series WHERE employee_id = :id"),
            {"id": employee_id}
        )
        
        # Удаляем сотрудника
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
                "cleanup": "Удалены все связи с сериалами"
            },
            "testing_notes": [
                "Проверьте, что сотрудник действительно удален (GET должен вернуть 404)",
                "Попробуйте удалить того же сотрудника повторно (должен быть 404)",
                "Проверьте, что связи в employee_series удалены",
                "Протестируйте удаление несуществующего ID"
            ]
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

# ========== ЭНДПОИНТЫ ДЛЯ ДЕПАРТАМЕНТОВ ==========

@app.get("/departments",
         response_model=List[Dict[str, Any]],
         tags=["🏢 Департаменты"],
         summary="Получить все департаменты",
         description="Список всех департаментов с количеством сотрудников")
async def get_departments(db: Session = Depends(get_db)):
    """
    Получение списка всех департаментов.
    
    Возвращает для каждого департамента:
    - Основную информацию
    - Количество сотрудников
    - Список должностей в департаменте
    
    Идеально для тестирования:
    - Получение списка ресурсов
    - Проверка агрегированных данных
    - Валидация структуры ответа
    """
    try:
        result = db.execute(text("""
            SELECT 
                d.id,
                d.name,
                COUNT(e.id) as employee_count,
                STRING_AGG(DISTINCT e.position, ', ') as positions,
                MIN(e.first_name || ' ' || e.last_name) as sample_employee
            FROM departments d
            LEFT JOIN employees e ON d.id = e.department_id
            GROUP BY d.id, d.name
            ORDER BY employee_count DESC, d.name
        """))
        
        columns = result.keys()
        departments = []
        
        for row in result:
            dept = dict(zip(columns, row))
            # Обрабатываем строку с должностями
            if dept.get('positions'):
                dept['positions'] = [p.strip() for p in dept['positions'].split(',')]
            else:
                dept['positions'] = []
            
            departments.append(dept)
        
        return {
            "data": departments,
            "metadata": {
                "total_departments": len(departments),
                "total_employees": sum(d['employee_count'] for d in departments),
                "departments_with_employees": len([d for d in departments if d['employee_count'] > 0])
            },
            "endpoints": {
                "department_employees": "/departments/{id}/employees",
                "create_department": "POST /departments (не реализовано)",
                "statistics": "/stats"
            }
        }
        
    except SQLAlchemyError as e:
        logger.error(f"Error fetching departments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while fetching departments"
        )

@app.get("/departments/{department_id}/employees",
         response_model=Dict[str, Any],
         tags=["🏢 Департаменты"],
         summary="Получить сотрудников департамента",
         description="Список всех сотрудников конкретного департамента")
async def get_department_employees(
    department_id: int,
    db: Session = Depends(get_db)
):
    """
    Получение сотрудников конкретного департамента.
    
    Идеально для тестирования:
    - Фильтрация по внешнему ключу
    - Обработка несуществующего департамента
    - Проверка пустых результатов
    """
    try:
        # Проверяем существование департамента
        department = db.execute(
            text("SELECT id, name FROM departments WHERE id = :id"),
            {"id": department_id}
        ).fetchone()
        
        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Department not found",
                    "department_id": department_id,
                    "message": f"Департамент с ID {department_id} не найден",
                    "available_departments": "GET /departments"
                }
            )
        
        # Получаем сотрудников департамента
        result = db.execute(text("""
            SELECT 
                e.id,
                e.first_name,
                e.last_name,
                e.position,
                c.brand as car_brand,
                c.model as car_model
            FROM employees e
            LEFT JOIN cars c ON e.car_id = c.id
            WHERE e.department_id = :dept_id
            ORDER BY e.last_name, e.first_name
        """), {"dept_id": department_id})
        
        columns = result.keys()
        employees = [dict(zip(columns, row)) for row in result]
        
        return {
            "department": {
                "id": department[0],
                "name": department[1]
            },
            "employees": employees,
            "metadata": {
                "employee_count": len(employees),
                "retrieved_at": datetime.now().isoformat()
            },
            "related_data": {
                "department_info": f"/departments/{department_id}",
                "all_employees": "/employees",
                "statistics": f"/stats"
            }
        }
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Error fetching department employees: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while fetching department employees"
        )

# ========== ЭНДПОИНТЫ ДЛЯ АВТОМОБИЛЕЙ ==========

@app.get("/cars",
         response_model=List[Dict[str, Any]],
         tags=["🚗 Автомобили"],
         summary="Получить все автомобили",
         description="Список всех автомобилей с фильтрацией по бренду")
async def get_cars(
    brand: Optional[str] = Query(None, description="Фильтр по бренду автомобиля"),
    db: Session = Depends(get_db)
):
    """
    Получение списка автомобилей.
    
    Поддерживает фильтрацию по бренду.
    Возвращает информацию об использовании каждого автомобиля.
    """
    try:
        sql = """
            SELECT 
                c.id,
                c.brand,
                c.model,
                COUNT(e.id) as assigned_count,
                STRING_AGG(e.first_name || ' ' || e.last_name, ', ') as assigned_employees
            FROM cars c
            LEFT JOIN employees e ON c.id = e.car_id
        """
        
        params = {}
        if brand:
            sql += " WHERE LOWER(c.brand) = LOWER(:brand)"
            params["brand"] = brand
        
        sql += " GROUP BY c.id, c.brand, c.model ORDER BY c.brand, c.model"
        
        result = db.execute(text(sql), params)
        columns = result.keys()
        cars = []
        
        for row in result:
            car = dict(zip(columns, row))
            # Обрабатываем список сотрудников
            if car.get('assigned_employees'):
                car['assigned_employees'] = [e.strip() for e in car['assigned_employees'].split(',')]
            else:
                car['assigned_employees'] = []
            
            cars.append(car)
        
        return {
            "data": cars,
            "metadata": {
                "total_cars": len(cars),
                "filter": {"brand": brand} if brand else None,
                "most_popular_brand": max(
                    [(car['brand'], car['assigned_count']) for car in cars],
                    key=lambda x: x[1]
                )[0] if cars else None
            }
        }
        
    except SQLAlchemyError as e:
        logger.error(f"Error fetching cars: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while fetching cars"
        )

# ========== ЭНДПОИНТЫ ДЛЯ СЕРИАЛОВ ==========

@app.get("/series",
         response_model=List[Dict[str, Any]],
         tags=["📺 Сериалы"],
         summary="Получить все сериалы",
         description="Список сериалов с фильтрацией по рейтингу и сортировкой")
async def get_series(
    min_rating: Optional[float] = Query(
        None, 
        ge=0, 
        le=10, 
        description="Минимальный рейтинг (0-10)"
    ),
    max_rating: Optional[float] = Query(
        None,
        ge=0,
        le=10,
        description="Максимальный рейтинг (0-10)"
    ),
    sort_by: str = Query(
        "rating",
        description="Сортировка (rating, title, fans)",
        example="rating"
    ),
    sort_order: str = Query(
        "desc",
        description="Порядок сортировки (asc, desc)",
        example="desc"
    ),
    db: Session = Depends(get_db)
):
    """
    Получение списка сериалов.
    
    Расширенная фильтрация и сортировка:
    - Фильтр по рейтингу (min, max)
    - Сортировка по рейтингу, названию или количеству фанатов
    - Информация о популярности среди сотрудников
    """
    try:
        # Валидация параметров сортировки
        valid_sort_fields = ["rating", "title", "fans"]
        if sort_by not in valid_sort_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid sort field. Valid options: {', '.join(valid_sort_fields)}"
            )
        
        # Строим SQL запрос
        sql = """
            SELECT 
                s.id,
                s.title,
                s.rating,
                COUNT(es.employee_id) as fans_count,
                STRING_AGG(DISTINCT e.first_name || ' ' || e.last_name, ', ') as sample_fans
            FROM series s
            LEFT JOIN employee_series es ON s.id = es.series_id
            LEFT JOIN employees e ON es.employee_id = e.id
        """
        
        params = {}
        conditions = []
        
        # Добавляем фильтры по рейтингу
        if min_rating is not None:
            conditions.append("s.rating >= :min_rating")
            params["min_rating"] = min_rating
        
        if max_rating is not None:
            conditions.append("s.rating <= :max_rating")
            params["max_rating"] = max_rating
        
        # Добавляем условия если есть
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        
        sql += " GROUP BY s.id, s.title, s.rating"
        
        # Добавляем сортировку
        if sort_by == "fans":
            sql += f" ORDER BY fans_count {sort_order.upper()}, s.rating DESC"
        else:
            sql += f" ORDER BY s.{sort_by} {sort_order.upper()}"
        
        result = db.execute(text(sql), params)
        columns = result.keys()
        series_list = []
        
        for row in result:
            series = dict(zip(columns, row))
            # Обрабатываем список фанатов
            if series.get('sample_fans'):
                series['sample_fans'] = [f.strip() for f in series['sample_fans'].split(',')][:3]  # первые 3
            else:
                series['sample_fans'] = []
            
            series_list.append(series)
        
        return {
            "data": series_list,
            "metadata": {
                "total_series": len(series_list),
                "average_rating": round(
                    sum(s['rating'] for s in series_list) / len(series_list), 2
                ) if series_list else 0,
                "most_popular_series": max(
                    series_list, 
                    key=lambda x: x['fans_count']
                )['title'] if series_list else None,
                "filters_applied": {
                    "min_rating": min_rating,
                    "max_rating": max_rating,
                    "sort_by": sort_by,
                    "sort_order": sort_order
                }
            }
        }
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Error fetching series: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while fetching series"
        )

# ========== СЛОЖНЫЕ ЗАПРОСЫ ДЛЯ ОБУЧЕНИЯ ==========

@app.get("/complex/join-example",
         response_model=List[Dict[str, Any]],
         tags=["🔍 Поиск"],
         summary="Пример сложного JOIN запроса",
         description="Демонстрация сложного SQL запроса с несколькими JOIN")
async def complex_join_example(db: Session = Depends(get_db)):
    """
    Пример сложного SQL запроса для обучения.
    
    Показывает:
    - Множественные JOIN между таблицами
    - Агрегатные функции
    - Подзапросы
    - Форматирование данных
    
    Идеально для тестирования сложных ответов API.
    """
    try:
        result = db.execute(text("""
            SELECT 
                e.id as employee_id,
                e.first_name || ' ' || e.last_name as full_name,
                e.position,
                d.name as department,
                c.brand || ' ' || c.model as company_car,
                (
                    SELECT COUNT(*) 
                    FROM employee_series es 
                    WHERE es.employee_id = e.id
                ) as favorite_series_count,
                (
                    SELECT STRING_AGG(s.title, ', ') 
                    FROM employee_series es
                    JOIN series s ON es.series_id = s.id
                    WHERE es.employee_id = e.id
                    ORDER BY s.rating DESC
                    LIMIT 3
                ) as top_3_series,
                (
                    SELECT ROUND(AVG(s.rating), 2)
                    FROM employee_series es
                    JOIN series s ON es.series_id = s.id
                    WHERE es.employee_id = e.id
                ) as avg_series_rating
            FROM employees e
            JOIN departments d ON e.department_id = d.id
            JOIN cars c ON e.car_id = c.id
            ORDER BY e.last_name, e.first_name
            LIMIT 10
        """))
        
        columns = result.keys()
        data = [dict(zip(columns, row)) for row in result]
        
        return {
            "description": "Сотрудники с полной информацией: департамент, автомобиль, любимые сериалы",
            "sql_features": [
                "3 JOIN операции",
                "2 подзапроса с агрегатными функциями",
                "Форматирование строк (CONCAT)",
                "Сортировка и лимит"
            ],
            "data": data,
            "testing_recommendations": [
                "Проверьте, что все поля присутствуют в ответе",
                "Проверьте типы данных (строки, числа, NULL)",
                "Протестируйте граничные значения (LIMIT=0)",
                "Измерьте время ответа для сложного запроса"
            ],
            "educational_value": [
                "Пример реального production запроса",
                "Демонстрация связей между таблицами",
                "Практика тестирования сложных структур данных"
            ]
        }
        
    except SQLAlchemyError as e:
        logger.error(f"Error executing complex join: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while executing complex query"
        )

@app.get("/complex/series-fans/{series_title}",
         response_model=Dict[str, Any],
         tags=["🔍 Поиск"],
         summary="Найти поклонников сериала",
         description="Сотрудники, которые добавили указанный сериал в избранное")
async def series_fans(
    series_title: str,
    db: Session = Depends(get_db)
):
    """
    Поиск сотрудников, которым нравится конкретный сериал.
    
    Демонстрирует:
    - Поиск по тексту (ILIKE для регистронезависимости)
    - JOIN через промежуточную таблицу
    - Фильтрацию по связанным данным
    
    Идеально для тестирования поисковых функций.
    """
    try:
        result = db.execute(text("""
            SELECT 
                e.id,
                e.first_name,
                e.last_name,
                e.position,
                d.name as department,
                c.brand as car_brand,
                c.model as car_model,
                s.rating as series_rating
            FROM employees e
            JOIN departments d ON e.department_id = d.id
            JOIN cars c ON e.car_id = c.id
            JOIN employee_series es ON e.id = es.employee_id
            JOIN series s ON es.series_id = s.id
            WHERE LOWER(s.title) LIKE LOWER(:title)
            ORDER BY e.last_name, e.first_name
        """), {"title": f"%{series_title}%"})
        
        columns = result.keys()
        fans = [dict(zip(columns, row)) for row in result]
        
        if not fans:
            return {
                "series": series_title,
                "fans_count": 0,
                "fans": [],
                "message": f"Сериал '{series_title}' не найден в избранном у сотрудников",
                "suggestions": [
                    "Проверьте название сериала",
                    "Получите список всех сериалов: GET /series",
                    "Используйте частичное совпадение (например: 'теория')"
                ]
            }
        
        # Получаем точное название сериала из первого результата
        exact_title = fans[0].get('series_rating')  # В данном случае rating, но нужен title
        
        return {
            "series": series_title,
            "exact_match": exact_title if exact_title else series_title,
            "fans_count": len(fans),
            "fans": fans,
            "statistics": {
                "departments_represented": len(set(f['department'] for f in fans)),
                "average_series_rating": round(
                    sum(f['series_rating'] for f in fans) / len(fans), 2
                ) if fans else 0
            },
            "search_details": {
                "search_term": series_title,
                "search_type": "partial match (ILIKE)",
                "case_sensitive": False
            }
        }
        
    except SQLAlchemyError as e:
        logger.error(f"Error searching series fans: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while searching series fans"
        )

# ========== ЭНДПОИНТЫ ДЛЯ ТЕСТИРОВАНИЯ ==========

@app.get("/test/error/{error_code}",
         tags=["🧪 Тестирование"],
         summary="Тестирование HTTP ошибок",
         description="Генерация различных HTTP ошибок для обучения тестированию",
         responses={
             200: {"description": "Успешный запрос (для кодов не-ошибок)"},
             400: {"description": "Bad Request"},
             401: {"description": "Unauthorized"},
             403: {"description": "Forbidden"},
             404: {"description": "Not Found"},
             422: {"description": "Validation Error"},
             429: {"description": "Too Many Requests"},
             500: {"description": "Internal Server Error"},
             502: {"description": "Bad Gateway"},
             503: {"description": "Service Unavailable"}
         })
async def test_error_endpoint():
    error_code: int,
    message: Optional[str] = Query(
        None,
        description="Кастомное сообщение об ошибке"
    ),
    sleep: Optional[int] = Query(
        None,
        ge=0,
        le=30,
        description="Искусственная задержка в секундах (0-30)"
    ):
    """
    Эндпоинт для генерации HTTP ошибок.
    
    Поддерживает все основные HTTP коды ошибок.
    Позволяет тестировать:
    - Обработку ошибок клиентом
    - Поведение при разных статус кодах
    - Таймауты и задержки
    - Кастомные сообщения об ошибках
    """
    # Искусственная задержка если указана
    if sleep and sleep > 0:
        time.sleep(sleep)
    
    # Словарь стандартных сообщений об ошибках
    error_messages = {
        400: message or "Bad Request - проверьте параметры запроса",
        401: message or "Unauthorized - требуется аутентификация",
        403: message or "Forbidden - доступ запрещен",
        404: message or "Not Found - запрашиваемый ресурс не найден",
        422: message or "Unprocessable Entity - ошибка валидации данных",
        429: message or "Too Many Requests - превышен лимит запросов",
        500: message or "Internal Server Error - внутренняя ошибка сервера",
        502: message or "Bad Gateway - проблема с прокси-сервером",
        503: message or "Service Unavailable - сервис временно недоступен",
        504: message or "Gateway Timeout - таймаут шлюза"
    }
    
    # Если запрошен код ошибки - выбрасываем исключение
    if error_code in error_messages:
        raise HTTPException(
            status_code=error_code,
            detail={
                "error_code": error_code,
                "error_message": error_messages[error_code],
                "error_type": "TEST_ERROR",
                "generated_at": datetime.now().isoformat(),
                "test_purpose": "Для обучения тестированию HTTP ошибок",
                "testing_notes": [
                    f"Это тестовая ошибка {error_code}",
                    "В реальном API такие ошибки возникают при различных условиях",
                    "Протестируйте обработку этой ошибки в вашем клиенте"
                ]
            },
            headers={
                "X-Error-Test": "true",
                "X-Test-Error-Code": str(error_code),
                "X-Generated-At": datetime.now().isoformat()
            }
        )
    
    # Если код не ошибка - возвращаем успешный ответ
    return {
        "status": "success",
        "code": error_code,
        "message": message or "Это не код ошибки, поэтому запрос успешен",
        "testing_info": {
            "purpose": "Демонстрация успешных кодов ответа",
            "note": f"Код {error_code} не является кодом ошибки",
            "common_success_codes": [200, 201, 204],
            "common_error_codes": list(error_messages.keys())
        }
    }

@app.get("/test/validation",
         tags=["🧪 Тестирование"],
         summary="Тестирование валидации параметров",
         description="Эндпоинт с строгой валидацией параметров для обучения")
async def test_validation(
    string_param: str = Query(
        "default",
        min_length=2,
        max_length=10,
        description="Строковый параметр (2-10 символов)",
        example="test"
    ),
    number_param: int = Query(
        1,
        ge=1,
        le=100,
        description="Числовой параметр (1-100)",
        example=50
    ),
    optional_param: Optional[str] = Query(
        None,
        min_length=1,
        max_length=5,
        description="Опциональный параметр (1-5 символов)",
        example="opt"
    ),
    enum_param: Optional[str] = Query(
        None,
        regex="^(asc|desc|none)$",
        description="Параметр с ограниченными значениями (asc/desc/none)",
        example="asc"
    )
):
    """
    Эндпоинт для тестирования валидации параметров запроса.
    
    Демонстрирует различные типы валидации:
    - Длина строки (min_length, max_length)
    - Диапазон чисел (ge, le)
    - Обязательные и опциональные параметры
    - Регулярные выражения (enum-like)
    
    Идеально для обучения тестированию валидации.
    """
    return {
        "validation_passed": True,
        "parameters_received": {
            "string_param": {
                "value": string_param,
                "length": len(string_param),
                "constraints": "min_length=2, max_length=10"
            },
            "number_param": {
                "value": number_param,
                "constraints": "ge=1, le=100"
            },
            "optional_param": {
                "value": optional_param,
                "was_provided": optional_param is not None,
                "constraints": "optional, min_length=1, max_length=5 if provided"
            },
            "enum_param": {
                "value": enum_param,
                "was_provided": enum_param is not None,
                "constraints": "optional, must be 'asc', 'desc', or 'none' if provided"
            }
        },
        "testing_scenarios": {
            "positive_tests": [
                "Все параметры в допустимых диапазонах",
                "optional_param не указан",
                "enum_param не указан",
                "Граничные значения: string_param длиной 2 и 10",
                "Граничные значения: number_param = 1 и 100"
            ],
            "negative_tests": [
                "string_param длиной 1 (слишком короткий)",
                "string_param длиной 11 (слишком длинный)",
                "number_param = 0 (меньше минимума)",
                "number_param = 101 (больше максимума)",
                "enum_param = 'invalid' (недопустимое значение)",
                "Передача не строки для string_param"
            ],
            "edge_cases": [
                "Пустая строка для string_param",
                "Отрицательное число для number_param",
                "Специальные символы в string_param",
                "Очень длинная строка (превышает max_length)"
            ]
        },
        "educational_value": [
            "Пример валидации параметров в FastAPI",
            "Демонстрация разных типов ограничений",
            "Практика тестирования граничных значений",
            "Понимание кодов ошибок 422 (Validation Error)"
        ]
    }

# ========== ЭНДПОИНТЫ ДЛЯ МОНИТОРИНГА И СТАТИСТИКИ ==========

@app.get("/stats",
         response_model=Dict[str, Any],
         tags=["📊 Мониторинг"],
         summary="Статистика базы данных",
         description="Полная статистика по всем таблицам и данным")
async def get_stats(db: Session = Depends(get_db)):
    """
    Получение полной статистики базы данных.
    
    Собирает информацию:
    - Количество записей в каждой таблице
    - Статистика по департаментам
    - Популярность сериалов
    - Информация об использовании автомобилей
    
    Идеально для мониторинга и тестирования агрегированных данных.
    """
    try:
        stats = {}
        
        # 1. Основная статистика по таблицам
        tables = ["employees", "departments", "cars", "series", "employee_series"]
        table_stats = {}
        
        for table in tables:
            try:
                result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                table_stats[table] = count
            except SQLAlchemyError as e:
                table_stats[table] = f"error: {str(e)}"
                logger.warning(f"Could not get count for table {table}: {e}")
        
        stats["tables"] = table_stats
        
        # 2. Детальная статистика по департаментам
        dept_stats_result = db.execute(text("""
            SELECT 
                d.id,
                d.name,
                COUNT(e.id) as employee_count,
                ROUND(AVG(LENGTH(e.first_name || ' ' || e.last_name)), 2) as avg_name_length,
                STRING_AGG(DISTINCT e.position, '; ') as unique_positions,
                MIN(e.first_name || ' ' || e.last_name) as first_employee,
                MAX(e.first_name || ' ' || e.last_name) as last_employee
            FROM departments d
            LEFT JOIN employees e ON d.id = e.department_id
            GROUP BY d.id, d.name
            ORDER BY employee_count DESC
        """))
        
        dept_stats = []
        for row in dept_stats_result:
            dept = {
                "id": row[0],
                "name": row[1],
                "employee_count": row[2],
                "avg_name_length": float(row[3]) if row[3] else 0,
                "unique_positions": row[4].split('; ') if row[4] else [],
                "first_employee": row[5],
                "last_employee": row[6]
            }
            dept_stats.append(dept)
        
        stats["departments"] = dept_stats
        
        # 3. Статистика популярности сериалов
        series_stats_result = db.execute(text("""
            SELECT 
                s.title,
                s.rating,
                COUNT(es.employee_id) as fans_count,
                ROUND(AVG(s.rating) OVER (), 2) as overall_avg_rating,
                COUNT(es.employee_id) * 100.0 / (SELECT COUNT(DISTINCT employee_id) FROM employee_series) as popularity_percent
            FROM series s
            LEFT JOIN employee_series es ON s.id = es.series_id
            GROUP BY s.id, s.title, s.rating
            ORDER BY fans_count DESC, s.rating DESC
            LIMIT 5
        """))
        
        top_series = []
        for row in series_stats_result:
            series = {
                "title": row[0],
                "rating": float(row[1]),
                "fans_count": row[2],
                "overall_avg_rating": float(row[3]),
                "popularity_percent": round(float(row[4]), 2) if row[4] else 0
            }
            top_series.append(series)
        
        stats["top_series"] = top_series
        
        # 4. Статистика по автомобилям
        car_stats_result = db.execute(text("""
            SELECT 
                c.brand,
                COUNT(DISTINCT c.id) as car_count,
                COUNT(e.id) as assigned_count,
                ROUND(COUNT(e.id) * 100.0 / NULLIF(COUNT(DISTINCT c.id), 0), 2) as usage_percent,
                STRING_AGG(DISTINCT c.model, ', ') as models
            FROM cars c
            LEFT JOIN employees e ON c.id = e.car_id
            GROUP BY c.brand
            ORDER BY assigned_count DESC
        """))
        
        car_stats = []
        for row in car_stats_result:
            car = {
                "brand": row[0],
                "car_count": row[1],
                "assigned_count": row[2],
                "usage_percent": float(row[3]) if row[3] else 0,
                "models": row[4].split(', ') if row[4] else []
            }
            car_stats.append(car)
        
        stats["car_usage"] = car_stats
        
        # 5. Общая статистика API
        api_info = {
            "start_time": app_start_time.isoformat(),
            "uptime_seconds": (datetime.now() - app_start_time).total_seconds(),
            "total_requests": request_count,
            "requests_per_minute": round(request_count / max((datetime.now() - app_start_time).total_seconds() / 60, 1), 2),
            "database_connection": "active",
            "hosting": {
                "provider": "Render.com",
                "plan": "Free Tier",
                "region": "Frankfurt, EU",
                "cold_start_possible": True
            },
            "limits": {
                "concurrent_users": "10-15",
                "rate_limits": "None (for training purposes)",
                "max_response_size": "10MB",
                "timeout": "30 seconds"
            }
        }
        
        return {
            "statistics": stats,
            "api_info": api_info,
            "timestamp": datetime.now().isoformat(),
            "collection_time_ms": 0,  # Можно добавить вычисление времени сбора статистики
            "educational_use": [
                "Мониторинг состояния базы данных",
                "Анализ использования данных",
                "Тестирование агрегированных запросов",
                "Практика работы со сложной статистикой"
            ]
        }
        
    except SQLAlchemyError as e:
        logger.error(f"Error collecting statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while collecting statistics"
        )

@app.get("/db/tables",
         tags=["📊 Мониторинг"],
         summary="Информация о таблицах БД",
         description="Получение метаинформации о всех таблицах базы данных")
async def get_database_tables(db: Session = Depends(get_db)):
    """
    Получение информации о структуре базы данных.
    
    Возвращает:
    - Список всех таблиц
    - Колонки каждой таблицы
    - Типы данных колонок
    - Информацию о первичных ключах
    
    Идеально для изучения структуры БД.
    """
    try:
        inspector = inspect(engine)
        tables_info = []
        
        # Получаем список всех таблиц
        tables = inspector.get_table_names(schema="public")
        
        for table_name in tables:
            # Получаем колонки таблицы
            columns = inspector.get_columns(table_name, schema="public")
            columns_info = []
            
            for column in columns:
                col_info = {
                    "name": column['name'],
                    "type": str(column['type']),
                    "nullable": column.get('nullable', True),
                    "default": str(column.get('default', 'None')),
                    "primary_key": column.get('primary_key', False)
                }
                columns_info.append(col_info)
            
            # Получаем первичные ключи
            primary_keys = inspector.get_pk_constraint(table_name, schema="public")
            
            # Получаем внешние ключи
            foreign_keys = inspector.get_foreign_keys(table_name, schema="public")
            
            # Получаем индексы
            indexes = inspector.get_indexes(table_name, schema="public")
            
            table_info = {
                "name": table_name,
                "columns": columns_info,
                "primary_key": primary_keys.get('constrained_columns', []),
                "foreign_keys": [
                    {
                        "columns": fk['constrained_columns'],
                        "referenced_table": fk['referred_table'],
                        "referenced_columns": fk['referred_columns']
                    }
                    for fk in foreign_keys
                ],
                "indexes": [
                    {
                        "name": idx['name'],
                        "columns": idx['column_names'],
                        "unique": idx.get('unique', False)
                    }
                    for idx in indexes
                ]
            }
            
            tables_info.append(table_info)
        
        return {
            "database": {
                "name": "WORK2025",
                "schema": "public",
                "total_tables": len(tables_info)
            },
            "tables": tables_info,
            "educational_value": [
                "Изучение структуры базы данных",
                "Понимание связей между таблицами",
                "Анализ типов данных и ограничений",
                "Подготовка тестовых данных"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting database tables info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving database metadata"
        )

# ========== ЭНДПОИНТЫ ДЛЯ ОБУЧЕНИЯ ==========

@app.get("/learning/tasks",
         tags=["🎓 Обучение"],
         summary="Задания для обучения тестировщиков",
         description="Полный план обучения тестированию REST API")
async def get_learning_tasks():
    """
    Полный учебный план для тестировщиков.
    
    Содержит:
    - Поэтапный план обучения
    - Конкретные задания для каждого этапа
    - Тест-кейсы для практики
    - Критерии оценки
    
    Идеально для самостоятельного обучения.
    """
    return {
        "course": "Практическое тестирование REST API",
        "description": "Комплексный курс по тестированию REST API на реальном примере",
        "duration": "3 дня (15-20 часов)",
        "prerequisites": [
            "Базовое понимание HTTP протокола",
            "Знакомство с JSON форматом",
            "Установленный инструмент для тестирования API (Postman, Insomnia, curl)"
        ],
        "learning_objectives": [
            "Научиться тестировать все HTTP методы",
            "Освоить работу со статус кодами",
            "Практиковать тестирование валидации",
            "Научиться тестировать ошибки и граничные случаи",
            "Освоить интеграционное тестирование"
        ],
        "daily_plan": {
            "day_1": {
                "topic": "Основы REST API и HTTP методов",
                "duration": "5-6 часов",
                "modules": [
                    {
                        "module": "Знакомство с API",
                        "duration": "1 час",
                        "tasks": [
                            "Изучите Swagger UI документацию",
                            "Протестируйте корневой эндпоинт GET /",
                            "Проверьте health check GET /health",
                            "Изучите статистику GET /stats"
                        ],
                        "learning_outcomes": [
                            "Понимание структуры API",
                            "Умение читать документацию",
                            "Навык проверки работоспособности"
                        ]
                    },
                    {
                        "module": "Тестирование GET запросов",
                        "duration": "2 часа",
                        "tasks": [
                            "Протестируйте GET /employees (проверьте статус 200)",
                            "Изучите пагинацию (параметры page, per_page)",
                            "Протестируйте фильтрацию (department_id, search)",
                            "Проверьте сортировку (sort_by, sort_order)",
                            "Протестируйте GET /departments, /cars, /series",
                            "Проверьте граничные значения параметров"
                        ],
                        "test_cases": [
                            "positive: все параметры в допустимых диапазонах",
                            "negative: page=0, per_page=101, department_id=999",
                            "boundary: per_page=1, per_page=100, page=9999"
                        ]
                    },
                    {
                        "module": "Тестирование ошибок",
                        "duration": "2 часа",
                        "tasks": [
                            "Протестируйте все коды ошибок через /test/error/{code}",
                            "Проверьте GET несуществующего сотрудника",
                            "Тестируйте невалидные ID (0, -1, строка)",
                            "Проверьте кастомные сообщения об ошибках",
                            "Протестируйте таймауты (параметр sleep)"
                        ],
                        "expected_errors": [
                            "400 Bad Request",
                            "404 Not Found",
                            "422 Validation Error",
                            "500 Internal Server Error"
                        ]
                    }
                ],
                "homework": "Написать 20 тест-кейсов для изученных эндпоинтов"
            },
            "day_2": {
                "topic": "Модифицирующие операции и валидация",
                "duration": "6-7 часов",
                "modules": [
                    {
                        "module": "Создание ресурсов (POST)",
                        "duration": "3 часа",
                        "tasks": [
                            "Создайте нового сотрудника через POST /employees",
                            "Протестируйте валидацию полей сотрудника",
                            "Проверьте обработку несуществующих department_id/car_id",
                            "Тестируйте обязательные и опциональные поля",
                            "Проверьте уникальность данных (если применимо)"
                        ],
                        "validation_tests": [
                            "Корректные данные → 201 Created",
                            "Неполные данные → 422 Validation Error",
                            "Несуществующие foreign keys → 400 Bad Request",
                            "Некорректные типы данных → 422"
                        ]
                    },
                    {
                        "module": "Удаление ресурсов (DELETE)",
                        "duration": "2 часа",
                        "tasks": [
                            "Удалите созданного сотрудника",
                            "Проверьте повторное удаление (должен быть 404)",
                            "Протестируйте удаление несуществующего ресурса",
                            "Проверьте каскадное удаление (если настроено)"
                        ],
                        "test_scenarios": [
                            "Удаление существующего ресурса → 200",
                            "Повторное удаление → 404",
                            "Удаление несуществующего → 404",
                            "Удаление с невалидным ID → 422"
                        ]
                    },
                    {
                        "module": "Тестирование валидации параметров",
                        "duration": "1-2 часа",
                        "tasks": [
                            "Протестируйте /test/validation со всеми параметрами",
                            "Проверьте граничные значения строковых параметров",
                            "Тестируйте числовые диапазоны",
                            "Проверьте регулярные выражения (enum_param)",
                            "Протестируйте опциональные параметры"
                        ]
                    }
                ],
                "homework": "Создать коллекцию Postman с 30+ запросами"
            },
            "day_3": {
                "topic": "Продвинутое тестирование",
                "duration": "4-6 часов",
                "modules": [
                    {
                        "module": "Интеграционное тестирование",
                        "duration": "2 часа",
                        "tasks": [
                            "Протестируйте сложные запросы (/complex/join-example)",
                            "Проверьте поиск поклонников сериалов",
                            "Тестируйте связи между таблицами",
                            "Проверьте целостность данных после операций",
                            "Измерьте время ответа для сложных запросов"
                        ],
                        "integration_tests": [
                            "Проверка связей employees-departments-cars",
                            "Тестирование many-to-many через employee_series",
                            "Валидация агрегированных данных"
                        ]
                    },
                    {
                        "module": "Нагрузочное тестирование",
                        "duration": "1-2 часа",
                        "tasks": [
                            "Создайте скрипт для последовательных запросов",
                            "Протестируйте 10+ последовательных вызовов GET /employees",
                            "Проверьте параллельные запросы (имитация 3 пользователей)",
                            "Измерьте производительность API под нагрузкой"
                        ],
                        "tools": ["Postman Runner", "Python scripts", "Apache Bench"]
                    },
                    {
                        "module": "Документирование и отчетность",
                        "duration": "1-2 часа",
                        "tasks": [
                            "Создайте баг-репорты для найденных проблем",
                            "Напишите итоговый отчет по тестированию",
                            "Подготовьте рекомендации по улучшению API",
                            "Создайте чек-лист для регрессионного тестирования"
                        ],
                        "deliverables": [
                            "Баг-репорты (если баги найдены)",
                            "Отчет о тестировании",
                            "Чек-лист регрессионных тестов",
                            "Рекомендации по улучшению"
                        ]
                    }
                ],
                "final_project": "Полный цикл тестирования одного модуля API"
            }
        },
        "assessment_criteria": {
            "technical_skills": [
                "Знание HTTP методов и статус кодов",
                "Умение тестировать валидацию",
                "Навыки работы с инструментами тестирования"
            ],
            "testing_skills": [
                "Качество тест-кейсов",
                "Умение находить граничные случаи",
                "Навыки документирования багов"
            ],
            "soft_skills": [
                "Аналитическое мышление",
                "Внимательность к деталям",
                "Умение структурировать информацию"
            ]
        },
        "grading_scale": {
            "excellent": "Выполнено 90-100% заданий, качественная документация",
            "good": "Выполнено 75-89% заданий, хорошее понимание концепций",
            "satisfactory": "Выполнено 60-74% заданий, базовое понимание",
            "needs_improvement": "Менее 60% заданий"
        },
        "resources": {
            "tools": [
                {"name": "Postman", "url": "https://www.postman.com/"},
                {"name": "Insomnia", "url": "https://insomnia.rest/"},
                {"name": "curl", "url": "https://curl.se/"}
            ],
            "documentation": [
                {"name": "Swagger UI", "url": "/docs"},
                {"name": "ReDoc", "url": "/redoc"},
                {"name": "OpenAPI Spec", "url": "/openapi.json"}
            ],
            "learning_materials": [
                {"name": "HTTP Status Codes", "url": "https://httpstatuses.com/"},
                {"name": "REST API Tutorial", "url": "https://restfulapi.net/"},
                {"name": "API Testing Guide", "url": "https://www.softwaretestinghelp.com/api-testing/"}
            ]
        },
        "support": {
            "technical_issues": "Используйте Swagger UI для тестирования и изучения",
            "learning_questions": "Анализируйте ответы API и документацию",
            "note": "Это учебный проект - некоторые функции могут быть ограничены"
        }
    }

# ========== ЭНДПОИНТЫ ДЛЯ АДМИНИСТРИРОВАНИЯ ==========

@app.get("/admin/clear-test-data",
         tags=["🔧 Администрирование"],
         summary="Очистка тестовых данных",
         description="Удаление данных, созданных во время тестирования (для обучения)")
async def clear_test_data(
    confirm: bool = Query(False, description="Подтверждение удаления данных"),
    db: Session = Depends(get_db)
):
    """
    Очистка тестовых данных.
    
    Внимание: Удаляет только сотрудников, созданных через API
    с определенными именами (Test, Тест, etc).
    
    Только для учебных целей!
    """
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Confirmation required",
                "message": "Для удаления тестовых данных необходимо подтверждение",
                "usage": "Добавьте параметр ?confirm=true к URL"
            }
        )
    
    try:
        # Удаляем тестовых сотрудников (по имени)
        result = db.execute(text("""
            DELETE FROM employees 
            WHERE first_name IN ('Test', 'Тест', 'TestUser', 'Тестовый')
            OR first_name LIKE 'Test%'
            OR first_name LIKE 'Тест%'
            RETURNING COUNT(*)
        """))
        
        deleted_count = result.scalar() or 0
        db.commit()
        
        return {
            "status": "success",
            "message": f"Удалено {deleted_count} тестовых записей",
            "deleted_count": deleted_count,
            "criteria": [
                "first_name IN ('Test', 'Тест', 'TestUser', 'Тестовый')",
                "first_name LIKE 'Test%'",
                "first_name LIKE 'Тест%'"
            ],
            "note": "Удалены только тестовые данные. Оригинальные данные сохранены."
        }
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error clearing test data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while clearing test data"
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
    
    # Добавляем дополнительные заголовки если есть
    headers = dict(exc.headers) if exc.headers else {}
    
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
            "note": "This error has been logged for investigation"
        },
        "path": request.url.path,
        "method": request.method,
        "timestamp": datetime.now().isoformat()
    }
    
    # В production не показываем детали ошибки
    if os.getenv("ENVIRONMENT") == "production":
        error_response["detail"]["message"] = "Internal server error"
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response
    )

# ========== ЗАПУСК СЕРВЕРА ==========

if __name__ == "__main__":
    import uvicorn
    
    # Выводим информацию о запуске
    print("=" * 70)
    print("🏢 COMPANYDB API ДЛЯ ОБУЧЕНИЯ ТЕСТИРОВЩИКОВ")
    print("=" * 70)
    print(f"📖 Swagger UI: http://localhost:{PORT}/docs")
    print(f"📚 ReDoc:      http://localhost:{PORT}/redoc")
    print(f"🔧 Health:     http://localhost:{PORT}/health")
    print(f"📊 Stats:      http://localhost:{PORT}/stats")
    print(f"🎓 Learning:   http://localhost:{PORT}/learning/tasks")
    print("-" * 70)
    print(f"👥 Поддержка:  10-15 одновременных пользователей")
    print(f"🗄️  Database:   PostgreSQL на Reg.ru")
    print(f"🌐 Hosting:    Render.com (Free Tier)")
    print(f"⚡ Port:       {PORT}")
    print("=" * 70)
    
    # Запускаем сервер
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level="info",
        access_log=True,
        reload=False  # На продакшене лучше False
    )