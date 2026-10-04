# 🚌 Bus Depot Management System

An enterprise-grade, full-stack web application designed for comprehensive bus depot management, fleet logistics, driver scheduling, and operational tracking with strict **Role-Based Access Control (RBAC)**.

Built with **Python FastAPI**, **SQLite**, and modern **HTML5/CSS3/JavaScript**.

---

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Key Features](#key-features)
- [Role-Based Access Overview](#role-based-access-overview)
- [Technology Stack](#technology-stack)
- [System Architecture](#system-architecture)
- [Project Directory Structure](#project-directory-structure)
- [Quick Start Guide](#quick-start-guide)
- [Default Demo Credentials](#default-demo-credentials)
- [API Documentation](#api-documentation)
- [Database Schema](#database-schema)
- [Automated Testing](#automated-testing)
- [Security Features](#security-features)
- [Viva & Presentation Materials](#viva--presentation-materials)
- [Future Improvements](#future-improvements)

---

## 📌 Project Overview

The **Bus Depot Management System** automates the end-to-end operational activities of a commercial or municipal transit depot. It replaces error-prone manual paper registers and disconnected spreadsheets with a unified, real-time web portal.

The application serves three distinct user roles:
1. **Admin**: Complete system oversight, user account management, fleet master catalog, driver licensure, transit routes, and audit activity logs.
2. **Operations Staff**: Daily fleet dispatching, monitoring vehicle availability, assigning road-ready buses and licensed drivers to routes, and recording trip status.
3. **Driver**: Dedicated mobile-responsive interface showing assigned bus specifications, route corridors, duty timetables, and interactive trip progress controls.

---

## ✨ Key Features

### 🔐 Authentication & Role-Based Authorization
- **Bcrypt Password Hashing**: Passwords are encrypted with 12 rounds of salt. Zero plain-text storage.
- **JWT + HTTP-Only Cookies**: Stateless JWT token authentication stored in secure cookies to prevent XSS.
- **Server-Side RBAC**: Every API route and page URL is protected by FastAPI dependencies (`Depends(require_role(...))`).
- **URL Tampering Protection**: Unauthorized direct URL navigation automatically redirects to the user's role dashboard.

### 🛡️ Admin Module
- **Live Metrics Dashboard**: Real-time counters for total buses, available fleet, maintenance bays, total drivers, active drivers, and scheduled trips.
- **User Management**: Create, edit, activate/deactivate accounts, and assign roles (`admin`, `operations`, `driver`).
- **Fleet Inventory**: Add, edit, and track buses by registration, type (Electric, Standard AC, Volvo Luxury), passenger capacity, and maintenance status.
- **Driver Records**: Manage driver ID badges, phone numbers, commercial driver licenses, and duty states.
- **Route Planning**: Configure routes, origin/destination terminals, and intermediate waypoints.
- **Audit Logs**: Immutable activity log capturing all administrative and dispatch actions timestamped in UTC.
- **Visual Analytics**: Distribution breakdown for fleet status, maintenance, driver availability, and route loads.

### 📋 Operations Module
- **Fleet Availability Tracker**: Instant view of available, assigned, and out-of-service buses.
- **Driver Roster**: Live check of driver availability (Active, On Duty, Off Duty).
- **Intelligent Dispatching**: Schedule trips and assign buses and drivers with automated conflict checks (prevents assigning buses under maintenance or drivers already on duty).
- **Automatic Resource De-allocation**: Marking a trip as `Completed` or `Cancelled` automatically releases the bus back to `Available` and the driver back to `Active`.

### 👨‍✈️ Driver Portal
- **Pilot Hero Banner**: Welcomes the driver with their name, driver ID badge, and live duty status.
- **Assigned Bus Details**: Full vehicle specifications including bus number, registration plate, type, capacity, and maintenance verification.
- **Route Corridor**: View source terminal, destination, intermediate stops, and timetables.
- **Duty Schedule**: View all past, present, and upcoming assigned trips.
- **Trip Milestone Buttons**: One-click **"Start Trip"** (`In Progress`) and **"Complete Trip"** (`Completed`).

---

## 👥 Role-Based Access Overview

| Capabilities | Admin | Operations | Driver |
| :--- | :---: | :---: | :---: |
| **Manage Users & Roles** | ✅ Yes | ❌ No | ❌ No |
| **Manage Fleet Catalog** | ✅ Yes | ❌ View/Status Only | ❌ Assigned Only |
| **Manage Driver Records** | ✅ Yes | ❌ View/Duty Only | ❌ Own Profile |
| **Manage Routes** | ✅ Yes | ❌ View Only | ❌ Assigned Only |
| **Create & Dispatch Trips**| ✅ Yes | ✅ Yes | ❌ No |
| **Update Trip Status** | ✅ Yes | ✅ Yes | ✅ Own Trips Only |
| **View Audit Trail Logs** | ✅ Yes | ❌ No | ❌ No |
| **View Operational Reports**| ✅ Yes | ✅ Yes | ❌ No |

---

## 🛠️ Technology Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend Framework** | Python 3.12 + FastAPI | Asynchronous RESTful API server |
| **Database** | SQLite 3 | Embedded, zero-configuration relational storage |
| **ORM** | SQLAlchemy 2.0 | Type-safe database interactions and query protection |
| **Authentication** | PyJWT + Bcrypt | Secure token generation and password hashing |
| **Server** | Uvicorn (ASGI) | Lightning-fast ASGI production server |
| **Frontend Structure** | HTML5 | Accessible, semantic document layout |
| **Frontend Styling** | Vanilla CSS3 | Custom dark mode design system with CSS tokens |
| **Frontend Logic** | Vanilla JavaScript (ES6+) | Single-Page Application (SPA) view routing & Fetch API |
| **Presentation** | Python-pptx | Generation of slide deck presentation |

---

## 🏗️ System Architecture

```text
Frontend Web Interface (HTML5, Vanilla CSS3, Vanilla ES6 JavaScript)
                           │
                 HTTP / JSON / Cookies
                           │
                           ▼
FastAPI Backend Gateway (main.py)
   ├── Security & Auth Guard (auth.py: Bcrypt + JWT + HTTP-Only Cookie)
   ├── /auth Router: Login, Logout, Session Verification
   ├── /admin Router: User CRUD, Fleet Master, Driver Master, Routes, Audit Logs
   ├── /operations Router: Fleet Dispatch, Assignment Controls, Duty Roster
   └── /driver Router: Personal Assignment, Timetable, Trip Milestones
                           │
                     SQLAlchemy ORM
                           │
                           ▼
SQLite Relational Database (database/depot.db)
   ├── users          ├── routes
   ├── drivers        ├── trips
   ├── buses          ├── assignments
   └── activity_logs
```

---

## 📂 Project Directory Structure

```text
bus_depot/
├── main.py                          # FastAPI application entrypoint & page routing
├── database.py                      # SQLite database connection & engine setup
├── models.py                        # SQLAlchemy relational models
├── schemas.py                       # Pydantic schemas for data validation
├── auth.py                          # Bcrypt hashing, JWT generation, & RBAC dependencies
├── seed.py                          # Database initialization & demo account seeding
├── requirements.txt                 # Project Python dependencies
├── .env                             # Environment configuration variables
├── .env.example                     # Environment template
├── test_system.py                   # Automated end-to-end test suite (29 tests)
│
├── routers/                         # Modular FastAPI API routers
│   ├── __init__.py
│   ├── auth.py                      # Authentication endpoints
│   ├── admin.py                     # Administrator CRUD & analytics endpoints
│   ├── operations.py                # Fleet dispatch & operational endpoints
│   └── driver.py                    # Driver portal endpoints
│
├── templates/                       # Jinja2 HTML5 templates
│   ├── login.html                   # Professional login page with 1-click demo fill
│   ├── admin_dashboard.html         # Admin dashboard view & CRUD modal dialogs
│   ├── operations_dashboard.html    # Operations staff dispatch & fleet controls
│   └── driver_dashboard.html        # Driver mobile-friendly portal & trip controls
│
├── static/                          # Static assets
│   ├── css/
│   │   ├── style.css                # Core design system tokens & base components
│   │   ├── login.css                # Glowing glassmorphic login styling
│   │   └── dashboard.css            # Enterprise dashboard layouts, tables, & cards
│   │
│   └── js/
│       ├── login.js                 # Login interaction & authentication logic
│       ├── admin.js                 # Admin SPA view switcher & CRUD controllers
│       ├── operations.js            # Operations fleet dispatch & status controllers
│       └── driver.js                # Driver trip progress & assignment controllers
│
├── database/
│   └── depot.db                     # SQLite database file
│
├── docs/
│   └── PROJECT_EXPLANATION.md       # Comprehensive viva guide with 25+ Q&As
│
├── README.md                        # Project documentation
└── Bus_Depot_Management_System.pptx # 12-slide PowerPoint presentation
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
Ensure **Python 3.10+** and `pip` are installed on your machine.

### 2. Set Up Virtual Environment

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (PowerShell / Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Initialize and Seed Database
Initializes the SQLite database with default demo accounts, buses, routes, and trips:
```bash
python seed.py
```

### 5. Launch the Server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Access the Application
Open your web browser and navigate to:
- **Application Portal**: [http://localhost:8000](http://localhost:8000)
- **Interactive API Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative ReDoc Docs**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🔑 Default Demo Credentials

The login page includes **1-click quick-fill buttons** for instant testing:

| Role | Username | Password | Direct Dashboard URL |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `Admin@123` | [http://localhost:8000/admin/dashboard](http://localhost:8000/admin/dashboard) |
| **Operations Staff** | `operations` | `Ops@123` | [http://localhost:8000/operations/dashboard](http://localhost:8000/operations/dashboard) |
| **Driver 1 (Rajesh Kumar)** | `driver1` | `Driver@123` | [http://localhost:8000/driver/dashboard](http://localhost:8000/driver/dashboard) |
| **Driver 2 (Suresh Reddy)** | `driver2` | `Driver@123` | [http://localhost:8000/driver/dashboard](http://localhost:8000/driver/dashboard) |

---

## 🧪 Automated Testing

A comprehensive end-to-end automated test suite is included in `test_system.py`:

```bash
python test_system.py
```

### Test Coverage (29 Total Checks):
- ✅ Login page rendering
- ✅ Invalid and empty credentials rejection
- ✅ Role identification and redirection for Admin, Operations, and Driver
- ✅ RBAC enforcement: Unauthenticated requests blocked (401)
- ✅ RBAC enforcement: Driver blocked from Admin and Operations routes (403)
- ✅ RBAC enforcement: Operations blocked from User administration (403)
- ✅ Admin Bus, Driver, and Route CRUD operations
- ✅ Operations trip scheduling and vehicle/driver conflict checks
- ✅ Status transition to `In Progress` and `Completed`
- ✅ Automatic vehicle release back to `Available` upon trip completion
- ✅ Driver profile and schedule retrieval
- ✅ Activity audit log recording

---

## 🔒 Security Features

1. **Passwords Salted & Hashed**: Uses `bcrypt.hashpw` with 12 salt rounds.
2. **Stateless JWT Authorization**: Tokens signed with HS256 and verified per request.
3. **HTTP-Only Cookies**: Eliminates client-side JavaScript access to tokens, mitigating Cross-Site Scripting (XSS).
4. **Server-Side Authorization**: Roles are checked in FastAPI dependencies, not frontend UI flags.
5. **SQL Injection Immune**: All database queries are compiled via SQLAlchemy parameterized statements.
6. **Detailed Audit Logging**: Critical security and operational events are logged to the `activity_logs` table.

---

## 📚 Viva & Presentation Materials

- **Project Viva & Review Guide**: [`docs/PROJECT_EXPLANATION.md`](file:///home/rkvalley-rgukt/Desktop/login/docs/PROJECT_EXPLANATION.md) (Contains 21 numbered sections and 25+ frequently asked viva interview questions with answers).
- **PowerPoint Presentation Deck**: [`Bus_Depot_Management_System.pptx`](file:///home/rkvalley-rgukt/Desktop/login/Bus_Depot_Management_System.pptx) (12 professional widescreen slides with architecture, modules, security flow, and conclusions).

---

## 🔮 Future Improvements

1. **IoT OBD-II GPS Telemetry**: Real-time vehicle location tracking on interactive OpenStreetMap/Leaflet maps.
2. **Passenger Mobile App**: Live bus arrival countdowns, QR code ticketing, and route notices.
3. **Predictive Maintenance**: Machine learning models predicting brake and engine servicing based on mileage.
4. **Automated Rostering Algorithms**: Dynamic shift scheduling optimizing driver rest hours and fuel economy.
