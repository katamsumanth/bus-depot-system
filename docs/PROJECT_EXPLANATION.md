# Bus Depot Management System — Project Explanation & Viva Guide

---

## 1. Project Introduction

The **Bus Depot Management System** is a modern, enterprise-grade web application designed to streamline, automate, and monitor the end-to-end operational activities of a commercial or public bus depot. 

A bus depot is the central nervous system of any public transit or private bus fleet. On a daily basis, depot supervisors must track fleet availability, schedule daily dispatches, assign licensed drivers to specific routes, log periodic bus maintenance, and maintain accountability.

This system replaces outdated paper registers and uncoordinated spreadsheets with an asynchronous, role-based web platform powered by **Python FastAPI**, an **SQLite** relational database, and a responsive **HTML5/CSS3/JavaScript** user interface.

---

## 2. Problem Statement

Commercial bus depots face daily operational complexities:
* Managing large fleets with vehicles entering and leaving service.
* Coordinating driver duty rosters and preventing double-booking.
* Preventing unroadworthy or maintenance-due buses from being dispatched.
* Lack of real-time visibility into active trips and delays.
* Inability to verify user actions due to missing audit logs.

Without a centralized digital platform, depot operations suffer from dispatch bottlenecks, administrative errors, and communication breakdowns between operations staff and drivers.

---

## 3. Existing System

In most conventional depots, operations rely on:
* Physical paper registers maintained at the depot gate.
* Manual whiteboards listing bus numbers and assigned driver names.
* Standalone Excel spreadsheets updated on an ad-hoc basis.
* Phone calls and verbal notices to inform drivers of duty assignments.

---

## 4. Problems with Existing System

1. **High Risk of Human Error:** Manual entry leads to duplicate vehicle assignments or dispatching buses that require mechanical servicing.
2. **Zero Access Control:** Spreadsheets lack role-based access; anyone with file access can alter driver duty hours or delete schedules.
3. **Absence of Real-time Sync:** When a bus breaks down or a driver calls in sick, paper records cannot automatically notify operations or reassign routes.
4. **No Security or Audit Trail:** Passwords are not encrypted, and there is no trace of who created, edited, or deleted records.
5. **Slow Turnaround Time:** Generating weekly utilization or maintenance reports requires hours of manual compilation.

---

## 5. Proposed System

The proposed **Bus Depot Management System** delivers a unified web platform with:
* **Centralized Database:** An ACID-compliant SQLite relational database storing users, drivers, buses, routes, trips, assignments, and audit logs.
* **Server-Side Authentication & RBAC:** Passwords hashed with **bcrypt (12 rounds)**; sessions validated via **JWT** and secure **HTTP-only cookies**; role privileges strictly enforced by FastAPI dependencies.
* **Automated Operational Lifecycles:** When a trip is created with a bus and driver, the bus status automatically transitions to `Assigned` and driver to `On Duty`. When the trip finishes (`Completed`), the system automatically releases the bus back to `Available` and the driver back to `Active`.
* **Three Dedicated Portals:** Tailored user experiences for **Admin**, **Operations Staff**, and **Drivers**.
* **Audit Trail:** An immutable activity log recording all administrative and dispatch actions.

---

## 6. Objectives

1. Automate bus scheduling and dispatch workflows.
2. Eliminate vehicle double-booking and unauthorized dispatch of buses under maintenance.
3. Provide drivers with a personal mobile-friendly dashboard to check assigned routes and update trip milestones.
4. Enforce strict role-based access control (RBAC) on both API endpoints and frontend views.
5. Provide depot management with real-time operational metrics and reports.

---

## 7. Technology Stack

### Backend
* **Python 3.12:** Clean, readable, and highly maintainable language with modern asynchronous support.
* **FastAPI:** High-performance, async-native ASGI web framework built on Starlette and Pydantic. Provides sub-millisecond response times and automatic OpenAPI/Swagger documentation.
* **SQLAlchemy 2.0 ORM:** Object-Relational Mapper that abstracts SQL queries into Python objects, protecting against SQL injection vulnerabilities.
* **Uvicorn:** Production-ready ASGI server built on `uvloop` and `httptools`.

### Database
* **SQLite 3:** Serverless, zero-configuration relational database stored as a single reliable file (`database/depot.db`). Ideal for rapid deployment and embedded systems.

### Security
* **Bcrypt:** Adaptive key-derivation password hashing with automatic cryptographic salting.
* **PyJWT:** Standard RFC 7519 JSON Web Token implementation for stateless, tamper-proof user authentication.
* **HTTP-Only Cookies:** Prevents client-side scripts from reading session tokens, mitigating XSS attacks.

### Frontend
* **HTML5:** Semantic HTML providing accessibility and structure.
* **Vanilla CSS3:** Custom enterprise design system with dark mode glassmorphism, responsive grid/flexbox layouts, and CSS variable tokens.
* **Vanilla JavaScript (ES6+):** Async `fetch()` API calls, DOM manipulation, interactive modal controllers, and live clock updates without heavy framework build overhead.

---

## 8. System Architecture

```text
+------------------------------------------------------------------------+
|                            PRESENTATION TIER                           |
|       Admin Dashboard  |  Operations Portal  |  Driver Interface       |
|                  (HTML5, Vanilla CSS3, Vanilla ES6 JS)                 |
+-----------------------------------+------------------------------------+
                                    |
                            HTTP / JSON / Cookies
                                    |
                                    v
+-----------------------------------+------------------------------------+
|                             SECURITY TIER                              |
|   • Cookie / Bearer JWT Extraction     • Bcrypt Password Verification  |
|   • Role Guard (require_role)          • CORS & Input Sanitization     |
+-----------------------------------+------------------------------------+
                                    |
                                    v
+-----------------------------------+------------------------------------+
|                           APPLICATION TIER                             |
|                           (Python FastAPI)                             |
|  • /auth Router: Login, Logout, Session Identity                       |
|  • /admin Router: User CRUD, Fleet Catalog, Routes, Audit Logs        |
|  • /operations Router: Dispatch, Status Overrides, Assignments        |
|  • /driver Router: Personal Roster, Schedule, Trip State Transitions   |
+-----------------------------------+------------------------------------+
                                    |
                              SQLAlchemy ORM
                                    |
                                    v
+-----------------------------------+------------------------------------+
|                              DATA TIER                                 |
|                         (SQLite: depot.db)                             |
|   users | drivers | buses | routes | trips | assignments | activity_logs|
+------------------------------------------------------------------------+
```

---

## 9. Authentication Flow

```text
User enters Username/Email & Password
               │
               ▼
       POST /auth/login
               │
               ▼
Backend queries database for User record
               │
       ┌───────┴───────┐
       │               │
  Not Found         Found
       │               │
       ▼               ▼
   Return 401     Verify password hash using bcrypt.checkpw()
                       │
               ┌───────┴───────┐
               │               │
            Invalid          Valid
               │               │
               ▼               ▼
          Return 401     Check if user.is_active == True
                               │
                       ┌───────┴───────┐
                       │               │
                   Inactive          Active
                       │               │
                       ▼               ▼
                  Return 403     1. Generate signed JWT token
                                 2. Set HTTP-Only Cookie
                                 3. Log "Login" activity
                                 4. Return redirect URL based on role
```

---

## 10. Role-Based Authorization (RBAC)

The system implements strict **Role-Based Access Control** enforced on the server side:

| Feature / Resource | Admin | Operations Staff | Driver |
| :--- | :---: | :---: | :---: |
| **System Users (CRUD)** | ✅ Full Control | ❌ Denied (403) | ❌ Denied (403) |
| **Bus Master Catalog (CRUD)** | ✅ Full Control | ❌ Read & Status Only | ❌ View Assigned Only |
| **Driver Personnel Records** | ✅ Full Control | ❌ Read & Duty Only | ❌ View Own Profile |
| **Route Master (CRUD)** | ✅ Full Control | ❌ Read Only | ❌ View Assigned Only |
| **Trip Scheduling & Dispatch** | ✅ Full Control | ✅ Full Control | ❌ Denied (403) |
| **Live Trip Status Update** | ✅ Full Control | ✅ Full Control | ✅ Own Trips Only |
| **Depot Activity Audit Logs** | ✅ Full Access | ❌ Denied (403) | ❌ Denied (403) |
| **Operational Reports** | ✅ Full Access | ✅ Operational View | ❌ Denied (403) |

If an unauthorized user attempts to call an endpoint (e.g. Driver calling `/admin/users`), the server immediately rejects the request with `HTTP 403 Forbidden`. If a driver enters `/admin/dashboard` in the browser URL bar, the server detects the driver role and issues an immediate `HTTP 302` redirect to `/driver/dashboard?warning=forbidden`.

---

## 11. Database Design

The relational database consists of 7 normalized tables:

```text
+-------------------+       +--------------------+
|       users       |       |      drivers       |
+-------------------+       +--------------------+
| id (PK)           |<-----\| id (PK)            |
| username (Unique) |       | user_id (FK, Null) |
| email (Unique)    |       | driver_id (Unique) |
| password_hash     |       | name               |
| role              |       | phone              |
| is_active         |       | license_number     |
| created_at        |       | status             |
+-------------------+       +--------------------+
          │                           │
          │                           │
          ▼                           ▼
+-------------------+       +--------------------+       +--------------------+
|   activity_logs   |       |       trips        |       |       buses        |
+-------------------+       +--------------------+       +--------------------+
| id (PK)           |       | id (PK)            |       | id (PK)            |
| user_id (FK, Null)|       | route_id (FK)      |/----->| bus_number (Unique)|
| username          |       | bus_id (FK, Null)  |       | registration_number|
| role              |       | driver_id(FK, Null)|       | bus_type           |
| action            |       | departure_time     |       | capacity           |
| details           |       | arrival_time       |       | status             |
| timestamp         |       | status             |       | maintenance_status |
+-------------------+       +--------------------+       +--------------------+
                                      │                            │
                                      ▼                            │
                            +--------------------+                 │
                            |    assignments     |                 │
                            +--------------------+                 │
                            | id (PK)            |                 │
                            | trip_id (FK)       |                 │
                            | bus_id (FK)        |<----------------/
                            | driver_id (FK)     |
                            | assigned_by (FK)   |
                            | assigned_date      |
                            | notes              |
                            | status             |
                            +--------------------+
```

---

## 12. API Architecture

All endpoints follow RESTful conventions:

### Authentication
* `POST /auth/login` — Authenticates credentials, sets cookie, returns token & redirect.
* `POST /auth/logout` — Revokes session cookie and logs sign-out.
* `GET  /auth/me` — Returns the profile and role of the currently logged-in user.

### Admin Endpoints (Requires `admin` role)
* `GET    /admin/stats` — Overall depot statistics.
* `GET    /admin/users` — List and filter system users.
* `POST   /admin/users` — Create user with hashed password.
* `PUT    /admin/users/{id}` — Update user email, role, or active status.
* `DELETE /admin/users/{id}` — Delete user (preventing self-deletion).
* `GET    /admin/buses`, `POST /admin/buses`, `PUT /admin/buses/{id}`, `DELETE /admin/buses/{id}` — Bus CRUD.
* `GET    /admin/drivers`, `POST /admin/drivers`, `PUT /admin/drivers/{id}`, `DELETE /admin/drivers/{id}` — Driver CRUD.
* `GET    /admin/routes`, `POST /admin/routes`, `PUT /admin/routes/{id}`, `DELETE /admin/routes/{id}` — Route CRUD.
* `GET    /admin/reports` — Analytical breakdowns.
* `GET    /admin/activity-logs` — Audit trail logs.

### Operations Endpoints (Requires `operations` or `admin` role)
* `GET    /operations/stats` — Fleet availability, driver duty, and pending assignments.
* `GET    /operations/buses` — View road-ready fleet.
* `PUT    /operations/buses/{id}/status` — Change operational or maintenance status.
* `GET    /operations/drivers` — View driver roster and availability.
* `PUT    /operations/drivers/{id}/status` — Update driver duty status.
* `GET    /operations/trips` — View dispatches.
* `POST   /operations/trips` — Schedule trip, assign bus & driver (with conflict checks).
* `PUT    /operations/trips/{id}/status` — Transition status (`In Progress`, `Completed`, `Cancelled`).
* `GET    /operations/assignments` — View historic assignment logs.

### Driver Endpoints (Requires `driver` role)
* `GET /driver/profile` — Fetch driver's personal and license information.
* `GET /driver/assignment` — Fetch current assigned bus and active trip.
* `GET /driver/schedule` — Fetch driver's personal trip timetable.
* `PUT /driver/trip/{id}/status` — Driver marks trip as `In Progress` or `Completed`.

---

## 13. Admin Module

The Admin Module provides top-level command over depot assets:
1. **Dashboard Overview:** Live counters for total buses, available buses, maintenance bays, total drivers, active drivers, and scheduled trips.
2. **User Administration:** Provisioning accounts, changing permissions, and activating or deactivating staff access.
3. **Fleet Inventory Management:** Adding new buses, specifying fuel/propulsion type (Electric, Standard AC, Luxury), passenger capacities, and service schedules.
4. **Driver Licensure Oversight:** Tracking driver badges, commercial licenses, contact details, and duty states.
5. **Route Planning:** Configuring route numbers, source and destination terminals, and intermediate waypoints.
6. **Audit Logs:** Immutable inspection of all actions timestamped in UTC.

---

## 14. Operations Module

The Operations Module focuses on the daily dispatch workflow:
1. **Fleet Availability Monitoring:** Quickly identifying which buses are ready for dispatch and which are in maintenance.
2. **Driver Roster Management:** Checking which drivers are on duty versus off duty.
3. **Trip Dispatching:** Creating trips and pairing a route with an available bus and ready driver.
4. **Validation Rules:** Prevents assigning a bus that is `Under Maintenance` or a driver who is already `On Duty`.
5. **Lifecycle Management:** Updating trip status from `Scheduled` to `In Progress` to `Completed`.

---

## 15. Driver Module

The Driver Module is a mobile-responsive interface designed for bus pilots:
1. **Hero Banner:** Displays driver name, driver ID badge, and current duty status.
2. **My Bus:** Displays the assigned bus number, registration plate, passenger capacity, bus class, and maintenance verification status.
3. **My Route:** Details the route corridor, starting terminal, destination, and waypoints.
4. **My Schedule:** Lists all past, current, and upcoming dispatches assigned to that specific driver.
5. **Interactive Controls:** Drivers can click **"Start Trip"** to update status to `In Progress`, and **"Complete Trip"** upon arrival.

---

## 16. Security Implementation

1. **Password Hashing:** Passwords are never stored as plain text. Bcrypt hashes passwords with 12 rounds of salt.
2. **Stateless JWT:** Signed using HMAC-SHA256 with an expiration time of 8 hours.
3. **HTTP-Only Cookies:** Tokens stored in browser cookies have the `HttpOnly` flag enabled, blocking client-side JavaScript access to prevent token theft.
4. **Server-Side Authorization:** Every endpoint checks user permissions on the server using dependency injection (`Depends(require_role(...))`).
5. **SQL Injection Defense:** SQLAlchemy ORM compiles queries using parameterized statements.
6. **Prevention of Privilege Escalation:** Operations and Drivers have no access to user modification routes.

---

## 17. Advantages

* **High Performance:** Built on FastAPI's asynchronous event loop, capable of handling thousands of requests per second.
* **Elimination of Operational Bottlenecks:** Instant visibility into bus and driver availability eliminates scheduling delays.
* **Complete Accountability:** The activity log ensures that every dispatch, edit, or status change is traceable to a specific user.
* **Zero Dependency Setup:** SQLite database runs embedded without needing a heavy database server daemon like PostgreSQL or MySQL.
* **Modern UI:** Dark mode aesthetic with glassmorphic cards and responsive mobile layouts.

---

## 18. Limitations

* Single-server SQLite deployment is optimized for low-to-medium concurrency (single-writer model); high-concurrency multi-instance deployments would require PostgreSQL.
* GPS vehicle tracking is simulated through status updates rather than live satellite IoT hardware telemetry.
* Does not include passenger ticketing or seat reservation integrations.

---

## 19. Future Scope

1. **IoT OBD-II GPS Integration:** Real-time satellite telemetry mapping bus locations on a live map.
2. **Automated Preventive Maintenance:** Machine learning models forecasting component wear based on route mileage.
3. **Passenger Facing Portal:** Mobile app displaying live bus arrival countdowns.
4. **Automated Crew Scheduling:** Algorithmic crew scheduling adhering to legal maximum driving hour regulations.

---

## 20. Complete User Flow

```text
                      [USER OPENS BROWSER]
                               │
                               ▼
               Visits http://localhost:8000
                               │
               Redirected to /login (if no session)
                               │
              Enters Username & Password
                               │
                               ▼
                      POST /auth/login
                               │
                    [BACKEND CHECKS ROLE]
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
         ▼                     ▼                     ▼
      [ADMIN]             [OPERATIONS]            [DRIVER]
   /admin/dashboard   /operations/dashboard   /driver/dashboard
         │                     │                     │
  • Create Users        • Check Fleet         • View Assigned Bus
  • Add Buses           • Assign Drivers      • View Route Stops
  • Add Routes          • Create Trips        • Click "Start Trip"
  • View Audit Logs     • Monitor Status      • Click "Complete"
```

---

## 21. 25+ Viva Questions and Answers

### Q1: What is the Bus Depot Management System?
**A:** It is a web-based management platform that automates bus depot operations including fleet tracking, driver rostering, route allocation, and trip scheduling using role-based access.

### Q2: Why did you choose FastAPI over Flask or Django?
**A:** FastAPI is asynchronous by default (ASGI), significantly faster than Flask/Django (WSGI), has native Pydantic data validation, and generates automatic interactive Swagger API documentation.

### Q3: Why did you choose SQLite?
**A:** SQLite is serverless, zero-configuration, ACID-compliant, stores data in a single local file, and provides exceptional read performance without managing an external database server.

### Q4: What is a REST API?
**A:** Representational State Transfer (REST) is an architectural style for web services where clients interact with server resources using standard HTTP methods (`GET`, `POST`, `PUT`, `DELETE`).

### Q5: What is the difference between Authentication and Authorization?
**A:** **Authentication** verifies *who you are* (e.g., verifying username and password). **Authorization** determines *what you are allowed to do* (e.g., verifying if an authenticated user has the Admin role).

### Q6: What is RBAC?
**A:** **Role-Based Access Control** is a security approach where system access is restricted based on defined user roles (Admin, Operations, Driver) rather than individual user accounts.

### Q7: How does login work in this project?
**A:** The user submits username and password via `POST /auth/login`. The backend checks the user table, validates the password hash with bcrypt, generates a signed JWT token, sets an HTTP-only cookie, and redirects the user to their role-specific dashboard.

### Q8: How are passwords stored in the database?
**A:** Passwords are never stored in plain text. They are hashed using **bcrypt** with 12 salt rounds, producing a one-way irreversible cryptographic string.

### Q9: What happens when login credentials are invalid?
**A:** The backend rejects the request with an `HTTP 401 Unauthorized` status and a message `"Invalid username/email or password"`, without exposing whether the username or password specifically was incorrect.

### Q10: How does the backend know what role a user has?
**A:** The backend looks up the authenticated user's record in the `users` table, reads the `role` column (`admin`, `operations`, `driver`), and verifies it using the `require_role()` dependency.

### Q11: Why shouldn't passwords be stored in plain text?
**A:** If plain text passwords are stored, any database breach or unauthorized access exposes all user credentials, compromising user accounts across systems.

### Q12: What is an API endpoint?
**A:** An API endpoint is a specific URL route (such as `/admin/buses` or `/auth/login`) where a client application sends requests to interact with server resources.

### Q13: What is HTTP and what methods are used?
**A:** Hypertext Transfer Protocol is the foundation of data communication on the web. We use `GET` (retrieve), `POST` (create), `PUT` (update), and `DELETE` (remove).

### Q14: What is a Foreign Key?
**A:** A Foreign Key is a database column that references the primary key of another table, establishing a relationship (e.g., `trips.bus_id` references `buses.id`).

### Q15: How are buses assigned to trips?
**A:** Operations staff select an available bus and driver when creating or updating a trip. The system verifies the bus is not currently assigned or under maintenance, sets the bus status to `Assigned`, and creates an assignment record.

### Q16: What happens when a trip is marked "Completed"?
**A:** The system automatically releases the assigned bus back to `Available` status and transitions the assigned driver back to `Active` duty status, making them immediately available for new dispatches.

### Q17: What can an Admin do?
**A:** Admins have full system control: managing user accounts and roles, adding/editing buses, drivers, routes, trips, viewing analytical reports, and inspecting security activity logs.

### Q18: What can Operations staff do?
**A:** Operations staff can view fleet availability, update bus operational status, check driver duty states, schedule trips, and assign resources. They **cannot** manage users or change user roles.

### Q19: What can a Driver do?
**A:** Drivers can view their assigned bus specifications, view route stops, view their personal duty schedule, and update the status of their assigned trips (e.g. from `In Progress` to `Completed`).

### Q20: What happens if a Driver manually types `/admin/dashboard` in the browser?
**A:** The backend cookie verification checks the user's role. Seeing that the user is a `driver`, it blocks access and returns an `HTTP 302 Redirect` to `/driver/dashboard?warning=forbidden`.

### Q21: What is JWT and why is it used?
**A:** JSON Web Token is a compact, URL-safe means of representing claims between two parties. It contains a signed payload verifying user identity without requiring server-side session lookups on every request.

### Q22: What is the purpose of the `activity_logs` table?
**A:** It maintains an immutable audit trail of actions (logins, user creation, bus additions, trip updates) with timestamps and actor details for security and accountability.

### Q23: How are SQL injection attacks prevented?
**A:** By using **SQLAlchemy ORM**, all query parameters are automatically sanitized and bound to prepared statements, preventing malicious SQL code execution.

### Q24: What are the main limitations of this system?
**A:** GPS tracking is simulated through status updates rather than live IoT hardware telemetry, and the single-file SQLite database is best suited for small to medium scale deployments.

### Q25: What future improvements can be made?
**A:** Integrating real-time IoT GPS tracking, passenger mobile apps with live arrival times, automated crew scheduling algorithms, and predictive bus maintenance using machine learning.

---
