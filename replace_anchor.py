with open('src/core/schemas.py', 'r') as f:
    lines = f.readlines()

new_lines = []
in_anchor = False
for line in lines:
    if line.startswith("class AnchorSubmission(BaseSubmission):"):
        in_anchor = True
        new_lines.append(line)
        continue
    if in_anchor and line.strip() == "":
        new_lines.append("    document_metadata: Optional[DocumentMetadata] = None\n")
        new_lines.append("    firm_details: Optional[FirmDetails] = None\n")
        new_lines.append("    iflr_section_1_lawyers: Optional[IFLRSection1Lawyers] = None\n")
        new_lines.append("    iflr_section_2_practice_overview: Optional[IFLRSection2PracticeOverview] = None\n")
        new_lines.append("    iflr_section_3_deal_highlights: Optional[IFLRSection3DealHighlights] = None\n")
        new_lines.append("    itr_section_1_practice_developments: Optional[ITRSection1PracticeDevelopments] = None\n")
        new_lines.append("    itr_section_2_deal_and_case_highlights: Optional[ITRSection2DealAndCaseHighlights] = None\n")
        in_anchor = False
    new_lines.append(line)

with open('src/core/schemas.py', 'w') as f:
    f.writelines(new_lines)
