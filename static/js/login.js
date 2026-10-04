// ===================================================================
// LOGIN JAVASCRIPT - AUTHENTICATION & FORM HANDLING
// ===================================================================

document.addEventListener("DOMContentLoaded", () => {
  const loginForm = document.getElementById("loginForm");
  const usernameInput = document.getElementById("username");
  const passwordInput = document.getElementById("password");
  const togglePasswordBtn = document.getElementById("togglePassword");
  const loginBtn = document.getElementById("loginBtn");
  const loginBtnText = document.getElementById("loginBtnText");
  const loginSpinner = document.getElementById("loginSpinner");
  const alertError = document.getElementById("alertError");
  const alertText = document.getElementById("alertText");

  // Check URL query parameters for feedback messages
  const urlParams = new URLSearchParams(window.location.search);
  const errorParam = urlParams.get("error");
  const warningParam = urlParams.get("warning");

  if (errorParam === "auth_required") {
    showError("Please log in to access this page.");
  } else if (errorParam === "session_expired") {
    showError("Your session has expired. Please log in again.");
  } else if (errorParam === "unauthorized" || warningParam === "forbidden") {
    showError("Access denied: You do not have permissions for that area.");
  }

  // Toggle Password Visibility
  if (togglePasswordBtn) {
    togglePasswordBtn.addEventListener("click", () => {
      const isPassword = passwordInput.getAttribute("type") === "password";
      passwordInput.setAttribute("type", isPassword ? "text" : "password");
      togglePasswordBtn.innerHTML = isPassword
        ? `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M3.98 8.223A10.477 10.477 0 0 0 1.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.451 10.451 0 0 1 12 4.5c4.756 0 8.773 3.162 10.065 7.498a10.522 10.522 0 0 1-4.293 5.774M6.228 6.228 3 3m3.228 3.228 3.65 3.65m7.894 7.894L21 21m-3.228-3.228-3.65-3.65m0 0a3 3 0 1 0-4.243-4.243m4.242 4.242L9.88 9.88" /></svg>`
        : `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z" /><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" /></svg>`;
    });
  }

  // Quick Demo Credentials Buttons
  document.querySelectorAll(".demo-chip").forEach((btn) => {
    btn.addEventListener("click", () => {
      const u = btn.getAttribute("data-user");
      const p = btn.getAttribute("data-pass");
      usernameInput.value = u;
      passwordInput.value = p;
      hideError();
      usernameInput.focus();
    });
  });

  // Handle Form Submission
  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      hideError();

      const username = usernameInput.value.trim();
      const password = passwordInput.value.trim();

      if (!username || !password) {
        showError("Please enter both username/email and password.");
        return;
      }

      setLoading(true);

      try {
        const response = await fetch("/auth/login", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.detail || "Authentication failed. Please verify your credentials.");
        }

        // Store token in localStorage for API client authorization header as backup
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("user_role", data.role);
        localStorage.setItem("username", data.username);

        // Redirect to role dashboard determined by the backend
        window.location.href = data.redirect_url;
      } catch (err) {
        setLoading(false);
        showError(err.message);
      }
    });
  }

  function showError(msg) {
    alertText.textContent = msg;
    alertError.classList.add("active");
  }

  function hideError() {
    alertError.classList.remove("active");
    alertText.textContent = "";
  }

  function setLoading(isLoading) {
    if (isLoading) {
      loginBtn.disabled = true;
      loginBtnText.textContent = "Authenticating...";
      loginSpinner.style.display = "inline-block";
    } else {
      loginBtn.disabled = false;
      loginBtnText.textContent = "Sign In to Depot";
      loginSpinner.style.display = "none";
    }
  }
});
