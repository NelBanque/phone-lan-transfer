(() => {
  "use strict";

  const status = document.querySelector("#connection-status");
  const fileInput = document.querySelector("#file-input");
  const chooseFilesButton = document.querySelector("#choose-files");
  const selectedFilesList = document.querySelector("#selected-files");
  const selectionSummary = document.querySelector("#selection-summary");
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

  chooseFilesButton.disabled = false;

  function formatSize(bytes) {
    const units = ["B", "KB", "MB", "GB", "TB"];
    let size = bytes;
    let unitIndex = 0;

    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex += 1;
    }

    return `${new Intl.NumberFormat(undefined, { maximumFractionDigits: 1 }).format(size)} ${units[unitIndex]}`;
  }

  function isPortableName(value) {
    return value.length > 0
      && value.length <= 255
      && value.trim() === value
      && value !== "."
      && value !== ".."
      && !/[<>:"/\\|?*\x00-\x1f]/u.test(value)
      && !/[. ]$/u.test(value)
      && !/^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)/iu.test(value);
  }

  function fileExtension(name) {
    const lastDot = name.lastIndexOf(".");
    return lastDot > 0 && lastDot < name.length - 1 ? name.slice(lastDot) : "";
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
      action.textContent = "View and rename";
      openButton.addEventListener("click", () => {
        openEntry = openEntry === entry ? null : entry;
        renderSelectedFiles();
        selectedFilesList.querySelectorAll(".file-open")[index].focus();
      });
      removeButton.className = "remove-file";
      removeButton.type = "button";
      removeButton.textContent = "Remove";
      removeButton.setAttribute("aria-label", `Remove ${entry.file.name}`);
      removeButton.addEventListener("click", () => {
        if (openEntry === entry) openEntry = null;
        selectedFiles.splice(index, 1);
        renderSelectedFiles();
      });

      openButton.append(name, size, action);
      row.append(openButton, removeButton);
      item.append(row);

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
        nameInput.maxLength = 255;
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
        nameError.textContent = "Use a different name without system characters or trailing spaces or periods.";
        nameInput.setAttribute("aria-describedby", nameError.id);
        const initialValid = nameInput.value.length > 0 && isPortableName(entry.destinationName);
        nameInput.setAttribute("aria-invalid", String(!initialValid));
        nameError.hidden = initialValid;
        nameInput.addEventListener("input", () => {
          entry.destinationName = nameInput.value + entry.extension;
          name.textContent = entry.destinationName || entry.file.name;
          const valid = nameInput.value.length > 0 && isPortableName(entry.destinationName);
          nameInput.setAttribute("aria-invalid", String(!valid));
          nameError.hidden = valid;
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
  fileInput.addEventListener("change", () => {
    if (fileInput.files.length === 0) return;
    selectedFiles.push(...Array.from(fileInput.files, (file) => ({
      file,
      destinationName: file.name,
      extension: fileExtension(file.name),
    })));
    fileInput.value = "";
    renderSelectedFiles();
  });
})();
