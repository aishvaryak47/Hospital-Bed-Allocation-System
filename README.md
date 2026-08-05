# Hospital Bed Allocation System Using Discrete Mathematics

A full-stack web application demonstrating the practical application of **Discrete Mathematics** concepts in healthcare resource optimization and bed allocation.

![Hospital Bed Allocation System](https://img.shields.io/badge/Python-3.11-blue.svg) ![Flask](https://img.shields.io/badge/Flask-3.1.0-green.svg) ![NetworkX](https://img.shields.io/badge/NetworkX-3.6-orange.svg) ![License](https://img.shields.io/badge/License-MIT-purple.svg)

---

## 📌 Project Overview

Hospital bed allocation is a critical challenge in healthcare management. This application applies core Discrete Mathematics principles—including **Graph Theory**, **Priority Queues**, **Set Theory**, **Binary Relations**, and **Optimization Logic**—to dynamically match incoming patients with available hospital beds based on urgency, department eligibility, and capacity constraints.

---

## 🧮 Discrete Mathematics Concepts Implemented

### 1. Graph Theory (`NetworkX`)
- **Topology:** Multi-partite graph $G = (V_{\text{Patients}} \cup V_{\text{Depts}} \cup V_{\text{Beds}}, E)$.
- **Edges:** $(P_i, D_j)$ weighted by urgency score, $(D_j, B_k)$ representing bed containment.
- **Matching Algorithm:** Maximum Weight Bipartite Matching via `NetworkX`.
- **Live Canvas:** Rendered using Vis.js force-directed topology map on the Dashboard.

### 2. Priority Queue Invariant (`heapq`)
- **Order Invariant:** Priority tuple $(L, T_{\text{adm}})$ where:
  $$\text{Emergency (L1)} > \text{Critical (L2)} > \text{General (L3)}$$
- **Tie-Breaker:** First-In, First-Out (FIFO) ordering based on admission timestamp $T_{\text{adm}}$.

### 3. Set Theory State Management
- Enforces strict set partition of Universal Bed Set $U_{\text{Beds}}$:
  $$S_{\text{Available}} \cap S_{\text{Occupied}} \cap S_{\text{Maint}} = \emptyset$$
  $$S_{\text{Available}} \cup S_{\text{Occupied}} \cup S_{\text{Maint}} = U_{\text{Beds}}$$
- Automatic set transitions upon bed allocation or patient discharge.

### 4. Binary Relations & Mappings
- Patient-to-Department relation $R_{PD} \subseteq P \times D$.
- Department-to-Bed relation $R_{DB} \subseteq D \times B$.
- Active Allocation Composite Relation $R_{PB} = R_{PD} \circ R_{DB} \subseteq P \times B$.

---

## 💻 Tech Stack

- **Backend:** Python 3.11, Flask, Flask-SQLAlchemy
- **Discrete Math Engines:** NetworkX, `heapq`
- **Database:** SQLite (default) / MySQL support
- **Frontend:** HTML5, CSS3 (Custom Hospital Blue/White Theme), JavaScript, Bootstrap 5
- **Visualizations:** Vis.js (Graph Canvas), Chart.js (Analytics & Occupancy Bar/Pie Charts)

---

## 🚀 Quick Start Guide

### 1. Clone the Repository
```bash
git clone https://github.com/aishvaryak47/Hospital-Bed-Allocation-System-Discrete-Math.git
cd Hospital-Bed-Allocation-System-Discrete-Math
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Seed Database with Sample Data
```bash
python seed_data.py
```

### 4. Run the Flask Web Application
```bash
python app.py
```
Open your browser and navigate to `http://127.0.0.1:5000`.

---

## 🎨 System Screenshots & Modules

- **Dashboard:** KPI summary cards, live NetworkX bipartite graph topology, department occupancy metrics.
- **Patient Directory:** Register new patients, priority queue badges, search, filter, and edit records.
- **Bed Inventory:** 130 beds across 5 departments (*ICU, Emergency, General Ward, Pediatrics, Orthopedics*), real-time set theory counters.
- **Intelligent Allocation Engine:** Priority graph auto-allocation solver with step-by-step math execution logs.
- **Allocation History:** Real-time audit trail of allocations, reallocations, and discharges.
- **Discrete Math Reports:** Formal proofs and mathematical formulations.

---

## 📄 License
Distributed under the MIT License.
