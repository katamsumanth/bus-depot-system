// ===================================================================
// ADMIN DASHBOARD CONTROLLER (SPA Architecture with Real-time APIs)
// ===================================================================

document.addEventListener("DOMContentLoaded", () => {
  // Navigation View Switching
  const navItems = document.querySelectorAll(".sidebar-nav .nav-item[data-target]");
  const viewSections = document.querySelectorAll(".view-section");
  const pageTitle = document.getElementById("pageTitle");

  navItems.forEach(item => {
    item.addEventListener("click", () => {
      const targetView = item.getAttribute("data-target");
      switchView(targetView);
    });
  });

  function switchView(viewName) {
    navItems.forEach(nav => {
      if (nav.getAttribute("data-target") === viewName) {
        nav.classList.add("active");
        pageTitle.textContent = nav.querySelector("span") ? nav.querySelector("span").textContent : "Dashboard";
      } else {
        nav.classList.remove("active");
      }
    });

    viewSections.forEach(sec => {
      if (sec.id === `view-${viewName}`) {
        sec.classList.add("active");
      } else {
        sec.classList.remove("active");
      }
    });

    // Refresh data for the active view
    if (viewName === "dashboard") loadStats();
    else if (viewName === "users") loadUsers();
    else if (viewName === "buses") loadBuses();
    else if (viewName === "drivers") loadDrivers();
    else if (viewName === "routes") loadRoutes();
    else if (viewName === "trips") loadTrips();
    else if (viewName === "reports") loadReports();
    else if (viewName === "logs") loadActivityLogs();
  }

  // Logout Functionality
  document.querySelectorAll(".btn-logout").forEach(btn => {
    btn.addEventListener("click", async () => {
      try {
        await fetch("/auth/logout", { method: "POST" });
      } catch (e) {
        console.error(e);
      } finally {
        localStorage.clear();
        window.location.href = "/login";
      }
    });
  });

  // Clock Update
  function updateClock() {
    const clockEl = document.getElementById("liveClock");
    if (clockEl) {
      const now = new Date();
      clockEl.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) +
                            " | " + now.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' });
    }
  }
  setInterval(updateClock, 1000);
  updateClock();

  // ==========================================
  // TOAST NOTIFICATIONS
  // ==========================================
  window.showToast = function(message, type = "success") {
    const container = document.getElementById("toastContainer");
    if (!container) return;
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateX(100%)";
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  };

  // ==========================================
  // MODAL UTILITIES
  // ==========================================
  window.openModal = function(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.add("active");
  };

  window.closeModal = function(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove("active");
  };

  document.querySelectorAll(".modal-backdrop").forEach(modal => {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) modal.classList.remove("active");
    });
    const closeBtn = modal.querySelector(".modal-close");
    if (closeBtn) closeBtn.addEventListener("click", () => modal.classList.remove("active"));
  });

  // ==========================================
  // 1. STATS (DASHBOARD)
  // ==========================================
  async function loadStats() {
    try {
      const res = await fetch("/admin/stats");
      if (!res.ok) throw new Error("Failed to load statistics");
      const data = await res.json();

      document.getElementById("statTotalBuses").textContent = data.buses.total;
      document.getElementById("statAvailBuses").textContent = data.buses.available;
      document.getElementById("statMaintBuses").textContent = data.buses.maintenance;

      document.getElementById("statTotalDrivers").textContent = data.drivers.total;
      document.getElementById("statActiveDrivers").textContent = data.drivers.active;

      document.getElementById("statTodayTrips").textContent = data.trips.total;
      document.getElementById("statScheduledTrips").textContent = data.trips.scheduled;
    } catch (err) {
      console.error("Stats load error:", err);
    }
  }

  // ==========================================
  // 2. USERS MANAGEMENT
  // ==========================================
  let allUsers = [];
  async function loadUsers() {
    try {
      const res = await fetch("/admin/users");
      if (!res.ok) throw new Error("Failed to fetch users");
      allUsers = await res.json();
      renderUsers(allUsers);
    } catch (err) {
      showToast(err.message, "error");
    }
  }

  function renderUsers(users) {
    const tbody = document.getElementById("usersTableBody");
    tbody.innerHTML = "";
    if (users.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="empty-state"><p>No users found</p></td></tr>`;
      return;
    }

    users.forEach(u => {
      const tr = document.createElement("tr");
      const roleBadge = u.role === "admin" ? "badge-purple" : (u.role === "operations" ? "badge-success" : "badge-warning");
      const statusBadge = u.is_active ? '<span class="badge badge-success">Active</span>' : '<span class="badge badge-danger">Inactive</span>';

      tr.innerHTML = `
        <td><span class="id-tag">#${u.id}</span></td>
        <td><strong>${u.username}</strong></td>
        <td>${u.email}</td>
        <td><span class="badge ${roleBadge}">${u.role}</span></td>
        <td>${statusBadge}</td>
        <td>
          <div class="table-actions">
            <button class="btn btn-secondary btn-sm" onclick="editUser(${u.id})">Edit</button>
            <button class="btn btn-danger btn-sm" onclick="deleteUser(${u.id}, '${u.username}')">Delete</button>
          </div>
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  document.getElementById("searchUsers").addEventListener("input", (e) => {
    const val = e.target.value.toLowerCase();
    const filtered = allUsers.filter(u => u.username.toLowerCase().includes(val) || u.email.toLowerCase().includes(val) || u.role.toLowerCase().includes(val));
    renderUsers(filtered);
  });

  // User Form Submission (Create or Edit)
  const userForm = document.getElementById("userForm");
  userForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const userId = document.getElementById("userId").value;
    const username = document.getElementById("userUsername").value.trim();
    const email = document.getElementById("userEmail").value.trim();
    const role = document.getElementById("userRole").value;
    const password = document.getElementById("userPassword").value.trim();
    const isActive = document.getElementById("userStatus").value === "true";

    const payload = { username, email, role, is_active: isActive };
    if (password) payload.password = password;

    try {
      let res;
      if (userId) {
        // Edit
        res = await fetch(`/admin/users/${userId}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
      } else {
        // Create
        if (!password) throw new Error("Password is required for new users.");
        res = await fetch("/admin/users", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
      }

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Error saving user");

      showToast(userId ? "User updated successfully" : "User created successfully");
      closeModal("modalUser");
      loadUsers();
      loadStats();
    } catch (err) {
      showToast(err.message, "error");
    }
  });

  window.openAddUserModal = function() {
    document.getElementById("userModalTitle").textContent = "Add New User";
    document.getElementById("userId").value = "";
    document.getElementById("userUsername").value = "";
    document.getElementById("userUsername").disabled = false;
    document.getElementById("userEmail").value = "";
    document.getElementById("userPassword").value = "";
    document.getElementById("userPassword").placeholder = "Required for new users";
    document.getElementById("userRole").value = "operations";
    document.getElementById("userStatus").value = "true";
    openModal("modalUser");
  };

  window.editUser = function(id) {
    const user = allUsers.find(u => u.id === id);
    if (!user) return;
    document.getElementById("userModalTitle").textContent = "Edit User";
    document.getElementById("userId").value = user.id;
    document.getElementById("userUsername").value = user.username;
    document.getElementById("userUsername").disabled = true;
    document.getElementById("userEmail").value = user.email;
    document.getElementById("userPassword").value = "";
    document.getElementById("userPassword").placeholder = "Leave blank to keep unchanged";
    document.getElementById("userRole").value = user.role;
    document.getElementById("userStatus").value = user.is_active ? "true" : "false";
    openModal("modalUser");
  };

  window.deleteUser = async function(id, username) {
    if (!confirm(`Are you sure you want to permanently delete user "${username}"?`)) return;
    try {
      const res = await fetch(`/admin/users/${id}`, { method: "DELETE" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to delete user");
      showToast(data.message);
      loadUsers();
      loadStats();
    } catch (err) {
      showToast(err.message, "error");
    }
  };

  // ==========================================
  // 3. BUSES MANAGEMENT
  // ==========================================
  let allBuses = [];
  async function loadBuses() {
    try {
      const res = await fetch("/admin/buses");
      if (!res.ok) throw new Error("Failed to load buses");
      allBuses = await res.json();
      renderBuses(allBuses);
    } catch (err) {
      showToast(err.message, "error");
    }
  }

  function renderBuses(buses) {
    const tbody = document.getElementById("busesTableBody");
    tbody.innerHTML = "";
    if (buses.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="empty-state"><p>No buses found</p></td></tr>`;
      return;
    }

    buses.forEach(b => {
      const tr = document.createElement("tr");
      let statusBadge = "badge-success";
      if (b.status === "Assigned") statusBadge = "badge-info";
      else if (b.status === "On Route") statusBadge = "badge-purple";
      else if (b.status === "Out of Service") statusBadge = "badge-danger";

      let maintBadge = "badge-success";
      if (b.maintenance_status === "Due for Service") maintBadge = "badge-warning";
      else if (b.maintenance_status === "Under Maintenance") maintBadge = "badge-danger";

      tr.innerHTML = `
        <td><span class="id-tag">${b.bus_number}</span></td>
        <td><strong>${b.registration_number}</strong></td>
        <td>${b.bus_type}</td>
        <td>${b.capacity} Seats</td>
        <td><span class="badge ${statusBadge}">${b.status}</span></td>
        <td><span class="badge ${maintBadge}">${b.maintenance_status}</span></td>
        <td>
          <div class="table-actions">
            <button class="btn btn-secondary btn-sm" onclick="editBus(${b.id})">Edit</button>
            <button class="btn btn-danger btn-sm" onclick="deleteBus(${b.id}, '${b.bus_number}')">Delete</button>
          </div>
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  document.getElementById("searchBuses").addEventListener("input", (e) => {
    const val = e.target.value.toLowerCase();
    const filtered = allBuses.filter(b => b.bus_number.toLowerCase().includes(val) || b.registration_number.toLowerCase().includes(val) || b.bus_type.toLowerCase().includes(val));
    renderBuses(filtered);
  });

  const busForm = document.getElementById("busForm");
  busForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const busId = document.getElementById("busId").value;
    const busNumber = document.getElementById("busNumber").value.trim();
    const registrationNumber = document.getElementById("busRegNumber").value.trim();
    const busType = document.getElementById("busType").value;
    const capacity = parseInt(document.getElementById("busCapacity").value, 10);
    const status = document.getElementById("busStatus").value;
    const maintenanceStatus = document.getElementById("busMaintenanceStatus").value;

    const payload = {
      bus_number: busNumber,
      registration_number: registrationNumber,
      bus_type: busType,
      capacity: capacity,
      status: status,
      maintenance_status: maintenanceStatus
    };

    try {
      let res;
      if (busId) {
        res = await fetch(`/admin/buses/${busId}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
      } else {
        res = await fetch("/admin/buses", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
      }

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Error saving bus");

      showToast(busId ? "Bus updated successfully" : "Bus created successfully");
      closeModal("modalBus");
      loadBuses();
      loadStats();
    } catch (err) {
      showToast(err.message, "error");
    }
  });

  window.openAddBusModal = function() {
    document.getElementById("busModalTitle").textContent = "Add New Bus";
    document.getElementById("busId").value = "";
    document.getElementById("busNumber").value = "";
    document.getElementById("busRegNumber").value = "";
    document.getElementById("busType").value = "Standard AC";
    document.getElementById("busCapacity").value = "45";
    document.getElementById("busStatus").value = "Available";
    document.getElementById("busMaintenanceStatus").value = "Good";
    openModal("modalBus");
  };

  window.editBus = function(id) {
    const bus = allBuses.find(b => b.id === id);
    if (!bus) return;
    document.getElementById("busModalTitle").textContent = "Edit Bus";
    document.getElementById("busId").value = bus.id;
    document.getElementById("busNumber").value = bus.bus_number;
    document.getElementById("busRegNumber").value = bus.registration_number;
    document.getElementById("busType").value = bus.bus_type;
    document.getElementById("busCapacity").value = bus.capacity;
    document.getElementById("busStatus").value = bus.status;
    document.getElementById("busMaintenanceStatus").value = bus.maintenance_status;
    openModal("modalBus");
  };

  window.deleteBus = async function(id, busNumber) {
    if (!confirm(`Are you sure you want to delete bus "${busNumber}"?`)) return;
    try {
      const res = await fetch(`/admin/buses/${id}`, { method: "DELETE" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to delete bus");
      showToast(data.message);
      loadBuses();
      loadStats();
    } catch (err) {
      showToast(err.message, "error");
    }
  };

  // ==========================================
  // 4. DRIVER MANAGEMENT
  // ==========================================
  let allDrivers = [];
  async function loadDrivers() {
    try {
      const res = await fetch("/admin/drivers");
      if (!res.ok) throw new Error("Failed to load drivers");
      allDrivers = await res.json();
      renderDrivers(allDrivers);
    } catch (err) {
      showToast(err.message, "error");
    }
  }

  function renderDrivers(drivers) {
    const tbody = document.getElementById("driversTableBody");
    tbody.innerHTML = "";
    if (drivers.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="empty-state"><p>No drivers found</p></td></tr>`;
      return;
    }

    drivers.forEach(d => {
      const tr = document.createElement("tr");
      let statusBadge = "badge-success";
      if (d.status === "On Duty") statusBadge = "badge-purple";
      else if (d.status === "Off Duty") statusBadge = "badge-warning";
      else if (d.status === "Inactive") statusBadge = "badge-danger";

      tr.innerHTML = `
        <td><span class="id-tag">${d.driver_id}</span></td>
        <td><strong>${d.name}</strong></td>
        <td>${d.phone}</td>
        <td><span class="font-mono">${d.license_number}</span></td>
        <td><span class="badge ${statusBadge}">${d.status}</span></td>
        <td>
          <div class="table-actions">
            <button class="btn btn-secondary btn-sm" onclick="editDriver(${d.id})">Edit</button>
            <button class="btn btn-danger btn-sm" onclick="deleteDriver(${d.id}, '${d.name}')">Delete</button>
          </div>
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  document.getElementById("searchDrivers").addEventListener("input", (e) => {
    const val = e.target.value.toLowerCase();
    const filtered = allDrivers.filter(d => d.name.toLowerCase().includes(val) || d.driver_id.toLowerCase().includes(val) || d.license_number.toLowerCase().includes(val));
    renderDrivers(filtered);
  });

  const driverForm = document.getElementById("driverForm");
  driverForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const driverId = document.getElementById("driverDbId").value;
    const code = document.getElementById("driverCode").value.trim();
    const name = document.getElementById("driverName").value.trim();
    const phone = document.getElementById("driverPhone").value.trim();
    const license = document.getElementById("driverLicense").value.trim();
    const status = document.getElementById("driverStatus").value;

    const payload = {
      driver_id: code,
      name: name,
      phone: phone,
      license_number: license,
      status: status
    };

    // If new driver and user account fields filled
    if (!driverId) {
      const username = document.getElementById("driverUserAccount").value.trim();
      const email = document.getElementById("driverEmail").value.trim();
      const password = document.getElementById("driverPassword").value.trim();
      if (username && email && password) {
        payload.username = username;
        payload.email = email;
        payload.password = password;
      }
    }

    try {
      let res;
      if (driverId) {
        res = await fetch(`/admin/drivers/${driverId}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
      } else {
        res = await fetch("/admin/drivers", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
      }

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Error saving driver");

      showToast(driverId ? "Driver updated successfully" : "Driver created successfully");
      closeModal("modalDriver");
      loadDrivers();
      loadStats();
    } catch (err) {
      showToast(err.message, "error");
    }
  });

  window.openAddDriverModal = function() {
    document.getElementById("driverModalTitle").textContent = "Add New Driver";
    document.getElementById("driverDbId").value = "";
    document.getElementById("driverCode").value = "";
    document.getElementById("driverCode").disabled = false;
    document.getElementById("driverName").value = "";
    document.getElementById("driverPhone").value = "";
    document.getElementById("driverLicense").value = "";
    document.getElementById("driverStatus").value = "Active";
    document.getElementById("driverUserSection").style.display = "block";
    document.getElementById("driverUserAccount").value = "";
    document.getElementById("driverEmail").value = "";
    document.getElementById("driverPassword").value = "";
    openModal("modalDriver");
  };

  window.editDriver = function(id) {
    const drv = allDrivers.find(d => d.id === id);
    if (!drv) return;
    document.getElementById("driverModalTitle").textContent = "Edit Driver";
    document.getElementById("driverDbId").value = drv.id;
    document.getElementById("driverCode").value = drv.driver_id;
    document.getElementById("driverCode").disabled = true;
    document.getElementById("driverName").value = drv.name;
    document.getElementById("driverPhone").value = drv.phone;
    document.getElementById("driverLicense").value = drv.license_number;
    document.getElementById("driverStatus").value = drv.status;
    document.getElementById("driverUserSection").style.display = "none";
    openModal("modalDriver");
  };

  window.deleteDriver = async function(id, name) {
    if (!confirm(`Are you sure you want to delete driver "${name}"?`)) return;
    try {
      const res = await fetch(`/admin/drivers/${id}`, { method: "DELETE" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to delete driver");
      showToast(data.message);
      loadDrivers();
      loadStats();
    } catch (err) {
      showToast(err.message, "error");
    }
  };

  // ==========================================
  // 5. ROUTE MANAGEMENT
  // ==========================================
  let allRoutes = [];
  async function loadRoutes() {
    try {
      const res = await fetch("/admin/routes");
      if (!res.ok) throw new Error("Failed to load routes");
      allRoutes = await res.json();
      renderRoutes(allRoutes);
    } catch (err) {
      showToast(err.message, "error");
    }
  }

  function renderRoutes(routes) {
    const tbody = document.getElementById("routesTableBody");
    tbody.innerHTML = "";
    if (routes.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="empty-state"><p>No routes found</p></td></tr>`;
      return;
    }

    routes.forEach(r => {
      const tr = document.createElement("tr");
      const statusBadge = r.status === "Active" ? "badge-success" : "badge-danger";

      tr.innerHTML = `
        <td><span class="id-tag">${r.route_number}</span></td>
        <td><strong>${r.source}</strong></td>
        <td><strong>${r.destination}</strong></td>
        <td style="max-width: 250px; font-size: 0.8rem; color: var(--text-muted);">${r.stops || "None"}</td>
        <td><span class="badge ${statusBadge}">${r.status}</span></td>
        <td>
          <div class="table-actions">
            <button class="btn btn-secondary btn-sm" onclick="editRoute(${r.id})">Edit</button>
            <button class="btn btn-danger btn-sm" onclick="deleteRoute(${r.id}, '${r.route_number}')">Delete</button>
          </div>
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  document.getElementById("searchRoutes").addEventListener("input", (e) => {
    const val = e.target.value.toLowerCase();
    const filtered = allRoutes.filter(r => r.route_number.toLowerCase().includes(val) || r.source.toLowerCase().includes(val) || r.destination.toLowerCase().includes(val));
    renderRoutes(filtered);
  });

  const routeForm = document.getElementById("routeForm");
  routeForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const routeId = document.getElementById("routeId").value;
    const routeNumber = document.getElementById("routeNumber").value.trim();
    const source = document.getElementById("routeSource").value.trim();
    const destination = document.getElementById("routeDest").value.trim();
    const stops = document.getElementById("routeStops").value.trim();
    const status = document.getElementById("routeStatus").value;

    const payload = {
      route_number: routeNumber,
      source: source,
      destination: destination,
      stops: stops,
      status: status
    };

    try {
      let res;
      if (routeId) {
        res = await fetch(`/admin/routes/${routeId}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
      } else {
        res = await fetch("/admin/routes", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
      }

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Error saving route");

      showToast(routeId ? "Route updated successfully" : "Route created successfully");
      closeModal("modalRoute");
      loadRoutes();
      loadStats();
    } catch (err) {
      showToast(err.message, "error");
    }
  });

  window.openAddRouteModal = function() {
    document.getElementById("routeModalTitle").textContent = "Add New Route";
    document.getElementById("routeId").value = "";
    document.getElementById("routeNumber").value = "";
    document.getElementById("routeSource").value = "";
    document.getElementById("routeDest").value = "";
    document.getElementById("routeStops").value = "";
    document.getElementById("routeStatus").value = "Active";
    openModal("modalRoute");
  };

  window.editRoute = function(id) {
    const r = allRoutes.find(item => item.id === id);
    if (!r) return;
    document.getElementById("routeModalTitle").textContent = "Edit Route";
    document.getElementById("routeId").value = r.id;
    document.getElementById("routeNumber").value = r.route_number;
    document.getElementById("routeSource").value = r.source;
    document.getElementById("routeDest").value = r.destination;
    document.getElementById("routeStops").value = r.stops || "";
    document.getElementById("routeStatus").value = r.status;
    openModal("modalRoute");
  };

  window.deleteRoute = async function(id, num) {
    if (!confirm(`Are you sure you want to delete route "${num}"?`)) return;
    try {
      const res = await fetch(`/admin/routes/${id}`, { method: "DELETE" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to delete route");
      showToast(data.message);
      loadRoutes();
      loadStats();
    } catch (err) {
      showToast(err.message, "error");
    }
  };

  // ==========================================
  // 6. TRIPS MANAGEMENT
  // ==========================================
  let allTrips = [];
  async function loadTrips() {
    try {
      const res = await fetch("/admin/trips");
      if (!res.ok) throw new Error("Failed to load trips");
      allTrips = await res.json();
      renderTrips(allTrips);
    } catch (err) {
      showToast(err.message, "error");
    }
  }

  function renderTrips(trips) {
    const tbody = document.getElementById("tripsTableBody");
    tbody.innerHTML = "";
    if (trips.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="empty-state"><p>No trips scheduled</p></td></tr>`;
      return;
    }

    trips.forEach(t => {
      const tr = document.createElement("tr");
      let statusBadge = "badge-warning";
      if (t.status === "In Progress") statusBadge = "badge-purple";
      else if (t.status === "Completed") statusBadge = "badge-success";
      else if (t.status === "Cancelled") statusBadge = "badge-danger";
      else if (t.status === "Assigned") statusBadge = "badge-info";

      tr.innerHTML = `
        <td><span class="id-tag">#TR-${t.id}</span></td>
        <td><strong>${t.route_number}</strong><br><span style="font-size:0.75rem; color:var(--text-dim);">${t.source} &rarr; ${t.destination}</span></td>
        <td><span class="badge ${t.bus_number !== 'Unassigned' ? 'badge-info' : 'badge-warning'}">${t.bus_number}</span></td>
        <td>${t.driver_name}</td>
        <td>${t.departure_time} - ${t.arrival_time}</td>
        <td><span class="badge ${statusBadge}">${t.status}</span></td>
        <td>
          <div class="table-actions">
            <button class="btn btn-secondary btn-sm" onclick="editTrip(${t.id})">Edit</button>
            <button class="btn btn-danger btn-sm" onclick="deleteTrip(${t.id})">Delete</button>
          </div>
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  // Populate Route, Bus, and Driver dropdowns for trip creation
  async function populateTripDropdowns() {
    const routeSelect = document.getElementById("tripRoute");
    const busSelect = document.getElementById("tripBus");
    const driverSelect = document.getElementById("tripDriver");

    try {
      const [rRes, bRes, dRes] = await Promise.all([
        fetch("/admin/routes"),
        fetch("/admin/buses"),
        fetch("/admin/drivers")
      ]);
      const routes = await rRes.json();
      const buses = await bRes.json();
      const drivers = await dRes.json();

      routeSelect.innerHTML = routes.map(r => `<option value="${r.id}">${r.route_number} (${r.source} - ${r.destination})</option>`).join("");
      busSelect.innerHTML = `<option value="">-- None / Unassigned --</option>` +
        buses.map(b => `<option value="${b.id}">${b.bus_number} - ${b.bus_type} (${b.status})</option>`).join("");
      driverSelect.innerHTML = `<option value="">-- None / Unassigned --</option>` +
        drivers.map(d => `<option value="${d.id}">${d.driver_id} - ${d.name} (${d.status})</option>`).join("");
    } catch (e) {
      console.error("Failed to populate dropdowns", e);
    }
  }

  const tripForm = document.getElementById("tripForm");
  tripForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const tripId = document.getElementById("tripId").value;
    const routeId = parseInt(document.getElementById("tripRoute").value, 10);
    const busVal = document.getElementById("tripBus").value;
    const driverVal = document.getElementById("tripDriver").value;
    const depTime = document.getElementById("tripDepTime").value.trim();
    const arrTime = document.getElementById("tripArrTime").value.trim();
    const status = document.getElementById("tripStatus").value;

    const payload = {
      route_id: routeId,
      bus_id: busVal ? parseInt(busVal, 10) : null,
      driver_id: driverVal ? parseInt(driverVal, 10) : null,
      departure_time: depTime,
      arrival_time: arrTime,
      status: status
    };

    try {
      let res;
      if (tripId) {
        res = await fetch(`/admin/trips/${tripId}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
      } else {
        res = await fetch("/admin/trips", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
      }

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Error saving trip");

      showToast(tripId ? "Trip updated successfully" : "Trip created successfully");
      closeModal("modalTrip");
      loadTrips();
      loadStats();
    } catch (err) {
      showToast(err.message, "error");
    }
  });

  window.openAddTripModal = async function() {
    await populateTripDropdowns();
    document.getElementById("tripModalTitle").textContent = "Schedule New Trip";
    document.getElementById("tripId").value = "";
    document.getElementById("tripDepTime").value = "09:00 AM";
    document.getElementById("tripArrTime").value = "10:30 AM";
    document.getElementById("tripStatus").value = "Scheduled";
    openModal("modalTrip");
  };

  window.editTrip = async function(id) {
    await populateTripDropdowns();
    const t = allTrips.find(item => item.id === id);
    if (!t) return;
    document.getElementById("tripModalTitle").textContent = "Edit Trip";
    document.getElementById("tripId").value = t.id;
    document.getElementById("tripRoute").value = t.route_id;
    document.getElementById("tripBus").value = t.bus_id || "";
    document.getElementById("tripDriver").value = t.driver_id || "";
    document.getElementById("tripDepTime").value = t.departure_time;
    document.getElementById("tripArrTime").value = t.arrival_time;
    document.getElementById("tripStatus").value = t.status;
    openModal("modalTrip");
  };

  window.deleteTrip = async function(id) {
    if (!confirm(`Are you sure you want to delete Trip #${id}?`)) return;
    try {
      const res = await fetch(`/admin/trips/${id}`, { method: "DELETE" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to delete trip");
      showToast(data.message);
      loadTrips();
      loadStats();
    } catch (err) {
      showToast(err.message, "error");
    }
  };

  // ==========================================
  // 7. REPORTS
  // ==========================================
  async function loadReports() {
    try {
      const res = await fetch("/admin/reports");
      if (!res.ok) throw new Error("Failed to load reports");
      const data = await res.json();

      // Bus Status Bars
      renderStatBars("repBusStatus", data.bus_status, "var(--primary)");
      // Bus Maintenance Bars
      renderStatBars("repBusMaint", data.bus_maintenance, "var(--warning)");
      // Driver Status Bars
      renderStatBars("repDriverStatus", data.driver_status, "var(--success)");
      // Trip Status Bars
      renderStatBars("repTripStatus", data.trip_status, "var(--accent-purple)");

      // Route overview table in reports
      const rBody = document.getElementById("repRoutesBody");
      rBody.innerHTML = "";
      data.routes.forEach(r => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td><span class="id-tag">${r.route_number}</span></td>
          <td>${r.source} &rarr; ${r.destination}</td>
          <td><strong>${r.total_trips} Trips</strong></td>
          <td><span class="badge ${r.status === 'Active' ? 'badge-success' : 'badge-danger'}">${r.status}</span></td>
        `;
        rBody.appendChild(tr);
      });
    } catch (err) {
      showToast(err.message, "error");
    }
  }

  function renderStatBars(containerId, dataMap, color) {
    const container = document.getElementById(containerId);
    container.innerHTML = "";
    const total = Object.values(dataMap).reduce((a, b) => a + b, 0) || 1;

    for (const [key, count] of Object.entries(dataMap)) {
      const pct = Math.round((count / total) * 100);
      const div = document.createElement("div");
      div.className = "stat-bar-item";
      div.innerHTML = `
        <div class="stat-bar-header">
          <span>${key}</span>
          <strong>${count} (${pct}%)</strong>
        </div>
        <div class="stat-bar-progress">
          <div class="stat-bar-fill" style="width: ${pct}%; background: ${color};"></div>
        </div>
      `;
      container.appendChild(div);
    }
  }

  // ==========================================
  // 8. ACTIVITY LOGS
  // ==========================================
  async function loadActivityLogs() {
    try {
      const res = await fetch("/admin/activity-logs");
      if (!res.ok) throw new Error("Failed to load activity logs");
      const logs = await res.json();
      const tbody = document.getElementById("logsTableBody");
      tbody.innerHTML = "";

      if (logs.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="empty-state"><p>No activity logs recorded yet</p></td></tr>`;
        return;
      }

      logs.forEach(l => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td><span class="id-tag">#${l.id}</span></td>
          <td><strong>${l.username}</strong> <span class="badge ${l.role === 'admin' ? 'badge-purple' : 'badge-info'}">${l.role || 'System'}</span></td>
          <td><span class="badge badge-info">${l.action}</span></td>
          <td style="color: var(--text-muted); font-size: 0.85rem;">${l.details || ''}</td>
          <td style="font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-dim);">${l.timestamp}</td>
        `;
        tbody.appendChild(tr);
      });
    } catch (err) {
      showToast(err.message, "error");
    }
  }

  // Initial load
  loadStats();
});
