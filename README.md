# Task Prioritization System  
A smart task–ranking engine built using **Django (backend)** + **React (frontend)**.  
It evaluates tasks based on urgency, importance, effort, deadlines, and dependencies, and returns the optimal order to execute them.

---

## 🚀 Features

### ✔ Task Analysis  
Each task is scored based on:
- Urgency (according to deadline)
- Importance level  
- Effort required  
- Dependency impact  
- Penalty for prerequisites  
- Circular dependency detection  
- Weighted scoring (depending on chosen strategy)

### ✔ Smart Task Suggestion  
Automatically recommends the single best next task.

### ✔ Frontend Capabilities  
- Clean UI with priority color-coding  
- LocalStorage persistence  
- Edit/Delete tasks  
- Check as completed  
- See detailed scoring explanations  
- Task flow timeline (Completed → Suggested)

---

## 🎯 Scoring Algorithm

### 1. **Urgency Score**
Based on days until deadline:

| Days Left | Score |
|----------|--------|
| Overdue  | 10 |
| 0–1      | 9 |
| 2–3      | 8 |
| 4–7      | 6 |
| 8–14     | 4 |
| >14      | 2 |

---

### 2. **Effort Score**
| Hours | Score |
|--------|--------|
| ≤1     | 10 |
| ≤2     | 8 |
| ≤4     | 6 |
| ≤8     | 4 |
| >8     | 2 |

---

### 3. **Dependency Score**
Counts how many tasks depend *on this task*:

| Dependents | Score |
|------------|--------|
| 0 | 0 |
| 1 | 5 |
| 2–4 | 8 |
| ≥5 | 10 |

---

### 4. **Prerequisite Penalty**
If a task itself depends on others:

| Prereqs | Penalty |
|---------|-----------|
| 0 | 0 |
| 1 | –1 |
| 2 | –3 |
| ≥3 | –5 |

---

### 5. **Circular Dependencies**  
Detected using DFS.  
If present → **final score × 0.7**

---

### 6. **Final Score Formula**

final_score =urgencyw_u +importancew_i +effortw_e +dependencyw_d +penalty


### Strategy Weights

| Strategy        | U (Urgency) | I (Importance) | E (Effort) | D (Dependency) |
|----------------|-------------|----------------|------------|----------------|
| smart_balance  | 0.3         | 0.4            | 0.15       | 0.15           |
| deadline_driven| 0.6         | 0.2            | 0.1        | 0.1            |
| high_impact    | 0.2         | 0.6            | 0.1        | 0.1            |
| fastest_wins   | 0.2         | 0.2            | 0.5        | 0.1            |

---

## 📦 API Endpoints

### **POST `/api/tasks/analyze/`**
Input:
```json
{
  "strategy": "smart_balance",
  "tasks": [
    {
      "id": "T1",
      "title": "Prepare resume",
      "due_date": "2025-02-28",
      "estimated_hours": 2,
      "importance": 9,
      "dependencies": []
    }
  ]
}
```

### **POST `/api/tasks/suggest/`**

Returns:

The single most important next task, based on strategy.

### Running the Project

## Backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

## Frontend
npm install
npm start