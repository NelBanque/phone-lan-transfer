(() => {
  "use strict";

  const status = document.querySelector("#connection-status");
  const statusTitle = document.querySelector("#status-title");
  const statusMessage = document.querySelector("#status-message");
  const fragmentParameters = new URLSearchParams(window.location.hash.slice(1));
  const accessToken = fragmentParameters.get("token");

  const cleanUrl = `${window.location.pathname}${window.location.search}`;
  window.history.replaceState(null, "", cleanUrl);

  if (!accessToken) {
    status.dataset.state = "error";
    statusTitle.textContent = "Transfer link incomplete";
    statusMessage.textContent = "Scan the QR code shown on your computer again.";
    return;
  }

  status.dataset.state = "ready";
  statusTitle.textContent = "Connected to your computer";
  statusMessage.textContent = "Your temporary transfer link is ready.";
})();
