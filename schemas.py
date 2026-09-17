from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal

# ==========================================
# 1. CONTRATS POUR L'EXPANSION ET LE RADAR
# ==========================================

class SearchDork(BaseModel):
    query_string: str = Field(..., description="Chaîne de recherche formatée avec opérateurs booléens")
    strategic_rationale: str = Field(..., description="Angle métier ciblé (ex: Mécénat Outdoor, Insertion Jeunes)")
    priority_level: Literal["HAUTE", "MOYENNE", "EXPLORATION"]

class SearchQueryMatrix(BaseModel):
    generated_dorks: List[SearchDork]
    execution_horizon_year: int = Field(default=2026)

class DiscoveredUrlCandidate(BaseModel):
    url: str
    page_title: str
    discovery_query: str
    funder_guess: Optional[str] = None
    snippet: str

class DiscoveredUrlList(BaseModel):
    candidates: List[DiscoveredUrlCandidate]

# ==========================================
# 2. CONTRATS D'ENTRÉE & SCREENING
# ==========================================

class ExtractedAAPAttributes(BaseModel):
    extracted_grant_ceiling: Optional[Decimal] = None
    required_annual_budget_ceiling: Optional[Decimal] = None
    submission_deadline: str
    geographic_scope: str

class AAPRawMetadata(BaseModel):
    id: str = Field(..., description="Identifiant unique SHA-256 de l'AAP")
    source_url: str = Field(..., description="URL canonique du portail source")
    title: str = Field(..., min_length=5)
    funder_name: str = Field(..., min_length=2)
    extracted_grant_ceiling: Optional[Decimal] = None
    required_annual_budget_ceiling: Optional[Decimal] = None
    submission_deadline: str
    geographic_scope: str
    raw_guidelines_text: str

    @field_validator("extracted_grant_ceiling", "required_annual_budget_ceiling", mode="before")
    @classmethod
    def convert_to_decimal(cls, value):
        return Decimal(str(value)) if value is not None else None

class AAPStrategicScore(BaseModel):
    aap_id: str
    strategic_fit_score: float = Field(..., ge=0.0, le=1.0, description="Score d'adéquation thématique globale")
    primary_axis: Literal["QPV_Inclusion", "Sport_Montagne_Depassement", "Insertion_Mentorat"]
    alignment_reasoning: str = Field(..., max_length=500)
    recommended_for_selection: bool

# ==========================================
# 3. CONTRATS DE FORMULAIRE & RÉDACTION NARRATIVE
# ==========================================

class FormFieldConstraint(BaseModel):
    field_id: str
    question_label: str
    character_limit: Optional[int] = Field(None, description="Contrainte de longueur stricte")
    expected_content_type: str = Field("narrative", description="narrative | budget | metrics")

class FormStructureDefinition(BaseModel):
    aap_id: str
    form_fields: List[FormFieldConstraint]
    mandatory_attachments: List[str]

class NarrativeResponseItem(BaseModel):
    field_id: str
    question_label: str
    final_text: str
    character_count: int
    referenced_partners: List[str]

# ==========================================
# 4. CONTRATS BUDGÉTAIRES DÉTERMINISTES
# ==========================================

class ExpenseLineItem(BaseModel):
    category: Literal["Transport_Train", "Hebergement_Refuge", "Encadrement_Guide", "Equipement_Pret", "Suivi_Mentorat"]
    unit_cost_euro: Decimal
    units_count: int
    total_cost_euro: Decimal
    grant_allocation_euro: Decimal
    association_share_euro: Decimal

class FinancialApplicationPlan(BaseModel):
    aap_id: str
    total_project_cost: Decimal
    total_grant_requested: Decimal
    total_self_financing: Decimal
    budget_breakdown: List[ExpenseLineItem]

class FullProposalDocument(BaseModel):
    aap_id: str
    project_title: str
    executive_pitch: str
    narrative_sections: List[NarrativeResponseItem]
    financial_plan: FinancialApplicationPlan