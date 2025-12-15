// ✅ Aplicar el tema guardado al cargar la página
document.addEventListener("DOMContentLoaded", () => {
    const savedTheme = localStorage.getItem("theme");

    if (savedTheme === "dark") {
        document.body.classList.add("dark-mode");
    }
});

// ✅ Función para alternar entre modo claro y oscuro
function toggleTheme() {
    const body = document.body;

    if (body.classList.contains("dark-mode")) {
        body.classList.remove("dark-mode");
        localStorage.setItem("theme", "light");  // Guarda preferencia
    } else {
        body.classList.add("dark-mode");
        localStorage.setItem("theme", "dark");   // Guarda preferencia
    }
}
