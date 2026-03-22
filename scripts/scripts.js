//camera html
    function startCamera() {
      const video = document.getElementById("video");
      const placeholder = document.querySelector(".camera-placeholder");

      navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
          video.srcObject = stream;
          video.style.display = "block";
          placeholder.style.display = "none";
        })
        .catch(error => {
          alert("Camera nu poate fi accesată.");
          console.error(error);
        });
    }
