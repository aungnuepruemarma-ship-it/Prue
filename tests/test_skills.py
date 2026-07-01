from ncp.memory.skills import SkillLibrary, SkillExtractor

def test_skill_extraction_promotes_repeated_pattern():
    lib = SkillLibrary()
    extractor = SkillExtractor(threshold=2)
    events = [
        {"candidate": "update_entity"},
        {"candidate": "query_memory"},
        {"candidate": "update_entity"},
        {"candidate": "query_memory"},
    ]
    extractor.promote(lib, events)
    assert lib.skills
