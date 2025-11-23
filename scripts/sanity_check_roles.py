import json

def sanity_check_roles(final_payload_path: str, roles_json_path: str):
    # Load final payload
    with open(final_payload_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    # Load roles.json
    with open(roles_json_path, "r", encoding="utf-8") as f:
        roles_data = json.load(f)

    # Extract valid role IDs
    valid_role_ids = {item["role_id"] for item in roles_data}

    # Extract role_ids referenced in payload
    predicted_ids = set(payload.get("predicted_role_ids", []))
    flagged_ids = set(payload.get("flagged_role_ids", []))
    all_payload_ids = predicted_ids.union(flagged_ids)

    # Check missing role_ids (appear in payload but not in roles.json)
    unknown_ids = all_payload_ids - valid_role_ids

    print("\n===== ROLE SANITY CHECK =====")

    # Unknown role IDs
    if unknown_ids:
        print("Unknown role_ids found in payload (NOT in roles.json):")
        for rid in sorted(unknown_ids):
            print(f" - {rid}")
    else:
        print("No unknown role_ids. All payload IDs exist in roles.json.")

    print("================================\n")


# Quick local manual test
if __name__ == "__main__":
    sanity_check_roles(
        final_payload_path="FINAL_PAYLOAD/NEW_SAMPLE_2_final_payload.json", # just change the path accordingly
        roles_json_path="static_data/roles_upd.json"
    )
