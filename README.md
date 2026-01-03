# 🏢 CompanyDB API для обучения тестировщиков

Полнофункциональное REST API на FastAPI для практического обучения тестированию.

## 🌐 Демо
- **API URL**: https://company-api.onrender.com
- **Swagger UI**: https://company-api.onrender.com/docs  
- **Health Check**: https://company-api.onrender.com/health
- **Статистика**: https://company-api.onrender.com/stats

## 🎯 Цель проекта
Обучение тестировщиков практическим навыкам работы с REST API через реальный работающий пример.

## 🛠 Технологии
- **Backend**: FastAPI (Python 3.10)
- **Database**: PostgreSQL
- **Hosting**: Render.com (бесплатный тариф)
- **Documentation**: Swagger UI, ReDoc

## 🗄️ Структура базы данных
1. **employees** - сотрудники компании
2. **departments** - отделы компании
3. **cars** - автомобили сотрудников
4. **series** - сериалы
5. **employee_series** - связь сотрудников и сериалов

## 🚀 Быстрый старт

### Локальная разработка:
```bash
# Клонирование репозитория
git clone https://github.com/ВАШ_ЛОГИН/company_api.git
cd company_api

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или venv\Scripts\activate  # Windows

# Установка зависимостей
pip install -r requirements.txt

# Запуск сервера
uvicorn main:app --reload