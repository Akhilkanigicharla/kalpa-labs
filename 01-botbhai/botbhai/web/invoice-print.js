// Print button on invoice pages (A220: no inline onclick, so the CSP needs no 'unsafe-inline').
document.getElementById("print-btn")?.addEventListener("click", () => window.print());
