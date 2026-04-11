import unittest
from src.core.workflow import build_workflow
from src.core.state import AgentState

class TestWorkflow(unittest.TestCase):
    def test_workflow_execution(self):
        workflow = build_workflow()

        import base64

        # Initial state
        dummy_content = b"Dummy PDF content"
        b64_string = base64.b64encode(dummy_content).decode('utf-8')

        initial_state: AgentState = {
            "base64_documents": [{"filename": "test.pdf", "base64": b64_string}],
            "decoded_file_paths": [],
            "submission_type": None,
            "submission": None,
            "gaps": [],
            "questions": [],
            "messages": [],
            "current_step": "init",
            "errors": []
        }

        # Run workflow
        result = workflow.invoke(initial_state)

        # Verify it went through ingestion, classification, audit
        # The exact message depends on whether text was extracted. Since the dummy pdf is invalid, it outputs 'No text extracted'
        self.assertTrue(any("Ingestion node:" in msg for msg in result["messages"]))
        self.assertIn("Classification node: Classified as Legal500.", result["messages"])

        # We expect gaps for an empty submission, so interrogator should run
        self.assertTrue(len(result["gaps"]) > 0)
        self.assertTrue(result["new_answer"]["question_text"] != "")

        # Workflow now stops at interrogator to wait for Laravel
        self.assertEqual(result["current_step"], "interrogator")
