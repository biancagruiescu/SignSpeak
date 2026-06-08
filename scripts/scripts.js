// =========================================================================
// 1. MANAGEMENTUL CAMEREI WEB ȘI AL PREDICȚIILOR (SINCRONIZAT CU BACKEND-UL)
// =========================================================================
let predictInterval;

function startCamera() {
  const video = document.getElementById("video");
  const placeholder = document.querySelector(".camera-placeholder");

  if (!video) return;

  // Cerem acces la camera fizica/USB conectata la laptop
  navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
      video.srcObject = stream;
      video.style.display = "block";
      if (placeholder) placeholder.style.display = "none";
      
      // Odata ce porneste camera, trimitem un cadru transformat în Base64 la fiecare 500ms
      if (!predictInterval) {
        predictInterval = setInterval(sendFrameToBackend, 500);
      }
    })
    .catch(error => {
      alert("Camera can not be accessed. Verify the browser permissions!");
      console.error(error);
    });
}

// Trimite cadrul capturat direct ca JSON Base64 către backend-ul Flask
function sendFrameToBackend() {
  const video = document.getElementById("video");
  const canvas = document.getElementById("canvas");
  
  if (!video || video.videoWidth === 0) return; 

  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  const ctx = canvas.getContext("2d");
  
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

  canvas.toBlob(blob => {
    const formData = new FormData();
    formData.append("image", blob, "frame.jpg");

    // Eliminăm URL-ul complet (http://127.0.0.1:5000) ca să evităm problemele de CORS în browser
    fetch("/predict", {
      method: "POST",
      body: formData
    })
    .then(response => response.json())
    .then(data => {
      const letterElement = document.getElementById("currentLetter");
      if (letterElement) {
        // Dacă modelul a recunoscut o literă validă din cele 8 antrenate (A, B, C, L, O, V, W, Y)
        if (data.prediction && data.prediction !== "-" && data.prediction !== "No hand detected" && data.prediction !== "Invalid image") {
          letterElement.innerText = data.prediction;
        } else {
          letterElement.innerText = "-";
        }
      }
    })
    .catch(err => console.error("Eroare la predicție:", err));
  }, "image/jpeg");
}

// =========================================================================
// LOGICA PENTRU ADUNAREA LITERELOR ȘI SALVAREA LOR ÎN BAZA DE DATE
// =========================================================================

// 1. Ia litera recunoscută live și o lipește de celelalte pe ecran
function addLetter() {
  const currentLetter = document.getElementById("currentLetter").innerText;
  
  // Adăugăm doar dacă este o literă validă, nu o cratimă sau eroare
  if (currentLetter !== "-" && currentLetter !== "" && currentLetter !== "Error") {
    const sequenceSpan = document.getElementById("letterSequence");
   if (sequenceSpan.innerText.trim() === "") {
      sequenceSpan.innerText = currentLetter;
    } else {
      sequenceSpan.innerText += "-" + currentLetter;
    }
  }
}

// 2. Șterge tot șirul de litere de pe ecran ca să o iei de la capăt
function clearSequence() {
  document.getElementById("letterSequence").innerText = "";
}

// 3. Ia șirul de litere păstrat pe ecran și îl trimite la profilul utilizatorului
function saveSequenceToDB() {
  const email = getLoggedInUser();
  if (!email) {
    alert("Trebuie să fii logat pentru a salva!");
    return;
  }

  const sequence = document.getElementById("letterSequence").innerText;
  if (sequence === "") {
    alert("Nu ai adăugat nicio literă de salvat!");
    return;
  }

  // Trimitem secvența către backend-ul tău Python (app.py)
  fetch("/save_translation", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: email,
      input_text: "Secvență litere ASL", // Sursa datelor
      translated_text: sequence        // Literele adunate (ex: "VAL")
    })
  })
  .then(response => response.json())
  .then(data => {
    if (data.message) {
      alert("Literele au fost salvate cu succes în profilul tău!");
      clearSequence(); // Curățăm ecranul automat după ce s-a salvat
    } else {
      alert("Eroare la salvare: " + data.error);
    }
  })
  .catch(err => console.error("Eroare la conexiunea de salvare:", err));
}

// =========================================================================
// 3. VALIDARE ȘI TRIMITERE PENTRU CONT NOU (SIGN UP)
// =========================================================================
function validateSignup() {
  const name = document.getElementById("name").value.trim();
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  const confirmPassword = document.getElementById("confirmPassword").value;
  const error = document.getElementById("error");

  if (!error) return false;
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

  // Conectare cu ruta /signup din app.py
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
        alert(data.message || "Signed up successfully!");
        window.location.href = "login-page.html";
      }
    })
    .catch(() => {
      error.innerText = "Server error connection.";
    });

  return false;
}


// =========================================================================
// 4. VALIDARE ȘI AUTENTIFICARE UTILIZATOR (SIGN IN)
// =========================================================================
function validateLogin() {
  const emailInput = document.getElementById("loginEmail");
  const passwordInput = document.getElementById("loginPassword");
  const error = document.getElementById("loginError");

  if (!emailInput || !passwordInput || !error) {
    alert("Login form structure error.");
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

  // Apelăm endpoint-ul exact '/signin' configurat în app.py
  fetch("http://127.0.0.1:5000/signin", {
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
        alert(data.message || "Autentificare reușită!");
        window.location.href = "userpage.html";
      }
    })
    .catch(() => {
      error.innerText = "Server login error connection.";
    });

  return false;
}


// =========================================================================
// 5. SESIUNE ȘI INFORMAȚII CONT UTILIZATOR (USER PROFILE & HISTORY)
// =========================================================================
function goToCamera() {
  window.location.href = "camera.html";
}

function saveLoggedInUser(email) {
  localStorage.setItem("loggedInUserEmail", email);
}

// Returnează email-ul stocat local pentru a ști cine face traducerea
function getLoggedInUser() {
  return localStorage.getItem("loggedInUserEmail");
}

function logout() {
  localStorage.removeItem("loggedInUserEmail");
  if (predictInterval) clearInterval(predictInterval);
  window.location.href = "login-page.html";
}

function loadUserPage() {
  const email = getLoggedInUser();
  if (!email) {
    window.location.href = "login-page.html";
    return;
  }
  // incarca din backend istoricul de traduceri stocat în SQLite pentru utilizatorul curent
  fetch(`http://127.0.0.1:5000/history/${encodeURIComponent(email)}`)
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        alert(data.error);
        return;
      }
      // Seteaza datele în profilul utilizatorului (din userpage.html)
      if (document.getElementById("userName")) {
         // Foloseste prima parte din email ca nume implicit sau email-ul complet ca fallback
         document.getElementById("userName").innerText = email.split('@')[0];
      }
      if (document.getElementById("userEmail")) {
         document.getElementById("userEmail").innerText = email;
      }
      const historyList = document.getElementById("historyList");
      if (!historyList) return;
      historyList.innerHTML = "";

      if (!data || data.length === 0) {
historyList.innerHTML = `<p class="empty-history">No saved predictions yet.</p>`;
        return;
      }
      // Populeaza vizual interfata cu istoricul real adus din baza de date
      data.forEach(item => {
        const div = document.createElement("div");
        div.className = "history-item";
       div.innerHTML = `
  <div class="history-input"><strong>Source:</strong> ASL Camera</div>
  <div class="history-output"><strong>Recognized letters:</strong> ${item.translated_text}</div>
  <small style="color: #888;">${item.timestamp || ''}</small>
`;
        historyList.appendChild(div);
      });
    })
    .catch(() => {
      alert("Could not load user data history from database.");
    });
}

function updateCameraNavbar() {
  const navActions = document.getElementById("cameraNavActions");
  if (!navActions) return;

  const email = getLoggedInUser();

  if (email) {
    navActions.innerHTML = `
      <a href="index.html" class="back-link">← Back</a>
      <a href="userpage.html" class="sign-btn">👤 Profile</a>
      <button class="sign-btn" onclick="logout()" style="cursor:pointer;">Logout</button>
    `;
  } else {
    navActions.innerHTML = `
      <a href="index.html" class="back-link">← Back</a>
      <a href="login-page.html" class="sign-btn">Sign In</a>
    `;
  }
}

document.addEventListener("DOMContentLoaded", function () {
  updateCameraNavbar();
});