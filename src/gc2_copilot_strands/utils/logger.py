"""Logging utilities for GC2 Copilot."""

import logging
import json
from pathlib import Path
from typing import Any


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with console and optional file output.

    Args:
        name: Logger name
        level: Logging level

    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    return logger


def log_tool_call(tool_name: str, arguments: dict, logger: logging.Logger = None):
    """
    Log a tool call with its arguments.

    Args:
        tool_name: Name of the tool being called
        arguments: Tool arguments
        logger: Logger to use (creates one if None)
    """
    if logger is None:
        logger = setup_logger("gc2_copilot.tools")

    logger.info(f"🔧 Tool Call: {tool_name}")
    logger.debug(f"   Arguments: {json.dumps(arguments, indent=2)}")


def log_tool_result(tool_name: str, result: Any, logger: logging.Logger = None):
    """
    Log a tool result.

    Args:
        tool_name: Name of the tool
        result: Tool result
        logger: Logger to use
    """
    if logger is None:
        logger = setup_logger("gc2_copilot.tools")

    logger.info(f"✅ Tool Result: {tool_name}")

    # Log first 200 chars of result
    result_str = str(result)
    if len(result_str) > 200:
        logger.debug(f"   Result: {result_str[:200]}...")
    else:
        logger.debug(f"   Result: {result_str}")


def log_agent_call(agent_name: str, prompt: str, logger: logging.Logger = None):
    """
    Log an agent call.

    Args:
        agent_name: Name of the agent
        prompt: Prompt being sent
        logger: Logger to use
    """
    if logger is None:
        logger = setup_logger("gc2_copilot.agents")

    logger.info(f"🤖 Agent Call: {agent_name}")
    logger.debug(f"   Prompt (first 200 chars): {prompt[:200]}...")


def log_error(error: Exception, context: str = "", logger: logging.Logger = None):
    """
    Log an error with context.

    Args:
        error: Exception that occurred
        context: Context description
        logger: Logger to use
    """
    if logger is None:
        logger = setup_logger("gc2_copilot.errors")

    logger.error(f"❌ Error in {context}: {type(error).__name__}: {error}")
    logger.debug("Stack trace:", exc_info=True)
