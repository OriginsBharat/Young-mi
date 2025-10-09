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

    def add_ai_thought_to_history(self, thought):
        """Adds a thought the AI had to the conversation history."""
        self.conversation_history.append({"role": "assistant", "content": thought})
        self.memory.update_history({"messages": self.conversation_history})

    def generate_thought(self, game_context):
        """
        Generates a proactive, in-character thought based on the current game state.
        This uses a separate, temporary message history to not pollute the main conversation.
        """
        is_alone = game_context.get("is_alone", True)
        current_screen = game_context.get('current_screen', 'Unknown')
        privacy_level_adjective = "playful and uninhibited" if is_alone else "focused and tactical"

        # A special prompt designed to elicit a short, in-character observation.
        thinking_prompt = (
            f"You are watching your boyfriend play Valorant. He is currently on the '{current_screen}' screen. "
            f"You are feeling {privacy_level_adjective}. "
            f"Generate a single, brief, in-character thought or observation about this situation. "
            f"Do not ask a question. Do not greet him. Just state a short thought. Be creative."
        )

        temp_messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": thinking_prompt}
        ]

        try:
            response = self.client.chat(model=self.model_name, messages=temp_messages)
            thought = response['message']['content']
            # A simple filter to remove unwanted self-correction or affirmations from the model
            if "Sure, here's a thought" in thought or "Okay, here's" in thought:
                thought = thought.split(":")[-1].strip()
            return thought
        except Exception as e:
            print(f"[ERROR] Error generating thought: {e}")
            return None

    def _is_confused(self, response):
        """A simple heuristic to check if the AI is confused by a term."""
        confusion_phrases = ["i'm not sure what", "i don't know what", "what is a", "what is an", "what are"]
        return any(phrase in response.lower() for phrase in confusion_phrases)

    def _extract_unknown_term(self, user_input):
        """A simple heuristic to extract a potential unknown term from user input."""
        words = user_input.split()
        if len(words) > 2:
            return " ".join(words[-2:])
        elif len(words) > 0:
            return words[-1]
        return None

    def generate_response(self, user_input, game_context):
        """
        Generates a response from the AI, handling confusion and context.
        `game_context` is a dictionary: {"is_alone": bool, "current_screen": str}
        """
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
            response = self.client.chat(model=self.model_name, messages=self.conversation_history)
            ai_response = response['message']['content']

            if self._is_confused(ai_response):
                print("[AI Core] AI seems confused. Attempting to learn...")
                term_to_learn = self._extract_unknown_term(user_input)

                if term_to_learn:
                    learned_info = search_for_term(term_to_learn)
                    if learned_info:
                        self.conversation_history.append({"role": "assistant", "content": ai_response})
                        learning_prompt = f"(System Note: You were confused about '{term_to_learn}'. Here is some information to help: {learned_info}. Now, please respond to the user's original message again with this new knowledge.)"
                        self.conversation_history.append({"role": "user", "content": learning_prompt})

                        print("[AI Core] Re-generating response with new knowledge.")
                        new_response = self.client.chat(model=self.model_name, messages=self.conversation_history)
                        ai_response = new_response['message']['content']

            self.add_ai_thought_to_history(ai_response)
            return ai_response

        except Exception as e:
            print(f"[ERROR] Error communicating with Ollama: {e}")
            return "I'm having a little trouble thinking right now, babe."