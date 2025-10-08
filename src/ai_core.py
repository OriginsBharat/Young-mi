# src/ai_core.py
# This module contains the AI's "brain".

import ollama
import os
from dotenv import load_dotenv
from src.memory import Memory
from src.learning import search_for_term

class AICore:
    def __init__(self, character_sheet_path="data/character_sheet.md"):
        load_dotenv()
        self.client = ollama.Client()
        self.memory = Memory()
        self.model_name = os.getenv("OLLAMA_MODEL", "llama3")
        self.system_prompt = self._load_character_sheet(character_sheet_path)
        self.conversation_history = self._load_or_initialize_history()

    def _load_character_sheet(self, path):
        """Loads the character sheet from the file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"[ERROR] Character sheet not found at {path}. Using a fallback persona.")
            return "You are a helpful AI assistant."

    def _load_or_initialize_history(self):
        """Loads conversation history from memory or starts a new one."""
        history = self.memory.get_history()
        if history and "messages" in history:
            print("Found and loaded previous conversation history.")
            history["messages"][0] = {"role": "system", "content": self.system_prompt}
            return history["messages"]
        else:
            print("No previous history found. Starting a new conversation.")
            return [{"role": "system", "content": self.system_prompt}]

    def _is_confused(self, response):
        """A simple heuristic to check if the AI is confused by a term."""
        confusion_phrases = ["i'm not sure what", "i don't know what", "what is a", "what is an", "what are"]
        return any(phrase in response.lower() for phrase in confusion_phrases)

    def _extract_unknown_term(self, user_input):
        """A simple heuristic to extract a potential unknown term from user input."""
        # This can be improved, but for now, it's a decent starting point.
        # It assumes the unknown term might be the last noun phrase.
        words = user_input.split()
        if len(words) > 2:
            return " ".join(words[-2:]) # "what is a dragon lore" -> "dragon lore"
        elif len(words) > 0:
            return words[-1] # "what is gekko" -> "gekko"
        return None

    def generate_response(self, user_input, game_context):
        """
        Generates a response from the AI, handling confusion and context.
        `game_context` is a dictionary: {"is_alone": bool, "current_screen": str}
        """
        # 1. Construct the prompt with full context
        is_alone = game_context.get("is_alone", True)
        privacy_level = "We are alone, so you can be your full, unfiltered self." if is_alone else "Be careful, others are in the party. Keep it SFW and focused on tactical callouts or safe topics."

        context_prompt = (
            f"--- Your Current Situation ---\n"
            f"Privacy Level: {privacy_level}\n"
            f"Current Game Screen: {game_context.get('current_screen', 'Unknown')}\n"
            f"--- User's Message ---\n"
            f"{user_input}"
        )

        self.conversation_history.append({"role": "user", "content": context_prompt})

        try:
            # 2. First attempt at generating a response
            response = self.client.chat(model=self.model_name, messages=self.conversation_history)
            ai_response = response['message']['content']

            # 3. Check for confusion and attempt to learn
            if self._is_confused(ai_response):
                print("[AI Core] AI seems confused. Attempting to learn...")
                term_to_learn = self._extract_unknown_term(user_input)

                if term_to_learn:
                    learned_info = search_for_term(term_to_learn)
                    if learned_info:
                        # If learning was successful, add the new info to the conversation and try again
                        self.conversation_history.append({"role": "assistant", "content": ai_response}) # Add the confused response
                        learning_prompt = f"(System Note: You were confused about '{term_to_learn}'. Here is some information to help: {learned_info}. Now, please respond to the user's original message again with this new knowledge.)"
                        self.conversation_history.append({"role": "user", "content": learning_prompt})

                        print("[AI Core] Re-generating response with new knowledge.")
                        new_response = self.client.chat(model=self.model_name, messages=self.conversation_history)
                        ai_response = new_response['message']['content']

            # 4. Save and return the final response
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            self.memory.update_history({"messages": self.conversation_history})
            return ai_response

        except Exception as e:
            print(f"[ERROR] Error communicating with Ollama: {e}")
            return "I'm having a little trouble thinking right now, babe."