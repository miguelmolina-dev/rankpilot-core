from typing import List, Optional
from pydantic import BaseModel, Field

# =====================================================================
#
#                         BASE SUBMISSION
#
# =====================================================================

class BaseSubmission(BaseModel):
    """
    Base submission class.
    Different ranking templates (Legal500, Chambers) will extend this
    or be structurally compatible with the overarching strategy pattern.
    """
    pass


# =====================================================================
#
#                         LEGAL 500 SCHEMA
#
# =====================================================================

# -----------------------------------
# Identity & Contacts (Legal 500)
# -----------------------------------
class InterviewContact(BaseModel):
    name: Optional[str] = Field(None, description="Full name of the interview contact.")
    job_title: Optional[str] = Field(None, description="Job title of the contact.")
    email: Optional[str] = Field(None, description="Email address. Extract cleanly without mailto: prefixes.")
    phone: Optional[str] = Field(None, description="Telephone number. Keep international codes if present.")

class Identity(BaseModel):
    firm_name: Optional[str] = Field(None, description="The official name of the law firm.")
    country: Optional[str] = Field(None, description="The country for the submission (e.g., 'United States').")
    practice_area: Optional[str] = Field(None, description="The specific practice area selected for this submission.")
    interview_contacts: List[InterviewContact] = Field(default_factory=list, description="List of contacts to arrange interviews with.")

# -----------------------------------
# Department Information (Legal 500)
# -----------------------------------
class HeadOfTeam(BaseModel):
    name: Optional[str] = Field(None, description="Full name of the team or department head.")
    location: Optional[str] = Field(None, description="Office location or city of the team head.")

class Metrics(BaseModel):
    partners_count_50_percent_plus: int = Field(0, description="Number of partners who spend at least 50% of their time in this department. Return 0 if none.")
    non_partners_count_50_percent_plus: int = Field(0, description="Number of non-partners who spend at least 50% of their time in this department. Return 0 if none.")

class DepartmentInfo(BaseModel):
    team_name_internal: Optional[str] = Field(None, description="The Team or Department Name as used internally by the firm.")
    heads_of_team: List[HeadOfTeam] = Field(default_factory=list, description="List of the Head(s) of the Team.")
    metrics: Metrics = Field(default_factory=Metrics)

class Narratives(BaseModel):
    what_sets_us_apart: Optional[str] = Field(None, description="Narrative detailing what sets the practice apart from other firms.")
    initiatives_and_innovation: Optional[str] = Field(None, description="Narrative detailing measures introduced or maintained over the last year to benefit clients.")
    rankings_feedback: Optional[str] = Field(None, description="Feedback regarding existing rankings or commentary. Return null if blank.")

# -----------------------------------
# Nominations & People (Legal 500)
# -----------------------------------
class Partner(BaseModel):
    name: Optional[str] = Field(None, description="Full name of the leading partner.")
    location: Optional[str] = Field(None, description="Office location or city of the partner.")
    ranked_in_previous_edition: bool = Field(False, description="Were they ranked in the previous edition? Map 'Yes'/'Y' to true, 'No'/'N' to false.")
    supporting_information: Optional[str] = Field(None, description="Detailed supporting evidence and narrative for why this partner is pre-eminent. Extract full text.")

class Associate(BaseModel):
    name: Optional[str] = Field(None, description="Full name of the leading associate/next gen partner (can include counsel).")
    location: Optional[str] = Field(None, description="Office location or city of the associate.")
    supporting_information: Optional[str] = Field(None, description="Detailed supporting evidence for this associate/partner. Extract full text.")

class ArrivalDeparture(BaseModel):
    name: Optional[str] = Field(None, description="Name of the person who arrived, departed, or was promoted.")
    position_role: Optional[str] = Field(None, description="The position or role of the person (e.g., Partner).")
    action: Optional[str] = Field(None, description="Specify strictly 'Joined', 'Departed', or 'Promoted'.")
    firm_source_destination: Optional[str] = Field(None, description="The firm they joined from, or the destination firm they departed to.")
    month_year: Optional[str] = Field(None, description="The month and year of the action (e.g., 'March 2025').")

class IndividualNominations(BaseModel):
    leading_partners: List[Partner] = Field(default_factory=list, description="Nominations for genuinely exceptional, pre-eminent partners.")
    next_generation_partners: List[Associate] = Field(default_factory=list, description="Nominations for junior/new/younger partners making a material difference.")
    leading_associates: List[Associate] = Field(default_factory=list, description="Nominations for junior/new/younger associates or counsels making a material difference.")

class TeamDynamics(BaseModel):
    arrivals_and_departures: List[ArrivalDeparture] = Field(default_factory=list, description="List of significant recent arrivals, departures, or promotions at the partner level.")

# -----------------------------------
# Clients & Matters (Legal 500)
# -----------------------------------
class Client(BaseModel):
    active_key_client: Optional[str] = Field(None, description="The official name of the active key client.")
    is_new_client: bool = Field(False, description="Determine if this is a new client. Map 'Yes' or 'Y' to true, 'No', 'N' or blank to false.")
    is_publishable: bool = Field(False, description="Whether the client is publishable.")

class WorkHighlight(BaseModel):
    publishable_summary: Optional[str] = Field(None, description="A brief 1-2 sentence summary of a highlight matter (e.g., 'Advised X on acquisition of Y'). MUST be publishable.")

class TeamMember(BaseModel):
    name: Optional[str] = Field(None, description="Name of the lead partner or other key team member.")
    office: Optional[str] = Field(None, description="Office location of the team member.")
    practice_area: Optional[str] = Field(None, description="Specific practice area of the team member.")

class ExternalFirm(BaseModel):
    firm_name: Optional[str] = Field(None, description="Name of the other law firm advising on the matter.")
    role_details: Optional[str] = Field(None, description="Description of their role.")
    entity_advised: Optional[str] = Field(None, description="The specific firm, company, or individual that this external firm advised.")

class Dates(BaseModel):
    start: Optional[str] = Field(None, description="Start date of the matter. Return null if not provided.")
    end: Optional[str] = Field(None, description="End date of the matter. Return null if not provided.")

class Matter(BaseModel):
    id: Optional[int] = Field(None, description="Matter ID.")
    client_name: Optional[str] = Field(None, description="The name of the client.")
    industry_sector: Optional[str] = Field(None, description="The industry sector of the matter/client. Return null if blank.")
    matter_description: Optional[str] = Field(None, description="Detailed description of the matter, background, and firm's role. DO NOT include generic marketing text.")
    deal_value: Optional[str] = Field(None, description="Financial value of the deal/matter. Return null if blank.")
    is_cross_border: bool = Field(False)
    jurisdictions_involved: List[str] = Field(default_factory=list, description="If cross-border, list the jurisdictions involved.")
    lead_partners: List[TeamMember] = Field(default_factory=list, description="List of lead partners working on this specific matter.")
    other_key_team_members: List[TeamMember] = Field(default_factory=list, description="List of other key team members (associates, counsels) on the matter.")
    external_firms_advising: List[ExternalFirm] = Field(default_factory=list, description="List of other external firms involved in the matter.")
    dates: Optional[Dates] = Field(None, description="Start and end dates for the matter.")
    is_publishable: bool = Field(False)

# -----------------------------------
# Top-Level Document (Legal 500)
# -----------------------------------
class Legal500Submission(BaseSubmission):
    identity: Optional[Identity] = None
    department_info: Optional[DepartmentInfo] = None
    narratives: Optional[Narratives] = None
    clients: List[Client] = Field(default_factory=list)
    individual_nominations: Optional[IndividualNominations] = None
    team_dynamics: Optional[TeamDynamics] = None
    work_highlights_summaries: List[WorkHighlight] = Field(default_factory=list, max_length=3, description="Up to 3 brief summaries of publishable work highlights.")
    matters: List[Matter] = Field(default_factory=list)


# =====================================================================
#
#                           CHAMBERS SCHEMA
#
# =====================================================================

# -----------------------------------
# Section A: Preliminary Information
# -----------------------------------
class ContactPerson(BaseModel):
    name: Optional[str] = Field(None, description="Full name of the contact person.")
    email: Optional[str] = Field(None, description="Email address. Extract cleanly without mailto: prefixes.")
    telephone_number: Optional[str] = Field(None, description="Telephone number. Keep international codes if present.")

class PreliminaryInformation(BaseModel):
    A1_firm_name: Optional[str] = Field(None, description="The official, registered name of the law firm. Strip conversational filler.")
    A2_practice_area: Optional[str] = Field(None, description="The specific practice area being submitted for (e.g., 'FinTech Legal').")
    A3_location_jurisdiction: Optional[str] = Field(None, description="The country or jurisdiction the submission applies to.")
    A4_contact_persons: List[ContactPerson] = Field(default_factory=list, description="List of personnel designated to arrange interviews.")

# -----------------------------------
# Section B: Department Information
# -----------------------------------
class PartnerStats(BaseModel):
    total_number: Optional[int] = Field(None, description="The total raw integer number of lawyers/partners in this category. Return 0 if none.")
    male_ratio_percentage: Optional[str] = Field(None, description="The percentage of males. Include the '%' sign if present in text.")
    female_ratio_percentage: Optional[str] = Field(None, description="The percentage of females. Include the '%' sign if present in text.")

class DepartmentLawyersRanked(BaseModel):
    name: Optional[str] = Field(None, description="Full name of the lawyer.")
    comments_or_web_link: Optional[str] = Field(None, description="Include the bio URL or specific comments/key areas of focus listed for this lawyer.")
    is_partner: Optional[str] = Field(None, description="Evaluate if they are a partner based on the text. You MUST output exactly 'Y' or 'N'.")
    is_ranked: Optional[str] = Field(None, description="Evaluate if they are already ranked based on the text. You MUST output exactly 'Y' or 'N'.")
    parental_leave_or_part_time: Optional[str] = Field(None, description="Details regarding parental leave or part-time arrangements. Return null if blank.")

class HireDeparture(BaseModel):
    name: Optional[str] = Field(None, description="Name of the lawyer who joined or departed.")
    status_joined_departed: Optional[str] = Field(None, description="Specify strictly 'Joined' or 'Departed'.")
    from_or_destination_firm: Optional[str] = Field(None, description="The name of the previous firm (if joined) or destination firm (if departed).")

class DepartmentInfoFeature(BaseModel):
    B1_department_name: Optional[str] = Field(None, description="The internal name the firm uses for this specific department.")
    B2_partners: Optional[PartnerStats] = Field(None, description="Total number and gender ratio of partners in the department.")
    B3_other_qualified_lawyers: Optional[PartnerStats] = Field(None, description="Total number and gender ratio of other qualified lawyers (associates, counsels).")
    B4_department_heads: List[ContactPerson] = Field(default_factory=list, description="List of Department Head(s) or Key Partners (USA Template).")
    B5_diversity_lgbt_percentage: Optional[str] = Field(None, description="Percentage of the team identifying as LGBT+. Must be a raw number/percentage string. Return null if blank.")
    B6_diversity_disability_percentage: Optional[str] = Field(None, description="Percentage of the team with a disability. Must be a raw number/percentage string. Return null if blank.")
    B7_heads_of_department: List[ContactPerson] = Field(default_factory=list, description="List of the Heads of the Department.")
    B8_hires_departures_last_12_months: List[HireDeparture] = Field(default_factory=list, description="List of partners who joined or left the firm in the last 12 months.")
    B9_lawyers_ranked_unranked: List[DepartmentLawyersRanked] = Field(default_factory=list, description="Details regarding ranked and unranked lawyers, including their key areas of focus and standout work.")
    B10_department_best_known_for: Optional[str] = Field(None, description="A narrative summary of what the department is best known for. Include industry sector expertise, recent growth, and market disruptor status. Extract the full block of text.")

# -----------------------------------
# Section C: Feedback
# -----------------------------------
class BarristerAdvocate(BaseModel):
    name: Optional[str] = Field(None, description="Name of the barrister or advocate.")
    firm_set: Optional[str] = Field(None, description="The Firm or Set the barrister belongs to.")
    comments: Optional[str] = Field(None, description="Feedback or comments provided about this barrister.")

class FeedbackFeature(BaseModel):
    C1_barristers_advocates: List[BarristerAdvocate] = Field(default_factory=list, description="List of external barristers or advocates used by the firm.")
    C2_feedback_on_other_firms: Optional[str] = Field(None, description="Feedback provided regarding other competing firms or the ranking status of their own lawyers. Return null if blank.")

# -----------------------------------
# Section D: Publishable Information
# -----------------------------------
class PublishableClient(BaseModel):
    name_of_client: Optional[str] = Field(None, description="The official name of the client.")
    is_new_client: Optional[bool] = Field(None, description="Determine if this is a new client within the last 12 months. Map 'Yes' to true, 'No' or blank to false.")

class PublishableMatter(BaseModel):
    matter_id: Optional[str] = Field(None, description="The internal matter ID or sequential number (e.g., 'Publishable Matter 1').")
    D1_name_of_client: Optional[str] = Field(None, description="The name of the client. MUST be publishable.")
    D2_summary_of_matter_and_role: Optional[str] = Field(None, description="Summarizes the publishable matter and the firm's specific role. MUST NOT contain confidential information. If text says 'CONFIDENTIAL', route it to section E instead.")
    D3_matter_value: Optional[str] = Field(None, description="The financial value of the matter including currency. Return null if N/A or blank.")
    D4_cross_border_jurisdictions: Optional[str] = Field(None, description="List of jurisdictions involved if cross-border. If it explicitly says 'No', return null.")
    D5_lead_partner: Optional[str] = Field(None, description="Name(s) of the lead partner(s) on the matter.")
    D6_other_team_members: Optional[str] = Field(None, description="Names of other associates or team members involved.")
    D7_other_firms_advising: Optional[str] = Field(None, description="Names of other law firms involved and their roles. Return null if N/A.")
    D8_date_completion_or_status: Optional[str] = Field(None, description="The current status (e.g., 'Ongoing') or completion date.")
    D9_other_information_links: Optional[str] = Field(None, description="URLs to press coverage or additional notes. Return null if blank.")

class PublishableInformationFeature(BaseModel):
    D0_publishable_clients_list: List[PublishableClient] = Field(default_factory=list, description="List of clients whose identities can be published. Exclude any client marked confidential.")
    publishable_matters: List[PublishableMatter] = Field(default_factory=list, description="List of up to 20 publishable work highlights. MUST NOT contain confidential data.")

# -----------------------------------
# Section E: Confidential Information
# -----------------------------------
class ConfidentialMatter(BaseModel):
    matter_id: Optional[str] = Field(None, description="The internal matter ID or sequential number (e.g., 'Confidential Matter 1').")
    E1_name_of_client: Optional[str] = Field(None, description="The name of the client. Treat this as strictly confidential.")
    E2_summary_of_matter_and_role: Optional[str] = Field(None, description="Summarizes the confidential matter and the firm's role. This text is protected and not for publication.")
    E3_matter_value: Optional[str] = Field(None, description="The financial value of the matter. Often marked 'Confidential' or 'Non disclosable'. Extract the text as written.")
    E4_cross_border_jurisdictions: Optional[str] = Field(None, description="List of jurisdictions involved if cross-border. If it explicitly says 'No', return null.")
    E5_lead_lawyer: Optional[str] = Field(None, description="Name(s) of the lead partner/lawyer on the matter.")
    E6_other_team_members: Optional[str] = Field(None, description="Names of other associates or team members involved.")
    E7_other_firms_advising: Optional[str] = Field(None, description="Names of other law firms involved and their roles. Return null if N/A.")
    E8_date_completion_or_status: Optional[str] = Field(None, description="The current status (e.g., 'Ongoing') or completion date.")
    E9_other_information_links: Optional[str] = Field(None, description="URLs to press coverage or additional notes. Return null if blank.")
    is_confidential: Optional[bool] = Field(True, description="Always set to true for matters in Section E.")

class ConfidentialInformationFeature(BaseModel):
    E0_confidential_clients_list: List[PublishableClient] = Field(default_factory=list, description="List of clients whose identities MUST remain strictly confidential.")
    confidential_matters: List[ConfidentialMatter] = Field(default_factory=list, description="List of confidential work highlights. These matters are protected and not for publication.")

# -----------------------------------
# Top-Level Document (Chambers)
# -----------------------------------
class ChambersSubmission(BaseSubmission):
    """
    Top-level schema for Chambers Global and Chambers USA submissions.
    """
    A_preliminary_information: Optional[PreliminaryInformation] = None
    B_department_information: Optional[DepartmentInfoFeature] = None
    C_feedback: Optional[FeedbackFeature] = None
    D_publishable_information: Optional[PublishableInformationFeature] = None
    E_confidential_information: Optional[ConfidentialInformationFeature] = None

# =====================================================================
#
#                         LEADERS LEAGUE SCHEMA
#
# =====================================================================

# -----------------------------------
# Firm Information (Leaders League)
# -----------------------------------
class FirmInformationLL(BaseModel):
    firm_name: Optional[str] = Field(None, description="The official name of the firm.")
    year_established: Optional[str] = Field(None, description="The year the firm was established.")
    managing_partners: Optional[str] = Field(None, description="Name of the Managing Partner(s).")
    marketing_bd_persons: Optional[str] = Field(None, description="Name of the person(s) in charge of Marketing/Business Development.")
    list_of_offices: Optional[str] = Field(None, description="List of office locations.")
    total_partners: Optional[int] = Field(None, description="Number of Partners in the entire firm.")
    total_counsels_associates: Optional[int] = Field(None, description="Number of Counsels/Associates in the entire firm.")

# -----------------------------------
# Department Information (Leaders League)
# -----------------------------------
class DepartmentHeadLL(BaseModel):
    name: Optional[str] = Field(None, description="Name of the head of the department or key partner.")
    email: Optional[str] = Field(None, description="Email address.")
    partner_since: Optional[str] = Field(None, description="The year they became a partner.")
    specific_specialisms: Optional[str] = Field(None, description="Specific specialisms of the partner.")
    dedicates_less_than_50_percent: Optional[bool] = Field(False, description="True if the partner dedicates less than 50% of their time to this department (needs to be highlighted in red).")

class DepartmentChangeLL(BaseModel):
    name: Optional[str] = Field(None, description="Name of the person.")
    position: Optional[str] = Field(None, description="Position (e.g., Partner, Counsel, Associate).")
    action: Optional[str] = Field(None, description="Action: Arrived, left, promoted, or retired.")
    moved_to_from: Optional[str] = Field(None, description="Where they moved to or from.")
    month_year: Optional[str] = Field(None, description="Month and year of the change.")

class ActiveClientLL(BaseModel):
    company: Optional[str] = Field(None, description="Name of the company/client.")
    sector: Optional[str] = Field(None, description="Industry sector of the client.")
    is_new_client: Optional[bool] = Field(False, description="True if it is a new client.")
    is_confidential: Optional[bool] = Field(False, description="True if the client is confidential.")
    type_of_work: Optional[str] = Field(None, description="Type of work performed for the client.")

class DepartmentInformationLL(BaseModel):
    partners_completing_form: Optional[str] = Field(None, description="Name of the Partner(s) in charge of completing this form.")
    department_heads: List[DepartmentHeadLL] = Field(default_factory=list, description="List of Heads of the department and other key partners.")
    composition_male_partners: Optional[int] = Field(None, description="Number of Male Partners in the department.")
    composition_female_partners: Optional[int] = Field(None, description="Number of Female Partners in the department.")
    composition_counsels_associates: Optional[int] = Field(None, description="Number of Counsels/Associates in the department.")
    department_changes: List[DepartmentChangeLL] = Field(default_factory=list, description="Changes in the department over the last 12 months.")
    best_known_for: Optional[str] = Field(None, description="Narrative on what the department is best known for (max 500 words).")
    new_cases_last_12_months: Optional[str] = Field(None, description="Number of new cases taken on in the last 12 months.")
    top_five_sectors: List[str] = Field(default_factory=list, max_length=5, description="Top five sectors the department works with.")
    active_clients: List[ActiveClientLL] = Field(default_factory=list, max_length=30, description="List of active clients (up to 30).")

# -----------------------------------
# Peer Feedback (Leaders League)
# -----------------------------------
class EstablishedPractitionerLL(BaseModel):
    firm_lawyer: Optional[str] = Field(None, description="Name of the leading firm or lawyer.")
    comments: Optional[str] = Field(None, description="Comments supporting their leading status.")

class RisingStarLL(BaseModel):
    law_firm: Optional[str] = Field(None, description="Name of the rising star law firm.")
    lawyers: Optional[str] = Field(None, description="Names of the rising star lawyers.")
    main_specialty: Optional[str] = Field(None, description="Main specialty of the rising star.")

class PeerFeedbackLL(BaseModel):
    established_practitioners: List[EstablishedPractitionerLL] = Field(default_factory=list, description="Feedback on leading law firms/lawyers.")
    rising_stars: List[RisingStarLL] = Field(default_factory=list, description="Feedback on rising stars in the practice.")

# -----------------------------------
# Ranking Feedback (Leaders League)
# -----------------------------------
class RankingFeedbackLL(BaseModel):
    opinion_current_position: Optional[str] = Field(None, description="Opinion on the firm's current position in Leaders League ranking.")

# -----------------------------------
# Work Highlights (Leaders League)
# -----------------------------------
class WorkHighlightLL(BaseModel):
    matter_name: Optional[str] = Field(None, description="Name of the Matter.")
    is_confidential: Optional[bool] = Field(False, description="True if the matter is confidential.")
    client: Optional[str] = Field(None, description="Name of the Client.")
    matter_value: Optional[str] = Field(None, description="Value of the matter (specify currency) and/or other key numbers.")
    matter_status: Optional[str] = Field(None, description="Status of the matter (closed in last year or ongoing).")
    matter_context: Optional[str] = Field(None, description="Description of the context in which work was solicited.")
    firm_role_output: Optional[str] = Field(None, description="Explanation of what the firm did and strategy used.")
    lead_partners: Optional[str] = Field(None, description="Lead Partner(s) on the matter.")
    other_team_members: Optional[str] = Field(None, description="Other team members involved.")
    other_firms_advising: Optional[str] = Field(None, description="Other firms advising on the matter and their role.")
    press_links: Optional[str] = Field(None, description="Links to press coverage.")

# -----------------------------------
# Top-Level Document (Leaders League)
# -----------------------------------
class LeadersLeagueSubmission(BaseSubmission):
    """
    Top-level schema for Leaders League submissions.
    """
    firm_information: Optional[FirmInformationLL] = None
    department_information: Optional[DepartmentInformationLL] = None
    peer_feedback: Optional[PeerFeedbackLL] = None
    ranking_feedback: Optional[RankingFeedbackLL] = None
    work_highlights: List[WorkHighlightLL] = Field(default_factory=list, max_length=10, description="Up to 10 work highlights.")