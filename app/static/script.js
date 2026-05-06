
// // Templating header that is pre-login

// class PreLogHeader extends HTMLElement {
//     connectedCallback() {
//         this.innerHTML = `<img src="../assets/large-logo.svg" alt="">

//         <nav class="primary-navigation">
//             <ul>  
//                 <li><a href="start.html">Getting Started</a></li>
//                 <li><a href="about.html">About</a></li>
//             </ul>
//         </nav>`


//     }
// }

// customElements.define('prelog-header', PreLogHeader)


function toggleAccessCode() {
    const role = document.getElementById("role").value;
    const accessGroup = document.getElementById("access-code-group");

    if (role === "admin" || role === "mentor" || role === "teacher") {
        accessGroup.style.display = "block";
    } else {
        accessGroup.style.display = "none";
    }
}

// Weekly Feedback Summary Data (Mock Data)
const weeklyFeedbackData = {
    week1: {
        title: "Week 1 Feedback Summary",
        entries: 3,
        average: 4.3,
        topFocus: "Technical Skills"
    },
    week2: {
        title: "Week 2 Feedback Summary",
        entries: 4,
        average: 4.5,
        topFocus: "Communication"
    },
    week3: {
        title: "Week 3 Feedback Summary",
        entries: 3,
        average: 4.0,
        topFocus: "Problem-Solving"
    },
    week4: {
        title: "Week 4 Feedback Summary",
        entries: 5,
        average: 4.6,
        topFocus: "Technical Skills"
    },
    week5: {
        title: "Week 5 Feedback Summary",
        entries: 2,
        average: 4.2,
        topFocus: "Time Management"
    },
    all: {
        title: "All Weeks Summary",
        entries: 17,
        average: 4.3,
        topFocus: "Technical Skills"
    }
};

// Initialize feedback dropdown event listener
document.addEventListener('DOMContentLoaded', function() {
    const feedbackSelect = document.getElementById('weeklyFeedback');
    const weeklySummary = document.getElementById('weeklySummary');
    
    if (feedbackSelect) {
        feedbackSelect.addEventListener('change', function(e) {
            const selectedWeek = e.target.value;
            
            if (selectedWeek && weeklyFeedbackData[selectedWeek]) {
                const data = weeklyFeedbackData[selectedWeek];
                
                // Update summary display
                document.getElementById('summaryTitle').textContent = data.title;
                document.getElementById('entryCount').textContent = data.entries;
                document.getElementById('avgRating').textContent = data.average;
                document.getElementById('topFocus').textContent = data.topFocus;
                
                // Show summary section
                weeklySummary.classList.remove('hidden');
            } else {
                // Hide summary if no selection
                weeklySummary.classList.add('hidden');
            }
        });
    }
});

}