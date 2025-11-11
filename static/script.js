document.addEventListener("DOMContentLoaded", () => {
  const uploadBtn = document.getElementById("uploadBtn");
  const fileInput = document.createElement("input");
  fileInput.type = "file";
  fileInput.accept = "image/*";
  fileInput.style.display = "none";
  document.body.appendChild(fileInput);

  const generateBtn = document.getElementById("generateBtn");
  const feedback = document.getElementById("feedback");
  const captionResult = document.getElementById("captionResult");

  // Show file picker on button click
  uploadBtn.addEventListener("click", () => fileInput.click());

  // Process file upload
  fileInput.addEventListener("change", () => {
    if (fileInput.files.length > 0) {
      feedback.classList.add("show");
      feedback.textContent = "Image uploaded successfully! Click Generate.";
      generateBtn.disabled = false;
      captionResult.classList.remove("show");
    }
  });

  generateBtn.addEventListener("click", async () => {
    if (fileInput.files.length === 0) {
      feedback.textContent = "Please upload an image first.";
      return;
    }

    feedback.textContent = "Generating caption...";
    captionResult.classList.remove("show");

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    // Display loading state
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
        captionResult.textContent = `Caption: ${result.caption}`;
        captionResult.classList.add("show");
        feedback.textContent = "Caption generated successfully!";
      } else {
        captionResult.textContent = "No caption generated.";
        captionResult.classList.add("show");
        feedback.textContent = "Error generating caption. Please try again.";
      }

      generateBtn.textContent = "Regenerate";
    } catch (error) {
      feedback.textContent = "Error generating caption. Please try again.";
      console.error("Error:", error);
    } finally {
      generateBtn.disabled = false;
      fileInput.value = ""; // Clear file input to allow re-uploading
    }
  });
});
