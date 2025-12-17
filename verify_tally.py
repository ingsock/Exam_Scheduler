from forms_integration import FormsManager
from scheduler import Subject


def main():
    manager = FormsManager()
    subjects = [Subject("Math"), Subject("Physics"), Subject("History")]

    print("Creating Tally Form...")
    try:
        url = manager.create_exam_form("Test Exam Schedule", subjects)
        print(f"Form Created: {url}")

        # Parse ID
        form_id = ""
        if "/r/" in url:
            form_id = url.split("/r/")[1]

        print(f"Form ID: {form_id}")

        print("\nAttempting to fetch responses (should be empty)...")
        students = manager.fetch_and_parse(form_id, None, subjects)
        print(f"Fetched {len(students)} students.")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
