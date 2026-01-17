"""
Supabase client configuration for FastAPI.

Provides dependency injection for Supabase client instances.
"""

import os
from functools import lru_cache
from typing import Generator

from supabase import Client, create_client

from src.utils.logging import get_logger

logger = get_logger(__name__)


@lru_cache
def get_supabase_url() -> str:
    """Get Supabase URL from environment."""
    url = os.getenv("SUPABASE_URL")
    if not url:
        raise ValueError("SUPABASE_URL environment variable is required")
    return url


@lru_cache
def get_supabase_anon_key() -> str:
    """Get Supabase anon key from environment."""
    key = os.getenv("SUPABASE_ANON_KEY")
    if not key:
        raise ValueError("SUPABASE_ANON_KEY environment variable is required")
    return key


@lru_cache
def get_supabase_service_key() -> str:
    """Get Supabase service role key from environment."""
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not key:
        raise ValueError("SUPABASE_SERVICE_ROLE_KEY environment variable is required")
    return key


def get_supabase_client() -> Generator[Client, None, None]:
    """
    Get a Supabase client for authenticated requests.

    Uses the anon key - suitable for user-authenticated operations.

    Yields:
        Supabase client instance.
    """
    client = create_client(
        get_supabase_url(),
        get_supabase_anon_key(),
    )
    try:
        yield client
    finally:
        # Supabase client doesn't need explicit cleanup
        pass


def get_supabase_admin_client() -> Generator[Client, None, None]:
    """
    Get a Supabase admin client for privileged operations.

    Uses the service role key - bypasses RLS policies.
    Use with caution, only for server-side operations.

    Yields:
        Supabase admin client instance.
    """
    client = create_client(
        get_supabase_url(),
        get_supabase_service_key(),
    )
    try:
        yield client
    finally:
        pass
