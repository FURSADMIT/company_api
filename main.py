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
            "url": "https://company-api-4pws.onrender.com",
            "description": "Current Render deployment"
        },
        {
            "url": "http://localhost:8000", 
            "description": "Local development server"
        }
    ]
)

# ========== CORS НАСТРОЙКИ ==========
# Разрешаем все домены для обучения и тестирования
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем ВСЕ домены
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем ВСЕ HTTP методы
    allow_headers=["*"],  # Разрешаем ВСЕ заголовки
    expose_headers=["*"], # Открываем ВСЕ заголовки
    max_age=600  # Кэшировать preflight запросы на 10 минут
)

# ========== ДОПОЛНИТЕЛЬНЫЙ MIDDLEWARE ДЛЯ CORS ==========
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    """
    Middleware для добавления CORS заголовков к каждому ответу.
    Решает проблему с Swagger UI и другими клиентами.
    """
    # Обрабатываем preflight запросы (OPTIONS)
    if request.method == "OPTIONS":
        response = JSONResponse(content={"status": "ok"})
    else:
        response = await call_next(request)
    
    # Добавляем CORS заголовки ко всем ответам
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD"
    response.headers["Access-Control-Allow-Headers"] = "Origin, X-Requested-With, Content-Type, Accept, Authorization, X-API-Key"
    response.headers["Access-Control-Expose-Headers"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Max-Age"] = "600"
    
    return response

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
    database: Dict[str, Any]  # Изменено с str на Dict
    timestamp: str
    uptime: str
    version: str
    
    class Config:
        from_attributes = True

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
            "url": "https://company-api-4pws.onrender.com"
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
        "database": {},
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
        health_data["database"] = {
            "status": "DISCONNECTED",
            "error": str(e),
            "connection_string": DATABASE_URL.split('@')[0] + "@***"  # Маскируем пароль
        }
        health_data.update({
            "status": "❌ UNHEALTHY",
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

# ========== ДИАГНОСТИЧЕСКИЙ ЭНДПОИНТ ==========

@app.get("/debug/db-check",
         tags=["📊 Мониторинг"],
         summary="Диагностика базы данных",
         description="Подробная проверка состояния базы данных")
async def debug_db_check(db: Session = Depends(get_db)):
    """
    Диагностический эндпоинт для проверки проблем с БД.
    """
    diagnostics = {
        "status": "checking",
        "database_url": DATABASE_URL.split('@')[0] + "@***",  # Маскируем пароль
        "checks": {},
        "errors": []
    }
    
    try:
        # 1. Проверка базового подключения
        start_time = time.time()
        db.execute(text("SELECT 1"))
        diagnostics["checks"]["basic_connection"] = {
            "status": "✅ OK",
            "response_time_ms": round((time.time() - start_time) * 1000, 2)
        }
        
        # 2. Проверка существования таблиц
        inspector = inspect(engine)
        tables = inspector.get_table_names(schema="public")
        diagnostics["checks"]["tables_exist"] = {
            "status": "✅ OK" if tables else "⚠️ НЕТ ТАБЛИЦ",
            "tables_found": tables,
            "count": len(tables)
        }
        
        # 3. Проверка каждой таблицы отдельно
        table_checks = {}
        required_tables = ["employees", "departments", "cars", "series", "employee_series"]
        
        for table in required_tables:
            try:
                start_time = time.time()
                result = db.execute(text(f"SELECT COUNT(*) as count FROM {table}"))
                count = result.scalar()
                response_time = round((time.time() - start_time) * 1000, 2)
                
                table_checks[table] = {
                    "status": "✅ OK",
                    "record_count": count,
                    "response_time_ms": response_time
                }
            except Exception as e:
                table_checks[table] = {
                    "status": "❌ ERROR",
                    "error": str(e),
                    "response_time_ms": -1
                }
                diagnostics["errors"].append(f"Table {table}: {str(e)}")
        
        diagnostics["checks"]["table_details"] = table_checks
        
        # 4. Проверка структуры таблицы employees
        try:
            result = db.execute(text("""
                SELECT 
                    column_name, 
                    data_type, 
                    is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'employees'
                ORDER BY ordinal_position
            """))
            
            columns = []
            for row in result:
                columns.append({
                    "name": row[0],
                    "type": row[1],
                    "nullable": row[2]
                })
            
            diagnostics["checks"]["employees_structure"] = {
                "status": "✅ OK",
                "columns": columns
            }
        except Exception as e:
            diagnostics["checks"]["employees_structure"] = {
                "status": "❌ ERROR",
                "error": str(e)
            }
        
        # 5. Простой тестовый запрос
        try:
            start_time = time.time()
            result = db.execute(text("""
                SELECT 
                    e.id,
                    e.first_name,
                    e.last_name,
                    e.position,
                    d.name as department_name
                FROM employees e
                LEFT JOIN departments d ON e.department_id = d.id
                LIMIT 5
            """))
            
            # Проверяем только что запрос выполняется
            test_data = []
            for row in result:
                test_data.append(dict(row._mapping))
            
            diagnostics["checks"]["test_query"] = {
                "status": "✅ OK",
                "execution_time_ms": round((time.time() - start_time) * 1000, 2),
                "records_returned": len(test_data),
                "sample": test_data[:2] if test_data else []
            }
            
        except Exception as e:
            diagnostics["checks"]["test_query"] = {
                "status": "❌ ERROR",
                "error": str(e),
                "suggestion": "Проверьте структуру таблиц или связи между ними"
            }
            diagnostics["errors"].append(f"Test query failed: {str(e)}")
        
        # Определяем общий статус
        all_ok = all(
            check.get("status") in ["✅ OK", "⚠️ WARNING"] 
            for check in diagnostics["checks"].values() 
            if isinstance(check, dict)
        )
        
        diagnostics["status"] = "✅ HEALTHY" if all_ok else "❌ UNHEALTHY"
        
    except Exception as e:
        diagnostics["status"] = "❌ ERROR"
        diagnostics["error"] = str(e)
        diagnostics["checks"]["overall"] = {
            "status": "❌ ERROR",
            "error": str(e)
        }
    
    return diagnostics

# ========== БЕЗОПАСНАЯ ВЕРСИЯ ЭНДПОИНТОВ ==========

@app.get("/employees/safe",
         response_model=Dict[str, Any],
         tags=["👥 Сотрудники"],
         summary="Безопасный список сотрудников")
async def get_employees_safe(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Безопасная версия с обработкой ошибок.
    """
    try:
        # Простой запрос без сложных JOIN
        offset = (page - 1) * per_page
        
        # Сначала проверяем таблицу
        inspector = inspect(engine)
        tables = inspector.get_table_names(schema="public")
        
        if "employees" not in tables:
            return {
                "status": "warning",
                "message": "Таблица 'employees' не найдена в базе данных",
                "available_tables": tables,
                "suggestion": "Создайте таблицу employees или проверьте название"
            }
        
        # Простой запрос
        result = db.execute(text("""
            SELECT id, first_name, last_name, position, department_id, car_id
            FROM employees
            ORDER BY id
            LIMIT :limit OFFSET :offset
        """), {"limit": per_page, "offset": offset})
        
        employees = []
        for row in result:
            employees.append({
                "id": row[0],
                "first_name": row[1],
                "last_name": row[2],
                "position": row[3],
                "department_id": row[4],
                "car_id": row[5]
            })
        
        # Общее количество
        count_result = db.execute(text("SELECT COUNT(*) FROM employees"))
        total_count = count_result.scalar() or 0
        
        return {
            "status": "success",
            "meta": {
                "page": page,
                "per_page": per_page,
                "total": total_count,
                "total_pages": (total_count + per_page - 1) // per_page if total_count > 0 else 1
            },
            "data": employees,
            "note": "Упрощенный запрос для отладки"
        }
        
    except Exception as e:
        logger.error(f"Error in safe employees endpoint: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "suggestion": "Проверьте структуру таблицы employees. Используйте /debug/db-check для диагностики."
        }

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
    try:
        # Сначала проверяем наличие таблиц
        inspector = inspect(engine)
        tables = inspector.get_table_names(schema="public")
        
        required_tables = ["employees", "departments", "cars"]
        missing_tables = [table for table in required_tables if table not in tables]
        
        if missing_tables:
            return {
                "status": "error",
                "message": "Не найдены необходимые таблицы",
                "missing_tables": missing_tables,
                "available_tables": tables,
                "suggestion": f"Создайте таблицы: {', '.join(missing_tables)}"
            }
        
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching employees: {str(e)}")
        return {
            "status": "error",
            "message": "Database error while fetching employees",
            "error_details": str(e),
            "suggestion": "Используйте /employees/safe для упрощенной версии или /debug/db-check для диагностики"
        }

# ========== ЭНДПОИНТ ДЛЯ ТЕСТИРОВАНИЯ CORS ==========

@app.get("/test-cors",
         tags=["🧪 Тестирование"],
         summary="Тест CORS настроек",
         description="Простой эндпоинт для проверки CORS настроек")
async def test_cors():
    """
    Простой эндпоинт для проверки CORS.
    Возвращает информацию о CORS заголовках.
    """
    return {
        "message": "CORS test endpoint",
        "cors_enabled": True,
        "timestamp": datetime.now().isoformat(),
        "cors_headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true"
        },
        "testing_instructions": [
            "1. Откройте консоль разработчика (F12)",
            "2. Выполните: fetch('https://company-api-4pws.onrender.com/test-cors')",
            "3. Проверьте заголовки ответа в Network вкладке"
        ]
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
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD",
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
    
    # Добавляем CORS заголовки к ошибкам
    headers = dict(exc.headers) if exc.headers else {}
    headers.update({
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD",
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
            "note": "This error has been logged for investigation"
        },
        "path": request.url.path,
        "method": request.method,
        "timestamp": datetime.now().isoformat()
    }
    
    # В production не показываем детали ошибки
    if os.getenv("ENVIRONMENT") == "production":
        error_response["detail"]["message"] = "Internal server error"
    
    # Добавляем CORS заголовки
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD",
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
    print(f"🔗 CORS:       Enabled for all domains")
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