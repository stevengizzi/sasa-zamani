"""Supabase client initialization and database queries."""

import json

from supabase import Client, create_client

from app.config import get_settings

_client: Client | None = None


def get_db() -> Client:
    """Return the Supabase client singleton."""
    global _client
    if _client is None:
        settings = get_settings()
        _client = create_client(settings.supabase_url, settings.supabase_key)
    return _client


def reset_client() -> None:
    """Reset the client singleton (used by tests)."""
    global _client
    _client = None


def ensure_schema() -> None:
    """Verify database schema exists by probing tables. Idempotent.

    The actual schema is created via scripts/init_supabase.sql (run in the
    Supabase SQL editor or CLI).  This function validates the tables are
    present at startup so the app fails fast with a clear message.
    """
    client = get_db()
    for table in ("clusters", "events", "myths"):
        try:
            client.table(table).select("id", count="exact").limit(0).execute()
        except Exception as exc:
            raise RuntimeError(
                f"Table '{table}' not found. Run scripts/init_supabase.sql in "
                f"the Supabase SQL editor to create the schema."
            ) from exc


def check_connection() -> bool:
    """Return True if the database is reachable, False otherwise."""
    try:
        client = get_db()
        client.table("clusters").select("id", count="exact").limit(0).execute()
        return True
    except Exception:
        return False


def insert_event(
    label: str,
    note: str,
    participant: str,
    embedding: list[float],
    source: str,
    cluster_id: str | None = None,
    xs: float | None = None,
) -> dict:
    """Insert a new event and return the inserted row."""
    data: dict = {
        "label": label,
        "note": note,
        "participant": participant,
        "source": source,
        "embedding": embedding,
    }
    if cluster_id is not None:
        data["cluster_id"] = cluster_id
    if xs is not None:
        data["xs"] = xs
    response = get_db().table("events").insert(data).execute()
    return response.data[0]


def update_event_xs(event_id: str, xs: float) -> None:
    """Update the xs value for an existing event (used by backfill)."""
    get_db().table("events").update({"xs": xs}).eq("id", event_id).execute()


def get_events(participant: str | None = None) -> list[dict]:
    """Return events without embedding field. Optionally filter by participant (case-insensitive)."""
    query = get_db().table("events").select(
        "id, created_at, event_date, label, note, participant, source, cluster_id, xs, day"
    )
    if participant is not None:
        query = query.ilike("participant", participant)
    return query.execute().data


def get_clusters() -> list[dict]:
    """Return clusters without centroid embedding."""
    return (
        get_db()
        .table("clusters")
        .select("id, name, glyph_id, myth_text, myth_version, event_count, last_updated, is_seed")
        .execute()
        .data
    )


def insert_cluster(
    name: str,
    centroid_embedding: list[float],
    is_seed: bool = False,
    glyph_id: str | None = None,
) -> dict:
    """Insert a new cluster and return the inserted row."""
    data: dict = {
        "name": name,
        "centroid": centroid_embedding,
        "is_seed": is_seed,
    }
    if glyph_id is not None:
        data["glyph_id"] = glyph_id
    response = get_db().table("clusters").insert(data).execute()
    return response.data[0]


def cluster_exists(name: str) -> bool:
    """Return True if a cluster with the given name exists."""
    response = (
        get_db()
        .table("clusters")
        .select("id", count="exact")
        .eq("name", name)
        .limit(0)
        .execute()
    )
    return response.count > 0


def _parse_centroid(raw: str | list[float]) -> list[float]:
    """Parse a pgvector centroid value into a Python list of floats.

    Supabase returns pgvector columns as JSON strings; this ensures callers
    always receive a native list.
    """
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        return json.loads(raw)
    raise TypeError(f"centroid must be a list or str, got {type(raw).__name__}")


def get_cluster_centroids() -> list[tuple[str, list[float]]]:
    """Return list of (cluster_id, centroid) tuples for cluster assignment."""
    rows = get_db().table("clusters").select("id, centroid").execute().data
    return [(row["id"], _parse_centroid(row["centroid"])) for row in rows]


def increment_event_count(cluster_id: str) -> None:
    """Increment event_count for a cluster by 1 (atomic via Postgres RPC)."""
    get_db().rpc("increment_event_count", {"cid": cluster_id}).execute()


def get_cluster_by_id(cluster_id: str) -> dict | None:
    """Return a single cluster by ID, or None if not found."""
    response = (
        get_db()
        .table("clusters")
        .select("id, name, glyph_id, myth_text, myth_version, event_count, last_updated, is_seed")
        .eq("id", cluster_id)
        .execute()
    )
    if response.data:
        return response.data[0]
    return None


def get_cluster_events_labels(cluster_id: str) -> list[str]:
    """Return event labels for a cluster."""
    response = (
        get_db()
        .table("events")
        .select("label")
        .eq("cluster_id", cluster_id)
        .execute()
    )
    return [row["label"] for row in response.data]


def get_latest_myth(cluster_id: str) -> dict | None:
    """Return the most recent myth entry for a cluster, or None if none exist."""
    response = (
        get_db()
        .table("myths")
        .select("*")
        .eq("cluster_id", cluster_id)
        .order("version", desc=True)
        .limit(1)
        .execute()
    )
    if response.data:
        return response.data[0]
    return None


def insert_myth(cluster_id: str, text: str, event_count: int, version: int) -> dict:
    """Insert a new myth entry and return the inserted row."""
    data = {
        "cluster_id": cluster_id,
        "text": text,
        "event_count_at_generation": event_count,
        "version": version,
    }
    response = get_db().table("myths").insert(data).execute()
    return response.data[0]


def update_cluster_myth(cluster_id: str, myth_text: str) -> None:
    """Update a cluster's myth_text field."""
    get_db().table("clusters").update({"myth_text": myth_text}).eq("id", cluster_id).execute()
