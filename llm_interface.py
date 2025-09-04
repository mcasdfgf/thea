# file: llm_interface.py
# llm_interface.py: A standardized interface for communicating with a Large Language Model.
# This module abstracts the details of the API client (e.g., vLLM's OpenAI-compatible server),
# providing a simple `generate` method. It also includes logic for dynamically managing
# the token context window to prevent overflow errors.

import json
from typing import List, Dict, Any, Optional
import asyncio

from openai import AsyncOpenAI, OpenAIError
from logger import logger
from config import VLLM_API_BASE, VLLM_MODEL_NAME


class LLMInterface:
    def __init__(self):
        try:
            self.client = AsyncOpenAI(
                api_key="vllm",
                base_url=VLLM_API_BASE,
            )
            self.model_name = VLLM_MODEL_NAME
            # The client is initialized to communicate with an OpenAI-compatible API,
            # which is the standard interface provided by vLLM.
            logger.info(
                "LLMInterface",
                "vLLM client initialized successfully.",
                {"base_url": VLLM_API_BASE, "model": self.model_name},
            )
        except Exception as e:
            logger.error(
                "LLMInterface",
                "Error initializing vLLM client.",
                {"error": str(e)},
                exc_info=True,
            )
            raise

    async def generate(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.1,
        max_tokens: int = 2048,
    ) -> Dict[str, Optional[str]]:
        """
        Sends a request to the LLM and returns a standardized response.

        This method implements dynamic token management:
        1. It first tokenizes the input messages to determine their length.
        2. It calculates the available space for the response, considering the model's context limit.
        3. It adjusts the `max_tokens` parameter for the API call to prevent context overflow.

        Args:
            messages: A list of message dictionaries, following the OpenAI API format.
            temperature: The sampling temperature for the generation.
            max_tokens: The desired maximum number of tokens for the response.

        Returns:
            A dictionary containing the generated text, e.g., {"text": "..."}.
        """
        # --- Dynamic Token Calculation ---
        import requests
        import functools
        from config import VLLM_TOKENIZER_URL, LLM_CONTEXT_LIMIT

        # Step 1: Calculate the number of tokens in the input messages.
        # This requires a separate, lightweight call to the tokenizer endpoint.
        full_text_to_tokenize = "\n".join([msg.get("content", "") for msg in messages])
        input_token_count = 0
        try:
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,
                functools.partial(
                    requests.post,
                    VLLM_TOKENIZER_URL,
                    json={"prompt": full_text_to_tokenize},
                ),
            )
            response.raise_for_status()
            input_token_count = len(response.json().get("tokens", []))
        except requests.RequestException as e:
            logger.warning(
                "LLMInterface",
                "Failed to count tokens before generation, using conservative defaults.",
                {"error": str(e)},
            )

            input_token_count = int(LLM_CONTEXT_LIMIT * 0.8)

        # Step 2: Calculate the available token budget for the response.
        available_space = LLM_CONTEXT_LIMIT - input_token_count

        # Step 3: Determine the final `max_tokens` value.
        # It's the smaller of the requested amount and the available space.
        # `max(1, ...)` ensures we don't request zero or negative tokens.
        final_max_tokens = max(1, min(max_tokens, available_space))

        logger.info(
            "LLMInterface",
            "Dynamic max_tokens calculation.",
            {
                "input_tokens": input_token_count,
                "context_limit": LLM_CONTEXT_LIMIT,
                "requested_max_tokens": max_tokens,
                "final_max_tokens": final_max_tokens,
            },
        )

        # --- API Call ---
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": final_max_tokens,
        }
        logger.info(
            "LLMInterface", "Sending request to vLLM...", {"model": self.model_name}
        )

        try:
            response = await self.client.chat.completions.create(**payload)

            response_text = response.choices[0].message.content
            if response_text is None:
                response_text = ""

            result = {"text": response_text.strip()}
            logger.info(
                "LLMInterface",
                "Received response from vLLM.",
                {"response_preview": result["text"][:100] + "..."},
            )
            return result

        except OpenAIError as e:
            # Handle API-specific errors from the vLLM server (e.g., bad requests, server errors).
            logger.error(
                "LLMInterface",
                "API error during vLLM request.",
                {"error": str(e)},
                exc_info=True,
            )

            error_message = f"[SYSTEM: LLM Error - {str(e)}]"
            return {"text": error_message}
        except Exception as e:
            # Handle unexpected errors (e.g., network issues).
            logger.error(
                "LLMInterface",
                "Unexpected error during vLLM request.",
                {"error": str(e)},
                exc_info=True,
            )
            error_message = f"[SYSTEM: Unexpected LLM Interface Error - {str(e)}]"
            return {"text": error_message}
