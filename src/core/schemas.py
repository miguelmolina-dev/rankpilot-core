from typing import List, Optional
from pydantic import BaseModel, Field


class InterviewContact(BaseModel):
    name: Optional[str] = None
    job_title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class Identity(BaseModel):
    firm_name: Optional[str] = None
    country: Optional[str] = None
    practice_area: Optional[str] = None
    interview_contacts: List[InterviewContact] = Field(default_factory=list)


class HeadOfTeam(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None


class Metrics(BaseModel):
    partners_count_50_percent_plus: int = 0
    non_partners_count_50_percent_plus: int = 0


class DepartmentInfo(BaseModel):
    team_name_internal: Optional[str] = None
    heads_of_team: List[HeadOfTeam] = Field(default_factory=list)
    metrics: Metrics = Field(default_factory=Metrics)


class Narratives(BaseModel):
    what_sets_us_apart: Optional[str] = None
    initiatives_and_innovation: Optional[str] = None
    rankings_feedback: Optional[str] = None


class Client(BaseModel):
    active_key_client: Optional[str] = None
    is_new_client: bool = False
    is_publishable: bool = False


class Partner(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    ranked_in_previous_edition: bool = False
    supporting_information: Optional[str] = None


class Associate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    supporting_information: Optional[str] = None


class IndividualNominations(BaseModel):
    leading_partners: List[Partner] = Field(default_factory=list)
    next_generation_partners: List[Associate] = Field(default_factory=list)
    leading_associates: List[Associate] = Field(default_factory=list)


class ArrivalDeparture(BaseModel):
    name: Optional[str] = None
    position_role: Optional[str] = None
    action: Optional[str] = None  # Joined/Departed/Promoted
    firm_source_destination: Optional[str] = None
    month_year: Optional[str] = None


class TeamDynamics(BaseModel):
    arrivals_and_departures: List[ArrivalDeparture] = Field(default_factory=list)


class WorkHighlight(BaseModel):
    publishable_summary: Optional[str] = None


class TeamMember(BaseModel):
    name: Optional[str] = None
    office: Optional[str] = None
    practice_area: Optional[str] = None


class ExternalFirm(BaseModel):
    firm_name: Optional[str] = None
    role_details: Optional[str] = None
    entity_advised: Optional[str] = None


class Dates(BaseModel):
    start: Optional[str] = None
    end: Optional[str] = None


class Matter(BaseModel):
    id: Optional[int] = None
    client_name: Optional[str] = None
    industry_sector: Optional[str] = None
    matter_description: Optional[str] = None
    deal_value: Optional[str] = None
    is_cross_border: bool = False
    jurisdictions_involved: List[str] = Field(default_factory=list)
    lead_partners: List[TeamMember] = Field(default_factory=list)
    other_key_team_members: List[TeamMember] = Field(default_factory=list)
    external_firms_advising: List[ExternalFirm] = Field(default_factory=list)
    dates: Optional[Dates] = None
    is_publishable: bool = False


class Legal500Submission(BaseModel):
    identity: Optional[Identity] = None
    department_info: Optional[DepartmentInfo] = None
    narratives: Optional[Narratives] = None
    clients: List[Client] = Field(default_factory=list)
    individual_nominations: Optional[IndividualNominations] = None
    team_dynamics: Optional[TeamDynamics] = None
    work_highlights_summaries: List[WorkHighlight] = Field(default_factory=list)
    matters: List[Matter] = Field(default_factory=list)
