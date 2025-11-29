// Manage a small in-memory list if user uses the form
let localTasks = [];

function showMessage(msg, isErr=false) {
    const el = document.getElementById('message');
    el.textContent = msg;
    el.style.color = isErr ? 'red' : 'green';
}

document.getElementById('addTaskBtn').addEventListener('click', () => {
    const title = document.getElementById('title').value.trim();
    const due_date = document.getElementById('due_date').value.trim();
    const importance = parseInt(document.getElementById('importance').value) || 5;
    const estimated_hours = parseFloat(document.getElementById('estimated_hours').value) || 1;
    const depsRaw = document.getElementById('deps').value.trim();
    const deps = depsRaw ? depsRaw.split(',').map(s => s.trim()) : [];

    if (!title) {
        showMessage("Title required", true);
        return;
    }
    const id = Date.now().toString(36) + Math.floor(Math.random()*1000);
    localTasks.push({id, title, due_date: due_date || null, importance, estimated_hours, dependencies: deps});
    showMessage("Task added to local list");
    document.getElementById('taskForm').reset();
    renderLocalTasksPreview();
});

function renderLocalTasksPreview() {
    const t = localTasks.map(x => `${x.title} (${x.due_date || 'no date'})`).join(' | ');
    document.getElementById('taskInput').value = JSON.stringify(localTasks, null, 2);
}

document.getElementById('clearBtn').addEventListener('click', () => {
    localTasks = [];
    document.getElementById('taskInput').value = "";
    document.getElementById('results').innerHTML = "";
    showMessage("Cleared");
});

document.getElementById('analyzeBtn').addEventListener('click', analyzeTasks);

async function analyzeTasks() {
    const inputVal = document.getElementById('taskInput').value.trim();
    let tasks;
    if (!inputVal) {
        showMessage("No tasks provided", true);
        return;
    }
    try {
        tasks = JSON.parse(inputVal);
        if (!Array.isArray(tasks)) throw new Error("Please provide a JSON array of tasks.");
    } catch (err) {
        showMessage("Invalid JSON: " + err.message, true);
        return;
    }

    const strategy = document.getElementById('strategy').value || 'smart_balance';
    showMessage("Analyzing...");

    try {
        const resp = await fetch(`http://127.0.0.1:8000/api/tasks/analyze/?strategy=${strategy}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(tasks)
        });

        if (!resp.ok) {
            const text = await resp.text();
            throw new Error(text || resp.statusText);
        }
        const data = await resp.json();
        displayResults(data.tasks || []);
        showMessage("Analysis complete");
    } catch (err) {
        showMessage("Error: " + err.message, true);
    }
}

function displayResults(tasks) {
    const container = document.getElementById('results');
    container.innerHTML = "";
    if (!tasks.length) {
        container.innerHTML = "<p>No tasks returned</p>";
        return;
    }
    tasks.forEach(t => {
        const card = document.createElement('div');
        card.className = 'task-card';
        const score = t.score || 0;
        if (score >= 150) card.classList.add('high');
        else if (score >= 80) card.classList.add('med-high');
        else if (score >= 40) card.classList.add('med');
        else card.classList.add('low');

        card.innerHTML = `
            <strong>${t.title || '(no title)'}</strong>
            <div class="task-meta">Due: ${t.due_date || '—'} | Importance: ${t.importance || '—'} | Est hrs: ${t.estimated_hours || '—'} | Score: ${score}</div>
            <div class="explanation">${t.explanation || ''}</div>
        `;
        container.appendChild(card);
    });
}
