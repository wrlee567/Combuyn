"""Cross-dialect column types.

Production runs on PostgreSQL (JSONB); the test suite runs on SQLite. These
helpers let the same models target both: JSONB where available, generic JSON
otherwise.
"""

from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB

# Use JSONB on Postgres for indexable, queryable dynamic payloads
# (e.g. TPRM questionnaire data in later iterations); fall back to JSON on SQLite.
JSONBType = JSON().with_variant(JSONB(), "postgresql")
