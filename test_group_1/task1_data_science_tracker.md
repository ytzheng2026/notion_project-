Navigate to "Company In A Box" and create a child page named **"Data Science Tracker"**.

**UNIQUE STRUCTURE: Database-Centric with Multi-View System**

---

## Part A: Database Schema Design

1.  **Create "Projects" Database (Inline)**
    -   Create a new inline database titled **"Projects"**.
    -   Configure the following properties:
    -   Required Columns:
        -   `Name` (Title)
        -   `Status` (Select: Not started, In progress, Done)
        -   `Owner` (Person)
        -   `Start Date` (Date)
        -   `End Date` (Date)
        -   `Effort Hours` (Number)

2.  **Add Computed Properties**
    -   **"Days Remaining"** (Formula 2.0):
        ```
        if(empty(prop("End Date")), "—",
          let(rem, dateBetween(prop("End Date"), now(), "days"),
            if(rem < 0, "🔴 " + format(abs(rem)) + "d late",
              if(rem <= 3, "🟡 " + format(rem) + "d",
                "🟢 " + format(rem) + "d"))))
        ```
    -   **"Progress Bar"** (Formula 2.0):
        ```
        if(prop("Status") == "Done", "██████████ 100%",
          if(prop("Status") == "In progress", "█████░░░░░ 50%", "░░░░░░░░░░ 0%"))
        ```

---

## Part B: Data Population

3.  **Insert Project Records**
    -   Add the following rows to the **"Projects"** database:
    | Name | Status | Owner | Start | End | Hours |
    |------|--------|-------|-------|-----|-------|
    | ML Pipeline | In progress | Alice | 2026-01-10 | 2026-01-25 | 120 |
    | Data Lake | In progress | Bob | 2026-01-05 | 2026-01-20 | 80 |
    | Dashboards | Not started | Carol | — | — | 40 |

---

## Part C: View Configuration

4.  **Create 3 Database Views**
    -   Configure the following views for the **"Projects"** database:
    -   **View 1 "📋 Table"**: Default table, sort by Status
    -   **View 2 "📊 Board"**: Kanban grouped by Status (Not started → In progress → Done)
    -   **View 3 "📅 Timeline"**: Timeline view using Start/End Date, grouped by Owner

---

## Part D: Dashboard Assembly

5.  **Add Dashboard Header**
    -   Create a **Callout** block (Blue background, Icon 📊) with the text:
    -   **Callout (Blue, Icon 📊)**:
        "**Data Science Dashboard** | Total Effort: 240 hours | Active: 2"

6.  **Add Capacity Meter**
    -   Create the following blocks:
    -   Add **Divider**
    -   Add **Quote**: "Team Capacity: 160h/sprint | Utilization: 150%"
