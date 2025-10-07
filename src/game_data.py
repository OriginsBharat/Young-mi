# This module will be responsible for managing static game data,
# such as agent abilities, weapon stats, etc.

# For now, we will simulate a database of agent abilities.
# In a future version, this could be loaded from a JSON or YAML file.
AGENT_ABILITIES = {
    "jett": ["Cloudburst", "Updraft", "Tailwind", "Blade Storm"],
    "sova": ["Owl Drone", "Shock Bolt", "Recon Bolt", "Hunter's Fury"],
    "viper": ["Snake Bite", "Poison Cloud", "Toxic Screen", "Viper's Pit"],
    "reyna": ["Leer", "Devour", "Dismiss", "Empress"],
    "killjoy": ["Nanoswarm", "Alarmbot", "Turret", "Lockdown"],
    "cypher": ["Cyber Cage", "Spycam", "Trapwire", "Neural Theft"],
    "sage": ["Barrier Orb", "Slow Orb", "Healing Orb", "Resurrection"],
    "omen": ["Shrouded Step", "Paranoia", "Dark Cover", "From the Shadows"],
    "breach": ["Aftershock", "Flashpoint", "Fault Line", "Rolling Thunder"],
    "phoenix": ["Blaze", "Curveball", "Hot Hands", "Run it Back"],
    # This list can be expanded with all other agents.
}

# This will hold the data for the agents currently in the match.
loaded_agent_data = {}

def load_data_for_agents(agent_list):
    """
    Simulates loading data for the agents currently in the match
    to make processing more efficient.
    """
    global loaded_agent_data
    loaded_agent_data = {} # Clear old data

    print(f"[INFO] Loading game data for agents: {agent_list}...")
    for agent_name in agent_list:
        agent_name_lower = agent_name.lower()
        if agent_name_lower in AGENT_ABILITIES:
            loaded_agent_data[agent_name_lower] = AGENT_ABILITIES[agent_name_lower]
            print(f"  -> Loaded data for {agent_name_lower}")
        else:
            print(f"  -> Warning: No data found for agent '{agent_name_lower}'")

    print("[INFO] Agent data loaded for the current match.")
    return loaded_agent_data

def get_loaded_abilities():
    """
    Returns a list of all abilities for the currently loaded agents.
    """
    all_abilities = []
    for agent, abilities in loaded_agent_data.items():
        all_abilities.extend(abilities)
    return all_abilities

if __name__ == "__main__":
    print("--- Testing game_data.py ---")
    test_agents = ["sova", "jett", "kayo"] # kayo is not in our simple DB
    load_data_for_agents(test_agents)

    print("\nLoaded Agent Data:")
    print(loaded_agent_data)

    print("\nAll loaded abilities:")
    print(get_loaded_abilities())