document.addEventListener("DOMContentLoaded", () => {
  // Elements with null checks
  const dropZone = document.getElementById("dropZone");
  const generateBtn = document.getElementById("generateBtn");
  const feedback = document.getElementById("feedback");
  const captionResult = document.getElementById("captionResult");
  const captionBox = document.getElementById("captionBox");
  const languageSelect = document.getElementById("languageSelect");
  const modelQualitySelect = document.getElementById("modelQualitySelect");
  const historyIcon = document.getElementById("historyIcon");
  const historyPanel = document.getElementById("historyPanel");
  const historyList = document.getElementById("historyList");

  // Check core elements only — preview elements are queried lazily
  const requiredElements = {
    dropZone, generateBtn, feedback, captionResult,
    captionBox, languageSelect, modelQualitySelect
  };
  const missing = Object.entries(requiredElements)
    .filter(([, el]) => !el)
    .map(([name]) => name);

  if (missing.length > 0) {
    console.error('Required DOM elements not found:', missing.join(', '));
    return;
  }

  // Create file input
  const fileInput = document.createElement("input");
  fileInput.type = "file";
  fileInput.accept = "image/*";
  fileInput.style.display = "none";
  document.body.appendChild(fileInput);

  let captionHistory = JSON.parse(localStorage.getItem("captionHistory") || "[]");
  let currentImageFile = null; // store the File for chatbot use

  // Toggle history panel
  if (historyIcon && historyPanel) {
    historyIcon.addEventListener("click", () => {
      const isVisible = historyPanel.style.display === "block";
      historyPanel.style.display = isVisible ? "none" : "block";
    });
  }

  function truncateCaption(caption, maxLength = 60) {
    const singleLine = caption.replace(/\n/g, " ");
    return singleLine.length > maxLength
      ? singleLine.slice(0, maxLength).trimEnd() + "…"
      : singleLine;
  }

  function addToHistory(caption) {
    captionHistory.unshift({ full: caption, short: truncateCaption(caption) });
    if (captionHistory.length > 50) {
      captionHistory = captionHistory.slice(0, 50);
    }
    localStorage.setItem("captionHistory", JSON.stringify(captionHistory));
    renderHistory();
  }

  function renderHistory() {
    if (!historyList) return;
    historyList.innerHTML = "";
    captionHistory.forEach((entry) => {
      const li = document.createElement("li");
      const short = typeof entry === "string" ? entry : entry.short;
      const full = typeof entry === "string" ? entry : entry.full;
      li.textContent = short;
      li.title = full;
      historyList.appendChild(li);
    });
  }

  // Render persisted history on load
  renderHistory();

  function showFeedback(message, type = "info") {
    feedback.textContent = message;
    feedback.classList.remove("hidden", "feedback-success", "feedback-error");
    if (type === "success") feedback.classList.add("feedback-success");
    if (type === "error") feedback.classList.add("feedback-error");
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
    if (fileInput.files.length === 0) return;

    // Query preview elements lazily (guaranteed present after DOMContentLoaded)
    const previewImg = document.getElementById("previewImg");
    const previewName = document.getElementById("previewName");
    const previewSize = document.getElementById("previewSize");
    const dropZoneDefault = dropZone.querySelector(".drop-zone-default");
    const dropZonePreview = dropZone.querySelector(".drop-zone-preview");

    const file = fileInput.files[0];
    const maxSize = 16 * 1024 * 1024;
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];

    try {
      if (file.size > maxSize) {
        throw new Error("File too large. Maximum size is 16MB.");
      }
      if (!allowedTypes.includes(file.type)) {
        throw new Error("Invalid file type. Only JPEG, PNG, GIF and WebP are allowed.");
      }
      if (!previewImg || !previewName || !previewSize || !dropZoneDefault || !dropZonePreview) {
        throw new Error("Preview elements missing from page. Please hard-refresh (Ctrl+Shift+R).");
      }

      const objectUrl = URL.createObjectURL(file);
      currentImageFile = file; // save for chatbot

      previewImg.onerror = () => {
        URL.revokeObjectURL(objectUrl);
        showFeedback("Could not load image preview. The file may be corrupted.", "error");
        generateBtn.disabled = true;
      };
      previewImg.onload = () => URL.revokeObjectURL(objectUrl);
      previewImg.src = objectUrl;

      previewName.textContent = file.name.length > 28 ? file.name.slice(0, 25) + "…" : file.name;
      previewSize.textContent = file.size < 1024 * 1024
        ? `${(file.size / 1024).toFixed(1)} KB`
        : `${(file.size / (1024 * 1024)).toFixed(2)} MB`;

      dropZoneDefault.classList.add("hidden");
      dropZonePreview.classList.remove("hidden");
      dropZone.classList.add("has-preview");

      captionBox.classList.add("hidden");
      generateBtn.disabled = false;
      showFeedback("Image uploaded successfully. Ready to generate.", "success");

    } catch (err) {
      const dropZoneDefault = dropZone.querySelector(".drop-zone-default");
      const dropZonePreview = dropZone.querySelector(".drop-zone-preview");
      if (dropZoneDefault) dropZoneDefault.classList.remove("hidden");
      if (dropZonePreview) dropZonePreview.classList.add("hidden");
      dropZone.classList.remove("has-preview");
      generateBtn.disabled = true;
      showFeedback(err.message, "error");
      console.error("File selection error:", err);
    }
  });

  // Generate caption
  generateBtn.addEventListener("click", async () => {
    if (fileInput.files.length === 0) {
      showFeedback("Please upload an image first.", "error");
      return;
    }

    showFeedback("Generating caption...", "info");
    captionBox.classList.add("hidden");

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);
    formData.append("language", languageSelect.value);
    formData.append("model_quality", modelQualitySelect.value);

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

        feedback.classList.remove("hidden");
        showFeedback(errorMessage, "error");
        generateBtn.textContent = "Generate";
        generateBtn.disabled = false;
        return;
      }

      const result = await response.json();
      if (result.caption) {
        captionResult.textContent = result.caption;
        captionBox.classList.remove("hidden");
        showFeedback("Caption generated successfully!", "success");
        addToHistory(result.caption);
        generateBtn.textContent = "Regenerate";
        showExplorePopup(result.caption);
      } else {
        captionResult.textContent = "No caption generated.";
        captionBox.classList.remove("hidden");
        showFeedback("Error generating caption. Please try again.", "error");
        generateBtn.textContent = "Regenerate";
      }
    } catch (error) {
      showFeedback("Error generating caption. Please try again.", "error");
      console.error('Caption generation error:', error);
      generateBtn.textContent = "Generate";
    } finally {
      generateBtn.disabled = false;
    }
  });

  // ===== EXPLORE FEATURE =====
  const explorePopup = document.getElementById("explorePopup");
  const exploreYes = document.getElementById("exploreYes");
  const exploreNo = document.getElementById("exploreNo");
  const exploreLayout = document.getElementById("exploreLayout");
  const explorePanelImg = document.getElementById("explorePanelImg");
  const exploreCaptionText = document.getElementById("exploreCaptionText");
  const backBtn = document.getElementById("backBtn");
  const chatMessages = document.getElementById("chatMessages");
  const chatInput = document.getElementById("chatInput");
  const chatSend = document.getElementById("chatSend");

  let currentCaption = "";
  let explorePopupTimer = null;

  function showExplorePopup(caption) {
    currentCaption = caption;
    if (explorePopup) {
      explorePopup.classList.remove("hidden");
      // Auto-dismiss after 8 seconds
      clearTimeout(explorePopupTimer);
      explorePopupTimer = setTimeout(() => explorePopup.classList.add("hidden"), 8000);
    }
  }

  if (exploreNo) {
    exploreNo.addEventListener("click", () => {
      explorePopup.classList.add("hidden");
      clearTimeout(explorePopupTimer);
    });
  }

  if (exploreYes) {
    exploreYes.addEventListener("click", () => {
      explorePopup.classList.add("hidden");
      clearTimeout(explorePopupTimer);
      openExploreLayout();
    });
  }

  function openExploreLayout() {
    if (explorePanelImg && currentImageFile) {
      // Create a fresh persistent URL for the explore panel
      const panelUrl = URL.createObjectURL(currentImageFile);
      explorePanelImg.src = panelUrl;
    }
    if (exploreCaptionText) {
      exploreCaptionText.textContent = currentCaption;
    }
    if (chatMessages) chatMessages.innerHTML = "";
    addBotMessage("Hi! Ask me anything about this image. I'll only answer based on what I can see in it.");

    exploreLayout.classList.remove("hidden");
    requestAnimationFrame(() => exploreLayout.classList.add("visible"));
  }

  if (backBtn) {
    backBtn.addEventListener("click", () => {
      exploreLayout.classList.remove("visible");
      setTimeout(() => exploreLayout.classList.add("hidden"), 400);
    });
  }

  function addUserMessage(text) {
    const bubble = document.createElement("div");
    bubble.className = "chat-bubble user";
    bubble.textContent = text;
    chatMessages.appendChild(bubble);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function addBotMessage(text, isTyping = false) {
    const bubble = document.createElement("div");
    bubble.className = "chat-bubble bot" + (isTyping ? " typing" : "");
    bubble.textContent = text;
    chatMessages.appendChild(bubble);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return bubble;
  }

  async function sendChatMessage() {
    const question = chatInput.value.trim();
    if (!question) return;

    chatInput.value = "";
    chatSend.disabled = true;
    addUserMessage(question);

    const typingBubble = addBotMessage("Thinking...", true);

    try {
      if (!currentImageFile) {
        typingBubble.remove();
        addBotMessage("No image found. Please go back and upload an image first.");
        return;
      }

      const formData = new FormData();
      formData.append("file", currentImageFile, currentImageFile.name);
      formData.append("question", question);
      formData.append("caption", currentCaption);

      const response = await fetch("/chat", { method: "POST", body: formData });
      const data = await response.json();

      typingBubble.remove();
      if (data.answer) {
        addBotMessage(data.answer);
      } else {
        addBotMessage(data.error || "Sorry, I couldn't answer that.");
      }
    } catch (err) {
      typingBubble.remove();
      addBotMessage("Something went wrong. Please try again.");
      console.error("Chat error:", err);
    } finally {
      chatSend.disabled = false;
      chatInput.focus();
    }
  }

  if (chatSend) {
    chatSend.addEventListener("click", sendChatMessage);
  }

  if (chatInput) {
    chatInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendChatMessage();
      }
    });
  }
});
