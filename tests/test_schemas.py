import unittest
from src.core.schemas import Legal500Submission


class TestSchemas(unittest.TestCase):
    def test_legal500_submission_schema_matches_json(self):
        json_data = {
            "identity": {
                "firm_name": None,
                "country": None,
                "practice_area": None,
                "interview_contacts": [
                    {
                        "name": None,
                        "job_title": None,
                        "email": None,
                        "phone": None
                    },
                    {
                        "name": None,
                        "job_title": None,
                        "email": None,
                        "phone": None
                    }
                ]
            },
            "department_info": {
                "team_name_internal": None,
                "heads_of_team": [
                    { "name": None, "location": None },
                    { "name": None, "location": None },
                    { "name": None, "location": None }
                ],
                "metrics": {
                    "partners_count_50_percent_plus": 0,
                    "non_partners_count_50_percent_plus": 0
                }
            },
            "narratives": {
                "what_sets_us_apart": None,
                "initiatives_and_innovation": None,
                "rankings_feedback": None
            },
            "clients": [
                {
                    "active_key_client": None,
                    "is_new_client": False,
                    "is_publishable": False
                }
            ],
            "individual_nominations": {
                "leading_partners": [
                    {
                        "name": None,
                        "location": None,
                        "ranked_in_previous_edition": False,
                        "supporting_information": None
                    },
                    {
                        "name": None,
                        "location": None,
                        "ranked_in_previous_edition": False,
                        "supporting_information": None
                    },
                    {
                        "name": None,
                        "location": None,
                        "ranked_in_previous_edition": False,
                        "supporting_information": None
                    }
                ],
                "next_generation_partners": [
                    { "name": None, "location": None, "supporting_information": None },
                    { "name": None, "location": None, "supporting_information": None }
                ],
                "leading_associates": [
                    { "name": None, "location": None, "supporting_information": None },
                    { "name": None, "location": None, "supporting_information": None }
                ]
            },
            "team_dynamics": {
                "arrivals_and_departures": [
                    {
                        "name": None,
                        "position_role": None,
                        "action": None,
                        "firm_source_destination": None,
                        "month_year": None
                    }
                ]
            },
            "work_highlights_summaries": [
                { "publishable_summary": None },
                { "publishable_summary": None },
                { "publishable_summary": None }
            ],
            "matters": [
                {
                    "id": 1,
                    "client_name": None,
                    "industry_sector": None,
                    "matter_description": None,
                    "deal_value": None,
                    "is_cross_border": False,
                    "jurisdictions_involved": [],
                    "lead_partners": [
                        { "name": None, "office": None, "practice_area": None },
                        { "name": None, "office": None, "practice_area": None }
                    ],
                    "other_key_team_members": [
                        { "name": None, "office": None, "practice_area": None }
                    ],
                    "external_firms_advising": [
                        { "firm_name": None, "role_details": None, "entity_advised": None }
                    ],
                    "dates": { "start": None, "end": None },
                    "is_publishable": False
                }
            ]
        }

        # Instantiate model from dict
        submission = Legal500Submission(**json_data)

        # Validate that model successfully instantiates and handles data types properly
        self.assertEqual(len(submission.identity.interview_contacts), 2)
        self.assertEqual(len(submission.department_info.heads_of_team), 3)
        self.assertEqual(submission.department_info.metrics.partners_count_50_percent_plus, 0)
        self.assertEqual(len(submission.clients), 1)
        self.assertFalse(submission.clients[0].is_new_client)
        self.assertEqual(len(submission.individual_nominations.leading_partners), 3)
        self.assertEqual(len(submission.team_dynamics.arrivals_and_departures), 1)
        self.assertEqual(len(submission.work_highlights_summaries), 3)
        self.assertEqual(len(submission.matters), 1)

        # Verify a specific matter field
        matter = submission.matters[0]
        self.assertEqual(matter.id, 1)
        self.assertFalse(matter.is_cross_border)
        self.assertEqual(len(matter.jurisdictions_involved), 0)
        self.assertEqual(len(matter.lead_partners), 2)
        self.assertEqual(len(matter.external_firms_advising), 1)

if __name__ == '__main__':
    unittest.main()
