// Show data in table row as popup
function openRowModal(button) {
    const row = button.closest("tr");
    const headers = button.closest("table").querySelectorAll("th");
    const body = document.getElementById("row-modal-body");
    const skip = ["", "view", "action", "actions"];
    body.innerHTML = "";

    row.querySelectorAll("td").forEach((cell, i) => {
        const label = headers[i] ? headers[i].textContent.trim() : "";
        if (skip.includes(label.toLowerCase())) return;

        const dt = document.createElement("dt");
        dt.textContent = label;
        const dd = document.createElement("dd");
        dd.textContent = cell.textContent.trim() || "—";
        body.append(dt, dd);
    });

    document.getElementById("row-modal").showModal();
}

// Close popup by clicking outside
document.getElementById("row-modal").addEventListener("click", (e) => {
    if (e.target.id === "row-modal") e.target.close();
});

// Flash "toast" popup for success or error messages
document.querySelectorAll(".toast").forEach((toast) => {
    toast.addEventListener("click", () => toast.remove());
    setTimeout(() => toast.remove(), 6000);
});
