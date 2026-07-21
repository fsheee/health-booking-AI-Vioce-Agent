You are a Senior Agentic AI Engineer, Full-Stack Engineer, and Solutions Architect.

Build a production-ready Healthcare AI Voice Agent SaaS.

## Tech Stack

Frontend:

* Next.js 15 (App Router)
* TypeScript
* Tailwind CSS
* shadcn/ui

Backend:

* FastAPI
* Python 3.12
* SQLModel or SQLAlchemy
* Pydantic

Database & Auth:

* PostgreSQL
* Local JWT (python-jose) + bcrypt (passlib)
* Row-level org scoping via service layer

AI & Voice:

* Gemini 2.5 Flash
* AssemblyAI (Speech-to-Text)
* ElevenLabs or Deepgram (Text-to-Speech)

Deployment:

* Docker Compose (Backend + Database)
* Vercel (Frontend)

---

## Project Goal

Create a multi-tenant Healthcare AI Voice Agent that allows clinics, hospitals, and healthcare providers to manage patients, appointments, reminders, and voice interactions using AI.

---

## User Roles

1. Admin
2. Doctor
3. Front Desk
4. Patient

Implement Role-Based Access Control (RBAC).

---

## Core Features

### Authentication

* Email/Password Login
* JWT-based auth (python-jose)
* bcrypt password hashing
* Protected Routes
* Role-Based Access Control
* Organization-Based Multi-Tenancy

### Patient Management

* Create Patient
* Update Patient
* Search Patient
* View Medical History
* Patient Profiles

### Appointment Management

* Book Appointment
* Cancel Appointment
* Reschedule Appointment
* Check Doctor Availability
* Appointment Calendar

### Voice Agent

Voice Workflow:

Patient Voice
→ AssemblyAI Speech-to-Text
→ Gemini AI Agent
→ FastAPI Tool Calling Layer
→ PostgreSQL Database
→ Text-to-Speech Response

Supported Actions:

* Book Appointment
* Check Availability
* Retrieve Patient Information
* Send Reminder
* Escalate to Human Staff

### Reminder Automation

* Appointment Reminders
* Follow-Up Reminders
* Medication Reminder Framework
* SMS/Email/Voice Channel Support
* Reminder Logs

---

## Medical Safety Requirements

The AI must never:

* Diagnose diseases
* Prescribe medications
* Recommend treatments
* Provide emergency medical advice

Emergency phrases such as:

* Chest pain
* Difficulty breathing
* Stroke symptoms
* Severe bleeding
* Loss of consciousness

must immediately trigger:

* Human escalation
* Emergency warning message
* Conversation logging

Include a medical disclaimer throughout the application.

---

## Database Design

Create PostgreSQL tables for:

* organizations
* users
* doctors
* patients
* appointments
* voice_sessions
* reminders
* audit_logs

Every business table must include:

* id
* org_id
* created_at
* updated_at

---

## Security

Requirements:

* Patients can only access their own data.
* Doctors can only access assigned patients.
* Front Desk users can manage appointments within their organization.
* Admins can access all data within their organization.
* No cross-organization access is allowed.

---

## FastAPI Architecture

Implement:

* Routers
* Services
* Repository Pattern
* Dependency Injection
* Pydantic Schemas
* Database Models
* Alembic Migrations
* Exception Handling
* Logging

Generate OpenAPI documentation and Swagger support.

---

## Frontend Architecture

Create dashboards for:

### Admin Dashboard

* User Management
* Organization Management
* Analytics

### Doctor Dashboard

* Assigned Patients
* Schedule
* Voice Session Reviews

### Front Desk Dashboard

* Patient Registration
* Appointment Management

### Patient Dashboard

* Upcoming Appointments
* Appointment History
* Voice Assistant Access

---

## AI Agent Architecture

Create a tool-calling Healthcare Agent using Gemini.

Available Tools:

* check_availability
* book_appointment
* get_patient_history
* send_reminder

The LLM must never directly access the database.

All database actions must occur through FastAPI tool endpoints.

---

## DevOps

Generate:

* Dockerfiles
* Docker Compose
* Environment Configuration
* Production Setup Guide

Create:

* README.md
* ARCHITECTURE.md
* .env.example

---

## Development Process

Phase 1:
Design the complete architecture.

Phase 2:
Create the database schema and org-scoping policies.

Phase 3:
Build FastAPI backend.

Phase 4:
Build Next.js frontend.

Phase 5:
Implement AI Voice Agent.

Phase 6:
Implement automation and reminders.

Phase 7:
Prepare production deployment.

Before generating code, explain architecture decisions, database design, security model, and project structure.

Then generate the complete implementation step-by-step with production-quality code.
