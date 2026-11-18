"""JSON Schemas for the response shapes the tests depend on.

These cover the fields a client actually uses, not every field the API returns.
Extra fields are allowed, so new API additions don't break the suite.
"""

NAMED_RESOURCE = {
    "type": "object",
    "required": ["name", "url"],
    "properties": {"name": {"type": "string", "minLength": 1}, "url": {"type": "string", "pattern": "^https://pokeapi\\.co/api/v2/"}},
}

POKEMON = {
    "type": "object",
    "required": ["id", "name", "height", "weight", "base_experience", "is_default", "order",
                 "types", "abilities", "stats", "moves", "species", "sprites", "forms", "location_area_encounters"],
    "properties": {
        "id": {"type": "integer", "minimum": 1},
        "name": {"type": "string", "pattern": "^[a-z0-9-]+$"},
        "height": {"type": "integer", "minimum": 1},
        "weight": {"type": "integer", "minimum": 1},
        "is_default": {"type": "boolean"},
        "types": {
            "type": "array", "minItems": 1, "maxItems": 2,
            "items": {"type": "object", "required": ["slot", "type"],
                      "properties": {"slot": {"type": "integer"}, "type": NAMED_RESOURCE}},
        },
        "abilities": {
            "type": "array", "minItems": 1,
            "items": {"type": "object", "required": ["ability", "is_hidden", "slot"],
                      "properties": {"ability": NAMED_RESOURCE, "is_hidden": {"type": "boolean"}, "slot": {"type": "integer"}}},
        },
        "stats": {
            "type": "array", "minItems": 6, "maxItems": 6,
            "items": {"type": "object", "required": ["base_stat", "effort", "stat"],
                      "properties": {"base_stat": {"type": "integer", "minimum": 1, "maximum": 255},
                                     "effort": {"type": "integer", "minimum": 0, "maximum": 3},
                                     "stat": NAMED_RESOURCE}},
        },
        "species": NAMED_RESOURCE,
        "moves": {"type": "array"},
        "sprites": {"type": "object", "required": ["front_default"]},
        "location_area_encounters": {"type": "string"},
    },
}

SPECIES = {
    "type": "object",
    "required": ["id", "name", "generation", "is_legendary", "is_mythical", "egg_groups",
                 "evolution_chain", "varieties", "genera"],
    "properties": {
        "id": {"type": "integer", "minimum": 1},
        "is_legendary": {"type": "boolean"},
        "is_mythical": {"type": "boolean"},
        "generation": NAMED_RESOURCE,
        "egg_groups": {"type": "array", "minItems": 1, "items": NAMED_RESOURCE},
        "evolution_chain": {"type": "object", "required": ["url"]},
        "varieties": {
            "type": "array", "minItems": 1,
            "items": {"type": "object", "required": ["is_default", "pokemon"],
                      "properties": {"is_default": {"type": "boolean"}, "pokemon": NAMED_RESOURCE}},
        },
    },
}

PAGE = {
    "type": "object",
    "required": ["count", "next", "previous", "results"],
    "properties": {
        "count": {"type": "integer", "minimum": 0},
        "next": {"type": ["string", "null"]},
        "previous": {"type": ["string", "null"]},
        "results": {"type": "array", "items": NAMED_RESOURCE},
    },
}

NOT_FOUND = {
    "type": "object",
    "required": ["status", "message"],
    "properties": {"status": {"const": 404}, "message": {"const": "Not Found"}},
}
