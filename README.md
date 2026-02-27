# Boundary Circle

> **Find your perfect teammates within the right circles.**

[![CI Pipeline](https://github.com/your-team/repo/actions/workflows/ci.yml/badge.svg)](https://github.com/your-team/repo/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

---

## 📖 Introduction

**Boundary Circle** is a smart team formation and social networking platform designed for college students and professional communities. 

Unlike traditional social platforms that force you to choose between complete anonymity or full real-name exposure, Boundary Circle introduces a revolutionary **"Circle + Tag"** system:

- 🎯 **Join interest-based Circles** - Course projects, hackathons, sports clubs, research groups
- 🏷️ **Build contextual identity with Tags** - Different circles see different aspects of you
- 🤝 **AI-powered teammate matching** - Find partners who truly complement your skills
- 🔒 **Privacy by design** - Your data stays within each circle's boundary

### The Problem We Solve

When students look for course partners or activity teammates:
- ❌ Information is scattered across multiple WeChat groups and platforms
- ❌ Real-name networks make people reluctant to share struggles or sensitive topics
- ❌ Anonymous platforms lack community boundaries and accountability
- ❌ No efficient way to verify identities and skills

### Our Solution

A vertical social product with boundaries defined by **"Authentication + Tags"**:
- ✅ **Semi-verified identity** - University email verification without exposing real names
- ✅ **Contextual profiles** - You're defined by relevant tags in each circle
- ✅ **Smart matching** - AI algorithms recommend compatible teammates
- ✅ **Privacy isolation** - Complete data separation between circles

---

## ✨ Key Features

### 🎪 Circles
Create or join interest-based communities with custom identity schemas:
- **Course Circles** - Find teammates for specific classes
- **Event Circles** - Hackathons, competitions, sports events
- **Interest Circles** - AI research, music, gaming, entrepreneurship
- **Organization Circles** - Student clubs, lab groups, departments

### 🏷️ Tag-Based Profiles
Build your identity within each circle:
- **Mandatory Tags** - GPA, tech stack, availability (defined by circle creator)
- **Optional Tags** - Interests, previous experience, personality traits
- **Flexible Schema** - 5+ data types: integers, booleans, strings, enums

### 🤝 Team Formation
- **Post Recruitment** - Share your team needs with specific requirements
- **Smart Matching** - AI ranks candidates by compatibility score
- **Invite System** - Send and accept join invitations
- **Team Lifecycle** - From "Recruiting" to "Locked" status

### 🔐 Privacy & Security
- **Context Isolation** - No data linkage between different circles
- **Gated Access** - Must complete tag profile before viewing circle content
- **Access Control** - 403 protection against unauthorized data access
- **University Compliance** - Meets institutional data privacy standards

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI (Python 3.9+) |
| **Frontend** | Streamlit (Prototype) |
| **Database** | PostgreSQL |
| **Vector Store** | ChromaDB |
| **AI/LLM** | DeepSeek / OpenAI API |
| **Containerization** | Docker |
| **CI/CD** | GitHub Actions |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         Frontend (Streamlit)            │
│     Circle Browse | Tags | Teams        │
├─────────────────────────────────────────┤
│           FastAPI Backend               │
│  /auth | /circles | /tags | /matching   │
├─────────────────────────────────────────┤
│         Matching Engine                 │
│   Tag Similarity | LLM Ranking          │
├─────────────────────────────────────────┤
│         Data Layer                      │
│   PostgreSQL (Relational)               │
│   ChromaDB (Vector Embeddings)          │
└─────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Docker (optional, for containerized deployment)
- PostgreSQL (for local development)

### Local Development

```bash
# 1. Clone the repository
git clone https://github.com/your-team/course-project-ex2-team-12.git
cd course-project-ex2-team-12

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the backend server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 4. Run the frontend demo
streamlit run frontend_demo.py
```

### Docker Deployment

```bash
# Build the Docker image
docker build -t boundary-circle .

# Run the container
docker run -p 8000:8000 boundary-circle
```

### API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

## 📦 Core API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Welcome message and system status |
| `GET` | `/health` | Health check endpoint |
| `POST` | `/auth/register` | User registration |
| `POST` | `/auth/login` | User authentication |
| `GET` | `/circles` | List all circles |
| `POST` | `/circles` | Create a new circle |
| `POST` | `/circles/{id}/join` | Join a circle with tags |
| `GET` | `/matching/recommendations` | Get teammate recommendations |
| `POST` | `/teams` | Create a team |
| `POST` | `/teams/{id}/invite` | Send team invitation |

---

## 👥 Team

**EX2-Team-12** - BSAI301 Software Engineering Project

| Member | Student ID | Role |
|--------|------------|------|
| Chen-JunYu | 1230024606 | Backend & AI |
| Liu-YiBin | 1230018725 | Frontend & UX |
| Nie-HaoYu | 1230023251 | Database & DevOps |
| Guo-HaoXuan | 1230036051 | Testing & Documentation |

---

## 📅 Project Timeline

| Phase | Weeks | Focus |
|-------|-------|-------|
| **Design** | 5-6 | Requirements, Architecture |
| **Backend** | 7-8 | Core APIs, Database |
| **AI** | 9-10 | Matching Algorithm |
| **Integration** | 11 | Frontend + Backend |
| **Testing** | 12 | QA, Bug Fixes |
| **Demo** | 13-14 | Final Presentation |

---

## 📄 Documentation

- [Project Proposal](docs/proposal.md) - Detailed requirements and architecture
- [Course Requirements](docs/course-requirements.md) - Assignment guidelines
- [API Documentation](http://localhost:8000/docs) - Interactive API docs

---

## 📝 License

This project is developed for educational purposes as part of BSAI301 Software Engineering course.
