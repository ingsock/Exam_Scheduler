"""
Test script to fetch Tally form responses and verify parsing
"""

import json
from tally_manager import TallyClient
from scheduler import Subject

# The form ID from the URL: https://tally.so/r/yPNML8
FORM_ID = "yPNML8"


def main():
    client = TallyClient()

    # Fetch responses using new API
    api_data = client.fetch_responses(FORM_ID)
    questions, submissions = api_data

    results = {
        "questions_count": len(questions),
        "submissions_count": len(submissions),
        "questions": [{"id": q["id"], "title": q["title"]} for q in questions],
    }

    # Parse with our subjects
    subjects = [
        Subject(n) for n in ["Math", "Physics", "Chemistry", "Biology", "History"]
    ]
    students = client.parse_responses(api_data, subjects)

    results["parsed_students_count"] = len(students)
    results["students"] = []

    for student in students:
        enrolled = list(student.subjects.keys())
        student_data = {
            "id": student.id,
            "enrolled_subjects": [s.name for s in enrolled],
            "subject_details": [],
        }
        for subj, difficulty in student.subjects.items():
            trials = student.trials.get(subj, 0)
            student_data["subject_details"].append(
                {"subject": subj.name, "difficulty": difficulty, "trials": trials}
            )
        results["students"].append(student_data)

    # Save results
    with open("parse_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("Results saved to parse_results.json")
    print(f"Parsed {len(students)} students successfully!")


if __name__ == "__main__":
    main()
