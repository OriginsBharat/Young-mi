# src/learning.py
# This module gives Kim Young-mi her "Curiosity" by allowing her to learn about unknown terms.

from duckduckgo_search import DDGS

def search_for_term(term):
    """
    Searches for a given term using DuckDuckGo and returns a concise summary of the top result.
    """
    print(f"[Learning Engine] Searching for new term: '{term}'...")
    try:
        with DDGS() as ddgs:
            # We will take the first result as it's often the most relevant (e.g., a Wikipedia page).
            results = list(ddgs.text(term, max_results=1))
            if not results:
                print(f"  > No results found for '{term}'.")
                return None

            top_result = results[0]
            # Create a concise summary for the AI to use.
            summary = f"I just learned about '{term}'. According to a search, the title of the top result is '{top_result.get('title')}' and a brief summary is: '{top_result.get('body')}'"
            print(f"  > Found information: {top_result.get('title')}")
            return summary

    except Exception as e:
        print(f"[Learning Engine] An error occurred during search: {e}")
        return None

if __name__ == '__main__':
    # This block is for testing the module directly
    print("--- Testing Autonomous Learning Engine ---")

    # Test a common gaming term
    term_to_learn = "Gekko Valorant"
    learned_info = search_for_term(term_to_learn)

    if learned_info:
        print("\n--- Summary for AI ---")
        print(learned_info)
    else:
        print(f"\nCould not learn about '{term_to_learn}'.")

    print("\n--- Testing a non-existent term ---")
    term_to_learn_2 = "asdfqwerzxcv"
    learned_info_2 = search_for_term(term_to_learn_2)
    if not learned_info_2:
        print("\nCorrectly handled non-existent term.")