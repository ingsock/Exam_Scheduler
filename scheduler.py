from dataclasses import dataclass, field
from typing import List, Dict, Optional
import math


@dataclass(frozen=True)
class Subject:
    name: str


@dataclass
class Student:
    id: int
    subjects: Dict[Subject, int] = field(
        default_factory=dict
    )  # Subject -> Difficulty (1-10)
    trials: Dict[Subject, int] = field(
        default_factory=dict
    )  # Subject -> Previous Trials

    def add_subject(self, subject: Subject, difficulty: int, previous_trials: int = 0):
        self.subjects[subject] = difficulty
        self.trials[subject] = previous_trials


@dataclass
class Schedule:
    assignments: Dict[Subject, int]  # Subject -> Day Index
    num_days: int

    def get_day(self, subject: Subject) -> Optional[int]:
        return self.assignments.get(subject)


def calculate_penalty(
    schedule: Schedule, students: List[Student], initial_gap: int = 3, a: float = 1.0
) -> float:
    """
    Calculates the total penalty for a schedule given a list of students.
    Penalty = sum(2^t * d^2 * e^(-a * g))
    Constraint: Returns large penalty if any student has >1 exam on the same day.
    """
    total_penalty = 0.0

    for student in students:
        # Get days for this student's exams
        student_exams = []
        for subject, difficulty in student.subjects.items():
            day = schedule.get_day(subject)
            if day is not None:
                student_exams.append((day, difficulty, student.trials.get(subject, 0)))

        # Sort exams by day
        student_exams.sort(key=lambda x: x[0])

        # Check for overlaps (Hard Constraint converted to Soft Constraint)
        conflicts = 0
        for i in range(len(student_exams) - 1):
            if student_exams[i][0] == student_exams[i + 1][0]:
                conflicts += 1

        if conflicts > 0:
            total_penalty += conflicts * 1_000_000_000  # 1 Billion penalty per conflict

        # Calculate penalty for each exam
        last_day = -initial_gap - 1  # See logic below
        # If the first exam is on day 0, and we want 'initial_gap' empty days before it (e.g. 3)
        # Effectively the previous exam was at -4 (if gap is 3).
        # Gap = current_day - last_day - 1
        # Example: Exam at day 0. Gap should be 3.
        # 0 - last_day - 1 = 3 => last_day = -4.
        # General: last_day = -initial_gap - 1

        # Actually logic says: "if there are 2 empty days before an exam ... then the loss is..."
        # This implies gap is the number of empty days.
        # If exam is at day D, and prev exam at day P. Empty days = D - P - 1.

        last_day = -(initial_gap + 1)  # This sets the "virtual" previous exam day.

        for day, difficulty, trials in student_exams:
            gap = day - last_day - 1
            if gap < 0:
                # Should not happen if sorted and no overlaps, but safe guard
                gap = 0

            # Penalty formula: 2^t * d^2 * e^(-a * g)
            term = (2**trials) * (difficulty**2) * math.exp(-a * gap)
            total_penalty += term

            last_day = day

    return total_penalty
