"""Encounters: "Where can I catch it?" """


def test_encounters_link_resolves(api):
    # The docs describe this as a path; the live API returns a full URL. Either way it must resolve.
    psyduck = api.json("/pokemon/psyduck")
    link = psyduck["location_area_encounters"]
    assert link.endswith("/pokemon/54/encounters")
    assert isinstance(api.json(link), list)


def test_wild_encounter_data_is_valid(api):
    encounters = api.json("/pokemon/psyduck/encounters")
    assert len(encounters) > 0
    for area in encounters:
        for version in area["version_details"]:
            # max_chance is the total across all methods (walk + surf + ...), so it can exceed 100.
            assert version["max_chance"] == sum(d["chance"] for d in version["encounter_details"])
            for detail in version["encounter_details"]:
                assert 1 <= detail["min_level"] <= detail["max_level"] <= 100, area["location_area"]["name"]
                assert 0 < detail["chance"] <= 100


def test_psyduck_can_be_surfed_for_in_diamond(api):
    encounters = api.json("/pokemon/psyduck/encounters")
    diamond_methods = {
        (area["location_area"]["name"], detail["method"]["name"])
        for area in encounters
        for version in area["version_details"] if version["version"]["name"] == "diamond"
        for detail in version["encounter_details"]
    }
    assert ("eterna-city-area", "surf") in diamond_methods


def test_where_to_catch_giratina_in_platinum(api):
    encounters = api.json("/pokemon/giratina-altered/encounters")
    platinum_areas = {
        area["location_area"]["name"]
        for area in encounters
        if any(v["version"]["name"] == "platinum" for v in area["version_details"])
    }
    assert platinum_areas == {"distortion-world-area", "turnback-cave-after-pillar-3"}


def test_pokemon_with_no_wild_encounters_returns_empty_list(api):
    # Mega forms can't be caught; they should return an empty list, not an error.
    assert api.json("/pokemon/gengar-mega/encounters") == []
