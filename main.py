from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, Field
from typing import List, Optional
import os
from datetime import datetime
import logging

# ========== КОНФИГУРАЦИЯ ==========
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="🚀 CompanyDB API для обучения тестировщиков",
    description="""## Полное REST API для практики тестирования
    
### 📚 Возможности:
- **Swagger UI** - интерактивная документация
- **PostgreSQL** - реальная база данных
- **10+ эндпоинтов** - для комплексного обучения
- **Готовые тест-кейсы** - для самостоятельной работы
    
### 🎯 Для кого:
- Начинающие тестировщики
- Студенты IT-курсов
- Разработчики, изучающие API
    
### 🔗 База данных:
- PostgreSQL на Reg.ru
- 5 таблиц с реальными данными
- Связи между таблицами
""",
    version="1.0.0",
    contact={
        "name": "Для обучения",
        "url": "https://render.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "👥 Сотрудники",
            "description": "CRUD операции с сотрудниками"
        },
        {
            "name": "🏢 Департаменты",
            "description": "Работа с отделами компании"
        },
        {
            "name": "🚗 Автомобили",
            "description": "Данные об автомобилях сотрудников"
        },
        {
            "name": "📺 Сериалы",
            "description": "Любимые сериалы сотрудников"
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
        }
    ]
)

# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== БАЗА ДАННЫХ ==========
# Автоматическое определение порта для Render
PORT = int(os.getenv("PORT", 8000))

# Строка подключения к вашему PostgreSQL на Reg.ru
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user1:Qa_2025!@79.174.88.202:15539/WORK2025"
)

# Оптимизированный движок для облачного хостинга
engine = create_engine(
    DATABASE_URL,
    pool_size=5,           # Для 10+ пользователей
    max_overflow=10,       # Максимум соединений
    pool_recycle=300,      # Переподключение каждые 5 минут
    pool_pre_ping=True,    # Проверка соединения
    echo=False             # Отключить логи SQL в продакшене
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Зависимость для БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ========== МОДЕЛИ PYDANTIC ==========
class EmployeeCreate(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=50, example="Иван")
    last_name: str = Field(..., min_length=2, max_length=50, example="Иванов")
    position: str = Field(..., max_length=50, example="Тестировщик")
    department_id: int = Field(..., gt=0, example=1, description="ID департамента")
    car_id: int = Field(..., gt=0, example=1, description="ID автомобиля")

    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "Алексей",
                "last_name": "Петров",
                "position": "QA Engineer",
                "department_id": 1,
                "car_id": 3
            }
        }

class QueryRequest(BaseModel):
    sql: str = Field(
        ...,
        example="SELECT * FROM employees LIMIT 5",
        description="SQL запрос (разрешены только SELECT)"
    )

# ========== ЭНДПОИНТЫ ==========

@app.get("/", tags=["📊 Мониторинг"])
async def root():
    """Корневая страница API с информацией для тестировщиков"""
    return {
        "application": "CompanyDB API",
        "version": "1.0.0",
        "status": "🚀 Активно",
        "hosting": "Render.com (бесплатный тариф)",
        "database": "PostgreSQL на Reg.ru",
        "purpose": "Обучение тестированию REST API",
        
        "features": [
            "✅ Автоматическая документация Swagger UI",
            "✅ Поддержка 10+ одновременных пользователей",
            "✅ Реальная PostgreSQL база данных",
            "✅ Готовые тест-кейсы для обучения",
            "✅ Примеры ошибок для тестирования"
        ],
        
        "quick_start": [
            "1. Откройте Swagger UI: /docs",
            "2. Проверьте здоровье системы: /health",
            "3. Получите список сотрудников: /employees",
            "4. Протестируйте ошибки: /test/error/404"
        ],
        
        "learning_path": {
            "day_1": "Базовые HTTP методы (GET, POST, PUT, DELETE)",
            "day_2": "Параметры запросов и валидация",
            "day_3": "Тестирование ошибок и граничных значений",
            "day_4": "Интеграционное тестирование"
        },
        
        "useful_links": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "health_check": "/health",
            "statistics": "/stats",
            "learning_tasks": "/learning/tasks"
        }
    }

@app.get("/health", tags=["📊 Мониторинг"])
async def health_check(db: Session = Depends(get_db)):
    """Полная проверка здоровья системы"""
    health_data = {
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("RENDER", "development"),
        "service": "company-api",
    }
    
    try:
        # Проверка базы данных
        start_time = datetime.now()
        db.execute(text("SELECT 1"))
        db_response_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Получение статистики
        employees_count = db.execute(text("SELECT COUNT(*) FROM employees")).scalar()
        departments_count = db.execute(text("SELECT COUNT(*) FROM departments")).scalar()
        
        health_data.update({
            "status": "✅ HEALTHY",
            "components": {
                "database": {
                    "status": "CONNECTED",
                    "response_time_ms": round(db_response_time, 2),
                    "tables_accessible": True,
                    "statistics": {
                        "employees": employees_count,
                        "departments": departments_count
                    }
                },
                "api": {
                    "status": "RUNNING",
                    "port": PORT,
                    "concurrent_users_supported": 15
                }
            },
            "hosting": {
                "provider": "Render.com",
                "plan": "Free Tier",
                "uptime": "24/7 (с холодным стартом)"
            }
        })
        
        return health_data
        
    except Exception as e:
        health_data.update({
            "status": "❌ UNHEALTHY",
            "error": str(e),
            "components": {
                "database": {"status": "DISCONNECTED", "error": str(e)},
                "api": {"status": "RUNNING", "port": PORT}
            }
        })
        return health_data

# 👥 СОТРУДНИКИ
@app.get("/employees", tags=["👥 Сотрудники"])
async def get_employees(
    page: int = Query(1, ge=1, description="Номер страницы (начиная с 1)"),
    per_page: int = Query(20, ge=1, le=100, description="Количество записей на странице (1-100)"),
    department_id: Optional[int] = Query(None, description="Фильтр по ID департамента"),
    db: Session = Depends(get_db)
):
    """
    Получить список сотрудников с пагинацией и фильтрацией.
    
    ### Примеры использования:
    - `GET /employees` - все сотрудники, страница 1
    - `GET /employees?page=2&per_page=10` - вторая страница, 10 записей
    - `GET /employees?department_id=1` - сотрудники IT отдела
    """
    offset = (page - 1) * per_page
    
    # Базовый запрос
    sql = """
        SELECT e.*, d.name as department_name 
        FROM employees e
        LEFT JOIN departments d ON e.department_id = d.id
    """
    params = {"limit": per_page, "offset": offset}
    
    # Добавляем фильтр если есть
    if department_id:
        sql += " WHERE e.department_id = :dept_id"
        params["dept_id"] = department_id
    
    sql += " ORDER BY e.id LIMIT :limit OFFSET :offset"
    
    result = db.execute(text(sql), params)
    columns = result.keys()
    employees = [dict(zip(columns, row)) for row in result]
    
    # Общее количество для пагинации
    count_sql = "SELECT COUNT(*) FROM employees"
    if department_id:
        count_sql += " WHERE department_id = :dept_id"
    
    total = db.execute(text(count_sql), {"dept_id": department_id} if department_id else {}).scalar()
    
    return {
        "meta": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page if total > 0 else 1,
            "has_next": page * per_page < total,
            "has_prev": page > 1
        },
        "data": employees,
        "testing_notes": [
            "✅ Проверьте пагинацию: page=1000, per_page=0, per_page=101",
            "✅ Проверьте фильтрацию: department_id=999 (несуществующий)",
            "✅ Проверьте структуру ответа: meta + data",
            "✅ Проверьте граничные значения"
        ]
    }

@app.get("/employees/{employee_id}", tags=["👥 Сотрудники"])
async def get_employee(
    employee_id: int = Query(..., ge=1, description="ID сотрудника"),
    db: Session = Depends(get_db)
):
    """
    Получить подробную информацию о сотруднике.
    
    ### Тест-кейсы:
    1. **Валидный ID** -> 200 OK с данными сотрудника
    2. **Несуществующий ID** -> 404 Not Found
    3. **Некорректный ID** -> 422 Validation Error
    """
    result = db.execute(text("""
        SELECT 
            e.*,
            d.name as department_name,
            c.brand as car_brand,
            c.model as car_model,
            (
                SELECT json_agg(json_build_object('id', s.id, 'title', s.title, 'rating', s.rating))
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
            detail=f"Сотрудник с ID {employee_id} не найден"
        )
    
    columns = result.keys()
    return dict(zip(columns, employee))

@app.post("/employees",
          status_code=status.HTTP_201_CREATED,
          tags=["👥 Сотрудники"])
async def create_employee(
    employee: EmployeeCreate,
    db: Session = Depends(get_db)
):
    """
    Создать нового сотрудника.
    
    ### Пример тела запроса:
    ```json
    {
        "first_name": "Алексей",
        "last_name": "Петров",
        "position": "QA Engineer",
        "department_id": 1,
        "car_id": 3
    }
    ```
    """
    # Проверка существования департамента
    dept_exists = db.execute(
        text("SELECT 1 FROM departments WHERE id = :id"),
        {"id": employee.department_id}
    ).fetchone()
    
    if not dept_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Департамент с ID {employee.department_id} не существует"
        )
    
    # Проверка существования автомобиля
    car_exists = db.execute(
        text("SELECT 1 FROM cars WHERE id = :id"),
        {"id": employee.car_id}
    ).fetchone()
    
    if not car_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Автомобиль с ID {employee.car_id} не существует"
        )
    
    # Создание сотрудника
    result = db.execute(text("""
        INSERT INTO employees 
        (first_name, last_name, position, department_id, car_id)
        VALUES 
        (:first_name, :last_name, :position, :department_id, :car_id)
        RETURNING id, first_name, last_name, position, department_id, car_id
    """), employee.dict())
    
    db.commit()
    
    new_employee = result.fetchone()
    columns = result.keys()
    
    return {
        "status": "success",
        "message": "Сотрудник успешно создан",
        "data": dict(zip(columns, new_employee)),
        "created_at": datetime.now().isoformat(),
        "next_steps": [
            "Проверьте создание через GET /employees/{id}",
            "Протестируйте дублирование данных",
            "Проверьте валидацию полей"
        ]
    }

@app.delete("/employees/{employee_id}", tags=["👥 Сотрудники"])
async def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db)
):
    """
    Удалить сотрудника.
    
    ### Важные моменты для тестирования:
    - Удаление существующего сотрудника → 200
    - Повторное удаление → 404
    - Удаление несуществующего → 404
    """
    # Получаем информацию о сотруднике перед удалением
    employee_info = db.execute(
        text("SELECT first_name, last_name FROM employees WHERE id = :id"),
        {"id": employee_id}
    ).fetchone()
    
    if not employee_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Сотрудник с ID {employee_id} не найден"
        )
    
    # Удаляем сотрудника
    db.execute(
        text("DELETE FROM employees WHERE id = :id"),
        {"id": employee_id}
    )
    db.commit()
    
    return {
        "status": "success",
        "message": "Сотрудник удален",
        "deleted_employee": {
            "id": employee_id,
            "name": f"{employee_info[0]} {employee_info[1]}"
        },
        "timestamp": datetime.now().isoformat(),
        "testing_scenario": "Попробуйте удалить этого же сотрудника повторно"
    }

# 🏢 ДЕПАРТАМЕНТЫ
@app.get("/departments", tags=["🏢 Департаменты"])
async def get_departments(db: Session = Depends(get_db)):
    """Получить все департаменты с количеством сотрудников"""
    result = db.execute(text("""
        SELECT 
            d.*,
            COUNT(e.id) as employee_count,
            STRING_AGG(DISTINCT e.position, ', ') as positions
        FROM departments d
        LEFT JOIN employees e ON d.id = e.department_id
        GROUP BY d.id, d.name
        ORDER BY d.id
    """))
    
    columns = result.keys()
    return [dict(zip(columns, row)) for row in result]

# 🚗 АВТОМОБИЛИ
@app.get("/cars", tags=["🚗 Автомобили"])
async def get_cars(db: Session = Depends(get_db)):
    """Получить все автомобили"""
    result = db.execute(text("SELECT * FROM cars ORDER BY brand, model"))
    columns = result.keys()
    return [dict(zip(columns, row)) for row in result]

# 📺 СЕРИАЛЫ
@app.get("/series", tags=["📺 Сериалы"])
async def get_series(
    min_rating: Optional[float] = Query(None, ge=0, le=10, description="Минимальный рейтинг"),
    sort: str = Query("rating_desc", description="Сортировка: rating_desc, rating_asc, title")
):
    """Получить сериалы с фильтрацией и сортировкой"""
    sorting = {
        "rating_desc": "rating DESC",
        "rating_asc": "rating ASC",
        "title": "title ASC"
    }.get(sort, "rating DESC")
    
    sql = f"SELECT * FROM series"
    params = {}
    
    if min_rating is not None:
        sql += " WHERE rating >= :min_rating"
        params["min_rating"] = min_rating
    
    sql += f" ORDER BY {sorting}"
    
    with SessionLocal() as db:
        result = db.execute(text(sql), params)
        columns = result.keys()
        return [dict(zip(columns, row)) for row in result]

# 🔍 СЛОЖНЫЕ ЗАПРОСЫ
@app.get("/complex/join-example", tags=["🔍 Поиск"])
async def complex_join_example(db: Session = Depends(get_db)):
    """
    Пример сложного SQL запроса с несколькими JOIN.
    
    ### Идеально для обучения тестированию:
    - Проверка структуры сложного ответа
    - Тестирование производительности
    - Валидация данных из нескольких таблиц
    """
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
                LIMIT 3
            ) as top_3_series
        FROM employees e
        JOIN departments d ON e.department_id = d.id
        JOIN cars c ON e.car_id = c.id
        ORDER BY e.last_name, e.first_name
        LIMIT 10
    """))
    
    columns = result.keys()
    data = [dict(zip(columns, row)) for row in result]
    
    return {
        "description": "Сотрудники с полной информацией",
        "sql_complexity": "3 JOIN + 2 подзапроса",
        "data": data,
        "testing_recommendations": [
            "Проверьте, что все поля присутствуют",
            "Проверьте формат данных (строки, числа)",
            "Протестируйте с limit=0 и limit=1000",
            "Проверьте производительность (тайминги)"
        ]
    }

# 🧪 ТЕСТИРОВАНИЕ
@app.get("/test/error/{error_code}", tags=["🧪 Тестирование"])
async def test_error_endpoint(
    error_code: int = Query(..., ge=100, le=599, description="HTTP код ошибки"),
    custom_message: Optional[str] = Query(None, description="Кастомное сообщение об ошибке")
):
    """
    Эндпоинт для тестирования различных HTTP ошибок.
    
    ### Поддерживаемые коды:
    - **400** - Bad Request
    - **401** - Unauthorized  
    - **403** - Forbidden
    - **404** - Not Found
    - **422** - Validation Error
    - **429** - Too Many Requests
    - **500** - Internal Server Error
    - **502** - Bad Gateway
    - **503** - Service Unavailable
    
    ### Примеры:
    - `GET /test/error/404`
    - `GET /test/error/500?custom_message=Тестовая+ошибка`
    """
    error_messages = {
        400: custom_message or "Некорректный запрос - проверьте параметры",
        401: custom_message or "Требуется авторизация",
        403: custom_message or "Доступ запрещен",
        404: custom_message or "Ресурс не найден",
        422: custom_message or "Ошибка валидации данных",
        429: custom_message or "Слишком много запросов",
        500: custom_message or "Внутренняя ошибка сервера",
        502: custom_message or "Проблема с подключением к сервису",
        503: custom_message or "Сервис временно недоступен"
    }
    
    if error_code in error_messages:
        raise HTTPException(
            status_code=error_code,
            detail=error_messages[error_code],
            headers={"X-Error-Test": "true"}
        )
    
    return {
        "status": "unknown_error_code",
        "code": error_code,
        "message": "Этот код ошибки не настроен для тестирования",
        "supported_codes": list(error_messages.keys())
    }

@app.get("/test/validation", tags=["🧪 Тестирование"])
async def test_validation(
    string_param: str = Query("default", min_length=2, max_length=10),
    number_param: int = Query(1, ge=1, le=100),
    optional_param: Optional[str] = Query(None)
):
    """
    Эндпоинт для тестирования валидации параметров.
    
    ### Параметры для тестирования:
    - `string_param` (2-10 символов)
    - `number_param` (1-100)
    - `optional_param` (необязательный)
    
    ### Тест-кейсы:
    1. Корректные параметры → 200 OK
    2. string_param=1 → 422 (слишком короткий)
    3. number_param=0 → 422 (меньше 1)
    4. number_param=101 → 422 (больше 100)
    """
    return {
        "validation_passed": True,
        "parameters_received": {
            "string_param": string_param,
            "number_param": number_param,
            "optional_param": optional_param
        },
        "validation_rules": {
            "string_param": "min_length=2, max_length=10",
            "number_param": "ge=1, le=100",
            "optional_param": "optional"
        }
    }

# 📊 СТАТИСТИКА И МОНИТОРИНГ
@app.get("/stats", tags=["📊 Мониторинг"])
async def get_statistics(db: Session = Depends(get_db)):
    """Полная статистика базы данных и API"""
    stats = {}
    
    # Статистика по таблицам
    tables = ["employees", "departments", "cars", "series", "employee_series"]
    for table in tables:
        try:
            result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
            stats[table] = result.scalar()
        except Exception as e:
            stats[table] = f"error: {str(e)}"
    
    # Детальная статистика
    dept_stats = db.execute(text("""
        SELECT 
            d.name,
            COUNT(e.id) as employee_count,
            AVG(LENGTH(e.first_name || e.last_name)) as avg_name_length,
            STRING_AGG(DISTINCT e.position, '; ') as unique_positions
        FROM departments d
        LEFT JOIN employees e ON d.id = e.department_id
        GROUP BY d.id, d.name
        ORDER BY employee_count DESC
    """))
    
    stats["departments_detail"] = [
        {
            "department": row[0],
            "employee_count": row[1],
            "avg_name_length": float(row[2]) if row[2] else 0,
            "unique_positions": row[3].split('; ') if row[3] else []
        }
        for row in dept_stats
    ]
    
    # Статистика популярности сериалов
    series_stats = db.execute(text("""
        SELECT 
            s.title,
            s.rating,
            COUNT(es.employee_id) as fans_count
        FROM series s
        LEFT JOIN employee_series es ON s.id = es.series_id
        GROUP BY s.id, s.title, s.rating
        ORDER BY fans_count DESC, s.rating DESC
        LIMIT 5
    """))
    
    stats["top_series"] = [
        {"title": row[0], "rating": float(row[1]), "fans": row[2]}
        for row in series_stats
    ]
    
    return {
        "timestamp": datetime.now().isoformat(),
        "database_stats": stats,
        "api_info": {
            "hosting": "Render.com Free Tier",
            "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "concurrent_capacity": "15+ users",
            "status": "operational"
        },
        "learning_use_cases": [
            "Анализ структуры данных",
            "Тестирование сложных запросов",
            "Мониторинг производительности"
        ]
    }

@app.get("/learning/tasks", tags=["🧪 Тестирование"])
async def get_learning_tasks():
    """
    Полный план обучения для тестировщиков.
    
    ### День 1: Основы REST API
    1. Изучите Swagger UI
    2. Протестируйте GET эндпоинты
    3. Проверьте статус коды
    4. Изучите структуру ответов
    """
    return {
        "course": "Тестирование REST API с FastAPI",
        "duration": "3 дня (15-20 часов)",
        "prerequisites": [
            "Базовое понимание HTTP",
            "Знакомство с JSON",
            "Установленный Postman/Insomnia"
        ],
        "daily_plan": {
            "day_1": {
                "topic": "Основы HTTP и REST",
                "duration": "5-6 часов",
                "tasks": [
                    {
                        "task": "Изучить Swagger UI",
                        "endpoints": ["/", "/docs", "/health"],
                        "expected_outcome": "Понимание структуры API"
                    },
                    {
                        "task": "Тестирование GET запросов",
                        "endpoints": ["/employees", "/departments", "/cars", "/series"],
                        "test_cases": [
                            "Статус код 200",
                            "Структура JSON ответа",
                            "Пагинация (/employees?page=2)",
                            "Фильтрация (/series?min_rating=8)"
                        ]
                    },
                    {
                        "task": "Тестирование ошибок",
                        "endpoints": ["/test/error/404", "/test/error/500"],
                        "test_cases": [
                            "Все коды ошибок из документации",
                            "Кастомные сообщения об ошибках",
                            "Проверка заголовков ответа"
                        ]
                    }
                ],
                "homework": "Написать 10 тест-кейсов для GET эндпоинтов"
            },
            "day_2": {
                "topic": "Модифицирующие операции",
                "duration": "6-7 часов",
                "tasks": [
                    {
                        "task": "Создание ресурсов (POST)",
                        "endpoints": ["/employees"],
                        "test_cases": [
                            "Корректное создание (201 Created)",
                            "Валидация полей (некорректные данные)",
                            "Проверка дублирования",
                            "Проверка связанных данных (department_id, car_id)"
                        ]
                    },
                    {
                        "task": "Удаление ресурсов (DELETE)",
                        "endpoints": ["/employees/{id}"],
                        "test_cases": [
                            "Удаление существующего ресурса",
                            "Повторное удаление (404)",
                            "Удаление несуществующего ресурса",
                            "Проверка побочных эффектов"
                        ]
                    },
                    {
                        "task": "Тестирование валидации",
                        "endpoints": ["/test/validation"],
                        "test_cases": [
                            "Граничные значения параметров",
                            "Некорректные типы данных",
                            "Обязательные/опциональные параметры"
                        ]
                    }
                ],
                "homework": "Создать коллекцию Postman с 15+ запросами"
            },
            "day_3": {
                "topic": "Продвинутое тестирование",
                "duration": "4-6 часов",
                "tasks": [
                    {
                        "task": "Интеграционное тестирование",
                        "endpoints": ["/complex/join-example", "/stats"],
                        "test_cases": [
                            "Сложные SQL запросы",
                            "Связи между таблицами",
                            "Производительность и тайминги",
                            "Целостность данных"
                        ]
                    },
                    {
                        "task": "Нагрузочное тестирование",
                        "description": "Используйте Postman Runner или скрипты",
                        "scenarios": [
                            "10 последовательных запросов к /employees",
                            "Параллельные запросы от 3 пользователей",
                            "Длительная работа (5+ минут)"
                        ]
                    },
                    {
                        "task": "Документирование багов",
                        "description": "Создать баг-репорты для найденных проблем",
                        "template": "Шаги воспроизведения, ожидаемый/фактический результат, окружение"
                    }
                ],
                "homework": "Подготовить финальный отчет по тестированию"
            }
        },
        "assessment": {
            "criteria": [
                "Количество протестированных эндпоинтов",
                "Разнообразие тест-кейсов",
                "Найденные баги (если есть)",
                "Качество документации"
            ],
            "passing_score": "Выполнение 80% задач"
        },
        "resources": {
            "tools": ["Postman", "Insomnia", "curl", "Python requests"],
            "documentation": ["/docs", "/redoc"],
            "practice_data": "Реальная PostgreSQL база с тестовыми данными"
        }
    }

# ========== ЗАПУСК СЕРВЕРА ==========
if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("🚀 COMPANYDB API ДЛЯ ОБУЧЕНИЯ ТЕСТИРОВЩИКОВ")
    print("=" * 60)
    print(f"📖 Swagger UI: http://localhost:{PORT}/docs")
    print(f"📚 ReDoc: http://localhost:{PORT}/redoc")
    print(f"🔧 Health: http://localhost:{PORT}/health")
    print(f"👥 Поддержка: 15+ одновременных пользователей")
    print(f"🗄️  База данных: PostgreSQL на Reg.ru")
    print(f"🌐 Хостинг: Render.com (бесплатный тариф)")
    print("=" * 60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level="info",
        access_log=True
    )
