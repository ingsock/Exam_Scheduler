import os.path
from typing import List, Dict, Set, Optional
from dataclasses import dataclass

from scheduler import Student, Subject

# Note: These imports require 'google-api-python-client', 'google-auth-httplib2', 'google-auth-oauthlib'
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("Error: Google API libraries are not installed. Please install them using:")
    print(
        "pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib"
    )
    raise

# If modifying these scopes, delete the file token.json.
SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/forms.responses.readonly",
]


@dataclass
class FormConfig:
    title: str
    subjects: List[Subject]
    allowed_emails: Set[str]


class FormsManager:
    def __init__(
        self, credentials_file: str = "credentials.json", token_file: str = "token.json"
    ):
        self.creds = None
        self.credentials_file = credentials_file
        self.token_file = token_file
        self._authenticate()
        self.forms_service = build("forms", "v1", credentials=self.creds)

    def _authenticate(self):
        if os.path.exists(self.token_file):
            self.creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"Missing {self.credentials_file}. Please download it from Google Cloud Console."
                    )

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES
                )
                self.creds = flow.run_local_server(port=0)

            # Save the credentials for the next run
            with open(self.token_file, "w") as token:
                token.write(self.creds.to_json())

    def create_exam_form(self, title: str, subjects: List[Subject]) -> str:
        """Creates a new form and returns its URL."""

        # 1. Create the form
        form_body = {
            "info": {
                "title": title,
                "documentTitle": title,
            }
        }

        try:
            form = self.forms_service.forms().create(body=form_body).execute()
            form_id = form["formId"]

            # 2. Add questions (Batch Update)
            requests = []

            # Email Collection is usually a setting, but in API v1 it's tricky to toggle settings directly via 'create'.
            # We can ask for email as a text question or rely on domain collection.
            # Ideally, we add a required Short Answer Question for Email.
            requests.append(
                {
                    "createItem": {
                        "item": {
                            "title": "Email Address",
                            "questionItem": {
                                "question": {
                                    "required": True,
                                    "textQuestion": {},  # Short answer
                                }
                            },
                        },
                        "location": {"index": 0},
                    }
                }
            )

            # Difficulty Grid
            # Columns: 1 to 10
            diff_columns = [{"value": str(i)} for i in range(1, 11)]
            # Rows: Subjects
            subj_rows = [{"value": s.name} for s in subjects]

            requests.append(
                {
                    "createItem": {
                        "item": {
                            "title": "Subject Difficulty (1-10)",
                            "questionGroupItem": {
                                "grid": {
                                    "columns": {
                                        "type": "RADIO",
                                        "options": diff_columns,
                                    },
                                    "shuffleQuestions": False,
                                },
                                "questions": [
                                    {
                                        "required": False,
                                        "rowQuestion": {"title": row["value"]},
                                    }
                                    for row in subj_rows
                                ],
                            },
                        },
                        "location": {"index": 1},
                    }
                }
            )

            # Trials Grid
            # Columns: 0, 1, 2, 3+
            trial_columns = [
                {"value": "0"},
                {"value": "1"},
                {"value": "2"},
                {"value": "3+"},
            ]

            requests.append(
                {
                    "createItem": {
                        "item": {
                            "title": "Previous Trials",
                            "questionGroupItem": {
                                "grid": {
                                    "columns": {
                                        "type": "RADIO",
                                        "options": trial_columns,
                                    },
                                    "shuffleQuestions": False,
                                },
                                "questions": [
                                    {
                                        "required": False,
                                        "rowQuestion": {"title": row["value"]},
                                    }
                                    for row in subj_rows
                                ],
                            },
                        },
                        "location": {"index": 2},
                    }
                }
            )

            self.forms_service.forms().batchUpdate(
                formId=form_id, body={"requests": requests}
            ).execute()

            # Get the responder URL (requires re-fetching or knowing the format)
            # Typically: https://docs.google.com/forms/d/{formId}/viewform
            return f"https://docs.google.com/forms/d/{form_id}/viewform"

        except HttpError as error:
            print(f"An error occurred: {error}")
            return ""

    def get_form_responses(self, form_id: str) -> List[Dict]:
        """Fetches raw responses from the form."""
        try:
            result = (
                self.forms_service.forms().responses().list(formId=form_id).execute()
            )
            return result.get("responses", [])
        except HttpError as error:
            print(f"An error occurred fetching responses: {error}")
            return []

    def fetch_and_parse(
        self, form_id: str, allowed_emails: Optional[Set[str]], subjects: List[Subject]
    ) -> List[Student]:
        # Create a map of subject name to Subject object
        subj_map = {s.name: s for s in subjects}

        # 1. Fetch Form Metadata to map Question IDs to Titles
        form_meta = self.forms_service.forms().get(formId=form_id).execute()

        # Map: "Title" -> { "row_title": "question_id" }
        grid_map = {}  # "Subject Difficulty (1-10)" -> { "Math": "12345", "Physics": "67890" }
        email_q_id = None

        for item in form_meta.get("items", []):
            title = item.get("title")

            if title == "Email Address":
                email_q_id = (
                    item.get("questionItem", {}).get("question", {}).get("questionId")
                )

            elif title == "Subject Difficulty (1-10)" or title == "Previous Trials":
                group = item.get("questionGroupItem", {})
                q_rows = {}
                for q in group.get("questions", []):
                    row_title = q.get("rowQuestion", {}).get("title")
                    q_id = q.get("questionId")
                    q_rows[row_title] = q_id
                grid_map[title] = q_rows

        # 2. Fetch Responses
        responses = self.get_form_responses(form_id)

        students = []
        student_id_counter = 0

        for resp in responses:
            answers = resp.get("answers", {})

            # Check Email
            if not email_q_id or email_q_id not in answers:
                # Could be system collected email?
                email = resp.get("respondentEmail")  # Only if collected via settings
            else:
                email = answers[email_q_id]["textAnswers"]["answers"][0]["value"]

            if allowed_emails and email not in allowed_emails:
                continue

            student = Student(id=student_id_counter)
            student_id_counter += 1

            # Parse Difficulty
            diff_map = grid_map.get("Subject Difficulty (1-10)", {})
            trial_map = grid_map.get("Previous Trials", {})

            for subj_name, q_id in diff_map.items():
                if q_id in answers:
                    val_str = answers[q_id]["textAnswers"]["answers"][0]["value"]
                    try:
                        difficulty = int(val_str)
                    except ValueError:
                        difficulty = 5  # Default?

                    # Trial
                    trial_q_id = trial_map.get(subj_name)
                    trials = 0
                    if trial_q_id and trial_q_id in answers:
                        t_val = answers[trial_q_id]["textAnswers"]["answers"][0][
                            "value"
                        ]
                        if t_val == "3+":
                            trials = 3
                        else:
                            try:
                                trials = int(t_val)
                            except ValueError:
                                trials = 0

                    # Add to student
                    subject_obj = subj_map.get(subj_name)
                    if subject_obj:
                        student.add_subject(subject_obj, difficulty, trials)

            if student.subjects:
                students.append(student)

        return students
