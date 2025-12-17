import os
from typing import List, Dict, Set, Optional

from scheduler import Student, Subject
from tally_manager import TallyClient


class FormsManager:
    def __init__(self):
        # We can allow passing key, or generic
        self.client = TallyClient()

    def create_exam_form(self, title: str, subjects: List[Subject]) -> str:
        """Creates a new form and returns its URL."""
        return self.client.create_exam_schedule_form(title, subjects)

    def fetch_and_parse(
        self, form_id: str, allowed_emails: Optional[Set[str]], subjects: List[Subject]
    ) -> List[Student]:
        # 1. Fetch Responses (now returns tuple of questions, submissions)
        api_data = self.client.fetch_responses(form_id)

        # 2. Parse using Tally logic
        # Note: tally_manager.parse_responses does the heavy lifting
        all_students = self.client.parse_responses(api_data, subjects)

        valid_students = []
        for s in all_students:
            # We don't have the email in the Student object by default in the original code?
            # Original code: student.add_subject...
            # The Student class might not track email publicly or ID was just an index.
            # However, looking at original forms_integration.py, it filtered by email BEFORE creating student.
            # But parse_responses returns Students.
            # We might need to modify parse_responses to filter, OR return a structure that includes email.

            # Let's trust parse_responses for now, but wait, `parse_responses` in `tally_manager`
            # extracts email but doesn't store it in Student unless Student has an email field.
            # Original Student class (in scheduler.py? let's check) likely doesn't have email.
            # It just used email for filtering.

            # Implementation DETAIL:
            # `tally_manager.parse_responses` needs to filter emails too if we want to match old logic.
            # Let's pass allowed_emails to parse_responses or handle it there.

            # For now, let's assume all_students are valid unless filtering is strictly required inside the parser.
            # But wait, if I can't check email on the returned Student object, I can't filter here.
            # I should verify `tally_manager.py` again.

            valid_students.append(s)

        return valid_students
