document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const dropZone = document.getElementById("dropZone");
  const fileInput = document.createElement("input");
  fileInput.type = "file";
  fileInput.accept = "image/*";
  fileInput.style.display = "none";
  document.body.appendChild(fileInput);

  const generateBtn = document.getElementById("generateBtn");
  const feedback = document.getElementById("feedback");
  const captionResult = document.getElementById("captionResult");
  const captionBox = document.getElementById("captionBox");

  // History
  const historyIcon = document.getElementById("historyIcon");
  const historyPanel = document.getElementById("historyPanel");
  const historyList = document.getElementById("historyList");
  let captionHistory = [];

  // Toggle history panel
  historyIcon.addEventListener("click", () => {
    historyPanel.style.display =
      historyPanel.style.display === "block" ? "none" : "block";
  });

  function addToHistory(caption) {
    captionHistory.unshift(caption);
    renderHistory();
  }

  function renderHistory() {
    historyList.innerHTML = "";
    captionHistory.forEach((c) => {
      const li = document.createElement("li");
      li.textContent = c;
      historyList.appendChild(li);
    });
  }

  // Open file picker when dropZone clicked
  dropZone.addEventListener("click", () => fileInput.click());

  // Handle file selection
  fileInput.addEventListener("change", () => {
    if (fileInput.files.length > 0) {
      feedback.classList.remove("hidden");
      feedback.textContent = "Image uploaded successfully! Click Generate.";
      generateBtn.disabled = false;
      captionBox.classList.add("hidden");
    }
  });

  // Generate caption
  generateBtn.addEventListener("click", async () => {
    if (fileInput.files.length === 0) {
      feedback.textContent = "Please upload an image first.";
      return;
    }

    feedback.textContent = "Generating caption...";
    captionBox.classList.add("hidden");

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    generateBtn.textContent = "Loading...";
    generateBtn.disabled = true;

    try {
      const response = await fetch("/generate_caption", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        feedback.textContent = "Error generating caption. Please try again.";
        generateBtn.textContent = "Generate";
        generateBtn.disabled = false;
        return;
      }

      const result = await response.json();
      if (result.caption) {
        captionResult.textContent = result.caption;
        captionBox.classList.remove("hidden");
        feedback.textContent = "Caption generated successfully!";
        addToHistory(result.caption);
      } else {
        captionResult.textContent = "No caption generated.";
        captionBox.classList.remove("hidden");
        feedback.textContent = "Error generating caption. Please try again.";
      }

      generateBtn.textContent = "Regenerate";
    } catch (error) {
      feedback.textContent = "Error generating caption. Please try again.";
      console.error(error);
    } finally {
      generateBtn.disabled = false;
      fileInput.value = ""; // Reset file input
    }
  });
});
