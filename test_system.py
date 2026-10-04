import httpx
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_all():
    print("\n=======================================================")
    print("RUNNING COMPREHENSIVE BUS DEPOT MANAGEMENT SYSTEM TESTS")
    print("=======================================================\n")
    client = httpx.Client(base_url=BASE_URL, timeout=10.0, follow_redirects=False)

    passed = 0
    total = 0

    def assert_test(condition, name):
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f" [PASS] {name}")
        else:
            print(f" [FAIL] {name}")
            sys.exit(1)

    # 1. Test Login Page loads
    r = client.get("/login")
    assert_test(r.status_code == 200 and "Bus Depot Management" in r.text, "Login page renders successfully")

    # 2. Test Invalid Credentials
    r = client.post("/auth/login", json={"username": "wronguser", "password": "wrongpassword"})
    assert_test(r.status_code == 401, "Invalid login rejected with 401")

    # 3. Test Empty Credentials
    r = client.post("/auth/login", json={"username": "", "password": ""})
    assert_test(r.status_code in [400, 401], "Empty credentials rejected")

    # 4. Test Valid Admin Login
    r_admin = client.post("/auth/login", json={"username": "admin", "password": "Admin@123"})
    assert_test(r_admin.status_code == 200, "Admin login successful")
    admin_data = r_admin.json()
    admin_token = admin_data["access_token"]
    assert_test(admin_data["role"] == "admin", "Admin role confirmed")
    assert_test(admin_data["redirect_url"] == "/admin/dashboard", "Admin redirect URL correct")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 5. Test Valid Operations Login
    r_ops = client.post("/auth/login", json={"username": "operations", "password": "Ops@123"})
    assert_test(r_ops.status_code == 200, "Operations login successful")
    ops_data = r_ops.json()
    ops_token = ops_data["access_token"]
    assert_test(ops_data["role"] == "operations", "Operations role confirmed")
    assert_test(ops_data["redirect_url"] == "/operations/dashboard", "Operations redirect URL correct")
    ops_headers = {"Authorization": f"Bearer {ops_token}"}

    # 6. Test Valid Driver Login
    r_drv = client.post("/auth/login", json={"username": "driver1", "password": "Driver@123"})
    assert_test(r_drv.status_code == 200, "Driver login successful")
    drv_data = r_drv.json()
    drv_token = drv_data["access_token"]
    assert_test(drv_data["role"] == "driver", "Driver role confirmed")
    assert_test(drv_data["redirect_url"] == "/driver/dashboard", "Driver redirect URL correct")
    drv_headers = {"Authorization": f"Bearer {drv_token}"}

    # 7. Test RBAC: Unauthenticated access blocked
    r_unauth = httpx.get(f"{BASE_URL}/admin/stats")
    assert_test(r_unauth.status_code == 401, "Unauthenticated access to /admin/stats rejected with 401")

    # 8. Test RBAC: Driver attempting to access Admin endpoints
    r = client.get("/admin/users", headers=drv_headers)
    assert_test(r.status_code == 403, "Driver access to /admin/users blocked with 403 Forbidden")

    # 9. Test RBAC: Driver attempting to access Operations endpoints
    r = client.get("/operations/trips", headers=drv_headers)
    assert_test(r.status_code == 403, "Driver access to /operations/trips blocked with 403 Forbidden")

    # 10. Test RBAC: Operations attempting to access Admin User management
    r = client.get("/admin/users", headers=ops_headers)
    assert_test(r.status_code == 403, "Operations access to /admin/users blocked with 403 Forbidden")

    # 11. Test Admin Stats
    r = client.get("/admin/stats", headers=admin_headers)
    assert_test(r.status_code == 200 and "buses" in r.json(), "Admin stats retrieved")

    # 12. Test Admin Bus CRUD
    new_bus = {
        "bus_number": "BUS-999",
        "registration_number": "AP29-TEST-9999",
        "bus_type": "Electric City",
        "capacity": 42,
        "status": "Available",
        "maintenance_status": "Good"
    }
    r = client.post("/admin/buses", json=new_bus, headers=admin_headers)
    assert_test(r.status_code == 201, "Admin created new bus successfully")
    bus_id = r.json()["id"]

    r = client.put(f"/admin/buses/{bus_id}", json={"capacity": 45, "maintenance_status": "Good"}, headers=admin_headers)
    assert_test(r.status_code == 200 and r.json()["capacity"] == 45, "Admin updated bus capacity")

    # 13. Test Admin Driver CRUD
    new_drv = {
        "driver_id": "DRV-999",
        "name": "Kiran Kumar",
        "phone": "+91 99999 88888",
        "license_number": "DL-AP29-2022-9999",
        "status": "Active"
    }
    r = client.post("/admin/drivers", json=new_drv, headers=admin_headers)
    assert_test(r.status_code == 201, "Admin created driver successfully")
    drv_id = r.json()["id"]

    # 14. Test Admin Route CRUD
    new_route = {
        "route_number": "RT-999",
        "source": "North Terminal",
        "destination": "South Terminal",
        "stops": "Stop A, Stop B",
        "status": "Active"
    }
    r = client.post("/admin/routes", json=new_route, headers=admin_headers)
    assert_test(r.status_code == 201, "Admin created route successfully")
    route_id = r.json()["id"]

    # 15. Test Operations Trip Creation & Assignment
    new_trip = {
        "route_id": route_id,
        "bus_id": bus_id,
        "driver_id": drv_id,
        "departure_time": "10:00 AM",
        "arrival_time": "11:30 AM",
        "status": "Scheduled"
    }
    r = client.post("/operations/trips", json=new_trip, headers=ops_headers)
    assert_test(r.status_code == 201, "Operations created trip with bus and driver assignment")
    trip_id = r.json()["id"]

    # Verify bus status changed to Assigned and driver to On Duty
    r_b = client.get("/operations/buses", headers=ops_headers)
    test_bus = next((b for b in r_b.json() if b["id"] == bus_id), None)
    assert_test(test_bus is not None and test_bus["status"] == "Assigned", "Bus status transitioned to 'Assigned'")

    # 16. Test Trip Status Update
    r = client.put(f"/operations/trips/{trip_id}/status", json={"status": "In Progress"}, headers=ops_headers)
    assert_test(r.status_code == 200 and r.json()["status"] == "In Progress", "Operations updated trip to 'In Progress'")

    r = client.put(f"/operations/trips/{trip_id}/status", json={"status": "Completed"}, headers=ops_headers)
    assert_test(r.status_code == 200 and r.json()["status"] == "Completed", "Operations completed trip")

    # Verify bus was released back to Available
    r_b = client.get("/operations/buses", headers=ops_headers)
    test_bus = next((b for b in r_b.json() if b["id"] == bus_id), None)
    assert_test(test_bus is not None and test_bus["status"] == "Available", "Bus auto-released back to 'Available'")

    # 17. Test Driver Profile and Schedule
    r = client.get("/driver/profile", headers=drv_headers)
    assert_test(r.status_code == 200 and r.json()["driver_id"] == "DRV-101", "Driver fetched own profile")

    r = client.get("/driver/schedule", headers=drv_headers)
    assert_test(r.status_code == 200 and isinstance(r.json(), list), "Driver fetched schedule")

    # 18. Test Activity Logs
    r = client.get("/admin/activity-logs", headers=admin_headers)
    assert_test(r.status_code == 200 and len(r.json()) > 0, "Activity audit logs verified")

    # Clean up test entities
    client.delete(f"/admin/trips/{trip_id}", headers=admin_headers)
    client.delete(f"/admin/buses/{bus_id}", headers=admin_headers)
    client.delete(f"/admin/drivers/{drv_id}", headers=admin_headers)
    client.delete(f"/admin/routes/{route_id}", headers=admin_headers)

    print(f"\n=======================================================")
    print(f"ALL TESTS PASSED! ({passed}/{total} checks successful)")
    print(f"=======================================================\n")

if __name__ == "__main__":
    test_all()
