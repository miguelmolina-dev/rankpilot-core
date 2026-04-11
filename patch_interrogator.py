with open("src/agents/interrogator.py", "r") as f:
    content = f.read()

content = content.replace(
"""class StrategicQuestions(BaseModel):
    questions: List[str] = Field(
        description="A list of strategic questions asking for the missing information."
    )""",
"""class StrategicQuestion(BaseModel):
    question: str = Field(
        description="A strategic question asking for the specific missing information."
    )""")

content = content.replace(
"""            structured_llm = llm.with_structured_output(StrategicQuestions)

            system_prompt = (
                "You are an expert legal ranking strategist advising a law firm. "
                "The firm is preparing a submission for legal directories (like Chambers or Legal500), "
                "but some required fields are missing. "
                "Generate a set of clear, professional, and strategic questions to ask the attorneys "
                "to easily obtain the missing information. "
                "Address the attorneys directly."
            )

            gaps_text = "\\n".join([
                f"- Field: {gap.get('field', 'unknown')}. Reason: {gap.get('reason', 'Missing information.')}"
                for gap in gaps
            ])

            user_prompt = (
                "Here are the missing fields and the reasons they are flagged as missing:\\n"
                f"{gaps_text}\\n\\n"
                "Please generate the strategic questions to ask for this missing information."
            )

            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", user_prompt),
            ])

            chain = prompt | structured_llm
            result = chain.invoke({})

            questions = result.questions

        except Exception as e:
            # Fallback to simple logic if LLM fails (e.g., no API key in tests)
            updates["messages"].append(f"LLM generation failed: {e}. Falling back to simple questions.")
            for gap in gaps:
                field = gap.get("field", "unknown")
                questions.append(f"We are missing information for '{field}'. Could you provide details?")

    updates["questions"] = questions
    updates["messages"].append(f"Interrogator node: Generated {len(questions)} questions.")""",
"""            structured_llm = llm.with_structured_output(StrategicQuestion)

            system_prompt = (
                "You are an expert legal ranking strategist advising a law firm. "
                "The firm is preparing a submission for legal directories (like Chambers or Legal500), "
                "but a specific required field is missing. "
                "Generate a single clear, professional, and strategic question to ask the attorneys "
                "to easily obtain the missing information. "
                "Address the attorneys directly."
            )

            first_gap = gaps[0]
            field = first_gap.get('field', 'unknown')
            reason = first_gap.get('reason', 'Missing information.')

            user_prompt = (
                f"We are missing information for the field '{field}' because: {reason}.\\n\\n"
                "Please generate one strategic question to ask for this missing information."
            )

            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", user_prompt),
            ])

            chain = prompt | structured_llm
            result = chain.invoke({})

            question = result.question

        except Exception as e:
            # Fallback to simple logic if LLM fails (e.g., no API key in tests)
            updates["messages"].append(f"LLM generation failed: {e}. Falling back to simple questions.")
            first_gap = gaps[0]
            field = first_gap.get("field", "unknown")
            question = f"We are missing information for '{field}'. Could you provide details?"

    updates["new_answer"] = {
        "question_text": question,
        "answer": ""
    }
    updates["messages"].append("Interrogator node: Generated 1 question and paused for Laravel.")""")

content = content.replace(
"""    gaps = state.get("gaps", [])
    questions = []

    if gaps:""",
"""    gaps = state.get("gaps", [])
    question = ""

    if gaps:""")

with open("src/agents/interrogator.py", "w") as f:
    f.write(content)
