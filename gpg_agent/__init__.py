"""
Point d'entrée du package gpg_agent exposant root_agent pour Google ADK et Cloud Run.
"""
# Expose le module agent.py à la commande `adk web` et `adk run`
from . import agent
