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

// Mobile navbar hamburger toggle
const navToggle = document.getElementById("nav-toggle");
if (navToggle) {
    navToggle.addEventListener("click", () => {
        document.getElementById("navbar").classList.toggle("open");
    });
}

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
    document.getElementById("edit_id").value = button.dataset.id;
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

// Feedback list: filter the feedback rows by student and week
function filterFeedback() {
    const student = document.getElementById("filter-student").value;
    const week = document.getElementById("filter-week").value;
    document.querySelectorAll("#feedback-table tr").forEach((row) => {
        if (!row.querySelector("td")) return;
        const okStudent = !student || row.children[0].textContent.trim() === student;
        const okWeek = !week || row.children[1].textContent.trim() === week;
        row.style.display = okStudent && okWeek ? "" : "none";
    });
}

// Mentor hours: open a read-only popup with the full worklog info
function openHoursDetail(button) {
    const d = button.dataset;
    document.getElementById("hd-date").textContent = d.date;
    document.getElementById("hd-hours").textContent = d.hours;
    document.getElementById("hd-what").textContent = d.what || "—";
    document.getElementById("hd-questions").textContent = d.questions || "—";
    document.getElementById("hd-reflection").textContent = d.reflection || "—";
    document.getElementById("hd-next").textContent = d.next || "—";
    document.getElementById("hours-detail").showModal();
}

// Mentor hours: open the shared message popup to reply to a question or clarify a rejection
function openHoursMessage(button) {
    const d = button.dataset;
    document.getElementById("hm-response").value = d.response || "";
    document.getElementById("hm-form").action = d.action;
    document.getElementById("hours-message").showModal();
}

// Close either mentor-hours popup by clicking outside it
["hours-detail", "hours-message"].forEach((id) => {
    const dialog = document.getElementById(id);
    if (dialog) {
        dialog.addEventListener("click", (e) => {
            if (e.target.id === id) e.target.close();
        });
    }
});

// Admin/mentor user tables: show the table matching the selected "view" radio
const viewRadios = document.querySelectorAll("input[name='admin-view']");
if (viewRadios.length) {
    const showView = (value) => {
        document.querySelectorAll(".admin-view-table").forEach((table) => {
            table.style.display = table.dataset.view === value ? "" : "none";
        });
    };
    viewRadios.forEach((radio) => radio.addEventListener("change", () => showView(radio.value)));
    const checked = document.querySelector("input[name='admin-view']:checked");
    if (checked) showView(checked.value);
}

// Filter the user table rows by name
const tableSearch = document.getElementById("table-search");
if (tableSearch) {
    tableSearch.addEventListener("input", () => {
        const query = tableSearch.value.trim().toLowerCase();
        document.querySelectorAll(".admin-view-table table tr").forEach((row) => {
            const nameCell = row.querySelector("td");
            if (!nameCell) return;
            row.style.display = nameCell.textContent.toLowerCase().includes(query) ? "" : "none";
        });
    });
}

// Build the approved-hours calendar (only present inside an open view popup)
function initStudentCalendar() {
    const calendarEl = document.getElementById("student-calendar");
    if (!calendarEl || typeof FullCalendar === "undefined" || calendarEl.dataset.rendered) return;
    const events = JSON.parse(calendarEl.dataset.events || "[]");
    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: "dayGridMonth",
        headerToolbar: { left: "prev,next today", center: "title", right: "" },
        events: events,
        dayMaxEvents: true,
        height: "auto",
        eventColor: "#6c63ff",
        eventTextColor: "#ffffff",
    });
    calendar.render();
    calendarEl.dataset.rendered = "1";
}

// A View/Edit link reloads with that record selected; auto-open its popup
const pageData = document.getElementById("page-data");
if (pageData && pageData.dataset.openDialog) {
    const openId = pageData.dataset.openDialog;
    if (openId === "view-student") {
        const mentorDialog = document.getElementById("view-mentor");
        if (mentorDialog) mentorDialog.showModal();
    }
    const dialog = document.getElementById(openId);
    if (dialog) {
        dialog.showModal();
        initStudentCalendar();
    }
}

// Close a wide popup by clicking outside it
document.querySelectorAll("dialog.modal-wide").forEach((dialog) => {
    dialog.addEventListener("click", (e) => {
        if (e.target === dialog) dialog.close();
    });
});