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

document.addEventListener("DOMContentLoaded", function() {
    document.getElementById("defaultOpen").click();
});

function addRow() {
    var container = document.getElementById("general-search-rows");
    var row = document.createElement("div");
    row.className = "input-group-horizontal";
    row.innerHTML = `
        <label for="type">Type:</label>
        <select name="type[]">
            <option value="track">Track</option>
            <option value="artist">Artist</option>
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
}
