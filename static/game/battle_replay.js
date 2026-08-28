(() => {
  const log = document.querySelector("[data-battle-replay]");
  if (!log || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  const lines = Array.from(log.querySelectorAll(".battle-line"));
  if (!lines.length) return;

  const delay = Number.parseInt(log.dataset.lineDelay, 10) || 550;
  lines.forEach((line) => { line.hidden = true; });

  let index = 0;
  const revealNext = () => {
    const line = lines[index];
    line.hidden = false;
    line.classList.add("is-revealed");
    log.scrollTop = log.scrollHeight;
    index += 1;
    if (index < lines.length) window.setTimeout(revealNext, delay);
  };

  revealNext();
})();
