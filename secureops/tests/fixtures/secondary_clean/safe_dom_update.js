function renderProfileName(name) {
  const label = document.querySelector("#profile-name");
  const normalized = String(name).trim();

  label.textContent = normalized;
}

export { renderProfileName };
