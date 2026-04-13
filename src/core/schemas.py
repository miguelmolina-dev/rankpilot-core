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


class BaseSubmission(BaseModel):
    """
    Base submission class.
    Different ranking templates (Legal500, Chambers) will extend this
    or be structurally compatible with the overarching strategy pattern.
    """
    pass

class Legal500Submission(BaseSubmission):
    identity: Optional[Identity] = None
    department_info: Optional[DepartmentInfo] = None
    narratives: Optional[Narratives] = None
    clients: List[Client] = Field(default_factory=list)
    individual_nominations: Optional[IndividualNominations] = None
    team_dynamics: Optional[TeamDynamics] = None
    work_highlights_summaries: List[WorkHighlight] = Field(default_factory=list)
    matters: List[Matter] = Field(default_factory=list)

class ContactPerson(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    telephone_number: Optional[str] = None

class PreliminaryInformation(BaseModel):
    A1_firm_name: Optional[str] = None
    A2_practice_area: Optional[str] = None
    A3_location_jurisdiction: Optional[str] = None
    A4_contact_persons: List[ContactPerson] = Field(default_factory=list)

class PartnerStats(BaseModel):
    total_number: Optional[int] = None
    male_ratio_percentage: Optional[str] = None
    female_ratio_percentage: Optional[str] = None

class DepartmentLawyersRanked(BaseModel):
    name: Optional[str] = None
    comments_or_web_link: Optional[str] = None
    is_partner: Optional[bool] = None
    is_ranked: Optional[bool] = None
    parental_leave_or_part_time: Optional[str] = None

class HireDeparture(BaseModel):
    name: Optional[str] = None
    status_joined_departed: Optional[str] = None
    from_or_destination_firm: Optional[str] = None

class DepartmentInfoFeature(BaseModel):
    B1_department_name: Optional[str] = None
    B2_partners: Optional[PartnerStats] = None
    B3_other_qualified_lawyers: Optional[PartnerStats] = None
    B5_diversity_lgbt_percentage: Optional[str] = None
    B6_diversity_disability_percentage: Optional[str] = None
    B7_heads_of_department: List[ContactPerson] = Field(default_factory=list)
    B8_hires_departures_last_12_months: List[HireDeparture] = Field(default_factory=list)
    B9_lawyers_ranked_unranked: List[DepartmentLawyersRanked] = Field(default_factory=list)
    B10_department_best_known_for: Optional[str] = None

class BarristerAdvocate(BaseModel):
    name: Optional[str] = None
    firm_set: Optional[str] = None
    comments: Optional[str] = None

class FeedbackFeature(BaseModel):
    C1_barristers_advocates: List[BarristerAdvocate] = Field(default_factory=list)
    C2_feedback_on_other_firms: Optional[str] = None

class PublishableClient(BaseModel):
    name_of_client: Optional[str] = None
    is_new_client: Optional[bool] = None

class PublishableMatter(BaseModel):
    matter_id: Optional[str] = None
    D1_name_of_client: Optional[str] = None
    D2_summary_of_matter_and_role: Optional[str] = None
    D3_matter_value: Optional[str] = None
    D4_cross_border_jurisdictions: Optional[str] = None
    D5_lead_partner: Optional[str] = None
    D6_other_team_members: Optional[str] = None
    D7_other_firms_advising: Optional[str] = None
    D8_date_completion_or_status: Optional[str] = None
    D9_other_information_links: Optional[str] = None

class PublishableInformationFeature(BaseModel):
    D0_publishable_clients_list: List[PublishableClient] = Field(default_factory=list)
    publishable_matters: List[PublishableMatter] = Field(default_factory=list)

class ConfidentialMatter(BaseModel):
    matter_id: Optional[str] = None
    E1_name_of_client: Optional[str] = None
    E2_summary_of_matter_and_role: Optional[str] = None
    E3_matter_value: Optional[str] = None
    E4_cross_border_jurisdictions: Optional[str] = None
    E5_lead_lawyer: Optional[str] = None
    E6_other_team_members: Optional[str] = None
    E7_other_firms_advising: Optional[str] = None
    E8_date_completion_or_status: Optional[str] = None
    E9_other_information_links: Optional[str] = None
    is_confidential: Optional[bool] = None

class ConfidentialInformationFeature(BaseModel):
    E0_confidential_clients_list: List[PublishableClient] = Field(default_factory=list)
    confidential_matters: List[ConfidentialMatter] = Field(default_factory=list)

# --- IFLR1000 and ITR World Tax ---
class DocumentMetadata(BaseModel):
    submission_type: Optional[str] = None
    research_period: Optional[str] = None
    research_period_tax: Optional[str] = None
    research_period_awards: Optional[str] = None

class FirmDetails(BaseModel):
    firm_name: Optional[str] = None
    jurisdiction: Optional[str] = None
    us_state: Optional[str] = None
    practice_area: Optional[str] = None
    primary_practice_area: Optional[str] = None
    primary_contact: Optional[ContactPerson] = None
    research_contact: Optional[ContactPerson] = None
    additional_contacts: List[ContactPerson] = Field(default_factory=list)

class IFLRLawyerMarketLeader(BaseModel):
    first_name: Optional[str] = None
    surname: Optional[str] = None
    position: Optional[str] = None
    already_rated_iflr1000: Optional[bool] = None
    primary_practice_areas: Optional[str] = None
    industry_sectors: Optional[str] = None
    rating_nominated_for: Optional[str] = None
    reasoning_and_deal_numbers: Optional[str] = None
    email_confidential: Optional[str] = None

class IFLRLawyerRisingStar(BaseModel):
    first_name: Optional[str] = None
    surname: Optional[str] = None
    email_confidential: Optional[str] = None
    already_rated: Optional[bool] = None
    rating_nominated_for: Optional[str] = None
    position: Optional[str] = None
    year_of_qualification: Optional[int] = None
    year_promoted_to_partner: Optional[int] = None
    primary_practice_area: Optional[str] = None
    most_important_legal_matter: Optional[str] = None
    date_completed: Optional[str] = None
    role_and_impact: Optional[str] = None

class IFLRLawyerExpertConsultant(BaseModel):
    first_name: Optional[str] = None
    surname: Optional[str] = None
    email_confidential: Optional[str] = None
    position: Optional[str] = None
    primary_practice_area: Optional[str] = None
    brief_reason_for_nomination: Optional[str] = None

class IFLRSection1Lawyers(BaseModel):
    market_leader_highly_regarded_women_leader: List[IFLRLawyerMarketLeader] = Field(default_factory=list)
    rising_star_nominees: List[IFLRLawyerRisingStar] = Field(default_factory=list)
    expert_consultants: List[IFLRLawyerExpertConsultant] = Field(default_factory=list)

class IFLRHire(BaseModel):
    first_name: Optional[str] = None
    surname: Optional[str] = None
    position_role: Optional[str] = None
    practice_area: Optional[str] = None
    hired_from: Optional[str] = None
    date: Optional[str] = None

class IFLRDeparture(BaseModel):
    first_name: Optional[str] = None
    surname: Optional[str] = None
    position_role: Optional[str] = None
    practice_area: Optional[str] = None
    departed_to: Optional[str] = None
    date: Optional[str] = None

class IFLRReferralWork(BaseModel):
    first_name: Optional[str] = None
    surname: Optional[str] = None
    role_in_relation_to_referrals: Optional[str] = None
    email_confidential: Optional[str] = None

class IFLRDiversityEquityInclusion(BaseModel):
    key_contact: Optional[str] = None
    email_confidential: Optional[str] = None
    diversity_statistics: Optional[str] = None
    description: Optional[str] = None

class IFLRAwardsNetZero(BaseModel):
    key_contact: Optional[str] = None
    email_confidential: Optional[str] = None
    description: Optional[str] = None
    why_impactful_innovative: Optional[str] = None

class IFLRAwardsInnovation(BaseModel):
    key_contact: Optional[str] = None
    email_confidential: Optional[str] = None
    is_internal_or_client_facing: Optional[str] = None
    description: Optional[str] = None
    key_achievements: Optional[str] = None

class IFLRKeyPublishableClient(BaseModel):
    client_name: Optional[str] = None
    relationship_partner: Optional[str] = None

class IFLRSection2PracticeOverview(BaseModel):
    practice_overview_text: Optional[str] = None
    hires: List[IFLRHire] = Field(default_factory=list)
    departures_and_retirements: List[IFLRDeparture] = Field(default_factory=list)
    referral_work: List[IFLRReferralWork] = Field(default_factory=list)
    diversity_equity_and_inclusion: Optional[IFLRDiversityEquityInclusion] = None
    iflr_awards_net_zero: Optional[IFLRAwardsNetZero] = None
    iflr_awards_tech_innovation: Optional[IFLRAwardsInnovation] = None
    iflr_awards_pro_bono: Optional[IFLRAwardsInnovation] = None
    key_publishable_clients: List[IFLRKeyPublishableClient] = Field(default_factory=list)
    feedback: Optional[str] = None

class IFLRDeal(BaseModel):
    deal_number: Optional[int] = None
    is_confidential: Optional[bool] = None
    deal_name: Optional[str] = None
    is_iflr_award_candidate: Optional[bool] = None
    clients_advised: Optional[str] = None
    clients_role: Optional[str] = None
    date_closed_or_milestones: Optional[str] = None
    value_usd: Optional[float] = None
    is_cross_border: Optional[bool] = None
    jurisdictions_involved: Optional[str] = None
    lead_or_local_counsel: Optional[str] = None
    lead_partners: Optional[str] = None
    senior_associates_key_roles: Optional[str] = None
    other_law_firms_your_side: Optional[str] = None
    other_law_firms_opposite_side: Optional[str] = None
    brief_description: Optional[str] = None
    why_legally_innovative_challenging: Optional[str] = None

class IFLRDealDidNotAdviseOn(BaseModel):
    deal_description: Optional[str] = None

class IFLRSection3DealHighlights(BaseModel):
    deals: List[IFLRDeal] = Field(default_factory=list)
    deal_firm_did_not_advise_on: Optional[IFLRDealDidNotAdviseOn] = None

class ITRRecruitment(BaseModel):
    name: Optional[str] = None
    job_title: Optional[str] = None
    recruitment_specialisms: Optional[str] = None
    hired_from: Optional[str] = None
    date_hired: Optional[str] = None

class ITRDeparture(BaseModel):
    name: Optional[str] = None
    job_title: Optional[str] = None
    specialisms: Optional[str] = None
    departed_to: Optional[str] = None
    date_departed: Optional[str] = None

class ITRTalentMovements(BaseModel):
    recruitment: List[ITRRecruitment] = Field(default_factory=list)
    departures: List[ITRDeparture] = Field(default_factory=list)

class ITRKeyPractitioner(BaseModel):
    name: Optional[str] = None
    job_title: Optional[str] = None
    specialisms: Optional[str] = None
    email: Optional[str] = None

class ITRRisingStar(BaseModel):
    name: Optional[str] = None
    job_title: Optional[str] = None
    specialisms: Optional[str] = None
    email: Optional[str] = None
    qualifying_year: Optional[int] = None

class ITRPractitionerProfiles(BaseModel):
    key_practitioners: List[ITRKeyPractitioner] = Field(default_factory=list)
    rising_stars: List[ITRRisingStar] = Field(default_factory=list)

class ITRCorporateSocialResponsibility(BaseModel):
    esg_programmes: Optional[str] = None
    dei_programmes: Optional[str] = None

class ITRGlobalExecutiveMobility(BaseModel):
    global_executive_mobility: Optional[str] = None
    corporate_incentives: Optional[str] = None

class ITRTechnologySolutions(BaseModel):
    tax_technology_solutions: Optional[str] = None
    transfer_pricing_technology_solutions: Optional[str] = None

class ITRTaxPolicyAndProBono(BaseModel):
    tax_policy_advising: Optional[str] = None
    pro_bono_work: Optional[str] = None

class ITRNarrativeOverviews(BaseModel):
    general_practice_overview: Optional[str] = None
    corporate_social_responsibility: Optional[ITRCorporateSocialResponsibility] = None
    global_executive_mobility_and_incentives: Optional[ITRGlobalExecutiveMobility] = None
    technology_solutions: Optional[ITRTechnologySolutions] = None
    tax_policy_and_pro_bono: Optional[ITRTaxPolicyAndProBono] = None
    compliance_and_reporting: Optional[str] = None
    innovation: Optional[str] = None

class ITRSection1PracticeDevelopments(BaseModel):
    talent_movements: Optional[ITRTalentMovements] = None
    practitioner_profiles: Optional[ITRPractitionerProfiles] = None
    narrative_overviews: Optional[ITRNarrativeOverviews] = None

class ITRMatter(BaseModel):
    matter_number: Optional[int] = None
    matter_name: Optional[str] = None
    is_confidential: Optional[bool] = None
    consider_for_impact_award: Optional[bool] = None
    categories: List[str] = Field(default_factory=list)
    specialisms: List[str] = Field(default_factory=list)
    is_cross_border: Optional[bool] = None
    jurisdictions_involved: Optional[str] = None
    date_completed_or_updated: Optional[str] = None
    transaction_value_usd: Optional[float] = None
    clients_advised: Optional[str] = None
    lead_practitioners: Optional[str] = None
    other_practitioners_with_notable_roles: Optional[str] = None
    firms_role_on_matter: Optional[str] = None
    other_companies_involved_and_roles: Optional[str] = None
    description_of_matter: Optional[str] = None
    why_highlighted: Optional[str] = None

class ITRSection2DealAndCaseHighlights(BaseModel):
    matters: List[ITRMatter] = Field(default_factory=list)

class AnchorSubmission(BaseSubmission):
    A_preliminary_information: Optional[PreliminaryInformation] = None
    B_department_information: Optional[DepartmentInfoFeature] = None
    C_feedback: Optional[FeedbackFeature] = None
    D_publishable_information: Optional[PublishableInformationFeature] = None
    E_confidential_information: Optional[ConfidentialInformationFeature] = None
    document_metadata: Optional[DocumentMetadata] = None
    firm_details: Optional[FirmDetails] = None
    iflr_section_1_lawyers: Optional[IFLRSection1Lawyers] = None
    iflr_section_2_practice_overview: Optional[IFLRSection2PracticeOverview] = None
    iflr_section_3_deal_highlights: Optional[IFLRSection3DealHighlights] = None
    itr_section_1_practice_developments: Optional[ITRSection1PracticeDevelopments] = None
    itr_section_2_deal_and_case_highlights: Optional[ITRSection2DealAndCaseHighlights] = None
