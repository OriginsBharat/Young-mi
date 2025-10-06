import os
import requests
from bs4 import BeautifulSoup
from serpapi import GoogleSearch
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
openai.api_key = os.getenv("OPENAI_API_KEY")

def search_and_summarize(query):
    """
    Searches the web for a given query using SerpApi, scrapes the top result,
    and uses an LLM to summarize the content.
    """
    if not SERPAPI_API_KEY:
        return "Search functionality is disabled. SERPAPI_API_KEY is missing."

    print(f"Searching the web for: '{query}'...")
    try:
        # Step 1: Perform the Google search using SerpApi
        params = {"q": query, "api_key": SERPAPI_API_KEY}
        search = GoogleSearch(params)
        results = search.get_dict()

        organic_results = results.get("organic_results", [])
        if not organic_results:
            return "I couldn't find any relevant web pages for that."

        # Step 2: Get the URL of the top result and fetch its content
        top_result_url = organic_results[0]['link']
        print(f"Fetching content from: {top_result_url}")

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(top_result_url, headers=headers, timeout=10)
        response.raise_for_status() # Raise an exception for bad status codes

        # Step 3: Parse the HTML and extract clean text using BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        # Get all the text, separate paragraphs with a space, and remove extra whitespace
        text_content = ' '.join(p.get_text() for p in soup.find_all('p'))

        if not text_content:
            return "I found a page, but I couldn't read its content."

        # Step 4: Use the LLM to summarize the content
        print("Summarizing the content...")
        summary_prompt = f"Based on the following content, provide a concise answer to the question: '{query}'\n\nContent:\n{text_content[:8000]}" # Limit content size

        completion = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes web content to answer a user's question."},
                {"role": "user", "content": summary_prompt}
            ]
        )
        summary = completion.choices[0].message.content
        print("Summary complete.")
        return summary

    except Exception as e:
        print(f"An error occurred during web search or summarization: {e}")
        return "I had a little trouble looking that up. My systems might be acting up. Maybe try asking again in a moment?"

if __name__ == '__main__':
    print("--- Testing web_search.py ---")
    if not SERPAPI_API_KEY or not openai.api_key:
        print("\nERROR: Make sure you have set both OPENAI_API_KEY and SERPAPI_API_KEY in your .env file.")
    else:
        test_query = "What's a good Viper's Pit lineup for the A site on the Valorant map Bind?"
        summary = search_and_summarize(test_query)
        print(f"\nQuery: {test_query}")
        print(f"Summary: {summary}")