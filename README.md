# Shortacadabra

**Shortacadabra** — современный сервис для безопасного сокращения ссылок с расширенной аналитикой и кастомными доменами.

## 🚀 Основные возможности

### 🔗 Сокращение ссылок
- Сокращение длинных URL в короткие коды
- Выбор кастомного домена для сокращённых ссылок
- Автоматическая проверка безопасности через VirusTotal API
- Защита от вредоносных ссылок

### 📊 Аналитика переходов
- **Геолокация**: страна, регион, город, координаты
- **Устройства**: тип устройства, операционная система, браузер
- **Время**: дата и время каждого перехода
- **Визуализация**: графики кликов за последние 30 дней
- **Статистика**: топ стран, браузеров, устройств

### 🌐 Кастомные домены
- Добавление собственных доменов
- Активация/деактивация доменов
- DNS инструкции для настройки
- Выбор домена при создании ссылки

### 🎨 Современный интерфейс
- Тёмная тема в стиле "black & white"
- Адаптивный дизайн на Bootstrap 5
- 3D TextSprite анимации на главной странице
- Плавные переходы и эффекты

## 🛠️ Технический стек

### Backend
- **Python 3.12**
- **Django 4.0.5** — веб-фреймворк
- **SQLite** — база данных (по умолчанию)
- **PostgreSQL** — для продакшена

### Frontend
- **Bootstrap 5.3.0** — UI компоненты
- **Chart.js** — графики и диаграммы
- **Three.js + three-spritetext** — 3D анимации
- **Custom CSS** — тёмная тема и эффекты

### База данных
- **SQLite** — локальная разработка
- **PostgreSQL** — продакшен
- **Django ORM** — работа с данными

### Мониторинг и безопасность
- **VirusTotal API** — проверка безопасности ссылок
- **ipapi.co** — геолокация по IP
- **django-axes** — защита от брутфорса
- **django-ratelimit** — ограничение запросов
- **django-csp** — политика безопасности контента
- **django-cors-headers** — CORS настройки

## 📦 Установка и запуск

### 1. Клонирование репозитория
```bash
git clone https://github.com/ewello/shortacadabra.git
cd Shortacadabra
```

### 2. Создание виртуального окружения
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows
```

### 3. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 4. Настройка переменных окружения
Создайте файл `.env` в корне проекта:
```env
SECRET_KEY=your_django_secret_key_here
api=your_virustotal_api_key_here
DEBUG=True
```

### 5. Применение миграций
```bash
python manage.py migrate
```

### 6. Создание суперпользователя
```bash
python manage.py createsuperuser
```

### 7. Запуск сервера
```bash
python manage.py runserver
```

Откройте http://127.0.0.1:8000/ в браузере.

## 🔧 Настройка API ключей

### VirusTotal API
1. Зарегистрируйтесь на [virustotal.com](https://www.virustotal.com/)
2. Получите API ключ в разделе API
3. Добавьте в `.env`: `api=your_api_key_here`

## 📁 Структура проекта

```
Shortacadabra/
├── Shortacadabra/           # Настройки Django
│   ├── settings.py          # Конфигурация
│   ├── urls.py             # Главные URL маршруты
│   └── wsgi.py, asgi.py    # WSGI/ASGI конфигурация
├── ss/                     # Основное приложение
│   ├── models.py           # Модели данных
│   ├── views.py            # Представления
│   ├── forms.py            # Формы
│   ├── urls.py             # URL маршруты приложения
│   ├── analytics.py        # Утилиты аналитики
│   ├── admin.py            # Админ панель
│   ├── migrations/         # Миграции БД
│   └── templates/          # HTML шаблоны
│       ├── ss/             # Основные страницы
│       └── registration/   # Регистрация/вход
├── docs/                   # Документация
├── requirements.txt        # Зависимости Python
├── .env                    # Переменные окружения
└── README.md              # Документация
```

## 🎯 Основные модели

### Url
- `url` — оригинальная ссылка
- `user` — владелец ссылки
- `custom_domain` — кастомный домен
- `created_at` — дата создания

### Click
- `url` — связанная ссылка
- `ip_address` — IP адрес
- `country`, `region`, `city` — геолокация
- `browser`, `os`, `device_type` — информация об устройстве
- `created_at` — время клика

### CustomDomain
- `domain` — доменное имя
- `user` — владелец домена
- `is_active` — статус активности
- `created_at` — дата добавления

## 🔒 Безопасность

- **VirusTotal интеграция** — автоматическая проверка ссылок
- **Rate limiting** — защита от спама
- **CSRF защита** — защита от межсайтовых атак
- **CSP заголовки** — политика безопасности контента
- **Axes защита** — защита от брутфорса

## 📊 Аналитика

Система собирает детальную статистику:
- **География**: страна, регион, город, координаты
- **Техническая**: браузер, ОС, тип устройства
- **Временная**: дата и время каждого перехода
- **Визуальная**: графики и диаграммы

## 🚀 Деплой

### Heroku
```bash
# Установите Heroku CLI
heroku create your-app-name
heroku addons:create heroku-postgresql:hobby-dev
heroku config:set SECRET_KEY=your_secret_key
heroku config:set api=your_virustotal_api_key
git push heroku main
```

### Docker
```bash
docker build -t shortacadabra .
docker run -p 8000:8000 shortacadabra
```

## 📝 Лицензия

MIT License

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для новой функции
3. Внесите изменения
4. Создайте Pull Request

## 📞 Поддержка

При возникновении проблем:
1. Проверьте настройки в `.env`
2. Убедитесь, что все зависимости установлены
3. Проверьте логи сервера
4. Создайте Issue в репозитории

---

**Shortacadabra** — магия сокращения ссылок!