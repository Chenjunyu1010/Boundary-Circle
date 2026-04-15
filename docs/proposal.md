# Boundary Circle - Project Proposal

**Team ID**: EX2-Team-12  
**Date**: February 10, 2026

> NOTE (2026-04-15): This is a cleaned version of the original proposal for documentation
> maintenance. It preserves the original project intent, but some implementation details in the
> repository changed over time. Treat this file as historical design intent, not a strict snapshot
> of the current codebase.

---

## 1. Project Overview

### Project Purpose

Boundary Circle is a social and team-formation platform designed for students and community-based
groups. Its core goal is to help users find suitable teammates inside specific circles such as
courses, competitions, clubs, or interest groups.

The system introduces a **tag-based identity model**. Instead of exposing one global profile to
everyone, users present circle-specific tags that describe their skills, interests, or background
within each context.

**Initial target users**: college students  
**Potential expansion**: enterprise departments, student clubs, and semi-closed communities

### Motivation

Students often form teams through fragmented chat groups or spreadsheets. These channels have two
common failures:
- real-name platforms reduce willingness to discuss sensitive or unfinished work
- anonymous platforms weaken trust and accountability

Boundary Circle aims to balance privacy and trust through **authentication plus contextual tags**.

### Stakeholders

| Stakeholder | Description |
|-------------|-------------|
| **End Users (Students)** | Users who want to recruit teammates or join teams while keeping appropriate privacy boundaries |
| **Circle Creators** | Community organizers who define circle rules and tag schemas |
| **Course Instructors** | Project sponsors and evaluators |
| **University Administration** | Interested in privacy, safety, and appropriate usage |
| **Development Team** | Responsible for architecture, implementation, testing, and maintenance |

### Goals

- Improve team formation efficiency in course and activity settings
- Provide contextual identity rather than one global social profile
- Support trust-building through structured tags and gated access
- Preserve privacy boundaries across different circles

---

## 2. Requirements Engineering

### User Requirements

- **UR-1: Contextual Identity and Isolation**  
  Users should participate in different circles with different visible identities.

- **UR-2: Gated Access via Mandatory Tags**  
  Circle creators should be able to require specific tags before members can fully participate.

- **UR-3: Goal-Oriented Team Formation**  
  Users should be able to discover teammates and form teams inside a circle.

### Functional Requirements

- **FR-1: Circle Schema Definition**  
  Circle creators define required and optional tag fields.

- **FR-2: Gated Entry Workflow**  
  New members fill in required tags before accessing circle content.

- **FR-3: Matching Support**  
  The system ranks users or teams based on circle-specific profile compatibility.

- **FR-4: Team Lifecycle**  
  Teams move through states such as recruiting, inviting, and locking membership.

- **FR-5: Visibility Control**  
  Circle-specific data should not be visible outside the circle boundary.

### Non-Functional Requirements

- **NFR-1: Privacy Isolation**  
  User data across circles must stay separated.

- **NFR-2: Usable Matching Performance**  
  Matching and filtering should respond quickly enough for interactive use.

- **NFR-3: Flexible Tag Types**  
  The system should support multiple tag types such as strings, booleans, integers, floats, and enums.

---

## 3. Example Use Case

### AI Competition Team Formation

**Preconditions**
- A circle exists for an AI competition.
- A user has joined the circle and filled in relevant tags.
- Another user is recruiting teammates with defined requirements.

**Normal Flow**
1. A recruiter posts team requirements.
2. The system compares those requirements against circle-specific user tags.
3. The recruiter reviews ranked candidates.
4. Invitations are sent and accepted inside the platform.

**Exception Flows**
- If no strong matches exist, the system suggests broadening requirements.
- If a user tries to access restricted content without membership, access is denied.

**End State**
- A team is formed with members selected from the circle.

---

## 4. Feasibility Study

| Aspect | Assessment |
|--------|------------|
| **Skills** | The team uses Python, FastAPI, Streamlit, testing, and GitHub-based collaboration |
| **Data** | User profile data, tag data, and team requirements can be represented in a relational model |
| **Time** | The project scope fits an incremental course schedule with milestone-based delivery |
| **Computing Resources** | No specialized hardware is required for the core product |
| **Budget** | The project is designed around a zero-cost or low-cost student tooling stack |

---

## 5. System Architecture

### Architecture Overview

The original design followed a modular layered structure:

```text
+--------------------------------------------------+
|            User Interface (UI) Layer              |
|        (Web / prototype frontend layer)           |
+--------------------------------------------------+
|          Application Service Layer                |
|       (Business logic and workflow rules)         |
+--------------------------------------------------+
|   Matching & Recommendation Module                |
|     (Tag similarity and ranking logic)            |
+--------------------------------------------------+
|   Authentication & Circle Management              |
|     (Accounts, membership, access control)        |
+--------------------------------------------------+
|              Data Storage Layer                   |
|   (Relational storage, optional vector storage)   |
+--------------------------------------------------+
```

### Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| **UI Layer** | Circle browsing, profile/tag input, team interaction |
| **Application Layer** | Validation, workflows, and business rules |
| **Matching Module** | Ranking and compatibility analysis |
| **Auth & Circle Management** | Accounts, membership, access control |
| **Data Layer** | Persistent storage for users, circles, tags, and teams |

---

## 6. Project Plan

### Timeline

| Week | Milestone | Deliverable |
|------|-----------|-------------|
| 5-6 | Requirements and design | Finalized requirements and architecture |
| 7-8 | Core backend development | Users, circles, tags, and related APIs |
| 9-10 | Matching implementation | Matching and filtering logic |
| 11 | Frontend integration | Frontend and backend integration |
| 12 | Testing and refinement | Test evidence and bug fixing |
| 13-14 | Final demo and delivery | Demo and documentation package |

### Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Matching complexity | Poor recommendations reduce usefulness | Start with simple logic and iterate |
| Ambiguous tags | Lower quality matching | Use structured tag definitions |
| Time pressure | Delivery slips or incomplete features | Keep milestones explicit and adjust scope early |

---

## 7. Technical Stack

The table below reflects the **proposal-time intended stack**. Some parts changed in the actual
repository implementation.

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI (Python) |
| **Frontend** | Streamlit prototype, with possible later React migration |
| **Database** | PostgreSQL in the original proposal; SQLite + SQLModel in the current repository |
| **Vector Store** | ChromaDB planned, but not required by the current repository state |
| **AI/LLM** | DeepSeek / OpenAI API planned for matching assistance |
| **Containerization** | Docker |
| **CI/CD** | GitHub Actions |
| **Version Control** | Git + GitHub |

### Current Repository Note

As of 2026-04-15, the repository implementation is centered on:
- `src/main.py` as the active FastAPI entry point
- `src/db/database.py` for SQLite initialization
- `src/models/core.py` and `src/models/tags.py` for SQLModel-based data models
- `src/api/auth.py`, `src/api/users.py`, `src/api/circles.py`, and `src/api/tags.py` for the current API surface
