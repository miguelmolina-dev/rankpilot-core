with open("src/core/state.py", "r") as f:
    content = f.read()

replacement = """    # Dynamic questions generated to cover gaps
    questions: List[str]

    # History of Q&A interactions with Laravel
    history: List[str]

    # Current question and incoming answer from Laravel
    new_answer: Dict[str, str]

    # Base64 output representation of the final document"""

content = content.replace(
    """    # Dynamic questions generated to cover gaps
    questions: List[str]

    # Base64 output representation of the final document""",
    replacement
)

with open("src/core/state.py", "w") as f:
    f.write(content)
