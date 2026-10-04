// ===================================================================
// OPERATIONS DASHBOARD CONTROLLER
// ===================================================================

document.addEventListener("DOMContentLoaded", () => {
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
        pageTitle.textContent = nav.querySelector("span") ? nav.querySelector("span").textContent : "Operations";
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

    if (viewName === "dashboard") loadOperationsStats();
    else if (viewName === "buses") loadOperationalBuses();
    else if (viewName === "drivers") loadOperationalDrivers();
    else if (viewName === "routes") loadOperationalRoutes();
    else if (viewName === "trips") loadOperationalTrips();
    else if (viewName === "assignments") loadAssignments();
    else if (viewName === "reports") loadReports();
  }

  // Logout
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

  // Clock
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
  // 1. STATS (OPERATIONS DASHBOARD)
  // ==========================================
  async function loadOperationsStats() {
    try {
      const res = await fetch("/operations/stats");
      if (!res.ok) throw new Error("Failed to load operations stats");
      const data = await res.json();

      document.getElementById("opsAvailBuses").textContent = data.available_buses;
      document.getElementById("opsAssignedBuses").textContent = data.assigned_buses;
      document.getElementById("opsAvailDrivers").textContent = data.available_drivers;
      document.getElementById("opsTodayTrips").textContent = data.today_trips;
      document.getElementById("opsActiveTrips").textContent = data.active_trips;
      document.getElementById("opsPendingAssign").textContent = data.pending_assignments;
    } catch (err) {
      console.error(err);
    }
  }

  // ==========================================
  // 2. BUS OPERATIONS
  // ==========================================
  let allBuses = [];
  async function loadOperationalBuses() {
    try {
      const res = await fetch("/operations/buses");
      if (!res.ok) throw new Error("Failed to fetch buses");
      allBuses = await res.json();
      renderOperationalBuses(allBuses);
    } catch (err) {
      showToast(err.message, "error");
    }
  }

  function renderOperationalBuses(buses) {
    const tbody = document.getElementById("opsBusesTableBody");
    tbody.innerHTML = "";
    if (buses.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="empty-state"><p>No buses found</p></td></tr>`;
      return;
    }

    buses.forEach(b => {
      const tr = document.createElement("tr");
      let statusBadge = "badge-success";
      if (b.status === "Assigned") statusBadge = "badge-info";
      else if (b.status === "On Route") statusBadge = "badge-purple";
      else if (b.status === "Out of Service") statusBadge = "badge-danger";

      tr.innerHTML = `
        <td><span class="id-tag">${b.bus_number}</span></td>
        <td><strong>${b.registration_number}</strong></td>
        <td>${b.bus_type} (${b.capacity} seats)</td>
        <td><span class="badge ${statusBadge}">${b.status}</span></td>
        <td><span class="badge ${b.maintenance_status === 'Good' ? 'badge-success' : 'badge-warning'}">${b.maintenance_status}</span></td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="openUpdateBusStatusModal(${b.id}, '${b.bus_number}', '${b.status}', '${b.maintenance_status}')">Change Status</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  document.getElementById("searchOpsBuses").addEventListener("input", (e) => {
    const val = e.target.value.toLowerCase();
    renderOperationalBuses(allBuses.filter(b => b.bus_number.toLowerCase().includes(val) || b.registration_number.toLowerCase().includes(val)));
  });

  window.openUpdateBusStatusModal = function(id, number, status, maint) {
    document.getElementById("opsBusStatusId").value = id;
    document.getElementById("opsBusNumberSpan").textContent = number;
    document.getElementById("opsBusStatusSelect").value = status;
    document.getElementById("opsBusMaintSelect").value = maint;
    openModal("modalOpsBusStatus");
  };

  const opsBusStatusForm = document.getElementById("opsBusStatusForm");
  opsBusStatusForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = document.getElementById("opsBusStatusId").value;
    const status = document.getElementById("opsBusStatusSelect").value;
    const maint = document.getElementById("opsBusMaintSelect").value;

    try {
      const res = await fetch(`/operations/buses/${id}/status`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: status, maintenance_status: maint })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to update bus status");

      showToast("Bus operational status updated");
      closeModal("modalOpsBusStatus");
      loadOperationalBuses();
      loadOperationsStats();
    } catch (err) {
      showToast(err.message, "error");
    }
  });

  // ==========================================
  // 3. DRIVER OPERATIONS
  // ==========================================
  let allDrivers = [];
  async function loadOperationalDrivers() {
    try {
      const res = await fetch("/operations/drivers");
      if (!res.ok) throw new Error("Failed to fetch drivers");
      allDrivers = await res.json();
      renderOperationalDrivers(allDrivers);
    } catch (err) {
      showToast(err.message, "error");
    }
  }

  function renderOperationalDrivers(drivers) {
    const tbody = document.getElementById("opsDriversTableBody");
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
          <button class="btn btn-secondary btn-sm" onclick="openUpdateDriverStatusModal(${d.id}, '${d.name}', '${d.status}')">Update Duty</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  document.getElementById("searchOpsDrivers").addEventListener("input", (e) => {
    const val = e.target.value.toLowerCase();
    renderOperationalDrivers(allDrivers.filter(d => d.name.toLowerCase().includes(val) || d.driver_id.toLowerCase().includes(val)));
  });

  window.openUpdateDriverStatusModal = function(id, name, status) {
    document.getElementById("opsDriverStatusId").value = id;
    document.getElementById("opsDriverNameSpan").textContent = name;
    document.getElementById("opsDriverStatusSelect").value = status;
    openModal("modalOpsDriverStatus");
  };

  const opsDriverStatusForm = document.getElementById("opsDriverStatusForm");
  opsDriverStatusForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = document.getElementById("opsDriverStatusId").value;
    const status = document.getElementById("opsDriverStatusSelect").value;

    try {
      const res = await fetch(`/operations/drivers/${id}/status`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: status })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to update driver status");

      showToast("Driver duty status updated");
      closeModal("modalOpsDriverStatus");
      loadOperationalDrivers();
      loadOperationsStats();
    } catch (err) {
      showToast(err.message, "error");
    }
  });

  // ==========================================
  // 4. ROUTE OPERATIONS
  // ==========================================
  async function loadOperationalRoutes() {
    try {
      const res = await fetch("/operations/routes");
      if (!res.ok) throw new Error("Failed to load routes");
      const routes = await res.json();
      const tbody = document.getElementById("opsRoutesTableBody");
      tbody.innerHTML = "";

      routes.forEach(r => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td><span class="id-tag">${r.route_number}</span></td>
          <td><strong>${r.source}</strong></td>
          <td><strong>${r.destination}</strong></td>
          <td style="font-size:0.8rem; color:var(--text-muted);">${r.stops || "None"}</td>
          <td><span class="badge badge-success">${r.status}</span></td>
        `;
        tbody.appendChild(tr);
      });
    } catch (err) {
      showToast(err.message, "error");
    }
  }

  // ==========================================
  // 5. TRIP MANAGEMENT & ASSIGNMENTS
  // ==========================================
  let allTrips = [];
  async function loadOperationalTrips() {
    try {
      const res = await fetch("/operations/trips");
      if (!res.ok) throw new Error("Failed to load trips");
      allTrips = await res.json();
      renderOperationalTrips(allTrips);
    } catch (err) {
      showToast(err.message, "error");
    }
  }

  function renderOperationalTrips(trips) {
    const tbody = document.getElementById("opsTripsTableBody");
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
            <button class="btn btn-secondary btn-sm" onclick="openEditTripModal(${t.id})">Edit / Reassign</button>
            <select class="form-control" style="width: auto; padding: 0.3rem 0.5rem; font-size: 0.75rem;" onchange="updateTripStatus(${t.id}, this.value)">
              <option value="" disabled selected>Change Status</option>
              <option value="Scheduled">Scheduled</option>
              <option value="Assigned">Assigned</option>
              <option value="In Progress">In Progress</option>
              <option value="Completed">Completed</option>
              <option value="Cancelled">Cancelled</option>
            </select>
          </div>
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  window.updateTripStatus = async function(tripId, newStatus) {
    try {
      const res = await fetch(`/operations/trips/${tripId}/status`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to update trip status");

      showToast(`Trip #${tripId} status changed to ${newStatus}`);
      loadOperationalTrips();
      loadOperationsStats();
    } catch (err) {
      showToast(err.message, "error");
    }
  };

  async function populateTripDropdowns() {
    const routeSelect = document.getElementById("opsTripRoute");
    const busSelect = document.getElementById("opsTripBus");
    const driverSelect = document.getElementById("opsTripDriver");

    try {
      const [rRes, bRes, dRes] = await Promise.all([
        fetch("/operations/routes"),
        fetch("/operations/buses"),
        fetch("/operations/drivers")
      ]);
      const routes = await rRes.json();
      const buses = await bRes.json();
      const drivers = await dRes.json();

      routeSelect.innerHTML = routes.map(r => `<option value="${r.id}">${r.route_number} (${r.source} - ${r.destination})</option>`).join("");
      busSelect.innerHTML = `<option value="">-- Unassigned --</option>` +
        buses.map(b => `<option value="${b.id}">${b.bus_number} - ${b.bus_type} (${b.status})</option>`).join("");
      driverSelect.innerHTML = `<option value="">-- Unassigned --</option>` +
        drivers.map(d => `<option value="${d.id}">${d.driver_id} - ${d.name} (${d.status})</option>`).join("");
    } catch (e) {
      console.error(e);
    }
  }

  window.openCreateTripModal = async function() {
    await populateTripDropdowns();
    document.getElementById("opsTripModalTitle").textContent = "Dispatch / Create Trip";
    document.getElementById("opsTripId").value = "";
    document.getElementById("opsTripDep").value = "09:30 AM";
    document.getElementById("opsTripArr").value = "11:00 AM";
    openModal("modalOpsTrip");
  };

  window.openEditTripModal = async function(id) {
    await populateTripDropdowns();
    const t = allTrips.find(item => item.id === id);
    if (!t) return;
    document.getElementById("opsTripModalTitle").textContent = "Edit / Reassign Trip";
    document.getElementById("opsTripId").value = t.id;
    document.getElementById("opsTripRoute").value = t.route_id;
    document.getElementById("opsTripBus").value = t.bus_id || "";
    document.getElementById("opsTripDriver").value = t.driver_id || "";
    document.getElementById("opsTripDep").value = t.departure_time;
    document.getElementById("opsTripArr").value = t.arrival_time;
    openModal("modalOpsTrip");
  };

  const opsTripForm = document.getElementById("opsTripForm");
  opsTripForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const tripId = document.getElementById("opsTripId").value;
    const routeId = parseInt(document.getElementById("opsTripRoute").value, 10);
    const busVal = document.getElementById("opsTripBus").value;
    const driverVal = document.getElementById("opsTripDriver").value;
    const dep = document.getElementById("opsTripDep").value.trim();
    const arr = document.getElementById("opsTripArr").value.trim();

    const payload = {
      route_id: routeId,
      bus_id: busVal ? parseInt(busVal, 10) : null,
      driver_id: driverVal ? parseInt(driverVal, 10) : null,
      departure_time: dep,
      arrival_time: arr,
      status: (busVal && driverVal) ? "Assigned" : "Scheduled"
    };

    try {
      let res;
      if (tripId) {
        res = await fetch(`/operations/trips/${tripId}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
      } else {
        res = await fetch("/operations/trips", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
      }

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Error scheduling trip");

      showToast(tripId ? "Trip updated & reassigned successfully" : "Trip scheduled successfully");
      closeModal("modalOpsTrip");
      loadOperationalTrips();
      loadOperationsStats();
    } catch (err) {
      showToast(err.message, "error");
    }
  });

  // ==========================================
  // 6. ASSIGNMENTS
  // ==========================================
  async function loadAssignments() {
    try {
      const res = await fetch("/operations/assignments");
      if (!res.ok) throw new Error("Failed to load assignments");
      const list = await res.json();
      const tbody = document.getElementById("opsAssignmentsTableBody");
      tbody.innerHTML = "";

      if (list.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="empty-state"><p>No assignments recorded yet</p></td></tr>`;
        return;
      }

      list.forEach(a => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td><span class="id-tag">#AS-${a.id}</span></td>
          <td><span class="badge badge-info">${a.bus_number}</span></td>
          <td><strong>${a.driver_name}</strong></td>
          <td>${a.notes || 'Trip Duty'}</td>
          <td><span class="badge ${a.status === 'Active' ? 'badge-success' : 'badge-purple'}">${a.status}</span></td>
          <td style="font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-dim);">${a.assigned_date}</td>
        `;
        tbody.appendChild(tr);
      });
    } catch (err) {
      showToast(err.message, "error");
    }
  }

  // ==========================================
  // 7. REPORTS
  // ==========================================
  async function loadReports() {
    try {
      const res = await fetch("/operations/reports");
      if (!res.ok) throw new Error("Failed to load reports");
      const data = await res.json();

      renderStatBars("opsRepBusStatus", data.bus_status, "var(--primary)");
      renderStatBars("opsRepDriverStatus", data.driver_status, "var(--success)");
      renderStatBars("opsRepTripStatus", data.trip_status, "var(--accent-purple)");
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

  // Initial load
  loadOperationsStats();
});
