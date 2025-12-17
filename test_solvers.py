import random
from typing import List, Tuple
from scheduler import Student, Subject


def generate_test_case() -> Tuple[List[Subject], List[Student]]:
    # 2 Sets of classes
    # Set A: 5 classes
    subjects_a = [Subject(f"SetA_Subj{i}") for i in range(1, 6)]
    # Set B: 7 classes
    subjects_b = [Subject(f"SetB_Subj{i}") for i in range(1, 8)]

    all_subjects = subjects_a + subjects_b

    # Define mean difficulties for each subject
    # Random mean between 3 and 8 to allow spread
    subject_means = {s: random.uniform(3, 8) for s in all_subjects}

    students = []

    # 10 Students share Set A
    for i in range(10):
        student = Student(id=i)
        for subj in subjects_a:
            # Difficulty: mean + std deviation (let's say std=1.5)
            diff = int(random.gauss(subject_means[subj], 1.5))
            diff = max(1, min(10, diff))
            # Trials: let's randomize (0-3)
            trials = random.randint(0, 3)
            student.add_subject(subj, diff, trials)
        students.append(student)

    # 10 Students share Set B
    for i in range(10, 20):
        student = Student(id=i)
        for subj in subjects_b:
            diff = int(random.gauss(subject_means[subj], 1.5))
            diff = max(1, min(10, diff))
            trials = random.randint(0, 3)
            student.add_subject(subj, diff, trials)
        students.append(student)

    # 5 Students mixed 5-7 classes from A U B
    for i in range(20, 25):
        student = Student(id=i)
        num_classes = random.randint(5, 7)
        student_subjects = random.sample(all_subjects, num_classes)
        for subj in student_subjects:
            diff = int(random.gauss(subject_means[subj], 1.5))
            diff = max(1, min(10, diff))
            trials = random.randint(0, 3)
            student.add_subject(subj, diff, trials)
        students.append(student)

    return all_subjects, students
