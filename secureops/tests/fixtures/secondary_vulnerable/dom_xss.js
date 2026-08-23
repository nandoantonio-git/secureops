function renderSearchTerm() {
  const results = document.querySelector("#results");
  const term = new URLSearchParams(window.location.search).get("q");

  results.innerHTML = `<strong>${term}</strong>`;
}

export { renderSearchTerm };
