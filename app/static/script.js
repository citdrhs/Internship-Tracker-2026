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

// After picking from a dropdown, jump to the profile that loaded
const profileCard = document.querySelector(".profile-card");
if (profileCard) profileCard.scrollIntoView();

// Allow mentors to add an extra week to give feedback for
// as a precautionary mechanism (just in case)
const weekSelect = document.getElementById("week");
const weekCustom = document.getElementById("week_custom");
if (weekSelect && weekCustom) {
    weekSelect.addEventListener("change", () => {
        const other = weekSelect.value === "other";
        weekCustom.style.display = other ? "block" : "none";
        weekCustom.required = other;
        weekCustom.name = other ? "week" : "";
        weekSelect.name = other ? "" : "week";
    });
}

// Feedback form: Overall Rating = rounded mean of the five sub-score sliders
const subscoreSliders = ["Quality_of_Work", "Professionalism", "Timeliness_of_Work", "Initiative", "Soft_Skills"]
    .map((id) => document.getElementById(id));
const overallDisplay = document.getElementById("overallDisplay");
if (overallDisplay && subscoreSliders.every(Boolean)) {
    const updateOverall = () => {
        const mean = subscoreSliders.reduce((sum, el) => sum + Number(el.value), 0) / subscoreSliders.length;
        overallDisplay.textContent = Math.round(mean);
    };
    subscoreSliders.forEach((el) => el.addEventListener("input", updateOverall));
    updateOverall();
}

// Feedback list: filter rows by student and week, and show chosen student's averages
function filterFeedback() {
    const student = document.getElementById("filter-student").value;
    const week = document.getElementById("filter-week").value;
    document.querySelectorAll("#feedback-table tr").forEach((row) => {
        if (!row.querySelector("td")) return;
        const okStudent = !student || row.children[0].textContent.trim() === student;
        const okWeek = !week || row.children[1].textContent.trim() === week;
        row.style.display = okStudent && okWeek ? "" : "none";
    });

    const averages = document.getElementById("student-averages");
    averages.style.display = student ? "" : "none";
    averages.querySelectorAll(".avg-row").forEach((row) => {
        row.style.display = row.dataset.student === student ? "" : "none";
    });
}

// Mentor hours: open popup with full worklog info + a box to respond to the student
function openHoursDetail(button) {
    const d = button.dataset;
    document.getElementById("hd-date").textContent = d.date;
    document.getElementById("hd-hours").textContent = d.hours;
    document.getElementById("hd-what").textContent = d.what || "—";
    document.getElementById("hd-questions").textContent = d.questions || "—";
    document.getElementById("hd-reflection").textContent = d.reflection || "—";
    document.getElementById("hd-next").textContent = d.next || "—";
    document.getElementById("hd-response").value = d.response;
    document.getElementById("hd-form").action = d.action;
    document.getElementById("hours-detail").showModal();
}

const hoursDetail = document.getElementById("hours-detail");
if (hoursDetail) {
    hoursDetail.addEventListener("click", (e) => {
        if (e.target.id === "hours-detail") e.target.close();
    });
}