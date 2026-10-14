from typing import Literal
from pydantic import BaseModel, Field

FunderArchetype = Literal[
    "FONDATION_BANCAIRE_ECHELLE",
    "FONDS_OUTDOOR_SPORT",
    "ENTREPRISE_RSE_RH",
    "SUBVENTION_PUBLIQUE"
]

ProgramTrack = Literal[
    "ALPINISME_48K",
    "ALPINISME_COMPLET_54K",
    "VOILE_48K",
    "PASSAGE_ECHELLE_3_ANS"
]

class SemanticRoutingDecision(BaseModel):
    aap_id: str = Field(
        default="aucun_aap_retenu",
        description="Identifiant court sans espace (ex: fondation_decathlon_2026). Mettre 'aucun_aap_retenu' si aucun AAP n'est éligible."
    )
    funder_name: str = Field(
        default="Aucun",
        description="Nom exact du financeur."
    )
    official_aap_url: str = Field(
        default="https://",
        description="URL officielle complète (https://...) de la page de l'appel à projets."
    )
    deadline_iso: str = Field(
        default="EXPIRED",
        description="Date limite EXACTE de dépôt au format strict YYYY-MM-DD (ex: '2026-11-30'). Mettre 'EXPIRED' si aucune opportunité valide."
    )
    requires_unavailable_consortium_or_status: bool = Field(
        default=False,
        description="True si l'AAP exige un statut que GPG n'a pas (collectivité, CROS/CDOS, consortium obligatoire)."
    )
    requires_exclusive_ase_or_non_qpv_public: bool = Field(
        default=False,
        description="True si l'AAP cible EXCLUSIVEMENT l'Aide Sociale à l'Enfance (ASE)."
    )
    funder_archetype: FunderArchetype = Field(
        default="ENTREPRISE_RSE_RH",
        description="Catégorie du financeur."
    )
    recommended_track: ProgramTrack = Field(
        default="ALPINISME_48K",
        description="Grille budgétaire GPG la plus adaptée."
    )
    requested_grant_euro: int = Field(
        default=15000,
        ge=0,
        le=100000,
        description="Montant sollicité en euros entiers (entre 5000 et 30000, mettre 15000 par défaut si le plafond n'est pas précisé, ou 0 si aucun AAP retenu)."
    )
    funder_key_priorities: list[str] = Field(
        default_factory=lambda: ["insertion", "jeunesse", "sport"],
        description="Les 3 priorités lexicales exactes du financeur."
    )
    go_recommendation: bool = Field(
        default=False,
        description="True uniquement si tous les critères d'éligibilité, de public QPV et de date sont respectés."
    )
