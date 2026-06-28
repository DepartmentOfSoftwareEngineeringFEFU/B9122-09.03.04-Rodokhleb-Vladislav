# Репозиторий программы для поиска фрагментов в видеофайле по ключевым словам и автоматической разметки видеоряда.

Платформа для загрузки, хранения и анализа видеороликов с использованием компьютерного зрения 

##Технологический стек
* **Backend:** Python, FastAPI, SQLAlchemy, PyTorch, Transformers (Grounding DINO), OpenCV
* **Frontend:** React 19, Vite, React Router, Axios
* **Infrastructure:** Docker, Docker Compose, PostgreSQL, MinIO (S3), pgAdmin

---

##Инструкция по запуску

### Предварительные требования
Убедитесь, что на вашей машине установлены:
* [Git](https://git-scm.com/)
* [Python 3.10+](https://www.python.org/)
* [Docker & Docker Compose](https://www.docker.com/products/docker-desktop/)
* [Node.js (v18+) & npm](https://nodejs.org/)

### Шаг 1. Клонирование репозитория
```bash
git clone <ссылка_на_репозиторий>
cd <название_папки_проекта>
```
### Шаг 2. Создание виртуального окружения (Backend)

**Для Windows (PowerShell / CMD):**
```bash
python -m venv venv
venv\Scripts\activate
```
**Для Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Шаг 3. Установка Python-зависимостей
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Шаг 4. Запуск инфраструктуры и Backend (Docker)
Docker Compose поднимет базу данных, объектное хранилище, pgAdmin и контейнер Backend-сервера.
Будут загружены образы всех необходимых сервисов, включая образ backend-части программы.

```bash
docker-compose up -d
```
*Чтобы посмотреть логи запущенных контейнеров, используйте:* `docker-compose logs -f`
*Для остановки сервисов:* `docker-compose down`

### Шаг 5. Запуск Frontend
Перейдите в папку frontend, установите зависимости и запустите dev-сервер.

```bash
cd frontend
npm install
npm run dev
```
*Vite автоматически настроит проксирование API-запросов (`/api/*`) на Backend-сервер (порт 5434).*

---

##Порты и доступ к сервисам

После успешного выполнения всех шагов, сервисы будут доступны по следующим адресам:

| Сервис | URL / Порт | Описание |
| :--- | :--- | :--- |
| **Frontend (UI)** | [http://localhost:3000](http://localhost:3000) | Основное веб-приложение (React) |
| **Backend (API)** | [http://localhost:5434](http://localhost:5434) | FastAPI сервер |
| **API Документация** | [http://localhost:5434/docs](http://localhost:5434/docs) | Swagger UI (FastAPI) |
| **MinIO Console** | [http://localhost:9001](http://localhost:9001) | Веб-интерфейс S3-хранилища |
| **MinIO API** | `http://localhost:9000` | Эндпоинт для взаимодействия с S3 |
| **pgAdmin** | [http://localhost:5050](http://localhost:5050) | Веб-интерфейс для управления PostgreSQL |
| **PostgreSQL** | `localhost:5432` | База данных |

---

##Учетные данные по умолчанию

### MinIO (Объектное хранилище)
* **URL:** [http://localhost:9001](http://localhost:9001)
* **Логин:** `minioadmin`
* **Пароль:** `admin1234`
* *База (Bucket):* `video-analytics`

###pgAdmin (Управление БД)
* **URL:** [http://localhost:5050](http://localhost:5050)
* **Email:** `admin@example.com`
* **Пароль:** `admin`
* **Подключение к БД внутри pgAdmin:**
  * Host: `postgres` *(или `localhost`, если подключаетесь с хост-машины)*
  * Port: `5432`
  * Username: `postgres`
  * Password: `postgres`
  * Database: `db`

### PostgreSQL
* **User:** `postgres`
* **Password:** `postgres`
* **Database:** `db`

---

##Примечания
1. **Запуск анализа видео** Модель работает на CPU, поэтому анализ видеоряда может занять продолжительное время.
