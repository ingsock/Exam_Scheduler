import requests
import uuid
from typing import List, Dict

from scheduler import Student, Subject

TALLY_API_URL = "https://api.tally.so"
API_KEY = "tly-HqxfxI2lFAIFwrQbLEjbPlJfWccisAXG"  # Provided by user


class TallyClient:
    def __init__(self, api_key: str = API_KEY):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self.workspace_id = None

    def get_me(self):
        """Fetches current user/workspace info."""
        response = requests.get(f"{TALLY_API_URL}/users/me", headers=self.headers)
        return response.json()

    def get_workspaces(self):
        """Fetches available workspaces."""
        response = requests.get(f"{TALLY_API_URL}/workspaces", headers=self.headers)
        return response.json()

    def _ensure_workspace_id(self):
        if self.workspace_id:
            return

        try:
            # The correct workspace ID comes from the /workspaces endpoint
            # NOT from organizationId in /users/me
            workspaces = self.get_workspaces()
            items = workspaces.get("items", [])
            if items:
                self.workspace_id = items[0]["id"]
                print(f"Using workspace ID: {self.workspace_id}")
            else:
                print("Warning: No workspaces found in the account")
        except Exception as e:
            print(f"Warning: Could not fetch workspace ID: {e}")

    def create_exam_schedule_form(self, title: str, subjects: List[Subject]) -> str:
        """
        Creates a new Tally form for exam scheduling with two pages:

        Page 1:
        - Email address
        - Checkboxes for subjects the student is taking
        - Checkboxes for subjects they have previously failed

        Page 2:
        - Difficulty rating (1-10) for each subject

        Note: Tally API doesn't support conditional logic via API, so we show all
        difficulty fields but filter responses based on selected subjects on backend.
        """
        self._ensure_workspace_id()

        blocks = []

        def make_title_block(
            label_text: str, group_uuid: str, is_required: bool = True
        ) -> dict:
            """Creates a TITLE block for question labels."""
            return {
                "uuid": str(uuid.uuid4()),
                "groupUuid": group_uuid,
                "groupType": "QUESTION",
                "type": "TITLE",
                "payload": {
                    "html": f"<p>{label_text}</p>",
                    "isRequired": is_required,
                },
            }

        def make_checkbox_group(
            label_text: str, options: List[str], is_required: bool = True
        ) -> list:
            """
            Creates a checkbox question with multiple options.
            Structure: TITLE block + multiple CHECKBOX_OPTION blocks sharing same groupUuid.
            """
            group_uuid = str(uuid.uuid4())
            blocks_list = []

            # TITLE block
            blocks_list.append(make_title_block(label_text, group_uuid, is_required))

            # CHECKBOX blocks for each option
            for idx, option in enumerate(options):
                blocks_list.append(
                    {
                        "uuid": str(uuid.uuid4()),
                        "groupUuid": group_uuid,
                        "groupType": "CHECKBOX",
                        "type": "CHECKBOX",
                        "payload": {
                            "text": option,
                            "html": f"<p>{option}</p>",
                            "index": idx,
                        },
                    }
                )

            return blocks_list

        def make_input_question(
            label_text: str,
            input_type: str,
            input_payload: dict,
            is_required: bool = True,
        ) -> list:
            """Creates a question with TITLE block + input block."""
            group_uuid = str(uuid.uuid4())
            return [
                make_title_block(label_text, group_uuid, is_required),
                {
                    "uuid": str(uuid.uuid4()),
                    "groupUuid": group_uuid,
                    "groupType": "QUESTION",
                    "type": input_type,
                    "payload": input_payload,
                },
            ]

        def make_page_break() -> dict:
            """Creates a page break block."""
            return {
                "uuid": str(uuid.uuid4()),
                "groupUuid": str(uuid.uuid4()),
                "groupType": "PAGE_BREAK",
                "type": "PAGE_BREAK",
                "payload": {},
            }

        # ===== PAGE 1: Subject Selection =====

        # 1. Email Question
        blocks.extend(
            make_input_question(
                "Your Email Address",
                "INPUT_EMAIL",
                {"placeholder": "student@example.com"},
                is_required=True,
            )
        )

        # 2. Which subjects are you taking? (Checkboxes)
        subject_names = [subj.name for subj in subjects]
        blocks.extend(
            make_checkbox_group(
                "Select the subjects you are enrolled in for this exam period:",
                subject_names,
                is_required=True,
            )
        )

        # 3. Which subjects have you previously failed? (Checkboxes)
        blocks.extend(
            make_checkbox_group(
                "Select any subjects you have previously failed (leave empty if none):",
                subject_names,
                is_required=False,
            )
        )

        # ===== PAGE BREAK =====
        blocks.append(make_page_break())

        # ===== PAGE 2: Difficulty Ratings =====

        # 4. Difficulty ratings for each subject
        for subj in subjects:
            blocks.extend(
                make_input_question(
                    f"How difficult is {subj.name} for you? (1=Easy, 10=Very Hard)",
                    "INPUT_NUMBER",
                    {"placeholder": "5", "min": 1, "max": 10},
                    is_required=False,  # Not required since student might not be taking this subject
                )
            )

        payload = {
            "name": title,
            "blocks": blocks,
            "status": "PUBLISHED",
            "settings": {"saveForLater": True, "progressBar": True},
        }

        if self.workspace_id:
            payload["workspaceId"] = self.workspace_id

        response = requests.post(
            f"{TALLY_API_URL}/forms", headers=self.headers, json=payload
        )

        if response.status_code == 201 or response.status_code == 200:
            data = response.json()
            form_id = data.get("id")
            return f"https://tally.so/r/{form_id}"
        else:
            raise Exception(
                f"Failed to create form. Status: {response.status_code}, Body: {response.text}"
            )

    def fetch_responses(self, form_id: str) -> tuple:
        """
        Fetches responses for the given form ID.
        Returns tuple of (questions, submissions) where:
        - questions: List of question definitions with id, title, type
        - submissions: List of submission objects with responses
        """
        response = requests.get(
            f"{TALLY_API_URL}/forms/{form_id}/submissions",
            headers=self.headers,
        )

        if response.status_code == 200:
            data = response.json()
            questions = data.get("questions", [])
            submissions = data.get("submissions", [])
            return questions, submissions
        else:
            print(f"Error fetching responses: {response.text}")
            return [], []

    def parse_responses(
        self, api_data: tuple, subjects: List[Subject]
    ) -> List[Student]:
        """
        Parses Tally form submissions into Student objects.

        api_data: tuple of (questions, submissions) from fetch_responses

        Tally API structure:
        - questions: [{id, title, type}, ...]
        - submissions: [{id, responses: [{questionId, answer}, ...]}, ...]

        Form structure:
        - "Select the subjects you are enrolled in..." -> checkbox list of enrolled subjects
        - "Select any subjects you have previously failed..." -> checkbox list of failed subjects
        - "How difficult is {subject}..." -> difficulty rating for each subject
        """
        questions, submissions = api_data
        students = []

        # Build question lookup: questionId -> question title
        question_lookup = {q["id"]: q.get("title", "") for q in questions}

        # Create lookup for subject names
        subject_lookup = {subj.name: subj for subj in subjects}

        for i, sub in enumerate(submissions):
            responses = sub.get("responses", [])

            # Helper to find answer by question title pattern
            def get_answer(title_contains: str):
                for resp in responses:
                    q_title = question_lookup.get(resp.get("questionId"), "")
                    if title_contains.lower() in q_title.lower():
                        return resp.get("answer")
                return None

            # Helper to get checkbox selections (returns list of selected options)
            def get_checkbox_selections(title_contains: str) -> List[str]:
                answer = get_answer(title_contains)
                if isinstance(answer, list):
                    return [str(v) for v in answer]
                elif answer:
                    return [str(answer)]
                return []

            # Extract email
            email = get_answer("Email")
            if not email:
                continue

            student = Student(id=i)

            # Get enrolled subjects (from checkbox)
            enrolled_subjects = get_checkbox_selections("enrolled in")

            # Get previously failed subjects (from checkbox)
            failed_subjects = get_checkbox_selections("previously failed")

            # For each enrolled subject, add to student
            for subj_name in enrolled_subjects:
                # Find the subject object
                subj = subject_lookup.get(subj_name)
                if not subj:
                    # Try partial match
                    for name, s in subject_lookup.items():
                        if (
                            subj_name.lower() in name.lower()
                            or name.lower() in subj_name.lower()
                        ):
                            subj = s
                            break

                if not subj:
                    continue

                # Get difficulty for this subject
                diff_answer = get_answer(f"How difficult is {subj.name}")
                difficulty = 5  # Default
                if diff_answer is not None:
                    try:
                        difficulty = int(diff_answer)
                    except (ValueError, TypeError):
                        pass

                # Check if this subject was previously failed (trials = 1)
                is_failed = any(
                    subj_name.lower() in f.lower() or subj.name.lower() in f.lower()
                    for f in failed_subjects
                )
                trials = 1 if is_failed else 0

                student.add_subject(subj, difficulty, trials)

            # Only add student if they have at least one subject
            if student.subjects:
                students.append(student)

        return students
