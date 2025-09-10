from la.parsers import parse_llc1, parse_con29

def test_llc1_parses_charges():
    llc = parse_llc1("This is in a Conservation Area and a Listed Building.")
    types = {c.charge_type for c in llc.charges if c.present}
    assert "ConservationArea" in types
    assert "ListedBuilding" in types

def test_con29_flags():
    c = parse_con29("Enforcement notice: yes. Contaminated land: yes. Abutting highway adopted: no. Flood Zone 3. CIL outstanding. Radon affected. Building Regulations completion: missing.")
    assert c.enforcement_notices_present is True
    assert c.contaminated_land_designation is True
    assert c.roads_footways.abutting_highway_adopted is False
    assert c.flood_zone == "3"
    assert c.cil_outstanding is True
    assert c.radon_affected is True
    assert c.building_regs_completion_present is False
