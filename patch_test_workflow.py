with open("tests/test_workflow.py", "r") as f:
    content = f.read()

content = content.replace(
"""        self.assertTrue(len(result["gaps"]) > 0)
        self.assertTrue(len(result["questions"]) > 0)

        # Finally it should reach assembly
        self.assertEqual(result["current_step"], "assembly")""",
"""        self.assertTrue(len(result["gaps"]) > 0)
        self.assertTrue(result["new_answer"]["question_text"] != "")

        # Workflow now stops at interrogator to wait for Laravel
        self.assertEqual(result["current_step"], "interrogator")""")

with open("tests/test_workflow.py", "w") as f:
    f.write(content)
