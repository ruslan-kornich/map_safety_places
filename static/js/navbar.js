window.addEventListener('scroll', function () {
  const navbar = document.querySelector('.navbar');
  navbar.style.transform = `translateY(${window.scrollY}px)`;
});
