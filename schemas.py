from decimal import Decimal
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


# --- 1. Expansion & Découverte Web ---


class SearchDork(BaseModel):
    query_string: str = Field(
        ...,
        description="Chaîne de recherche formatée avec opérateurs booléens (Google Dork)",
    )
    strategic_rationale: str = Field(
        ...,
        description="Angle métier ciblé (ex : Mécénat Outdoor, Insertion Jeunes QPV)",
    )
    priority_level: Literal["HAUTE", "MOYENNE", "EXPLORATION"] = Field(
        ..., description="Niveau de priorité d'exécution de la requête"
    )


class SearchQueryMatrix(BaseModel):
    generated_dorks: List[SearchDork] = Field(
        ..., description="Matrice de requêtes de recherche Google générées"
    )
    execution_horizon_year: int = Field(
        default=2026, description="Année d'exécution temporelle de référence"
    )


class DiscoveredUrlCandidate(BaseModel):
    url: str = Field(..., description="URL brute extraite du radar web")
    page_title: str = Field(..., description="Titre de la page web ou du document")
    discovery_query: str = Field(..., description="Dork ayant permis la découverte")
    funder_guess: Optional[str] = Field(
        None, description="Nom estimé de l'organisme financeur"
    )
    snippet: str = Field(..., description="Extrait textuel contextuel (snippet)")


class DiscoveredUrlList(BaseModel):
    candidates: List[DiscoveredUrlCandidate] = Field(
        ..., description="Liste des opportunités brutes découvertes"
    )


# --- 2. Ingestion & Screening AAP ---


class AAPRawMetadata(BaseModel):
    id: str = Field(..., description="Identifiant unique SHA-256 de l'AAP")
    source_url: str = Field(..., description="URL canonique du portail source")
    title: str = Field(..., min_length=5, description="Intitulé officiel de l'AAP")
    funder_name: str = Field(..., min_length=2, description="Nom du financeur")
    extracted_grant_ceiling: Optional[Decimal] = Field(
        None, description="Plafond maximal de subvention demandé (en EUR)"
    )
    required_annual_budget_ceiling: Optional[Decimal] = Field(
        None, description="Plafond de budget annuel de l'association requis (en EUR)"
    )
    submission_deadline: str = Field(..., description="Date limite de dépôt (AAAA-MM-JJ)")
    geographic_scope: str = Field(..., description="Périmètre géographique éligible")
    raw_guidelines_text: str = Field(..., description="Texte brut extrait du règlement")

    @field_validator(
        "extracted_grant_ceiling",
        "required_annual_budget_ceiling",
        mode="before",
    )
    @classmethod
    def convert_to_decimal(cls, value: Optional[object]) -> Optional[Decimal]:
        if value is None or value == "":
            return None
        return Decimal(str(value))


class AAPStrategicScore(BaseModel):
    aap_id: str = Field(..., description="Identifiant SHA-256 de l'AAP évalué")
    strategic_fit_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Score d'adéquation thématique avec Gravir Pour Grandir (0.0 à 1.0)",
    )
    primary_axis: Literal[
        "QPV_Inclusion",
        "Sport_Montagne_Depassement",
        "Insertion_Mentorat",
    ] = Field(..., description="Axe stratégique prédominant")
    alignment_reasoning: str = Field(
        ..., max_length=500, description="Synthèse explicative du score accordé"
    )
    recommended_for_selection: bool = Field(
        ..., description="Indicateur d'éligibilité qualifiée"
    )


# --- 3. Structure Formulaire & Rédaction ---


class FormFieldConstraint(BaseModel):
    field_id: str = Field(..., description="Identifiant unique du champ de formulaire")
    question_label: str = Field(..., description="Intitulé de la question posée")
    character_limit: Optional[int] = Field(
        None, description="Nombre maximal de caractères autorisés"
    )
    expected_content_type: str = Field(
        "narrative", description="Type de contenu attendu (narrative | budget | metrics)"
    )


class FormStructureDefinition(BaseModel):
    aap_id: str = Field(..., description="Identifiant de l'AAP rattaché")
    form_fields: List[FormFieldConstraint] = Field(
        ..., description="Liste des champs du formulaire de candidature"
    )
    mandatory_attachments: List[str] = Field(
        default_factory=list, description="Pièces justificatives obligatoires"
    )


class NarrativeResponseItem(BaseModel):
    field_id: str = Field(..., description="Identifiant du champ ciblé")
    question_label: str = Field(..., description="Intitulé exact de la question")
    final_text: str = Field(..., description="Texte rédigé pour le champ")
    character_count: int = Field(..., description="Nombre exact de caractères du texte")
    referenced_partners: List[str] = Field(
        default_factory=list, description="Partenaires cités dans la réponse"
    )


# --- 4. Chiffrage Budgétaire Déterministe ---


class ExpenseLineItem(BaseModel):
    category: Literal[
        "Transport_Train",
        "Hebergement_Refuge",
        "Encadrement_Guide",
        "Equipement_Pret",
        "Suivi_Mentorat",
    ] = Field(..., description="Poste budgétaire répertorié")
    unit_cost_euro: Decimal = Field(..., description="Coût unitaire unitaire TTC en EUR")
    units_count: int = Field(..., description="Quantité d'unités")
    total_cost_euro: Decimal = Field(..., description="Montant total de la ligne en EUR")
    grant_allocation_euro: Decimal = Field(
        ..., description="Quote-part financée par la subvention"
    )
    association_share_euro: Decimal = Field(
        ..., description="Quote-part financée par l'association (autofinancement)"
    )


class FinancialApplicationPlan(BaseModel):
    aap_id: str = Field(..., description="Identifiant de l'AAP rattaché")
    total_project_cost: Decimal = Field(..., description="Coût total du projet (EUR)")
    total_grant_requested: Decimal = Field(..., description="Subvention demandée (EUR)")
    total_self_financing: Decimal = Field(..., description="Autofinancement global (EUR)")
    budget_breakdown: List[ExpenseLineItem] = Field(
        ..., description="Ventilation détaillée des dépenses"
    )


class FullProposalDocument(BaseModel):
    aap_id: str = Field(..., description="Identifiant unique du dossier")
    project_title: str = Field(..., description="Titre du projet rédigé")
    executive_pitch: str = Field(..., description="Synthèse exécutive du projet")
    narrative_sections: List[NarrativeResponseItem] = Field(
        ..., description="Ensemble des réponses narratives rédigées"
    )
    financial_plan: FinancialApplicationPlan = Field(
        ..., description="Plan financier et ventilation budgétaire"
    )
