window.addEventListener("scroll", () => {
  const hero = document.querySelector(".hero");
  const login = document.querySelector(".login-container");
  const rect = login.getBoundingClientRect();

  if (window.scrollY > window.innerHeight / 3) {
    hero.classList.add("fade-out");
  } else {
    hero.classList.remove("fade-out");
  }

  if (rect.top < window.innerHeight - 120) {
    login.classList.add("visible");
  }
});

