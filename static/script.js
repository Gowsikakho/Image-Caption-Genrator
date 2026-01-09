document.addEventListener("DOMContentLoaded", () => {
  // Elements with null checks
  const dropZone = document.getElementById("dropZone");
  const generateBtn = document.getElementById("generateBtn");
  const feedback = document.getElementById("feedback");
  const captionResult = document.getElementById("captionResult");
  const captionBox = document.getElementById("captionBox");
  const historyIcon = document.getElementById("historyIcon");
  const historyPanel = document.getElementById("historyPanel");
  const historyList = document.getElementById("historyList");
  
  // Check if all required elements exist
  if (!dropZone || !generateBtn || !feedback || !captionResult || !captionBox) {
    console.error('Required DOM elements not found');
    return;
  }
  
  // Create file input
  const fileInput = document.createElement("input");
  fileInput.type = "file";
  fileInput.accept = "image/*";
  fileInput.style.display = "none";
  document.body.appendChild(fileInput);

  let captionHistory = [];

  // Toggle history panel
  if (historyIcon && historyPanel) {
    historyIcon.addEventListener("click", () => {
      const isVisible = historyPanel.style.display === "block";
      historyPanel.style.display = isVisible ? "none" : "block";
    });
  }

  function addToHistory(caption) {
    captionHistory.unshift(caption);
    // Limit history to 50 entries to prevent memory issues
    if (captionHistory.length > 50) {
      captionHistory = captionHistory.slice(0, 50);
    }
    renderHistory();
  }

  function renderHistory() {
    if (!historyList) return;
    
    historyList.innerHTML = "";
    captionHistory.forEach((caption) => {
      const li = document.createElement("li");
      li.textContent = caption;
      historyList.appendChild(li);
    });
  }

  // Open file picker when dropZone clicked
  dropZone.addEventListener("click", () => fileInput.click());
  
  // Drag and drop functionality
  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
  });
  
  dropZone.addEventListener("dragleave", (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
  });
  
  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      // Create a new FileList-like object
      const dt = new DataTransfer();
      dt.items.add(files[0]);
      fileInput.files = dt.files;
      
      // Trigger change event
      const changeEvent = new Event('change', { bubbles: true });
      fileInput.dispatchEvent(changeEvent);
    }
  });

  // Handle file selection
  fileInput.addEventListener("change", () => {
    if (fileInput.files.length > 0) {
      const file = fileInput.files[0];
      const maxSize = 16 * 1024 * 1024; // 16MB
      const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
      
      if (file.size > maxSize) {
        feedback.classList.remove("hidden");
        feedback.textContent = "File too large. Maximum size is 16MB.";
        generateBtn.disabled = true;
        return;
      }
      
      if (!allowedTypes.includes(file.type)) {
        feedback.classList.remove("hidden");
        feedback.textContent = "Invalid file type. Only images are allowed.";
        generateBtn.disabled = true;
        return;
      }
      
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
        let errorMessage = "Error generating caption. Please try again.";
        try {
          const errorData = await response.json();
          errorMessage = errorData.error || errorMessage;
        } catch (parseError) {
          console.warn('Could not parse error response:', parseError);
        }
        
        feedback.textContent = errorMessage;
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
        generateBtn.textContent = "Regenerate";
      } else {
        captionResult.textContent = "No caption generated.";
        captionBox.classList.remove("hidden");
        feedback.textContent = "Error generating caption. Please try again.";
        generateBtn.textContent = "Regenerate";
      }
    } catch (error) {
      feedback.textContent = "Error generating caption. Please try again.";
      console.error('Caption generation error:', error);
      generateBtn.textContent = "Generate";
    } finally {
      generateBtn.disabled = false;
    }
  });
});
