"""Retry logic with exponential backoff for API calls."""

import time
import functools
from typing import Callable, Any, TypeVar, Optional, Tuple, Type

# Import Anthropic errors
try:
    from anthropic import APIStatusError as AnthropicAPIStatusError
    from anthropic import RateLimitError as AnthropicRateLimitError
except ImportError:
    AnthropicAPIStatusError = Exception
    AnthropicRateLimitError = Exception

# Import OpenAI errors
try:
    from openai import APIStatusError as OpenAIAPIStatusError
    from openai import RateLimitError as OpenAIRateLimitError
    from openai import APIError as OpenAIAPIError
except ImportError:
    OpenAIAPIStatusError = Exception
    OpenAIRateLimitError = Exception
    OpenAIAPIError = Exception

T = TypeVar('T')


def with_retry(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    retryable_errors: tuple = None
) -> Callable:
    """
    Decorator to retry a function with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        retryable_errors: Tuple of exception types to retry on (auto-detected if None)

    Returns:
        Decorated function with retry logic

    Example:
        @with_retry(max_retries=3)
        def call_api():
            return agent("some request")
    """
    # Default retryable errors for both Anthropic and OpenAI
    if retryable_errors is None:
        retryable_errors = (
            AnthropicAPIStatusError,
            AnthropicRateLimitError,
            OpenAIAPIStatusError,
            OpenAIRateLimitError,
            OpenAIAPIError,
        )

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_errors as e:
                    last_exception = e

                    # Don't retry on last attempt
                    if attempt == max_retries:
                        break

                    # Check if it's an overload error (works for both Anthropic and OpenAI)
                    is_overload = False
                    error_message = str(e)
                    if "overloaded" in error_message.lower() or "rate limit" in error_message.lower():
                        is_overload = True

                    # Print retry message
                    if is_overload:
                        error_type = "API Overloaded/Rate Limited"
                    else:
                        error_type = type(e).__name__
                    print(f"⚠️  {error_type} error (attempt {attempt + 1}/{max_retries + 1})")
                    print(f"   Retrying in {delay:.1f} seconds...")

                    # Wait before retrying
                    time.sleep(delay)

                    # Exponential backoff
                    delay = min(delay * exponential_base, max_delay)
                except Exception as e:
                    # Don't retry on other exceptions
                    raise

            # All retries exhausted
            print(f"\n❌ Failed after {max_retries + 1} attempts")
            raise last_exception

        return wrapper
    return decorator


def retry_agent_call(agent_func: Callable[..., T], *args, **kwargs) -> T:
    """
    Helper function to retry an agent call with sensible defaults.

    Args:
        agent_func: The agent function to call
        *args: Arguments to pass to the agent function
        **kwargs: Keyword arguments to pass to the agent function

    Returns:
        Result from the agent function

    Example:
        result = retry_agent_call(agent, "Analyze this request...")
    """
    @with_retry(max_retries=3, initial_delay=2.0)
    def _call():
        return agent_func(*args, **kwargs)

    return _call()
