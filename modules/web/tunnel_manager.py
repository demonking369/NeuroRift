"""
NeuroRift Tunnel Manager
Provides public URL access via multiple tunnel providers
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict
import asyncio
import subprocess
import re
import logging

logger = logging.getLogger(__name__)


class TunnelProvider(ABC):
    """Base class for tunnel providers"""

    @abstractmethod
    async def start(self, port: int, **kwargs) -> str:
        """Start tunnel and return public URL"""
        pass

    @abstractmethod
    async def stop(self):
        """Stop tunnel"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is installed/available"""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name"""
        pass


class NgrokProvider(TunnelProvider):
    """ngrok tunnel provider"""

    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.public_url: Optional[str] = None

    @property
    def name(self) -> str:
        return "ngrok"

    def is_available(self) -> bool:
        try:
            result = subprocess.run(
                ["ngrok", "version"], capture_output=True, text=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    async def start(self, port: int, **kwargs) -> str:
        """Start ngrok tunnel"""
        if not self.is_available():
            raise RuntimeError(
                "ngrok is not installed. Install from https://ngrok.com/download"
            )

        # Start ngrok
        self.process = subprocess.Popen(
            ["ngrok", "http", str(port), "--log", "stdout"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Wait for URL to appear in output
        await asyncio.sleep(2)

        # Get tunnel URL from ngrok API
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:4040/api/tunnels") as resp:
                    data = await resp.json()
                    if data.get("tunnels"):
                        self.public_url = data["tunnels"][0]["public_url"]
                        return self.public_url
        except Exception as e:
            logger.error(f"Failed to get ngrok URL: {e}")

        raise RuntimeError("Failed to start ngrok tunnel")

    async def stop(self):
        """Stop ngrok tunnel"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None
            self.public_url = None


class CloudflareProvider(TunnelProvider):
    """Cloudflare Tunnel provider"""

    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.public_url: Optional[str] = None

    @property
    def name(self) -> str:
        return "cloudflare"

    def is_available(self) -> bool:
        try:
            result = subprocess.run(
                ["cloudflared", "--version"], capture_output=True, text=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    async def start(self, port: int, **kwargs) -> str:
        """Start Cloudflare Tunnel"""
        if not self.is_available():
            raise RuntimeError(
                "cloudflared is not installed. Install from https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/"
            )

        # Start cloudflared
        self.process = subprocess.Popen(
            ["cloudflared", "tunnel", "--url", f"http://localhost:{port}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        # Parse URL from output
        url_pattern = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")

        for _ in range(30):  # Try for 30 seconds
            if self.process.stdout:
                line = self.process.stdout.readline()
                if line:
                    match = url_pattern.search(line)
                    if match:
                        self.public_url = match.group(0)
                        return self.public_url
            await asyncio.sleep(1)

        raise RuntimeError("Failed to start Cloudflare Tunnel")

    async def stop(self):
        """Stop Cloudflare Tunnel"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None
            self.public_url = None


class LocaltunnelProvider(TunnelProvider):
    """localtunnel provider"""

    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.public_url: Optional[str] = None

    @property
    def name(self) -> str:
        return "localtunnel"

    def is_available(self) -> bool:
        try:
            result = subprocess.run(["lt", "--version"], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    async def start(self, port: int, **kwargs) -> str:
        """Start localtunnel"""
        if not self.is_available():
            raise RuntimeError(
                "localtunnel is not installed. Run: npm install -g localtunnel"
            )

        subdomain = kwargs.get("subdomain")
        cmd = ["lt", "--port", str(port)]
        if subdomain:
            cmd.extend(["--subdomain", subdomain])

        self.process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        # Parse URL from output
        url_pattern = re.compile(r"https://[a-z0-9-]+\.loca\.lt")

        for _ in range(10):
            if self.process.stdout:
                line = self.process.stdout.readline()
                if line:
                    match = url_pattern.search(line)
                    if match:
                        self.public_url = match.group(0)
                        return self.public_url
            await asyncio.sleep(1)

        raise RuntimeError("Failed to start localtunnel")

    async def stop(self):
        """Stop localtunnel"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None
            self.public_url = None


class TunnelManager:
    """Manages tunnel providers"""

    def __init__(self):
        self.providers: Dict[str, TunnelProvider] = {
            "ngrok": NgrokProvider(),
            "cloudflare": CloudflareProvider(),
            "localtunnel": LocaltunnelProvider(),
        }
        self.active_provider: Optional[TunnelProvider] = None

    def list_available_providers(self) -> List[str]:
        """List installed/available providers"""
        return [
            name for name, provider in self.providers.items() if provider.is_available()
        ]

    def get_provider(self, name: str) -> Optional[TunnelProvider]:
        """Get provider by name"""
        return self.providers.get(name)

    async def start_tunnel(self, provider_name: str, port: int, **kwargs) -> str:
        """Start tunnel with specified provider"""
        if provider_name == "auto":
            # Auto-select first available provider
            available = self.list_available_providers()
            if not available:
                raise RuntimeError(
                    "No tunnel providers available. Install ngrok, cloudflared, or localtunnel."
                )
            provider_name = available[0]
            logger.info(f"Auto-selected provider: {provider_name}")

        provider = self.get_provider(provider_name)
        if not provider:
            raise ValueError(f"Unknown provider: {provider_name}")

        if not provider.is_available():
            raise RuntimeError(f"Provider {provider_name} is not installed")

        logger.info(f"Starting {provider_name} tunnel on port {port}...")
        public_url = await provider.start(port, **kwargs)
        self.active_provider = provider

        logger.info(f"✅ Tunnel active: {public_url}")
        return public_url

    async def stop_tunnel(self):
        """Stop active tunnel"""
        if self.active_provider:
            await self.active_provider.stop()
            self.active_provider = None

    def get_public_url(self) -> Optional[str]:
        """Get current public URL"""
        if self.active_provider:
            return self.active_provider.public_url
        return None


# CLI interface
async def main():
    import argparse

    parser = argparse.ArgumentParser(description="NeuroRift Tunnel Manager")
    parser.add_argument(
        "action", choices=["start", "stop", "list"], help="Action to perform"
    )
    parser.add_argument(
        "--provider",
        default="auto",
        help="Tunnel provider (ngrok, cloudflare, localtunnel, auto)",
    )
    parser.add_argument("--port", type=int, default=3000, help="Local port to tunnel")
    parser.add_argument("--subdomain", help="Custom subdomain (if supported)")

    args = parser.parse_args()

    manager = TunnelManager()

    if args.action == "list":
        available = manager.list_available_providers()
        print("Available tunnel providers:")
        for provider in available:
            print(f"  • {provider}")
        if not available:
            print("  (none installed)")

    elif args.action == "start":
        try:
            url = await manager.start_tunnel(
                args.provider, args.port, subdomain=args.subdomain
            )
            print(f"\n🌐 Public URL: {url}\n")
            print("Press Ctrl+C to stop...")

            # Keep running
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping tunnel...")
                await manager.stop_tunnel()
        except Exception as e:
            print(f"❌ Error: {e}")
            return 1

    elif args.action == "stop":
        await manager.stop_tunnel()
        print("Tunnel stopped")

    return 0


if __name__ == "__main__":
    asyncio.run(main())
