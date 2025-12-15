// script.js
document.addEventListener('DOMContentLoaded', function() {
    // ========== INICIALIZAR AOS (ANIMACIONES AL HACER SCROLL) ==========
    AOS.init({
        duration: 1000,
        once: true,
        offset: 100,
        easing: 'ease-out-sine',
        delay: 100,
    });

    // ========== BOTÓN "VOLVER ARRIBA" ==========
    const backToTopButton = document.createElement('button');
    backToTopButton.innerHTML = '<i class="fas fa-arrow-up"></i>';
    backToTopButton.classList.add('btn', 'btn-back-to-top', 'btn-primary');
    document.body.appendChild(backToTopButton);

    // Mostrar/Ocultar botón según la posición del scroll
    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) {
            backToTopButton.style.display = 'block';
        } else {
            backToTopButton.style.display = 'none';
        }
    });

    // Funcionalidad del botón "Volver arriba"
    backToTopButton.addEventListener('click', function(e) {
        e.preventDefault();
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });

    // ========== EFECTO DE TARJETAS DEL EQUIPO (HOVER) ==========
    const teamCards = document.querySelectorAll('.bd-placeholder-img');
    teamCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.05)';
            this.style.boxShadow = '0 10px 25px rgba(0, 0, 0, 0.2)';
        });
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
            this.style.boxShadow = '0 0 0 7px rgba(0, 123, 255, 0.1)';
        });
    });

    // ========== ANIMACIÓN DEL BOTÓN PRIMARIO (PULSO) ==========
    const primaryButtons = document.querySelectorAll('.pulse-animation');
    primaryButtons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.05)';
            this.style.boxShadow = '0 8px 20px rgba(0, 123, 255, 0.3)';
        });
        button.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
            this.style.boxShadow = '0 5px 15px rgba(0, 0, 0, 0.2)';
        });
    });
});