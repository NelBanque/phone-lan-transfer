(() => {
  "use strict";

  const status = document.querySelector("#connection-status");
  const fileInput = document.querySelector("#file-input");
  const chooseFilesButton = document.querySelector("#choose-files");
  const selectedFilesList = document.querySelector("#selected-files");
  const selectionSummary = document.querySelector("#selection-summary");
  const fileLimit = document.querySelector("#file-limit");
  const retrySettingsButton = document.querySelector("#retry-settings");
  const statusTitle = document.querySelector("#status-title");
  const statusMessage = document.querySelector("#status-message");
  let maxFileBytes = null;
  const selectedFiles = [];
  let openEntry = null;
  let previewUrl = null;
  const fragmentParameters = new URLSearchParams(window.location.hash.slice(1));
  const accessToken = fragmentParameters.get("token");

  const cleanUrl = `${window.location.pathname}${window.location.search}`;
  window.history.replaceState(null, "", cleanUrl);

  if (!accessToken) {
    status.hidden = false;
    return;
  }

  async function loadTransferSettings() {
    chooseFilesButton.disabled = true;
    retrySettingsButton.hidden = true;
    status.hidden = true;
    fileLimit.textContent = "Checking file size limit…";
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 10000);
    try {
      const response = await fetch("/transfer-settings", {
        headers: { Authorization: `Bearer ${accessToken}` },
        cache: "no-store",
        signal: controller.signal,
      });
      if (response.status === 401) {
        statusTitle.textContent = "Transfer link expired or invalid";
        statusMessage.textContent = "Scan the current QR code on your computer again.";
        status.hidden = false;
        fileLimit.textContent = "File size limit unavailable.";
        return;
      }
      if (!response.ok) throw new Error("Settings request failed");
      const settings = await response.json();
      if (!Number.isSafeInteger(settings.max_file_bytes) || settings.max_file_bytes <= 0) {
        throw new Error("Invalid file size limit");
      }
      maxFileBytes = settings.max_file_bytes;
      fileLimit.textContent = `Maximum per file: ${formatSize(maxFileBytes)} (${new Intl.NumberFormat().format(maxFileBytes)} bytes).`;
      chooseFilesButton.disabled = false;
      renderSelectedFiles();
    } catch {
      statusTitle.textContent = "Could not reach transfer settings";
      statusMessage.textContent = "Check that the server is running and both devices are on the same network, then retry.";
      status.hidden = false;
      retrySettingsButton.hidden = false;
      fileLimit.textContent = "File size limit unavailable.";
    } finally {
      window.clearTimeout(timeout);
    }
  }

  function formatSize(bytes) {
    const units = ["B", "KiB", "MiB", "GiB", "TiB"];
    let size = bytes;
    let unitIndex = 0;

    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex += 1;
    }

    return `${new Intl.NumberFormat(undefined, { maximumFractionDigits: 1 }).format(size)} ${units[unitIndex]}`;
  }

  function destinationNameError(value) {
    if (!value || value === "." || value === "..") {
      return "Enter a destination name.";
    }
    // Match Python str.strip() whitespace at the filename boundaries.
    const boundaryWhitespace = /^[\u0009-\u000d\u001c-\u0020\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]|[\u0009-\u000d\u001c-\u0020\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]$/u;
    if (boundaryWhitespace.test(value) || value.endsWith(".")) {
      return "Remove surrounding whitespace or the trailing period.";
    }
    if (/[<>:"/\\|?*\x00-\x1f\x7f-\x9f]/u.test(value)) {
      return 'Remove control characters or any of these: < > : " / \\ | ? *';
    }
    const stem = value.split(".", 1)[0].toUpperCase();
    if (/^(CON|PRN|AUX|NUL|COM[1-9¹²³]|LPT[1-9¹²³])$/u.test(stem)) {
      return "This name is reserved by Windows. Choose another name.";
    }
    for (const character of value) {
      const point = character.codePointAt(0);
      if (point >= 0xd800 && point <= 0xdfff) {
        return "The name contains invalid Unicode. Replace the affected character.";
      }
    }
    if (new TextEncoder().encode(value).length > 255) {
      return "The full name, including its extension, must fit within 255 UTF-8 bytes. Accents and emoji may use several bytes each.";
    }
    return "";
  }

  function fileExtension(name) {
    const lastDot = name.lastIndexOf(".");
    return lastDot > 0 && lastDot < name.length - 1 ? name.slice(lastDot) : "";
  }

  function uploadValidationError(entry) {
    if (maxFileBytes === null) return "Reconnect to check the file size limit.";
    if (entry.file.size > maxFileBytes) return "This file exceeds the active size limit.";
    if (entry.destinationName === entry.extension) return "Enter a name before the extension.";
    return destinationNameError(entry.destinationName);
  }

  async function sendFile(entry) {
    if (entry.state === "sending" || entry.state === "saved") return;
    const validationError = uploadValidationError(entry);
    if (validationError) {
      entry.state = "failed";
      entry.message = validationError;
      renderSelectedFiles();
      return;
    }
    const destinationName = entry.destinationName;
    entry.state = "sending";
    entry.message = "Sending… Keep this page open until the computer confirms the save.";
    renderSelectedFiles();
    try {
      const query = new URLSearchParams({ destination_name: destinationName });
      const response = await fetch(`/uploads?${query}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${accessToken}` },
        body: entry.file,
      });
      if (!response.ok) {
        const errors = {
          400: "The name was rejected or the upload was interrupted. Check the name and retry.",
          401: "The transfer link is invalid. Open the current QR link again.",
          409: "A file with this name already exists. Check the computer before choosing another name and retrying.",
          413: "The file exceeds the server's size limit.",
          422: "The upload request was rejected. Check the destination name.",
          500: "The computer could not save this file. Check the destination folder and retry.",
          507: "The computer does not have enough space. Free some space and retry.",
        };
        entry.state = "failed";
        entry.message = errors[response.status]
          || "The server returned an unexpected response. Saving is not confirmed; check the computer before retrying.";
      } else {
        const result = await response.json();
        if (response.status !== 201 || result.status !== "saved" || result.destination_name !== destinationName) {
          throw new Error("Save not confirmed");
        }
        entry.state = "saved";
        entry.message = "Saved on the computer.";
      }
    } catch {
      entry.state = "failed";
      entry.message = "Saving could not be confirmed. The file may already be on the computer. Check before retrying; an existing name will not be overwritten.";
    }
    renderSelectedFiles();
  }

  function createPreview(file) {
    const preview = document.createElement("div");
    preview.className = "file-preview";

    const imageTypes = ["image/jpeg", "image/png", "image/gif", "image/webp", "image/heic", "image/heif", "image/avif", "image/bmp"];
    const isImage = imageTypes.includes(file.type);
    const isVideo = file.type.startsWith("video/");

    if (!isImage && !isVideo) {
      preview.textContent = "Preview is unavailable for this file type.";
      return preview;
    }

    const media = document.createElement(isImage ? "img" : "video");
    const objectUrl = URL.createObjectURL(file);
    previewUrl = objectUrl;
    media.src = objectUrl;
    if (isImage) {
      media.alt = `Preview of ${file.name}`;
    } else {
      media.controls = true;
      media.preload = "metadata";
      media.playsInline = true;
    }
    media.addEventListener("error", () => {
      preview.textContent = "This browser cannot preview this file.";
      if (previewUrl === objectUrl) {
        URL.revokeObjectURL(objectUrl);
        previewUrl = null;
      }
    });
    preview.append(media);
    return preview;
  }

  function renderSelectedFiles() {
    if (previewUrl !== null) {
      URL.revokeObjectURL(previewUrl);
      previewUrl = null;
    }
    selectedFilesList.replaceChildren();

    selectedFiles.forEach((entry, index) => {
      const item = document.createElement("li");
      const row = document.createElement("div");
      const openButton = document.createElement("button");
      const name = document.createElement("span");
      const size = document.createElement("span");
      const action = document.createElement("span");
      const removeButton = document.createElement("button");
      const sendButton = document.createElement("button");
      const panelId = `file-panel-${index}`;

      item.className = "selected-file";
      row.className = "file-row";
      openButton.className = "file-open";
      openButton.type = "button";
      openButton.setAttribute("aria-expanded", String(openEntry === entry));
      if (openEntry === entry) openButton.setAttribute("aria-controls", panelId);
      name.className = "file-name";
      name.textContent = entry.destinationName || entry.file.name;
      size.className = "file-size";
      size.textContent = formatSize(entry.file.size);
      action.className = "file-action";
      action.textContent = entry.state === "sending" || entry.state === "saved"
        ? "View file" : "View and rename";
      openButton.addEventListener("click", () => {
        openEntry = openEntry === entry ? null : entry;
        renderSelectedFiles();
        selectedFilesList.querySelectorAll(".file-open")[index].focus();
      });
      removeButton.className = "remove-file";
      removeButton.type = "button";
      removeButton.textContent = "Remove";
      removeButton.disabled = entry.state === "sending";
      removeButton.setAttribute("aria-label", `Remove ${entry.file.name}`);
      removeButton.addEventListener("click", () => {
        if (openEntry === entry) openEntry = null;
        selectedFiles.splice(index, 1);
        renderSelectedFiles();
      });

      openButton.append(name, size, action);
      row.append(openButton, removeButton);
      item.append(row);

      const transfer = document.createElement("div");
      const transferStatus = document.createElement("p");
      transfer.className = "file-transfer";
      transferStatus.className = "transfer-status";
      transferStatus.setAttribute("role", "status");
      transferStatus.textContent = entry.message || "Pending — not sent yet.";
      sendButton.className = "send-file";
      sendButton.type = "button";
      sendButton.textContent = entry.state === "saved" ? "Saved"
        : entry.state === "sending" ? "Sending…"
          : entry.state === "failed" ? "Retry" : "Send";
      sendButton.disabled = entry.state === "sending" || entry.state === "saved"
        || uploadValidationError(entry) !== "";
      sendButton.setAttribute("aria-label", `${sendButton.textContent} ${entry.destinationName}`);
      sendButton.addEventListener("click", () => sendFile(entry));
      transfer.append(transferStatus, sendButton);
      item.append(transfer);

      if (maxFileBytes !== null && entry.file.size > maxFileBytes) {
        const sizeError = document.createElement("p");
        sizeError.className = "file-size-error";
        sizeError.setAttribute("role", "status");
        sizeError.textContent = `This file exceeds the ${formatSize(maxFileBytes)} per-file limit. Choose a smaller file or restart the server with a higher limit.`;
        item.append(sizeError);
      }

      if (openEntry === entry) {
        const panel = document.createElement("div");
        const originalName = document.createElement("p");
        const label = document.createElement("label");
        const nameField = document.createElement("div");
        const nameInput = document.createElement("input");
        const extension = document.createElement("span");
        const nameError = document.createElement("p");

        panel.className = "file-panel";
        panel.id = panelId;
        originalName.className = "original-name";
        originalName.textContent = `Original: ${entry.file.name}`;
        label.className = "rename-label";
        label.htmlFor = `file-name-${index}`;
        label.textContent = entry.extension
          ? "Name on computer (without extension)"
          : "Name on computer";
        nameField.className = "rename-field";
        nameInput.className = "rename-input";
        nameInput.id = label.htmlFor;
        nameInput.type = "text";
        nameInput.disabled = entry.state === "sending" || entry.state === "saved";
        nameInput.autocomplete = "off";
        nameInput.spellcheck = false;
        nameInput.value = entry.extension
          ? entry.destinationName.slice(0, -entry.extension.length)
          : entry.destinationName;
        extension.className = "file-extension";
        extension.textContent = entry.extension;
        extension.hidden = entry.extension === "";
        nameError.className = "file-name-error";
        nameError.id = `file-name-error-${index}`;
        nameInput.setAttribute("aria-describedby", nameError.id);
        function updateNameFeedback() {
          const error = nameInput.value.length === 0
            ? "Enter a name before the extension."
            : destinationNameError(entry.destinationName);
          nameError.textContent = error;
          nameInput.setAttribute("aria-invalid", String(error !== ""));
          nameError.hidden = error === "";
        }
        updateNameFeedback();
        nameInput.addEventListener("input", () => {
          entry.destinationName = nameInput.value + entry.extension;
          name.textContent = entry.destinationName || entry.file.name;
          updateNameFeedback();
          sendButton.disabled = entry.state === "sending" || entry.state === "saved"
            || uploadValidationError(entry) !== "";
          sendButton.setAttribute("aria-label", `${sendButton.textContent} ${entry.destinationName}`);
        });

        nameField.append(nameInput, extension);
        panel.append(createPreview(entry.file), originalName, label, nameField, nameError);
        item.append(panel);
      }

      selectedFilesList.append(item);
    });

    const fileCount = selectedFiles.length;
    const totalBytes = selectedFiles.reduce((total, entry) => total + entry.file.size, 0);
    selectionSummary.textContent = fileCount === 0
      ? "No files selected"
      : `${fileCount} ${fileCount === 1 ? "file" : "files"} · ${formatSize(totalBytes)} total`;
  }

  chooseFilesButton.addEventListener("click", () => fileInput.click());
  retrySettingsButton.addEventListener("click", loadTransferSettings);
  fileInput.addEventListener("change", () => {
    if (fileInput.files.length === 0) return;
    selectedFiles.push(...Array.from(fileInput.files, (file) => ({
      file,
      destinationName: file.name,
      extension: fileExtension(file.name),
      state: "pending",
      message: "",
    })));
    fileInput.value = "";
    renderSelectedFiles();
  });
  loadTransferSettings();
})();
