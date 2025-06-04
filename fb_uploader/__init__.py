import logging

LOGGER = logging.getLogger(__name__)


def setup_logging() -> logging.Logger:
    """Set up logging configuration."""
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] - <%(name)s> - %(message)s",
        level=logging.INFO,
        handlers=[logging.StreamHandler()],
    )


def load_environment_variables() -> str:
    """Load environment variables from .env file."""
    try:
        from dotenv import load_dotenv

        if load_dotenv():
            return "Loaded environment variables from .env file."
        return (  # noqa: TRY300
            "No .env file found, skipping environment variable loading."
        )
    except ImportError:
        return (
            "Can't import dotenv & load .env, this is expected if running via Docker."
        )


def initialize() -> None:
    """Initialize the application."""
    setup_logging()
    env_message = load_environment_variables()
    if "Loaded" in env_message:
        LOGGER.info(env_message)
    else:
        LOGGER.warning(env_message)


initialize()
