let holidays = new Set();
let examOverlay = {}; // day -> subject string

document.addEventListener('DOMContentLoaded', () => {
    renderCalendar();

    // Listeners for auto-save config
    document.getElementById('numDays').addEventListener('change', renderCalendar);
    document.getElementById('startDate').addEventListener('change', renderCalendar);
});

function renderCalendar() {
    const numDays = parseInt(document.getElementById('numDays').value);
    const startDateVal = document.getElementById('startDate').value;
    const startDate = startDateVal ? new Date(startDateVal) : new Date();

    const grid = document.getElementById('calendar-grid');
    grid.innerHTML = '';

    // Result grid
    const resGrid = document.getElementById('result-calendar');
    resGrid.innerHTML = '';

    for (let i = 0; i < numDays; i++) {
        // Calculate Date
        // Create new date object to avoid mutating
        const currentDate = new Date(startDate);
        currentDate.setDate(startDate.getDate() + i);

        const dayName = currentDate.toLocaleDateString('en-US', { weekday: 'short' });
        const dateStr = currentDate.toLocaleDateString('en-US', { day: '2-digit', month: '2-digit' });
        const label = `${dayName} ${dateStr}`;

        // Setup Grid Item
        const day = document.createElement('div');
        day.className = 'day-box';
        if (holidays.has(i)) day.classList.add('is-holiday');
        day.innerHTML = `<span>${label}</span><br><span>(${i + 1})</span>`;
        day.onclick = () => toggleHoliday(i, day);
        grid.appendChild(day);

        // Result Grid Item
        const resDay = document.createElement('div');
        resDay.className = 'day-box';
        if (holidays.has(i)) resDay.classList.add('is-holiday');

        if (examOverlay[i]) {
            resDay.classList.add('has-exam');
            const tooltip = document.createElement('div');
            tooltip.className = 'day-content';
            tooltip.innerText = examOverlay[i];
            resDay.appendChild(tooltip);
        }
        resDay.innerHTML = `<span>${label}</span>`;
        resGrid.appendChild(resDay);
    }

    updateConfig();
}

function toggleHoliday(dayIndex, el) {
    if (holidays.has(dayIndex)) {
        holidays.delete(dayIndex);
        el.classList.remove('is-holiday');
    } else {
        holidays.add(dayIndex);
        el.classList.add('is-holiday');
    }
    renderCalendar(); // Re-render results too
}

async function updateConfig() {
    const data = {
        num_days: document.getElementById('numDays').value,
        holidays: Array.from(holidays),
        subjects: document.getElementById('subjects').value.split(','),
        allowed_emails: document.getElementById('allowedEmails').value,
        form_id: document.getElementById('formId').value,
        start_date: document.getElementById('startDate').value
    };

    await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
}

async function createForm() {
    await updateConfig();
    const title = document.getElementById('formTitle').value;

    const res = await fetch('/api/create_form', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title })
    });

    const json = await res.json();
    if (json.status === 'success') {
        document.getElementById('formURL').href = json.url;
        document.getElementById('formURL').innerText = json.url;
        document.getElementById('formId').value = json.form_id;
        document.getElementById('form-link-container').classList.remove('hidden');
        alert('Form Created!');
    } else {
        alert('Error: ' + json.message);
    }
}

async function runSchedule() {
    await updateConfig();
    document.querySelector('#status-bar').innerText = "Running Scheduler...";

    const res = await fetch('/api/run_schedule', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    });

    const json = await res.json();
    if (json.status === 'success') {
        document.querySelector('#status-bar').innerText = "Done!";
        document.getElementById('result-area').classList.remove('hidden');
        document.getElementById('algoName').innerText = json.algo;
        document.getElementById('penaltyVal').innerText = json.penalty.toFixed(2);

        // Map Results
        examOverlay = {};
        json.schedule.forEach(item => {
            if (!examOverlay[item.day]) examOverlay[item.day] = "";
            examOverlay[item.day] += item.subject + "\n";
        });
        renderCalendar();
    } else {
        document.querySelector('#status-bar').innerText = "Error!";
        alert('Error: ' + json.message);
    }
}
