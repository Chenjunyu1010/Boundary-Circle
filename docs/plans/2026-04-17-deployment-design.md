# Deployment Design

Date: 2026-04-17

## Goal

Define the simplest practical deployment strategy for taking the current project online, with the assumption that no domain name is available yet.

## Problem

The project is currently designed for local development and includes:

- a FastAPI backend
- a Streamlit frontend
- a local SQLite database file

The goal is to deploy the full system online, not just part of it.

Constraints:

- there is no domain name yet
- deployment should be simple and fast
- the solution should work for a course project and demo scenario

## Recommended Deployment Strategy

Use one Linux cloud server and access the app through the server's public IP.

This is the recommended primary deployment path because it is the simplest full-system solution for the current project structure.

Recommended stack:

- one Linux server
- one FastAPI process
- one Streamlit process
- one local SQLite database file
- optional Nginx reverse proxy

## Why This Is The Recommended Option

For the current repository, this option is the best balance of speed, simplicity, and practical reliability.

Reasons:

- the project contains two Python services, not one
- the project still uses SQLite, which is easiest to run on one machine with local file storage
- no domain name is required for a first deployment
- the deployment can be demonstrated using a public IP address
- the operational model is easier to understand for a student project than multi-platform hosting

Compared with platform-based alternatives, a single server avoids:

- splitting frontend and backend across different providers
- dealing with SQLite persistence constraints on multi-instance platforms
- extra cross-origin and routing complexity

## Access Without A Domain

The system can be exposed through the server public IP.

Example access patterns:

- frontend: `http://<server-ip>:8501`
- backend docs: `http://<server-ip>:8000/docs`
- backend API: `http://<server-ip>:8000/...`

If Nginx is added, the URL structure can be cleaner:

- `http://<server-ip>/` -> Streamlit frontend
- `http://<server-ip>/api/...` -> FastAPI backend

Important routing note:

- the current FastAPI app serves routes at the root, for example `/docs`, `/auth/*`, `/circles/*`, and `/teams/*`
- if Nginx exposes the backend under `/api/...`, it should strip the `/api` prefix before proxying to FastAPI
- alternatively, `/api/...` should only be used if the FastAPI app is explicitly mounted with an `/api` root path
- for example, `/api/docs` should map cleanly to FastAPI's `/docs`

This is acceptable for:

- course demonstration
- internal testing
- report screenshots or walkthroughs

## HTTPS And Domain Implications

Without a domain name:

- deployment is still possible
- plain HTTP over public IP is acceptable for a demo deployment
- proper HTTPS is harder and should not be treated as a blocker for first release

Recommended sequencing:

1. deploy first with public IP
2. verify the system works end to end
3. add a domain later only if a more formal public-facing release is needed

## Recommended Runtime Layout

### Minimal version

Run both services directly:

- `uvicorn src.main:app --host 0.0.0.0 --port 8000`
- `streamlit run frontend/Home.py --server.port 8501 --server.address 0.0.0.0`

Advantages:

- fastest to bring online
- minimal setup
- enough for first deployment and testing

Trade-offs:

- ports are exposed directly
- URLs are less polished
- no unified entry point

### Slightly more complete version

Run:

- FastAPI on port `8000`
- Streamlit on port `8501`
- Nginx on port `80`

Use Nginx to route:

- `/` to Streamlit
- `/api/` to FastAPI

Advantages:

- cleaner access path
- better presentation in demos
- easier future migration to domain-based hosting

Trade-offs:

- a bit more setup work than direct port exposure

## Data Persistence

The current project uses SQLite stored under:

- `data/boundary_circle.db`

For the recommended deployment:

- keep SQLite on the same server
- ensure the deployment process preserves the `data/` directory
- avoid multi-instance horizontal scaling for now

This is acceptable because:

- the project is a course project, not a large-scale production app
- single-node persistence is sufficient for expected demo traffic

## Environment And Configuration Notes

The deployment should explicitly configure:

- `APP_ENV=production`
- `SECRET_KEY=<real secret>`
- optional auth tuning values if needed

The frontend should also know how to reach the backend, for example through:

- `API_BASE_URL`

If frontend and backend are placed behind one server entry point, the frontend configuration should match that routing plan.

## Deployment Success Criteria

The deployment is considered successful if:

- users can open the frontend from the public IP
- users can register and log in
- circles can be created and browsed
- tag submission works
- teams can be created and invitations can be handled
- matching requests work against the live backend
- SQLite data persists across service restarts

## Alternative Possibilities

The following alternatives are possible, but are not the recommended first path.

### 1. PaaS deployment

Possible platforms:

- Railway
- Render
- Fly.io

Pros:

- quicker managed deployment experience
- built-in logs and environment variable management

Cons for this project:

- frontend and backend likely need separate service handling
- SQLite persistence is less natural
- more platform-specific adjustment may be needed

Use this path if:

- the team strongly prefers managed deployment over server control

### 2. Frontend and backend split hosting

Example pattern:

- Streamlit frontend on Streamlit Community Cloud
- FastAPI backend on a separate host

Pros:

- easy frontend hosting
- clean separation of presentation and backend hosting

Cons for this project:

- more configuration complexity
- backend still must be deployed separately
- cross-origin and integration details become more visible

Use this path if:

- the team wants the easiest possible Streamlit exposure and accepts a split deployment model

### 3. Docker-first server deployment

Instead of running Python processes directly, deploy with Docker on one Linux server.

Pros:

- cleaner reproducibility
- easier future handoff
- better alignment with infrastructure documentation

Cons:

- slightly more setup than the direct process approach
- still requires server operations knowledge

Use this path if:

- the team wants a more engineering-oriented deployment story while still staying on one server

## Recommendation Summary

Primary recommendation:

- deploy the current system on one Linux server using its public IP

Preferred rollout order:

1. direct public-IP deployment
2. verify all main workflows
3. optionally add Nginx for cleaner routing
4. optionally add a domain later

This path is the simplest, fastest, and most effective way to get the current project online without introducing unnecessary architecture changes.

## Follow-up

If this direction is approved, the next planning step should define:

- exact server preparation steps
- process management choice
- optional Nginx routing
- environment variable setup
- deployment verification checklist
