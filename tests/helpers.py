"""Constants and small pure helpers for reading PokéAPI responses the way a player would."""

BASE_URL = "https://pokeapi.co/api/v2"
TIMEOUT = 15  # seconds


def stat_map(pokemon: dict) -> dict[str, int]:
    """{'hp': 60, 'attack': 65, ...} from a /pokemon response."""
    return {s["stat"]["name"]: s["base_stat"] for s in pokemon["stats"]}


def base_stat_total(pokemon: dict) -> int:
    return sum(stat_map(pokemon).values())


def type_names(pokemon: dict) -> list[str]:
    return [t["type"]["name"] for t in sorted(pokemon["types"], key=lambda t: t["slot"])]


def names(resources: list[dict]) -> set[str]:
    """Names from a list of NamedAPIResource dicts."""
    return {r["name"] for r in resources}


def damage_multiplier(attacking_type: str, defending_types: dict[str, dict]) -> float:
    """Damage multiplier of an attack type against a Pokémon's types.

    `defending_types` maps each defending type name to its /type/{name} response.
    """
    multiplier = 1.0
    for type_data in defending_types.values():
        rel = type_data["damage_relations"]
        if attacking_type in names(rel["no_damage_from"]):
            multiplier *= 0
        elif attacking_type in names(rel["double_damage_from"]):
            multiplier *= 2
        elif attacking_type in names(rel["half_damage_from"]):
            multiplier *= 0.5
    return multiplier


def find_chain_link(link: dict, species: str) -> dict | None:
    """Depth-first search of an evolution chain for a species' ChainLink."""
    if link["species"]["name"] == species:
        return link
    for child in link["evolves_to"]:
        found = find_chain_link(child, species)
        if found:
            return found
    return None


def default_evolution_detail(link: dict) -> dict:
    """The one evolution method the API flags `is_default` for a ChainLink.

    Some species gained extra methods in later games (e.g. Linking Cord), so a link can have
    several details. The docs say exactly one is the default; anything else is a data error.
    """
    defaults = [d for d in link["evolution_details"] if d.get("is_default")]
    assert len(defaults) == 1, (
        f"{link['species']['name']}: expected exactly 1 default evolution method, found {len(defaults)}")
    return defaults[0]


def chain_species(link: dict) -> list[str]:
    """All species names in an evolution chain, in depth-first order."""
    out = [link["species"]["name"]]
    for child in link["evolves_to"]:
        out += chain_species(child)
    return out
