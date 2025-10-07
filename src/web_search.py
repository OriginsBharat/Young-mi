import os
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
import ollama
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

def search_and_summarize(query):
    """
    Searches the web using DuckDuckGo, scrapes the top result,
    and uses the local LLM to summarize the content.
    """
    print(f"[INFO] Searching the web for: '{query}'...")
    try:
        # Use a context manager for the search object
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=1))
            if not results:
                return "I couldn't find any relevant web pages for that."

        top_result_url = results[0]['href']
        print(f"[INFO] Fetching content from: {top_result_url}")

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(top_result_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        text_content = ' '.join(p.get_text() for p in soup.find_all('p'))

        if not text_content:
            return "I found a page, but I couldn't read its content."

        print("[INFO] Summarizing content with local model...")
        summary_prompt = f"Based on the following content, provide a concise answer to the question: '{query}'\n\nContent:\n{text_content[:8000]}"

        completion = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes web content to answer a user's question."},
                {"role": "user", "content": summary_prompt}
            ]
        )
        summary = completion['message']['content']
        print("[INFO] Summary complete.")
        return summary

    except Exception as e:
        print(f"[ERROR] An error occurred during web search or summarization: {e}")
        return "I had a little trouble looking that up. My systems might be acting up."

if __name__ == '__main__':
    print("--- Testing web_search.py (Definitive Key-Free Version) ---")
    test_query = "What are the best Viper lineups for the A site on the Valorant map Bind?"
    summary = search_and_summarize(test_query)
    print(f"\nQuery: {test_query}")
    print(f"Summary: {summary}")