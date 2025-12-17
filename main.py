import argparse
import time
from test_solvers import generate_test_case
from solvers import simulated_annealing, genetic_algorithm
from scheduler import calculate_penalty, Subject


def load_emails(file_path):
    with open(file_path, "r") as f:
        return set(line.strip() for line in f if line.strip())


def main():
    parser = argparse.ArgumentParser(description="Exam Scheduler CLI")
    parser.add_argument(
        "--days", type=int, default=20, help="Number of available slots"
    )
    parser.add_argument(
        "--holidays",
        type=int,
        nargs="*",
        default=[],
        help="List of day indices to be holidays",
    )

    # Forms Integration Arguments
    parser.add_argument(
        "--create-form", type=str, help="Create a form with the given title and exit"
    )
    parser.add_argument(
        "--poll-form", type=str, help="Poll responses from the given Form ID"
    )
    parser.add_argument(
        "--emails", type=str, help="Path to file containing allowed emails"
    )
    parser.add_argument(
        "--subjects",
        type=str,
        nargs="*",
        default=["Math", "Physics", "Chemistry", "Biology", "History"],
        help="List of subjects (for form creation)",
    )

    args = parser.parse_args()

    num_days = args.days
    holidays = set(args.holidays)

    # Check for Forms Logic
    if args.create_form:
        try:
            from forms_integration import FormsManager

            manager = FormsManager()
            subjects = [Subject(name) for name in args.subjects]
            url = manager.create_exam_form(args.create_form, subjects)
            print(f"Form created successfully: {url}")
            return
        except Exception as e:
            print(f"Error creating form: {e}")
            return

    if args.poll_form:
        try:
            from forms_integration import FormsManager

            manager = FormsManager()

            allowed_emails = None
            if args.emails:
                allowed_emails = load_emails(args.emails)
                print(f"Loaded {len(allowed_emails)} allowed emails.")

            # Need subjects list to parse responses against
            # In a real app, we'd persist the subjects with the form ID,
            # but here we'll assume the user passes the same subjects or we assume standard ones.
            # Let's use the provided subject list or default.
            subjects = [Subject(name) for name in args.subjects]

            print(f"Polling responses for Form ID: {args.poll_form}...")
            students = manager.fetch_and_parse(args.poll_form, allowed_emails, subjects)

            if not students:
                print("No valid responses found.")
                return

            print(f"Parsed {len(students)} students from responses.")

        except ImportError:
            print(
                "Error: Forms integration requires google-api-python-client. Please install it."
            )
            return
        except Exception as e:
            print(f"Error polling form: {e}")
            return
    else:
        # Default Test Case
        print("Generating Test Case...")
        subjects, students = generate_test_case()
        print(f"Generated {len(subjects)} subjects and {len(students)} students.")

    print("\n--- Running Simulated Annealing ---")
    start_time = time.time()
    sa_schedule = simulated_annealing(subjects, students, num_days, holidays)
    sa_time = time.time() - start_time
    sa_penalty = calculate_penalty(sa_schedule, students)
    print(f"SA Finished in {sa_time:.4f}s. Penalty: {sa_penalty:.4f}")
    if sa_penalty >= 1_000_000_000:
        print("  WARNING: Constraint Violated (Schedule Invalid)")
    else:
        print("  Status: Valid")

    print("\n--- Running Genetic Algorithm ---")
    start_time = time.time()
    ga_schedule = genetic_algorithm(subjects, students, num_days, holidays)
    ga_time = time.time() - start_time
    ga_penalty = calculate_penalty(ga_schedule, students)
    print(f"GA Finished in {ga_time:.4f}s. Penalty: {ga_penalty:.4f}")
    if ga_penalty >= 1_000_000_000:
        print("  WARNING: Constraint Violated (Schedule Invalid)")
    else:
        print("  Status: Valid")

    print("\n--- Comparison ---")
    if sa_penalty < ga_penalty:
        print("Simulated Annealing performed better.")
        best_schedule = sa_schedule
        best_solver = "Simulated Annealing"
    else:
        print("Genetic Algorithm performed better.")
        best_schedule = ga_schedule
        best_solver = "Genetic Algorithm"

    print(f"\nBest Schedule ({best_solver}):")
    # Print schedule sorted by day
    schedule_list = []
    for subj, day in best_schedule.assignments.items():
        schedule_list.append((day, subj.name))

    schedule_list.sort()

    current_day = -1
    for day, subj_name in schedule_list:
        if day != current_day:
            print(f"\nDay {day}:")
            current_day = day
        print(f"  - {subj_name}")


if __name__ == "__main__":
    main()
