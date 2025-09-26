# ✈️ Airport Management API

Airport Management API is a RESTful web service for managing airports, routes, airplanes, flights, and ticket bookings.  
It is built with **Django REST Framework**, secured with **JWT authentication**, and powered by **PostgreSQL**.  
The project is fully containerized using **Docker** for easy deployment.

---

## 🌟 Features

- **User Management**
  - User registration, login, profile management (`/api/user/me/`)
  - JWT-based authentication (access & refresh tokens)

- **Airports**
  - Create and list airports
  - Search airports by name or city

- **Routes**
  - CRUD operations for routes
  - Includes computed fields for route and trip names

- **Airplanes**
  - CRUD operations for airplanes
  - Upload airplane images ✈️
  - Capacity calculation (rows × seats per row)

- **Flights**
  - Manage flight schedules with airplane and route assignment
  - Filter by departure date or crew members
  - Pagination support

- **Orders & Tickets**
  - Create orders with associated tickets
  - List orders filtered by authenticated user

- **API Documentation**
  - Interactive Swagger UI with **drf-spectacular**

---

## 🛠️ Tech Stack

- **Backend:** Django 5, Django REST Framework  
- **Database:** PostgreSQL 16  
- **Authentication:** JWT (djangorestframework-simplejwt)  
- **Image Processing:** Pillow  
- **Containerization:** Docker, Docker Compose  
- **Documentation:** drf-spectacular (Swagger / OpenAPI)  

---

## ⚙️ Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/Sir-Churchill/airport-api-service.git
(create venv if needed)
source .venv/bin/activate
pip install requirements.txt
```
---
## 🐳 Docker Setup

To quickly start the project using Docker:

1. Build and run containers:

```bash
docker-compose up --build
