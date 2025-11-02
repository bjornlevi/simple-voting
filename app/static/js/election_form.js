// app/static/js/election_form.js
(() => {
  const form = document.getElementById("election-form");
  const startInput = document.getElementById("start_at");
  const endInput = document.getElementById("end_at");

  if (!form || !startInput || !endInput) return;

  // Init Flatpickr once it's available (defer ensures load order; guard anyway)
  function initPickers() {
    if (typeof flatpickr === "undefined") {
      setTimeout(initPickers, 10);
      return;
    }

    const common = {
      enableTime: true,
      time_24hr: true,
      minuteIncrement: 1,
      // IMPORTANT: keep value format compatible with server parser "%Y-%m-%dT%H:%M"
      dateFormat: "Y-m-d\\TH:i",
      // Optional: nice calendar/time UI
      allowInput: true,
    };

    const startPicker = flatpickr(startInput, {
      ...common,
      onChange: (selectedDates, dateStr) => {
        if (endPicker) {
          endPicker.set("minDate", dateStr || null);
          // If end < start, snap end to start
          if (endInput.value && endInput.value < dateStr) {
            endPicker.setDate(dateStr, true);
          }
        }
      },
    });

    const endPicker = flatpickr(endInput, {
      ...common,
      onChange: (selectedDates, dateStr) => {
        const sv = startInput.value;
        if (sv && dateStr && dateStr < sv) {
          startPicker.setDate(dateStr, true);
        }
      },
    });

    // Initialize constraint if start already set (e.g., back nav caching)
    if (startInput.value) endPicker.set("minDate", startInput.value);
  }

  initPickers();

  // Final guard before submit
  form.addEventListener("submit", (e) => {
    const sv = startInput.value;
    const ev = endInput.value;
    if (sv && ev && ev < sv) {
      e.preventDefault();
      alert("End time must be after start time.");
    }
  });
})();
