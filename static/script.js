document.querySelectorAll('.clickable-row').forEach(el => el.addEventListener("click", function() {
    window.location = this.getAttribute("data-href");
}));