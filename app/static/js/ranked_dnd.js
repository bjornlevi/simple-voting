// static/js/ranked_dnd.js
(function () {
  const root = document.getElementById('ranked-root');
  if (!root) return;

  const picked = document.getElementById('rank-picked');
  const avail  = document.getElementById('rank-available');
  const hidden = document.getElementById('rank-hidden');
  const form   = root.closest('form');
  const opts   = JSON.parse(root.dataset.options || '[]');

  // Utilities
  const makeAvailItem = (text) => {
    const li = document.createElement('li');
    li.className = 'rank-item';
    li.tabIndex = 0;
    li.draggable = true;
    li.dataset.value = text;
    li.innerHTML = `
      <span class="handle" aria-hidden="true">⋮⋮</span>
      <span class="label">${text}</span>
      <div class="item-actions">
        <button type="button" class="btn tiny secondary choose">Velja</button>
      </div>
    `;
    return li;
  };

  const makePickedItem = (text) => {
    const li = document.createElement('li');
    li.className = 'rank-item';
    li.tabIndex = 0;
    li.draggable = true;
    li.dataset.value = text;
    li.innerHTML = `
      <span class="handle" aria-hidden="true">⋮⋮</span>
      <span class="label">${text}</span>
      <div class="item-actions">
        <button type="button" class="btn tiny secondary up" aria-label="Færa upp">↑</button>
        <button type="button" class="btn tiny secondary down" aria-label="Færa niður">↓</button>
        <button type="button" class="btn tiny danger remove" aria-label="Sleppa">Sleppa</button>
      </div>
    `;
    return li;
  };

  // Populate ALL options on the left; right starts empty
  avail.innerHTML = '';
  picked.innerHTML = '';
  opts.forEach((o) => avail.appendChild(makeAvailItem(o)));

  // Drag & drop
  let dragSrc = null;   // the <li> being dragged
  let srcList = null;   // 'avail' or 'picked'

  const onDragStart = (e) => {
    const item = e.currentTarget;
    dragSrc = item;
    srcList = (item.parentElement === avail) ? 'avail' : 'picked';
    item.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', item.dataset.value);
  };

  const onDragEnd = (e) => {
    e.currentTarget.classList.remove('dragging');
    dragSrc = null;
    srcList = null;
    picked.classList.remove('drop-highlight');
  };

  const allowDrop = (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  // Highlight "Röðun þín" when dragging over it (only if dragging from avail)
  picked.addEventListener('dragenter', (e) => {
    if (srcList === 'avail') picked.classList.add('drop-highlight');
  });
  picked.addEventListener('dragleave', (e) => {
    // remove highlight if leaving the list area
    if (!picked.contains(e.relatedTarget)) picked.classList.remove('drop-highlight');
  });

  const onDropAvail = (e) => {
    e.preventDefault();
    // No-op: dropping onto avail doesn't change anything special
    if (dragSrc && dragSrc.parentElement !== avail) {
      // moved from picked back to avail: append to end
      avail.appendChild(toAvail(dragSrc));
    }
  };

  const onDropPicked = (e) => {
    e.preventDefault();
    picked.classList.remove('drop-highlight');
    if (!dragSrc) return;

    if (srcList === 'avail') {
      // From available → picked: always append to end
      picked.appendChild(toPicked(dragSrc));
    } else {
      // From picked → picked: reorder. If drop on empty area, append to end.
      const targetItem = e.target.closest('.rank-item');
      if (!targetItem || targetItem === dragSrc) {
        picked.appendChild(dragSrc);
      } else {
        // Reorder by position
        const rect = targetItem.getBoundingClientRect();
        const before = (e.clientY - rect.top) < rect.height / 2;
        if (before) picked.insertBefore(dragSrc, targetItem);
        else picked.insertBefore(dragSrc, targetItem.nextSibling);
      }
    }
  };

  // Wire lists to accept drops
  avail.addEventListener('dragover', allowDrop);
  picked.addEventListener('dragover', allowDrop);
  avail.addEventListener('drop', onDropAvail);
  picked.addEventListener('drop', onDropPicked);

  // Wire items (drag + buttons)
  const wireAvailItem = (item) => {
    item.addEventListener('dragstart', onDragStart);
    item.addEventListener('dragend', onDragEnd);
    item.querySelector('.choose')?.addEventListener('click', () => {
      picked.appendChild(toPicked(item));
    });
    // Keyboard: Enter to choose
    item.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') picked.appendChild(toPicked(item));
    });
  };

  const wirePickedItem = (item) => {
    item.addEventListener('dragstart', onDragStart);
    item.addEventListener('dragend', onDragEnd);
    item.querySelector('.up')?.addEventListener('click', () => {
      const prev = item.previousElementSibling;
      if (prev) item.parentElement.insertBefore(item, prev);
    });
    item.querySelector('.down')?.addEventListener('click', () => {
      const next = item.nextElementSibling;
      if (next) item.parentElement.insertBefore(next, item);
    });
    item.querySelector('.remove')?.addEventListener('click', () => {
      avail.appendChild(toAvail(item));
    });
    // Keyboard support inside picked
    item.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        const prev = item.previousElementSibling;
        if (prev) item.parentElement.insertBefore(item, prev);
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        const next = item.nextElementSibling;
        if (next) item.parentElement.insertBefore(next, item);
      } else if (e.key === 'Enter') {
        // Enter toggles back to available
        avail.appendChild(toAvail(item));
      }
    });
  };

  // Transform helpers (preserve text, rebuild appropriate controls)
  const toPicked = (item) => {
    const text = item.dataset.value;
    const newEl = makePickedItem(text);
    wirePickedItem(newEl);
    item.replaceWith(newEl);
    return newEl;
  };
  const toAvail = (item) => {
    const text = item.dataset.value;
    const newEl = makeAvailItem(text);
    wireAvailItem(newEl);
    item.replaceWith(newEl);
    return newEl;
  };

  // Initial wiring
  avail.querySelectorAll('.rank-item').forEach(wireAvailItem);

  // Submit → emit rank_1..rank_n based on picked order
  form.addEventListener('submit', () => {
    hidden.innerHTML = '';
    const values = Array.from(picked.querySelectorAll('.rank-item')).map((el) => el.dataset.value);
    values.forEach((val, i) => {
      const input = document.createElement('input');
      input.type = 'hidden';
      input.name = `rank_${i + 1}`;
      input.value = val;
      hidden.appendChild(input);
    });
  });
})();
