"""Shared Anthropic client setup.

Loads ANTHROPIC_API_KEY from .env and returns a configured client.
Every example imports `client` from here so we don't repeat setup boilerplate.
"""
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()
