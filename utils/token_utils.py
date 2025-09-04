# token_utils.py: A utility for counting tokens using a remote tokenizer service.
# This is used to accurately measure the size of prompts before sending them to the LLM,
# which is crucial for managing the context window.

import asyncio
import requests
import functools
from logger import logger
from config import VLLM_TOKENIZER_URL


async def count_tokens(text: str) -> int:
    """
    Sends text to the vLLM tokenizer endpoint and returns the number of tokens.
    Runs the synchronous `requests` call in an executor to avoid blocking the
    async event loop.
    """
    
    if not text.strip() or not VLLM_TOKENIZER_URL:
        return 0
    try:
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            functools.partial(requests.post, VLLM_TOKENIZER_URL, json={"prompt": text}),
        )
        response.raise_for_status()
        return len(response.json().get("tokens", []))
    except requests.RequestException as e:
        logger.warning(
            "token_utils", f"Could not count tokens via tokenizer API: {e}. Returning 0."
        )
        return 0
