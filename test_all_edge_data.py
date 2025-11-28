#!/usr/bin/env python3
"""
Comprehensive test of ALL NHL Edge API endpoints
Shows all available data structures
"""

from nhlpy import NHLClient
import json
import inspect

def print_section(title):
    print("\n" + "=" * 100)
    print(f"  {title}")
    print("=" * 100)

def print_subsection(title):
    print("\n" + "-" * 100)
    print(f"  {title}")
    print("-" * 100)

def show_data_structure(data, max_chars=1500):
    """Pretty print data structure"""
    if isinstance(data, dict):
        print(f"\n📊 Data Type: Dictionary with {len(data)} keys")
        print(f"🔑 Keys: {list(data.keys())}")
        print(f"\n📝 Sample Data:")
        print(json.dumps(data, indent=2)[:max_chars])
        if len(json.dumps(data, indent=2)) > max_chars:
            print(f"\n... (truncated, total size: {len(json.dumps(data))} chars)")
    elif isinstance(data, list):
        print(f"\n📊 Data Type: List with {len(data)} items")
        if len(data) > 0:
            print(f"📝 First item sample:")
            print(json.dumps(data[0], indent=2)[:max_chars])
    else:
        print(f"\n📊 Data Type: {type(data)}")
        print(f"📝 Value: {str(data)[:max_chars]}")

def test_all_edge_endpoints():
    """Test every Edge API endpoint"""
    
    print_section("🏒 NHL EDGE API - COMPLETE DATA CATALOG 🏒")
    
    client = NHLClient()
    
    # Test players
    mcdavid_id = 8478402  # Connor McDavid
    shesterkin_id = 8480045  # Igor Shesterkin
    oilers_team_id = 22  # Edmonton Oilers
    season = "20242025"
    
    results = {
        "working": [],
        "failed": []
    }
    
    # ====================
    # SKATER EDGE ENDPOINTS
    # ====================
    print_section("🏃 SKATER EDGE DATA")
    
    # 1. Skater Detail
    print_subsection("1. skater_detail() - Complete skater Edge stats")
    try:
        data = client.edge.skater_detail(player_id=mcdavid_id, season=season)
        print("✅ SUCCESS")
        show_data_structure(data)
        results["working"].append("skater_detail")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        results["failed"].append(f"skater_detail: {e}")
    
    # 2. CAT Skater Detail
    print_subsection("2. cat_skater_detail() - CAT (Catching and Tackling?) skater stats")
    try:
        # Try with different parameter names
        sig = inspect.signature(client.edge.cat_skater_detail)
        print(f"   Parameters: {list(sig.parameters.keys())}")
        data = client.edge.cat_skater_detail(mcdavid_id, season)
        print("✅ SUCCESS")
        show_data_structure(data)
        results["working"].append("cat_skater_detail")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        results["failed"].append(f"cat_skater_detail: {e}")
    
    # 3. Skater Skating Speed
    print_subsection("3. skater_skating_speed_detail() - Speed tracking data")
    try:
        data = client.edge.skater_skating_speed_detail(player_id=mcdavid_id, season=season)
        print("✅ SUCCESS")
        show_data_structure(data)
        results["working"].append("skater_skating_speed_detail")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        results["failed"].append(f"skater_skating_speed_detail: {e}")
    
    # 4. Skater Skating Distance
    print_subsection("4. skater_skating_distance_detail() - Distance covered data")
    try:
        data = client.edge.skater_skating_distance_detail(player_id=mcdavid_id, season=season)
        print("✅ SUCCESS")
        show_data_structure(data)
        results["working"].append("skater_skating_distance_detail")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        results["failed"].append(f"skater_skating_distance_detail: {e}")
    
    # 5. Skater Shot Speed
    print_subsection("5. skater_shot_speed_detail() - Shot velocity data")
    try:
        data = client.edge.skater_shot_speed_detail(player_id=mcdavid_id, season=season)
        print("✅ SUCCESS")
        show_data_structure(data)
        results["working"].append("skater_shot_speed_detail")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        results["failed"].append(f"skater_shot_speed_detail: {e}")
    
    # 6. Skater Zone Time
    print_subsection("6. skater_zone_time() - Time in offensive/defensive zones")
    try:
        data = client.edge.skater_zone_time(player_id=mcdavid_id, season=season)
        print("✅ SUCCESS")
        show_data_structure(data)
        results["working"].append("skater_zone_time")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        results["failed"].append(f"skater_zone_time: {e}")
    
    # 7. Skater Shot Location
    print_subsection("7. skater_shot_location_detail() - Shot heat map data")
    try:
        data = client.edge.skater_shot_location_detail(player_id=mcdavid_id, season=season)
        print("✅ SUCCESS")
        show_data_structure(data)
        results["working"].append("skater_shot_location_detail")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        results["failed"].append(f"skater_shot_location_detail: {e}")
    
    # 8. Skater Landing
    print_subsection("8. skater_landing() - Skater landing page data")
    try:
        sig = inspect.signature(client.edge.skater_landing)
        print(f"   Parameters: {list(sig.parameters.keys())}")
        data = client.edge.skater_landing(mcdavid_id)
        print("✅ SUCCESS")
        show_data_structure(data)
        results["working"].append("skater_landing")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        results["failed"].append(f"skater_landing: {e}")
    
    # 9. Skater Comparison
    print_subsection("9. skater_comparison() - Compare two skaters")
    try:
        sig = inspect.signature(client.edge.skater_comparison)
        print(f"   Parameters: {list(sig.parameters.keys())}")
        # Compare McDavid vs Draisaitl
        data = client.edge.skater_comparison(mcdavid_id, 8477934, season)
        print("✅ SUCCESS")
        show_data_structure(data)
        results["working"].append("skater_comparison")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        results["failed"].append(f"skater_comparison: {e}")
    
    # ====================
    # GOALIE EDGE ENDPOINTS
    # ====================
    print_section("🥅 GOALIE EDGE DATA")
    
    # 10. Goalie Detail
    print_subsection("10. goalie_detail() - Complete goalie Edge stats")
    try:
        data = client.edge.goalie_detail(player_id=shesterkin_id, season=season)
        print("✅ SUCCESS")
        show_data_structure(data)
        results["working"].append("goalie_detail")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        results["failed"].append(f"goalie_detail: {e}")
    
    # 11. CAT Goalie Detail
    print_subsection("11. cat_goalie_detail() - CAT goalie stats")
    try:
        sig = inspect.signature(client.edge.cat_goalie_detail)
        print(f"   Parameters: {list(sig.parameters.keys())}")
        data = client.edge.cat_goalie_detail(shesterkin_id, season)
        print("✅ SUCCESS")
        show_data_structure(data)
        results["working"].append("cat_goalie_detail")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        results["failed"].append(f"cat_goalie_detail: {e}")
    
    # 12. Goalie 5v5 Detail
    print_subsection("12. goalie_5v5_detail() - 5-on-5 goalie performance")
    try:
        data = client.edge.goalie_5v5_detail(player_id=shesterkin_id, season=season)
        print("✅ SUCCESS")
        show_data_structure(data)
        results["working"].append("goalie_5v5_detail")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        results["failed"].append(f"goalie_5v5_detail: {e}")
    
    # 13. Goalie Save Percentage Detail
    print_subsection("13. goalie_save_percentage_detail() - Save % breakdown")
    try:
        data = client.edge.goalie_save_percentage_detail(player_id=shesterkin_id, season=season)
        print("✅ SUCCESS")
        show_data_structure(data)
        results["working"].append("goalie_save_percentage_detail")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        results["failed"].append(f"goalie_save_percentage_detail: {e}")
    
    # 14. Goalie Shot Location Detail
    print_subsection("14. goalie_shot_location_detail() - Where goalies face shots")
    try:
        data = client.edge.goalie_shot_location_detail(player_id=shesterkin_id, season=season)
        print("✅ SUCCESS")
        show_data_structure(data)
        results["working"].append("goalie_shot_location_detail")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        results["failed"].append(f"goalie_shot_location_detail: {e}")
    
    # 15. Goalie Landing
    print_subsection("15. goalie_landing() - Goalie landing page data")
    try:
        sig = inspect.signature(client.edge.goalie_landing)
        print(f"   Parameters: {list(sig.parameters.keys())}")
        data = client.edge.goalie_landing(shesterkin_id)
        print("✅ SUCCESS")
        show_data_structure(data)
        results["working"].append("goalie_landing")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        results["failed"].append(f"goalie_landing: {e}")
    
    # 16. Goalie Comparison
    print_subsection("16. goalie_comparison() - Compare two goalies")
    try:
        sig = inspect.signature(client.edge.goalie_comparison)
        print(f"   Parameters: {list(sig.parameters.keys())}")
        # Compare Shesterkin vs Hellebuyck
        data = client.edge.goalie_comparison(shesterkin_id, 8476945, season)
        print("✅ SUCCESS")
        show_data_structure(data)
        results["working"].append("goalie_comparison")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        results["failed"].append(f"goalie_comparison: {e}")
    
    # ====================
    # TEAM EDGE ENDPOINTS
    # ====================
    print_section("🏆 TEAM EDGE DATA")
    
    # 17. Team Detail
    print_subsection("17. team_detail() - Complete team Edge stats")
    try:
        data = client.edge.team_detail(team_id=oilers_team_id, season=season)
        print("✅ SUCCESS")
        show_data_structure(data)
        results["working"].append("team_detail")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        results["failed"].append(f"team_detail: {e}")
    
    # 18. Team Skating Speed
    print_subsection("18. team_skating_speed_detail() - Team skating speeds")
    try:
        data = client.edge.team_skating_speed_detail(team_id=oilers_team_id, season=season)
        print("✅ SUCCESS")
        show_data_structure(data)
        results["working"].append("team_skating_speed_detail")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        results["failed"].append(f"team_skating_speed_detail: {e}")
    
    # 19. Team Skating Distance
    print_subsection("19. team_skating_distance_detail() - Team skating distances")
    try:
        data = client.edge.team_skating_distance_detail(team_id=oilers_team_id, season=season)
        print("✅ SUCCESS")
        show_data_structure(data)
        results["working"].append("team_skating_distance_detail")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        results["failed"].append(f"team_skating_distance_detail: {e}")
    
    # 20. Team Shot Speed
    print_subsection("20. team_shot_speed_detail() - Team shot speeds")
    try:
        data = client.edge.team_shot_speed_detail(team_id=oilers_team_id, season=season)
        print("✅ SUCCESS")
        show_data_structure(data)
        results["working"].append("team_shot_speed_detail")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        results["failed"].append(f"team_shot_speed_detail: {e}")
    
    # 21. Team Shot Location
    print_subsection("21. team_shot_location_detail() - Team shot locations")
    try:
        data = client.edge.team_shot_location_detail(team_id=oilers_team_id, season=season)
        print("✅ SUCCESS")
        show_data_structure(data)
        results["working"].append("team_shot_location_detail")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        results["failed"].append(f"team_shot_location_detail: {e}")
    
    # 22. Team Zone Time
    print_subsection("22. team_zone_time_details() - Team zone time")
    try:
        data = client.edge.team_zone_time_details(team_id=oilers_team_id, season=season)
        print("✅ SUCCESS")
        show_data_structure(data)
        results["working"].append("team_zone_time_details")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        results["failed"].append(f"team_zone_time_details: {e}")
    
    # 23. Team Landing
    print_subsection("23. team_landing() - Team landing page data")
    try:
        sig = inspect.signature(client.edge.team_landing)
        print(f"   Parameters: {list(sig.parameters.keys())}")
        data = client.edge.team_landing(oilers_team_id)
        print("✅ SUCCESS")
        show_data_structure(data)
        results["working"].append("team_landing")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        results["failed"].append(f"team_landing: {e}")
    
    # ====================
    # SUMMARY
    # ====================
    print_section("📊 SUMMARY")
    
    print(f"\n✅ WORKING ENDPOINTS ({len(results['working'])}):")
    for endpoint in results["working"]:
        print(f"   ✓ {endpoint}")
    
    print(f"\n❌ FAILED ENDPOINTS ({len(results['failed'])}):")
    for endpoint in results["failed"]:
        print(f"   ✗ {endpoint}")
    
    print(f"\n📈 Success Rate: {len(results['working'])}/{len(results['working']) + len(results['failed'])} endpoints working")
    
    print_section("🎉 CATALOG COMPLETE")

if __name__ == "__main__":
    test_all_edge_endpoints()

