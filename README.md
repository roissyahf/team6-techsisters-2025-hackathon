# Compassly: A Career Navigation Tool for Women in Tech

## Background

We aim to make it easier for women to navigate their tech career paths. With so many options and resources available, it's easy for someone interested in tech to feel overwhelmed. Compassly provides **clear, confident guidance** to help users define their path and execute a plan to achieve their career goals.

---

## App Workflow: Personalized Guidance Through Scenarios

Compassly is designed to serve users regardless of their current experience level by using two distinct career navigation scenarios.

### 1. Initial Assessment & Scenario Selection

1.  **Base Questions:** Users start by answering 10 base questions (education, work experience).
2.  **Scenario Determination:** The system identifies the user's background:
    * **Scenario 1 (Non-Technical):** For those new to tech and looking to break in.
    * **Scenario 2 (Technical):** For those already in tech looking for a career change or advancement.

### 2. Tailored Assessment & Recommendation

| Scenario | Background | Dynamic Assessment | Recommendation | Current Status |
| :--- | :--- | :--- | :--- | :--- |
| **1** | Non-Technical | 6 dynamic questions with **no technical jargon** (aptitude focus). | Top 3 tech role recommendations. | **Implemented** |
| **2** | Technical | 5 technical questions with **technical jargon** (skill/competency focus). | Top 3 tech role recommendations. | Hybrid model & API **Ready**, pending integration. |

### 3. Actionable Insights (Current Implemented Features)

After a user selects one of the recommended roles, Compassly provides actionable steps:

* **Detailed Role Insights:** The backend retrieves comprehensive data on the chosen role, including: role description, required skills, career opportunities (salary, growth paths), and competency expectations.
* **Course Recommendation:** Users receive tailored course suggestions to immediately begin upskilling for their chosen path.

---

## Key Features & Components

Compassly is built around core modules that deliver personalized guidance:

* **Assessment Module:** Captures essential user data, including background, experience, and personality traits, to fuel the recommendation engine.
* **Personalized Role Matcher:** Generates the core career recommendations based on the hybrid filtering model.
* **Resource Library:** Provides curated and context-specific upskilling resources (courses, projects, certifications).
* **User Authentication & Profile:** Allows users to **save their progress**, review past assessments, and maintain a **personalized action plan**.

---

## Technical Stack & Data Model

Compassly uses a modern, stable, and scalable stack.

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Frontend** | **HTML, CSS, JavaScript** | Simple, fast, and accessible user interface. |
| **Backend** | **Flask (Python)** | Lightweight and flexible server framework managing application logic and API endpoints. |
| **Database** | **PostgreSQL** | Robust relational database for storing user profiles, assessments, and the core career resource data. |
| **Recommendation Engine** | **Hybrid Model** | Combines **Weighted Scoring** and **Content-Based Filtering (TF-IDF)** for robust, context-aware matching. |
| **Dynamic Question API** | **OpenAI LLM** | Used to power the dynamic questions for both scenarios, ensuring relevant and current queries. |

---

## Getting Started (For Developers)

This section provides the basic steps required to set up and run Compassly locally.

### Prerequisites

* Python (3.10+)
* PostgreSQL
* A valid **OpenAI API Key** (for dynamic question generation)

### Installation and Setup

The definitive local setup instructions, including required environment variables, dependency lists (`requirements.txt`), and detailed data loading steps, are maintained within our dedicated feature branch.

**To obtain the full development configuration and instructions for running Compassly locally, please switch to the following branch:**

```bash
git checkout career-compass-app
```

---

## Future Enhancements (Roadmap)

The following features are developed or planned for integration to complete the Compassly experience:

| Feature | Description | Status |
| :--- | :--- | :--- |
| **Scenario 2 Integration** | Integrate the pre-built dynamic questions API and the hybrid model logic into the backend and frontend to fully support users with a technical background. | **High Priority** (APIs & Model Ready) |
| **Job Vacancy Motivator** | Display the latest sample of **3 job vacancies** relevant to the user's chosen role to boost motivation and provide market context. | Planned |
| **Personalized Action Plan** | Implement the full generation logic for the **targeted action plan**, providing a structured, step-by-step roadmap for users. | Planned |

---

## Meet the Team

We are a passionate team dedicated to empowering women in technology through clear, data-driven career guidance.

| Name | Role |
| :--- | :--- |
| **Fouzia Khan** | Project Manager & Full Stack Engineer |
| **Nimatallahi Masuud** | Data Scientist |
| **Roissyah Fernanda** | Machine Learning Engineer |
| **Mariam** | UI/UX Designer |