# Boundary Circle - Project Proposal

**Team ID**: EX2-Team-12  
**Date**: February 10, 2026

---

## 1. Project Overview

### Project Purpose (Product Description)

This project aims to design and develop a mobile social application named **"Boundary Circle"**. This system is a team formation and recruitment tool, with its core function being to help users efficiently match partners within specific interest or community "circles".

The application introduces a **tag-based user profile mechanism**, allowing users to be represented by a series of descriptive tags within the circles, thereby achieving precise and transparent member screening and team formation.

**Initial target users**: College students  
**Future expansion**: Enterprise departments, student clubs, and other closed or semi-closed communities

The system is dedicated to solving the problems of:
- Information dispersion
- Difficulty in verifying identities
- Low efficiency in team formation and collaboration within campuses and organizations

Providing a vertical social platform that combines **trust and flexibility**.

### Motivation and Goals (Business Requirements)

#### Motivation

In reality, when college students are looking for course partners or forming activity teams, their information is often scattered across multiple anonymous chat groups or real-name platforms, resulting in low efficiency and difficulty in verifying identities.

- In a completely **real-name** campus network, students are reluctant to share their life troubles or discuss sensitive topics
- In a completely **anonymous** platform, the lack of community boundaries can lead to information chaos or inappropriate content

Therefore, we have the opportunity to create a vertical social product with a boundary defined by **"authentication + tags"**.

#### Stakeholders

| Stakeholder | Description |
|-------------|-------------|
| **End Users (Students)** | Primary beneficiaries. Two roles: **Recruiters (Team Leaders)** need efficient filtering tools; **Applicants (Team Seekers)** seek to join projects while maintaining privacy |
| **Circle Creators (Community Admins)** | Establish interest-based communities and define "Tag Schemas" (identity rules) for membership |
| **Competitors (Existing Solutions)** | WeChat groups, Discord servers, shared spreadsheets - lack structured matching capabilities |
| **Course Instructors (Client)** | Project sponsors and primary evaluators |
| **University Administration (Regulator)** | Enforces data privacy and ethical standards |
| **Development and Operations Team** | Technical stakeholders responsible for architecture, implementation, deployment, and maintenance |

#### Goals

- Gain deep understanding of the balance between technical implementation, community operation and privacy security in social product design
- Improve communication efficiency in specific scenarios
- Establish basic trust through a labeled semi-verified mechanism
- Provide a secure and free anonymous expression environment
- Promote personalized emotional sharing and mutual assistance among users
- Cultivate a healthy digital community culture

---

## 2. Requirements Engineering

### User Requirements

- **UR-1: Contextual Identity and Isolation** - Users need to join distinct "Circles" (e.g., Course A, Hackathon B) to separate their social contexts. Identity in each Circle is defined solely by Circle-specific "Tags", ensuring global profile remains private.

- **UR-2: Gated Access via Mandatory Tags** - Circle creators require that new members must complete a mandatory "Tag Profile" (e.g., GPA, Tech Stack) **before** gaining access to view internal posts or member lists.

- **UR-3: Goal-Oriented Team Formation** - Users enter Circles with the specific goal of forming a "Team". The system should recommend teammates based on Tag compatibility and provide tools to formalize the team structure (invite, accept, lock).

### Functional Requirements

- **FR-1: Circle Schema Definition** - Interface for Circle Creators to define a "Tag Schema" (mandatory and optional data fields) that enforces the identity standard for that specific context.

- **FR-2: Gated Entry Workflow** - Upon joining a Circle, present the mandatory Tag form. Grant access to Circle content (posts/members) **only after** successful submission of valid Tag data.

- **FR-3: Context-Aware Matching Algorithm** - Implement a matching algorithm that ranks users and teams within a Circle based on similarity score between user's Circle-specific Tags and Team's requirements.

- **FR-4: Team Entity Lifecycle** - Allow users with "Active" status to instantiate a "Team" entity. Manage state transitions: from "Recruiting" (open) to "Locked" (full and finalized).

- **FR-5: Data Visibility Control** - Restrict data visibility such that a user's Tags and Posts within a specific Circle are strictly invisible to non-members of that Circle.

### Non-Functional Requirements

- **NFR-1: Strict Context Isolation (Privacy)** - No data linkage exists between a user's profiles in different Circles on the frontend interface, ensuring complete identity isolation across contexts.

- **NFR-2: Real-time Matching Performance (Efficiency)** - Recalculate and update the "Recommended Teammates" list within **3 seconds** after a user joins a Circle and completes their Tags.

- **NFR-3: Scalability of Tag Types (Maintainability)** - Support at least **5 distinct customizable Tag data types** (Integers, Booleans, Strings, Enumerated Lists) to accommodate diverse Circle themes.

---

## 3. Use Case: AI-Driven Teammate Matching

### Scenario: Technical Contest Team Formation

**Preconditions**:
- Captain Alice has created a circle for the "AI Competition Circle"
- Candidate Bob has entered the circle and filled out profile with "Good at LLM" tag
- AI matching engine is indexed and "Context-Aware View" module is active

**Normal Flow**:
1. Alice posts recruitment: "We need four members familiar with Large Language Model fine-tuning"
2. Backend extracts keywords [LLM, Fine-tuning] and identifies context as "Technical/AI"
3. System queries database for this circle, matches against Bob's profile
4. System generates matching list - Alice views Bob's profile (95% match, ranked #1), clicks "Send Join Invitation"
5. Bob receives real-time notification, reviews Alice's team goals, clicks "Accept"

**Exception Flows**:
- **Insufficient Match Confidence**: If no candidate scores >60%, system suggests broadening search
- **Privacy Violation Blocking**: Direct URL access without mutual match returns "403 Forbidden"

**End State**: Mutual match established; Bob's WeChat ID revealed to Alice; team recruitment status updated to "Completed"

---

## 4. Feasibility Study

| Aspect | Assessment |
|--------|------------|
| **Skills** | Team has strong Python foundation. Functional skeleton with **FastAPI** (Backend) and **Streamlit** (Frontend). **Docker** containerization and **GitHub Actions** CI pipeline implemented. Will use pre-trained LLM APIs (DeepSeek/OpenAI) for NLP. |
| **Data** | User profiles and team requirements. Initial phase: 200+ **synthetic student profiles** generated by LLM. Final phase: anonymized peer cohort data. Privacy ensured through "Context-Aware Data Masking". |
| **Time** | 10 weeks remaining. **Agile Incremental Model**. MVP (core matching + profile management) by Week 7. 3-week buffer for testing and unexpected changes. |
| **Computing Resources** | No specialized GPUs required. Standard laptops for development. External LLM APIs for AI computation. GitHub Actions for CI. **ChromaDB** for vector storage (low-resource). |
| **Budget** | **Zero-Cost**. GitHub free-tier, open-source stack (FastAPI, Streamlit, PostgreSQL). Free LLM API credits for students. |

---

## 5. System Architecture

### Architecture Overview

The system adopts a modular, layered architecture:

```
┌─────────────────────────────────────────┐
│         User Interface (UI) Layer       │
│  (Web/Mobile - Streamlit → React?)      │
├─────────────────────────────────────────┤
│      Application Service Layer          │
│  (Business Logic, Tag Management)       │
├─────────────────────────────────────────┤
│    Matching & Recommendation Module     │
│  (Tag Similarity, LLM-based Ranking)    │
├─────────────────────────────────────────┤
│  Authentication & Circle Management     │
│  (User Accounts, Access Control)        │
├─────────────────────────────────────────┤
│         Data Storage Layer              │
│  (PostgreSQL + ChromaDB)                │
└─────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| **UI Layer** | Core functionalities: recruitment posts, circle joining, tag management, matched users/teams |
| **Application Service Layer** | Business logic: posting, tag assignment, visibility rules enforcement |
| **Matching Module** | Tag analysis, circle context, recruitment requirements filtering and ranking |
| **Auth & Circle Management** | User accounts, membership, access control |
| **Data Storage Layer** | Persistent data: profiles, circles, tags, posts, matching records |

---

## 6. Project Plan

### Timeline (10 Weeks)

| Week | Milestone | Deliverable |
|------|-----------|-------------|
| 5-6 | Requirements refinement & system design | Finalized requirements + architecture diagram |
| 7-8 | Core backend development | User, circle, tag, recruitment post management |
| 9-10 | Matching module implementation | Tag-based matching and filtering |
| 11 | Frontend integration | Integrated UI + backend services |
| 12 | System testing and refinement | Tested prototype + bug fixes |
| 13-14 | Final demo and documentation | System demonstration + final report |

### Risk Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Tag-based matching complexity** | Inefficient/inaccurate matching reduces system usefulness | Start with simple rule-based algorithms, incrementally refine |
| **Ambiguity in user-defined tags** | Poorly defined tags decrease matching accuracy | Provide predefined tag categories and suggestions |
| **Time constraints & workload imbalance** | Development delays or incomplete features | Clear milestones, regular progress reviews, adjust scope if needed |

---

## 7. Technical Stack

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI (Python) |
| **Frontend** | Streamlit (prototype) → React? |
| **Database** | PostgreSQL |
| **Vector Store** | ChromaDB |
| **AI/LLM** | DeepSeek / OpenAI API |
| **Containerization** | Docker |
| **CI/CD** | GitHub Actions |
| **Version Control** | Git + GitHub |
