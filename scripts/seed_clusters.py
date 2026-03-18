"""Initialize the six seed cluster centroids by embedding representative text for each archetype.

Run once after Supabase schema is created.
"""

SEED_ARCHETYPES = [
    {
        "name": "The Gate",
        "glyph_id": "gate",
        "tags": ["dream", "threshold", "migration"],
        "representative_text": (
            "A dream about crossing a threshold. The door that appears when you are"
            " ready to leave. Migration, departure, the moment before."
        ),
    },
    {
        "name": "What the Body Keeps",
        "glyph_id": "body",
        "tags": ["body", "water", "morning"],
        "representative_text": (
            "The body remembering what the mind forgot. Swimming before sunrise."
            " The tide-like return of physical knowledge."
        ),
    },
    {
        "name": "The Table",
        "glyph_id": "table",
        "tags": ["food", "connection", "social"],
        "representative_text": (
            "Dinner with everyone. The communal center. Being fed and feeding."
            " Gathering around what sustains."
        ),
    },
    {
        "name": "The Silence",
        "glyph_id": "silence",
        "tags": ["silence", "solitude"],
        "representative_text": (
            "The quiet that arrives when you stop speaking. Solitude as presence,"
            " not absence. The mark that holds space."
        ),
    },
    {
        "name": "The Root",
        "glyph_id": "root",
        "tags": ["memory", "family", "language"],
        "representative_text": (
            "Your grandmother's kitchen. The word for tooth in a language you"
            " half-remember. What the family line carries forward."
        ),
    },
    {
        "name": "The Hand",
        "glyph_id": "hand",
        "tags": ["writing", "fieldwork"],
        "representative_text": (
            "The act of writing it down. Fieldwork. Making a mark that outlasts"
            " the moment. The trace of attention."
        ),
    },
]
