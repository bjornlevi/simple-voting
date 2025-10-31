// ranked.js — dynamic ranked-choice UI helpers with clear inactive states
(function () {
  const root = document.getElementById('ranked-root');
  if (!root) return;

  const allOptions = JSON.parse(root.dataset.options || '[]');
  const selects = Array.from(root.querySelectorAll('.rank-select'));

  function buildOptions({ allow, keepValue, disabled }) {
    const frag = document.createDocumentFragment();

    const optBlank = document.createElement('option');
    optBlank.value = '';
    optBlank.textContent = disabled ? '— select earlier ranks first —' : '— leave blank —';
    frag.appendChild(optBlank);

    for (const opt of allOptions) {
      if (!allow.has(opt) && opt !== keepValue) continue;
      const o = document.createElement('option');
      o.value = opt;
      o.textContent = opt;
      frag.appendChild(o);
    }
    return frag;
  }

  function refresh() {
    // Enforce contiguity in the UI: once a blank appears, all later ranks must be blank/disabled
    let sawBlank = false;
    for (const sel of selects) {
      if (!sel.value) {
        sawBlank = true;
      } else if (sawBlank) {
        sel.value = '';
      }
    }

    // Set of currently chosen values
    const chosen = new Set(selects.map(s => s.value).filter(Boolean));

    selects.forEach((sel, idx) => {
      const keepSelf = sel.value;

      // Disable if any previous rank is blank
      const prevBlank = selects.slice(0, idx).some(s => !s.value);
      const disabled = prevBlank && idx > 0;
      sel.disabled = disabled;

      // Visual cues + a11y hint
      if (disabled) {
        sel.classList.add('inactive');
        sel.setAttribute('aria-disabled', 'true');
        sel.title = 'Pick earlier ranks first';
      } else {
        sel.classList.remove('inactive');
        sel.removeAttribute('aria-disabled');
        sel.removeAttribute('title');
      }

      // Allowed options = all minus chosen (except its own current value)
      const allow = new Set(allOptions);
      for (const c of chosen) allow.delete(c);

      // Rebuild options list with context-aware blank label
      const frag = buildOptions({ allow, keepValue: keepSelf, disabled });
      sel.innerHTML = '';
      sel.appendChild(frag);

      // Restore selection if still valid
      if (keepSelf) sel.value = keepSelf;
    });
  }

  selects.forEach(sel => sel.addEventListener('change', refresh));
  refresh();
})();
