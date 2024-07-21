// backend/static/js/scripts.js

function showTab(event, tabName) {
    var i, tabcontent, tablinks;
    tabcontent = document.getElementsByClassName("tab-content");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }
    tablinks = document.getElementsByClassName("tab");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }
    document.getElementById(tabName).style.display = "block";
    event.currentTarget.className += " active";
}

function addRow() {
    var container = document.getElementById("general-search-rows");
    var row = document.createElement("div");
    row.className = "input-group-horizontal";
    row.innerHTML = `
       <label for="type">Type:</label>
                        <select name="type[]">
                            <option value="artist">Artist</option>
                            <option value="track">Track</option>
                            <option value="album">Album</option>
                            <option value="playlist">Playlist</option>
                            <option value="show">Show</option>
                            <option value="episode">Episode</option>
                            <option value="audiobook">Audiobook</option>
                        </select>
                        <label for="name">Name:</label>
                        <input type="text" name="name[]" required>
                        <label for="limit">Limit:</label>
                        <input type="number" name="limit[]" min="1" max="50" value="10" required>
    `;
    container.appendChild(row);
    var selectElement = row.querySelector('select[name="type[]"]');
    selectElement.value = "artist";
}
document.addEventListener('DOMContentLoaded', function() {
    var coll = document.getElementsByClassName("collapsible");
    for (var i = 0; i < coll.length; i++) {
        coll[i].addEventListener("click", function() {
            this.classList.toggle("active");
            var arrow = this.querySelector(".arrow");
            arrow.classList.toggle("active");
            var content = this.parentElement.nextElementSibling;
            if (content.style.display === "block") {
                content.style.display = "none";
            } else {
                content.style.display = "block";
            }
        });
    }
});

