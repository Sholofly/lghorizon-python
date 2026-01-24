"""Configuration handler for LG Horizon services."""

from typing import Any, Optional


class LGHorizonServicesConfig:
    """Handle LG Horizon configuration and service URLs."""

    def __init__(self, config_data: dict[str, Any]) -> None:
        """Initialize LG Horizon config.

        Args:
            config_data: Configuration dictionary with service endpoints
        """
        self._config = config_data

    async def get_service_url(self, service_name: str) -> str:
        """Get the URL for a specific service.

        Args:
            service_name: Name of the service (e.g., 'authService', 'recordingService')

        Returns:
            URL for the service

        Raises:
            ValueError: If the service or its URL is not found
        """
        if service_name in self._config and "URL" in self._config[service_name]:
            return self._config[service_name]["URL"]
        raise ValueError(f"Service URL for '{service_name}' not found in configuration")

    async def get_all_services(self) -> dict[str, str]:
        """Get all available services and their URLs.

        Returns:
            Dictionary mapping service names to URLs
        """
        return {
            name: url
            for name, service in self._config.items()
            if isinstance(service, dict) and (url := service.get("URL"))
        }

    async def __getattr__(self, name: str) -> Optional[str]:
        """Access service URLs as attributes.

        Example: config.authService returns the auth service URL

        Args:
            name: Service name

        Returns:
            URL for the service or None if not found
        """
        if name.startswith("_"):
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            )
        return await self.get_service_url(name)

    def __repr__(self) -> str:
        """Return string representation."""
        services = list(self._config.keys())
        return f"LGHorizonConfig({len(services)} services)"
