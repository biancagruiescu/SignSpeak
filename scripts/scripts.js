function startCamera() {
  const video = document.getElementById("video");
  const placeholder = document.querySelector(".camera-placeholder");

  if (!video) return;

  navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
      video.srcObject = stream;
      video.style.display = "block";
      if (placeholder) {
        placeholder.style.display = "none";
      }
    })
    .catch(error => {
      alert("Camera nu poate fi accesată.");
      console.error(error);
    });
}

function validateSignup() {
  const name = document.getElementById("name").value.trim();
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  const confirmPassword = document.getElementById("confirmPassword").value;
  const error = document.getElementById("error");

  error.innerText = "";

  const nameRegex = /^[A-Za-z\s]+$/;
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  if (name === "" || email === "" || password === "" || confirmPassword === "") {
    error.innerText = "All fields are required.";
    return false;
  }

  if (!nameRegex.test(name)) {
    error.innerText = "Name must contain only letters.";
    return false;
  }

  if (!emailRegex.test(email)) {
    error.innerText = "Invalid email format.";
    return false;
  }

  if (password.length < 6) {
    error.innerText = "Password must be at least 6 characters.";
    return false;
  }

  if (password !== confirmPassword) {
    error.innerText = "Passwords do not match.";
    return false;
  }

  fetch("http://127.0.0.1:5000/signup", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      username: name,
      email: email,
      password: password
    })
  })
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        error.innerText = data.error;
      } else {
        alert(data.message);
        window.location.href = "login-page.html";
      }
    })
    .catch(() => {
      error.innerText = "Server error.";
    });

  return false;
}

function validateLogin() {
  const emailInput = document.getElementById("loginEmail");
  const passwordInput = document.getElementById("loginPassword");
  const error = document.getElementById("loginError");

  if (!emailInput || !passwordInput || !error) {
    alert("Login form is not connected correctly.");
    return false;
  }

  const email = emailInput.value.trim();
  const password = passwordInput.value;

  error.innerText = "";

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  if (email === "" || password === "") {
    error.innerText = "All fields are required.";
    return false;
  }

  if (!emailRegex.test(email)) {
    error.innerText = "Invalid email format.";
    return false;
  }

  if (password.length < 6) {
    error.innerText = "Password must be at least 6 characters.";
    return false;
  }

  fetch("http://127.0.0.1:5000/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      email: email,
      password: password
    })
  })
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        error.innerText = data.error;
      } else {
        saveLoggedInUser(email);
        alert(data.message);
        window.location.href = "userpage.html";
      }
    })
    .catch(() => {
      error.innerText = "Server error.";
    });

  return false;
}

function goToCamera() {
  window.location.href = "camera.html";
}

function saveLoggedInUser(email) {
  localStorage.setItem("loggedInUserEmail", email);
}

function getLoggedInUser() {
  return localStorage.getItem("loggedInUserEmail");
}

function logout() {
  localStorage.removeItem("loggedInUserEmail");
  window.location.href = "login-page.html";
}

function loadUserPage() {
  const email = getLoggedInUser();

  if (!email) {
    window.location.href = "login-page.html";
    return;
  }

fetch(`http://127.0.0.1:5000/user/${encodeURIComponent(email)}`)
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        alert(data.error);
        return;
      }

      document.getElementById("userName").innerText = data.username;
      document.getElementById("userEmail").innerText = data.email;

      const historyList = document.getElementById("historyList");
      historyList.innerHTML = "";

      if (!data.history || data.history.length === 0) {
        historyList.innerHTML = `<p class="empty-history">No translations yet.</p>`;
        return;
      }

      data.history.forEach(item => {
        const div = document.createElement("div");
        div.className = "history-item";
        div.innerHTML = `
          <div class="history-input"><strong>Input:</strong> ${item.input_text}</div>
          <div class="history-output"><strong>Output:</strong> ${item.translated_text}</div>
        `;
        historyList.appendChild(div);
      });
    })
    .catch(() => {
      alert("Could not load user data.");
    });
}