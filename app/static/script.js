
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

}