// ===================================================================
// DRIVER DASHBOARD CONTROLLER
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
        pageTitle.textContent = nav.querySelector("span") ? nav.querySelector("span").textContent : "Driver Portal";
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

    if (viewName === "dashboard" || viewName === "mybus" || viewName === "myroute") loadDriverAssignment();
    else if (viewName === "schedule") loadDriverSchedule();
    else if (viewName === "profile") loadDriverProfile();
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

  let activeAssignmentData = null;

  // ==========================================
  // 1. DRIVER ASSIGNMENT & DASHBOARD
  // ==========================================
  async function loadDriverAssignment() {
    try {
      const res = await fetch("/driver/assignment");
      if (!res.ok) throw new Error("Failed to load driver assignment");
      activeAssignmentData = await res.json();

      const { driver, assigned_bus, current_trip } = activeAssignmentData;

      // Update Header info
      document.getElementById("driverBadgeName").textContent = driver.name;
      document.getElementById("driverHeroName").textContent = driver.name;
      document.getElementById("driverHeroCode").textContent = driver.driver_id;
      document.getElementById("driverHeroStatus").textContent = driver.status;

      // Update Assigned Bus Card
      if (assigned_bus) {
        document.getElementById("drvBusNumber").textContent = assigned_bus.bus_number;
        document.getElementById("drvBusReg").textContent = assigned_bus.registration_number;
        document.getElementById("drvBusType").textContent = `${assigned_bus.bus_type} (${assigned_bus.capacity} seats)`;
        document.getElementById("drvBusStatus").textContent = assigned_bus.status;

        // Populate dedicated "My Bus" tab
        document.getElementById("tabBusNumber").textContent = assigned_bus.bus_number;
        document.getElementById("tabBusReg").textContent = assigned_bus.registration_number;
        document.getElementById("tabBusType").textContent = assigned_bus.bus_type;
        document.getElementById("tabBusCap").textContent = `${assigned_bus.capacity} Passengers`;
        document.getElementById("tabBusStatus").textContent = assigned_bus.status;
        document.getElementById("tabBusMaint").textContent = assigned_bus.maintenance_status;
        document.getElementById("busCardState").style.display = "block";
        document.getElementById("noBusMessage").style.display = "none";
      } else {
        document.getElementById("drvBusNumber").textContent = "None Assigned";
        document.getElementById("drvBusReg").textContent = "Awaiting Fleet Assignment";
        document.getElementById("drvBusType").textContent = "-";
        document.getElementById("drvBusStatus").textContent = "Standby";

        document.getElementById("busCardState").style.display = "none";
        document.getElementById("noBusMessage").style.display = "block";
      }

      // Update Current Trip Banner & My Route Tab
      const banner = document.getElementById("currentTripBanner");
      if (current_trip) {
        banner.style.display = "flex";
        document.getElementById("drvTripId").textContent = `#TR-${current_trip.id}`;
        document.getElementById("drvRouteNumber").textContent = current_trip.route_number;
        document.getElementById("drvRouteCorridor").textContent = `${current_trip.source} ➔ ${current_trip.destination}`;
        document.getElementById("drvTripTimes").textContent = `${current_trip.departure_time} - ${current_trip.arrival_time}`;
        document.getElementById("drvTripStatusBadge").textContent = current_trip.status;

        // Trip action buttons
        const actionArea = document.getElementById("tripActionArea");
        actionArea.innerHTML = "";

        if (current_trip.status === "Scheduled" || current_trip.status === "Assigned") {
          actionArea.innerHTML = `
            <button class="btn btn-primary" onclick="setTripStatus(${current_trip.id}, 'In Progress')">
              🚀 Start Trip Now
            </button>
          `;
        } else if (current_trip.status === "In Progress") {
          actionArea.innerHTML = `
            <button class="btn btn-success" onclick="setTripStatus(${current_trip.id}, 'Completed')">
              🏁 Complete Trip
            </button>
          `;
        }

        // Populate dedicated "My Route" tab
        document.getElementById("tabRouteNum").textContent = current_trip.route_number;
        document.getElementById("tabRouteCorridor").textContent = `${current_trip.source} to ${current_trip.destination}`;
        document.getElementById("tabRouteSchedule").textContent = `Departure: ${current_trip.departure_time} | Est. Arrival: ${current_trip.arrival_time}`;
        document.getElementById("routeCardState").style.display = "block";
        document.getElementById("noRouteMessage").style.display = "none";
      } else {
        banner.style.display = "none";
        document.getElementById("routeCardState").style.display = "none";
        document.getElementById("noRouteMessage").style.display = "block";
      }
    } catch (err) {
      console.error(err);
    }
  }

  window.setTripStatus = async function(tripId, status) {
    try {
      const res = await fetch(`/driver/trip/${tripId}/status`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: status })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to update trip status");

      showToast(`Trip #${tripId} is now marked ${status}!`);
      loadDriverAssignment();
      loadDriverSchedule();
    } catch (err) {
      showToast(err.message, "error");
    }
  };

  // ==========================================
  // 2. DRIVER SCHEDULE
  // ==========================================
  async function loadDriverSchedule() {
    try {
      const res = await fetch("/driver/schedule");
      if (!res.ok) throw new Error("Failed to load driver schedule");
      const trips = await res.json();
      const tbody = document.getElementById("drvScheduleTableBody");
      tbody.innerHTML = "";

      if (trips.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="empty-state"><p>No trips scheduled for you</p></td></tr>`;
        return;
      }

      trips.forEach(t => {
        const tr = document.createElement("tr");
        let statusBadge = "badge-warning";
        if (t.status === "In Progress") statusBadge = "badge-purple";
        else if (t.status === "Completed") statusBadge = "badge-success";
        else if (t.status === "Cancelled") statusBadge = "badge-danger";
        else if (t.status === "Assigned") statusBadge = "badge-info";

        let actionBtn = "-";
        if (t.status === "Scheduled" || t.status === "Assigned") {
          actionBtn = `<button class="btn btn-primary btn-sm" onclick="setTripStatus(${t.id}, 'In Progress')">Start Trip</button>`;
        } else if (t.status === "In Progress") {
          actionBtn = `<button class="btn btn-success btn-sm" onclick="setTripStatus(${t.id}, 'Completed')">Complete Trip</button>`;
        }

        tr.innerHTML = `
          <td><span class="id-tag">#TR-${t.id}</span></td>
          <td><strong>${t.route_number}</strong><br><span style="font-size:0.75rem; color:var(--text-dim);">${t.source} &rarr; ${t.destination}</span></td>
          <td><span class="badge ${t.bus_number !== 'Unassigned' ? 'badge-info' : 'badge-warning'}">${t.bus_number}</span></td>
          <td>${t.departure_time} - ${t.arrival_time}</td>
          <td><span class="badge ${statusBadge}">${t.status}</span></td>
          <td>${actionBtn}</td>
        `;
        tbody.appendChild(tr);
      });
    } catch (err) {
      showToast(err.message, "error");
    }
  }

  // ==========================================
  // 3. DRIVER PROFILE
  // ==========================================
  async function loadDriverProfile() {
    try {
      const res = await fetch("/driver/profile");
      if (!res.ok) throw new Error("Failed to load driver profile");
      const p = await res.json();

      document.getElementById("profName").textContent = p.name;
      document.getElementById("profCode").textContent = p.driver_id;
      document.getElementById("profPhone").textContent = p.phone;
      document.getElementById("profLicense").textContent = p.license_number;
      document.getElementById("profStatus").textContent = p.status;
      document.getElementById("profUsername").textContent = p.username || "-";
      document.getElementById("profEmail").textContent = p.email || "-";
    } catch (err) {
      showToast(err.message, "error");
    }
  }

  // Initial load
  loadDriverAssignment();
});
