import React, { useState, useEffect } from "react";
import axios from "axios";
import "./App.css";

function normalizeDate(d) {
  if (!d) return "";
  if (d.includes("-")) return d; 
  if (!d.includes("/")) return d;

  const [dd, mm, yyyy] = d.split("/");
  return `${yyyy}-${mm}-${dd}`;
}

function getNextAvailableId(tasks) {
  const used = new Set(tasks.map((t) => Number(t.id.substring(1))));
  let i = 1;
  while (used.has(i)) i++;
  return i;
}

const emptyTask = (idNum) => ({
  uid: crypto.randomUUID(),
  id: "T" + idNum,
  title: "",
  importance: "",
  estimated_hours: "",
  due_date: "",
  dependencies: "",
  completed: false,
});

function getDaysLeft(dateStr) {
  if (!dateStr) return null;

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const due = new Date(dateStr);
  due.setHours(0, 0, 0, 0);

  return Math.ceil((due - today) / (1000 * 60 * 60 * 24));
}

function mergeAnalysisWithClient(analysis, tasksList) {
  return analysis.map((a) => {
    const original = tasksList.find((t) => t.id === a.id) || {};
    return {
      ...a,
      completed: original.completed || false,
      due_date: original.due_date || "",
    };
  });
}

function mergeSuggestedWithClient(suggested, tasksList) {
  if (!suggested) return null;
  const original = tasksList.find((t) => t.id === suggested.id) || {};
  return {
    ...suggested,
    completed: original.completed || false,
    due_date: original.due_date || "",
  };
}

const formatTasksForBackend = (list) =>
  list.map((t) => ({
    ...t,
    importance: Number(t.importance),
    estimated_hours: Number(t.estimated_hours),
    due_date: normalizeDate(t.due_date),
    dependencies: t.dependencies
      ? t.dependencies
          .split(",")
          .map((d) => d.trim())
          .filter(Boolean)
      : [],
  }));

function TaskCard({ t }) {
  const [open, setOpen] = useState(false);

  const priorityColor =
    t.final_score >= 7
      ? "#dc2626"
      : t.final_score >= 4
      ? "#f59e0b"
      : "#16a34a";

  const daysLeft = getDaysLeft(t.due_date);

  return (
    <div className="analysis-card">
      <div className="analysis-bar" style={{ backgroundColor: priorityColor }} />

      <div className="analysis-content">
        <div className="analysis-header">
          <h3 className="analysis-title">{t.title}</h3>
          <div className="score-pill" style={{ backgroundColor: priorityColor }}>
            {t.final_score}
          </div>
        </div>

        <div className="analysis-meta">
          <div>
            <strong>Urgency:</strong> {t.urgency_score}
          </div>
          <div>
            <strong>Effort:</strong> {t.effort_score}
          </div>
          <div>
            <strong>Dependency:</strong> {t.dependency_score}
          </div>
          <div>
            <strong>Strategy:</strong> {t.strategy}
          </div>

          <div className="deadline">
            <strong>Deadline:</strong>{" "}
            {daysLeft === null ? (
              "Not set"
            ) : daysLeft > 0 ? (
              <span className="deadline-green">{daysLeft} days left</span>
            ) : daysLeft === 0 ? (
              <span className="deadline-orange">Due today</span>
            ) : (
              <span className="deadline-red">
                Overdue by {Math.abs(daysLeft)} days
              </span>
            )}
          </div>
        </div>

        <button className="details-btn" onClick={() => setOpen(!open)}>
          {open ? "Hide Details" : "Show Details"}
        </button>

        {open && (
          <ul className="details-list">
            {t.explanations?.map((e, i) => (
              <li key={i}>{e}</li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}





function App() {
  const [tasks, setTasks] = useState(() => {
    const saved = localStorage.getItem("user_tasks");
    return saved ? JSON.parse(saved) : [];
  });

  const [nextId, setNextId] = useState(() =>
    getNextAvailableId(JSON.parse(localStorage.getItem("user_tasks") || "[]"))
  );

  const [form, setForm] = useState(emptyTask(nextId));
  const [editIndex, setEditIndex] = useState(null);

  const [strategy, setStrategy] = useState("smart_balance");
  const [result, setResult] = useState(null);
  const [suggested, setSuggested] = useState(null);
  const [flow, setFlow] = useState([]);
  const [jsonInput, setJsonInput] = useState("");
  const [jsonError, setJsonError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    localStorage.setItem("user_tasks", JSON.stringify(tasks));
  }, [tasks]);

  const handleFormChange = (field, value) => {
    if (field === "importance") {
      if (value === "") {
        setForm({ ...form, [field]: value });
        return;
      }
      const num = Number(value);
      if (Number.isNaN(num) || num < 1 || num > 10) return;
    }

    if (field === "estimated_hours") {
      if (value === "") {
        setForm({ ...form, [field]: value });
        return;
      }
      const num = Number(value);
      if (Number.isNaN(num) || num < 1) return;
    }

    setForm({ ...form, [field]: value });
  };

  const addTask = () => {
    const { title, importance, estimated_hours, due_date } = form;

    if (
      !title.trim() ||
      !importance.toString().trim() ||
      !estimated_hours.toString().trim() ||
      !due_date.trim()
    ) {
      alert("Please fill all fields before adding a task.");
      return;
    }

    const updated = [...tasks, form];
    const next = getNextAvailableId(updated);

    setTasks(updated);
    setNextId(next);
    setForm(emptyTask(next));
  };

  const loadEdit = (index) => {
    setForm(tasks[index]);
    setEditIndex(index);
  };

  const updateTask = () => {
    const { title, importance, estimated_hours, due_date } = form;

    if (
      !title.trim() ||
      !importance.toString().trim() ||
      !estimated_hours.toString().trim() ||
      !due_date.trim()
    ) {
      alert("Please fill all fields before saving.");
      return;
    }

    const updated = [...tasks];
    updated[editIndex] = form;

    setTasks(updated);
    setEditIndex(null);

    const next = getNextAvailableId(updated);
    setNextId(next);
    setForm(emptyTask(next));
  };

  const deleteTaskById = (taskId) => {
    const updated = tasks.filter((t) => t.id !== taskId);

    setTasks(updated);

    const next = getNextAvailableId(updated);
    setNextId(next);
    setForm(emptyTask(next));
  };

  const toggleCompletedById = async (taskId) => {
    const updated = tasks.map((t) =>
      t.id === taskId ? { ...t, completed: !t.completed } : t
    );

    setTasks(updated);

    const justCompleted = updated.find((t) => t.id === taskId);
    if (!justCompleted.completed) return;

    setFlow((prev) => [
      ...prev,
      { kind: "completed", id: justCompleted.id, title: justCompleted.title },
    ]);

    try {
      const res = await axios.post("http://127.0.0.1:8000/api/tasks/suggest/", {
        strategy,
        tasks: formatTasksForBackend(updated),
      });

      if (res.data?.recommended_task) {
        const next = mergeSuggestedWithClient(res.data.recommended_task, updated);
        setSuggested(next);

        setFlow((prev) => [
          ...prev,
          { kind: "suggested", id: next.id, title: next.title },
        ]);
      }
    } catch {
      alert("Backend not running");
    }
  };

  const analyze = async () => {
    const cleaned = tasks.filter((t) => {
      const imp = Number(t.importance);
      const hrs = Number(t.estimated_hours);

      return (
        t.title.trim() &&
        !Number.isNaN(imp) &&
        imp >= 1 &&
        imp <= 10 &&
        !Number.isNaN(hrs) &&
        hrs >= 1 &&
        t.due_date
      );
    });

    if (cleaned.length === 0) {
      alert("No valid tasks to analyze.");
      return;
    }

    try {
      const res = await axios.post("http://127.0.0.1:8000/api/tasks/analyze/", {
        strategy,
        tasks: formatTasksForBackend(cleaned),
      });

      setResult(mergeAnalysisWithClient(res.data, tasks));
    } catch {
      alert("Backend not running");
    }
  };

  const suggest = async () => {
    const cleaned = tasks.filter((t) => {
      const imp = Number(t.importance);
      const hrs = Number(t.estimated_hours);

      return (
        t.title.trim() &&
        !Number.isNaN(imp) &&
        imp >= 1 &&
        imp <= 10 &&
        !Number.isNaN(hrs) &&
        hrs >= 1 &&
        t.due_date
      );
    });

    if (cleaned.length === 0) {
      alert("No valid tasks to suggest from.");
      return;
    }

    try {
      const res = await axios.post("http://127.0.0.1:8000/api/tasks/suggest/", {
        strategy,
        tasks: formatTasksForBackend(cleaned),
      });

      if (res.data?.recommended_task) {
        const next = mergeSuggestedWithClient(res.data.recommended_task, tasks);
        setSuggested(next);

        setFlow((prev) => [
          ...prev,
          { kind: "suggested", id: next.id, title: next.title },
        ]);
      }
    } catch {
      alert("Backend not running");
    }
  };

  const clearAll = () => {
    setTasks([]);
    setNextId(1);
    setResult(null);
    setSuggested(null);
    setFlow([]);
    localStorage.removeItem("user_tasks");
    setForm(emptyTask(1));
  };
const handleJsonImport = () => {
  setJsonError("");

  if (!jsonInput.trim()) {
    setJsonError("Please paste a JSON array.");
    return;
  }

  let parsed;
  try {
    parsed = JSON.parse(jsonInput);
  } catch (err) {
    setJsonError("Invalid JSON format.");
    return;
  }

  if (!Array.isArray(parsed)) {
    setJsonError("JSON must be an array of task objects.");
    return;
  }

  const newTasks = [];
  let idCounter = nextId;

  for (let i = 0; i < parsed.length; i++) {
    const t = parsed[i];

    if (!t.title || !t.importance || !t.estimated_hours || !t.due_date) {
      setJsonError(`Task ${i + 1} is missing required fields.`);
      return;
    }

    const imp = Number(t.importance);
    const hrs = Number(t.estimated_hours);

    if (Number.isNaN(imp) || imp < 1 || imp > 10) {
      setJsonError(`Task ${i + 1}: importance must be 1–10.`);
      return;
    }

    if (Number.isNaN(hrs) || hrs < 1) {
      setJsonError(`Task ${i + 1}: estimated_hours must be ≥ 1.`);
      return;
    }

    const task = {
      uid: crypto.randomUUID(),
      id: "T" + idCounter++,
      title: t.title,
      importance: imp,
      estimated_hours: hrs,
      due_date: normalizeDate(t.due_date),
      dependencies: Array.isArray(t.dependencies)
        ? t.dependencies.join(",")
        : (t.dependencies || ""),
      completed: false,
    };

    newTasks.push(task);
  }

  const updated = [...tasks, ...newTasks];

  setTasks(updated);
  setNextId(idCounter);
  setForm(emptyTask(idCounter));

  // Clear textarea
  setJsonInput("");
  alert("Tasks imported successfully!");
};

  return (
    <div className="container">
      <h1 style={{ padding: "30px", fontSize: "5vh" }}>
        Task Harbour
      </h1>

      <div className="main-layout">
        <div>
          <h2 style={{ fontSize: "3vh" }}>
            {editIndex !== null ? "Edit Task" : "Add New Task"}
          </h2>

          <div className="card form-card">
            <input value={form.id} disabled style={{ background: "#eee" }} />

            <input
              placeholder="Title"
              value={form.title}
              onChange={(e) => handleFormChange("title", e.target.value)}
            />

            <input
              type="number"
              min="1"
              max="10"
              placeholder="Importance (1-10)"
              value={form.importance}
              onChange={(e) => handleFormChange("importance", e.target.value)}
            />

            <input
              type="number"
              min="1"
              placeholder="Estimated Hours"
              value={form.estimated_hours}
              onChange={(e) =>
                handleFormChange("estimated_hours", e.target.value)
              }
            />

            <input
              type="date"
              value={form.due_date}
              onChange={(e) => handleFormChange("due_date", e.target.value)}
            />

            <input
              placeholder="Dependencies: T1,T2"
              value={form.dependencies}
              onChange={(e) => handleFormChange("dependencies", e.target.value)}
            />

            {editIndex !== null ? (
              <button onClick={updateTask}>Save Changes</button>
            ) : (
              <button onClick={addTask}>Add Task</button>
            )}
          </div>
        </div>

        <div className="task-list-section">
          <h2 style={{ fontSize: "3vh" }}>Your Tasks</h2>

          {tasks.length === 0 && <p>No tasks yet.</p>}

          {tasks.map((t, index) => (
            <div key={t.uid} className="task-list-item enhanced-task-row">
              <div className="task-left">
                <input
                  type="checkbox"
                  checked={t.completed}
                  onChange={() => toggleCompletedById(t.id)}
                  className="task-checkbox"
                />

                <div className="task-text">
                  <span className="task-id">{t.id}</span>
                  <span className="task-title-text">
                    {t.title || "(No title)"}
                  </span>
                </div>
              </div>

              <div className="task-actions">
                <button
                  className="task-edit-btn"
                  onClick={() => loadEdit(index)}
                >
                  Edit
                </button>
                <button
                  className="task-delete-btn"
                  onClick={() => deleteTaskById(t.id)}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="strategy-row">
        <label htmlFor="strategy" className="strategy-label">
          Strategy:
        </label>

        <select
          id="strategy"
          value={strategy}
          onChange={(e) => setStrategy(e.target.value)}
          className="strategy-select"
        >
          <option value="fastest_wins">Fastest Wins</option>
          <option value="high_impact">High Impact</option>
          <option value="deadline_driven">Deadline Driven</option>
          <option value="smart_balance">Smart Balance</option>
        </select>
      </div>
<div className="bulk-import-card card">
  <h2>Bulk JSON Import</h2>

  <textarea
    className="json-textarea"
    placeholder='Paste JSON array here... Example:
[
  {"title": "Study", "importance": 8, "estimated_hours": 2, "due_date": "2025-12-07"},
  {"title": "Gym", "importance": 5, "estimated_hours": 1, "due_date": "2025-12-10"}
]'
    value={jsonInput}
    onChange={(e) => setJsonInput(e.target.value)}
  />

  {jsonError && <p className="json-error">{jsonError}</p>}

  <button className="import-btn" onClick={handleJsonImport}>
    Import Tasks
  </button>
</div>

      <div className="btn-group">
        <button onClick={analyze}>Analyze Tasks</button>
        <button onClick={suggest}>Suggest Task</button>
        <button onClick={clearAll}>Clear All</button>
      </div>

      {flow.length > 0 && (
        <div className="flow-chain">
          <h2>Task Flow</h2>

          <div className="flow-items">
            {flow.map((step, i) => (
              <div className={`flow-box ${step.kind}`} key={i}>
                <div className="flow-title">
                  {step.kind === "completed" ? "Completed" : "Suggested"}:
                </div>
                <div className="flow-id">{step.id}</div>
                <div className="flow-subtitle">{step.title}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {result && (
        <div className="card result-card">
          <div className="priority-legend">
            <span>
              <span className="legend-box high"></span> High Priority (score
              greater than 7)
            </span>
            <span>
              <span className="legend-box medium"></span> Medium Priority
              (4–6.9)
            </span>
            <span>
              <span className="legend-box low"></span> Low Priority (score less
              than 4)
            </span>
          </div>

          <h2>Analysis</h2>
          <div className="task-grid">
            {result.map((t) => (
              <TaskCard key={t.id} t={t} />
            ))}
          </div>
        </div>
      )}

      {suggested && (
        <div
          className="card result-card"
          onClick={() => toggleCompletedById(suggested.id)}
          style={{ cursor: "pointer" }}
        >
          <h2>Suggested Next Task</h2>
          <TaskCard t={suggested} />
        </div>
      )}
    </div>
  );
}

export default App;
