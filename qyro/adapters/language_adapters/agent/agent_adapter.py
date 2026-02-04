from qyro.lib import qyro
import os
import json
import logging

logger = logging.getLogger("qyro.agent")

class QyroAgent:
    def __init__(self, name, provider="openai"):
        self.name = name
        self.provider = provider
        self.system_prompt = "You are a helpful AI agent."
        self.handlers = {}

    def set_system_prompt(self, prompt):
        self.system_prompt = prompt

    def on(self, topic):
        def decorator(func):
            self.handlers[topic] = func
            # Register with Qyro lib
            qyro.on(topic)(self._handle_wrapper(func, topic))
            return func
        return decorator

    def _handle_wrapper(self, func, topic):
        def wrapper(data):
            logger.info(f"[{self.name}] Received task on {topic}")
            # Execute the user logic which might prepare prompts
            prompt_or_context = func(data)

            # Call LLM
            response = self._call_llm(prompt_or_context)

            # If function returns a topic to reply to, we could do that,
            # but for now we assume the user might manually emit inside the function
            # or we just return the result.
            return response
        return wrapper

    def _call_llm(self, prompt):
        if self.provider == "openai":
            # Mock OpenAI call for now as we don't have API keys in this env
            # In real impl, use openai library
            logger.info(f"[{self.name}] Calling OpenAI with: {prompt[:50]}...")
            return f"Mock response to: {prompt}"
        else:
            return f"Unknown provider: {self.provider}"

    def start(self):
        print(f"[Agent:{self.name}] Started. Provider: {self.provider}")
        qyro.start()

# Helper to be used in .qyro files
_agent_instance = None

def init(name, provider="openai"):
    global _agent_instance
    _agent_instance = QyroAgent(name, provider)
    return _agent_instance
