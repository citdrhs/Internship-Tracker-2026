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

// For worklog submission: Warn before overwriting an existing entry for the same day
const worklogForm = document.getElementById("worklog-form");
if (worklogForm) {
    const loggedDates = JSON.parse(worklogForm.dataset.loggedDates || "[]");
    const confirmDialog = document.getElementById("worklog-confirm");

    worklogForm.addEventListener("submit", (e) => {

        if (loggedDates.includes(document.getElementById("day_worked").value)) {
            e.preventDefault();
            confirmDialog.showModal();
        }
    });

    document.getElementById("worklog-confirm-replace").addEventListener("click", () => {
        confirmDialog.close();
        worklogForm.submit();
    });
}

// Edit worklog: copy the row's values back into the form
// The user can choose to override an existing entry per the functionality above
function editWorklog(button) {
    const cell = button.closest("tr").children;
    const hours = parseFloat(cell[1].textContent);
    document.getElementById("day_worked").value = cell[0].textContent.trim();
    document.getElementById("hours_worked").value = Math.floor(hours);
    document.getElementById("minutes_worked").value = Math.round((hours % 1) * 60);
    document.getElementById("what_they_did").value = cell[2].textContent.trim();
    document.getElementById("mentor_questions").value = cell[3].textContent.trim();
    document.getElementById("reflection").value = cell[4].textContent.trim();
    document.getElementById("next_steps").value = cell[5].textContent.trim();
    document.getElementById("self_questions").value = cell[6].textContent.trim();
    document.getElementById("worklog-form").scrollIntoView();
}
