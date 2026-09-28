(function () {
  "use strict";

  var reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* Reading progress bar */
  var bar = document.getElementById("progress-bar");
  function updateProgress() {
    var doc = document.documentElement;
    var max = doc.scrollHeight - window.innerHeight;
    var ratio = max > 0 ? Math.min(1, Math.max(0, window.scrollY / max)) : 0;
    if (bar) bar.style.width = (ratio * 100).toFixed(2) + "%";
  }
  window.addEventListener("scroll", updateProgress, { passive: true });
  window.addEventListener("resize", updateProgress);
  updateProgress();

  if (!("IntersectionObserver" in window)) return;

  /* Active chapter in the top navigation */
  var links = {};
  document.querySelectorAll("[data-nav]").forEach(function (a) { links[a.getAttribute("data-nav")] = a; });
  var current = null;
  function setActive(id) {
    if (id === current) return;
    if (current && links[current]) links[current].classList.remove("is-active");
    current = id;
    var link = id && links[id];
    if (link) {
      link.classList.add("is-active");
      var nav = link.closest(".chapnav");
      if (nav && nav.scrollWidth > nav.clientWidth) {
        nav.scrollTo({ left: link.offsetLeft - 16, behavior: reduceMotion ? "auto" : "smooth" });
      }
    }
  }
  var chapterObserver = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) setActive(e.target.id);
    });
  }, { rootMargin: "-40% 0px -55% 0px" });
  document.querySelectorAll("[data-chapter]").forEach(function (s) { chapterObserver.observe(s); });
  var cover = document.querySelector(".cover");
  if (cover) {
    new IntersectionObserver(function (entries) {
      if (entries[0].isIntersecting) setActive(null);
    }, { rootMargin: "-40% 0px -55% 0px" }).observe(cover);
  }

  if (reduceMotion) return;

  /* Gentle fade-in, applied only to blocks that start below the first screen,
     so the page is complete at rest and nothing visible on load is hidden. */
  var fold = window.innerHeight;
  var revealObserver = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (!e.isIntersecting) return;
      e.target.classList.remove("is-pending");
      revealObserver.unobserve(e.target);
    });
  }, { rootMargin: "0px 0px -10% 0px" });
  document.querySelectorAll(".reveal").forEach(function (el) {
    if (el.getBoundingClientRect().top > fold) {
      el.classList.add("is-pending");
      revealObserver.observe(el);
    }
  });

  /* Timeline line fills from 2023 to 2026 when it comes into view */
  var timeline = document.getElementById("timeline");
  if (timeline && timeline.getBoundingClientRect().top > fold) {
    timeline.style.setProperty("--tl-progress", "0%");
    new IntersectionObserver(function (entries, obs) {
      if (!entries[0].isIntersecting) return;
      requestAnimationFrame(function () { timeline.style.setProperty("--tl-progress", "100%"); });
      obs.disconnect();
    }, { threshold: 0.4 }).observe(timeline);
  }
})();
