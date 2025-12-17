# Exam Scheduler

A powerful, intelligent exam scheduling system that minimizes student stress using advanced optimization algorithms.

## 📌 Overview

This project automatically schedules exams into available time slots while minimizing a specific penalty function defined by student stress factors:
$$ \text{Penalty} = 2^t \cdot d^2 \cdot e^{-a \cdot g} $$
Where:
*   $t$: Number of previous attempts (trials).
*   $d$: Subject difficulty (1-10).
*   $g$: Gap (days) between exams.
*   $a$: Decay parameter.

It employs **Simulated Annealing** and **Genetic Algorithms** to find the optimal schedule and provides a modern **Admin UI** for easy management.

## ✨ Features

*   **Intelligent Scheduling**: Automatically resolves conflicts and optimizes exam spacing.
*   **Dual Solvers**: Compares Simulated Annealing and Genetic Algorithm results to pick the best schedule.
*   **Google Forms Integration**:
    *   One-click form generation for student preferences.
    *   Automatic response polling and parsing.
    *   Whitelist support for student emails.
*   **Admin Dashboard**:
    *   Interactive calendar for setting exam dates and holidays.
    *   Visual schedule result viewing.
    *   Real-time start date configuration.
*   **Export**: Generate professional Word (`.docx`) schedules with actual dates.

## 🛠️ Tech Stack

*   **Backend**: Python, Flask
*   **Optimization**: Custom Simulated Annealing & Genetic Algorithm implementations
*   **Frontend**: HTML5, Vanilla CSS (Glassmorphism design), JavaScript
*   **Integrations**: Google Forms API, `python-docx`

## 🚀 Getting Started

### Prerequisites

*   Python 3.8+
*   A Google Cloud Project with the Forms API enabled (for Forms integration).
*   `credentials.json` placed in the root directory (OAuth Client ID).

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/yourusername/exam-scheduler.git
    cd exam-scheduler
    ```

2.  Install dependencies:
    ```bash
    pip install flask python-docx google-api-python-client google-auth-oauthlib google-auth-httplib2
    ```

## 📖 Usage

### Option 1: Admin UI (Recommended)

The easiest way to use the scheduler is via the web dashboard.

1.  Start the application:
    ```bash
    python app.py
    ```
2.  Open your browser to `http://localhost:5000`.
3.  **Configure**: Set the number of days, start date, and mark holidays on the calendar.
4.  **Data Collection**: Use the "Create New Form" button to generate a Google Form for your students.
5.  **Schedule**: Once responses are in, click "Run Scheduler".
6.  **Export**: Download the final schedule as a Word document.

### Option 2: Command Line Interface (CLI)

You can also run the scheduler directly from the terminal.

*   **Run a simulation** (Default test case):
    ```bash
    python main.py --days 20 --holidays 5 10
    ```

*   **Create a Form**:
    ```bash
    python main.py --create-form "Spring 2025 Exams" --subjects Math Physics Chemistry
    ```

*   **Poll Responses & Schedule**:
    ```bash
    python main.py --poll-form <FORM_ID> --emails whitelist.txt --days 20
    ```

## 📂 Project Structure

*   `app.py`: Flask backend entry point.
*   `main.py`: CLI entry point.
*   `scheduler.py`: Core logic for `Student`, `Subject` and Penalty validation.
*   `solvers.py`: Implementation of SA and GA algorithms.
*   `forms_integration.py`: Logic for Google Forms API interaction.
*   `export.py`: Handles `.docx` file generation.
*   `templates/`, `static/`: Frontend assets.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
