
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


function toggleAdminCode() {
    const role = document.getElementById("role").value;
    const adminGroup = document.getElementById("admin-code-group");

    if (role === "admin") {
        adminGroup.style.display = "block";
    } else {
        adminGroup.style.display = "none";
    }
}