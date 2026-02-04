"""
CAPI Plugin - Meta Conversions API

Plugin for sending conversion events to Meta (Facebook/Instagram).
Integrates with Weni's conversions API.
"""

from typing import TYPE_CHECKING, Any, Dict

import requests

from .base import PluginBase

if TYPE_CHECKING:
    # from ..client import VTEXClient
    from ..context import SearchContext


class CAPI(PluginBase):
    """
    Meta Conversions API (CAPI) plugin.

    Features:
    - Sends lead events after product search
    - Sends purchase events after purchase
    - Integrates with Weni's conversions API

    Supported event types:
    - lead: User showed interest (searched products)
    - purchase: User made a purchase

    Example:
        concierge = ProductConcierge(
            base_url="...",
            store_url="...",
            plugins=[
                CAPI(
                    event_type="lead",
                    auto_send=True
                )
            ]
        )

        result = concierge.search(
            product_name="t-shirt",
            contact_info={
                "urn": "whatsapp:5511999999999",
                "channel_uuid": "channel-uuid"
            }
        )
    """

    name = "capi"

    VALID_EVENT_TYPES = ["lead", "purchase"]

    def __init__(
        self,
        event_type: str = "lead",
        auto_send: bool = True,
        weni_capi_url: str = "https://flows.weni.ai/conversion/",
        only_whatsapp: bool = True,
        timeout: int = 10,
    ):
        """
        Initialize the CAPI plugin.

        Args:
            event_type: Event type to send (lead or purchase)
            auto_send: If True, sends event automatically after search
            weni_capi_url: Weni's conversions API URL
            only_whatsapp: If True, only sends for WhatsApp contacts
            timeout: Request timeout
        """
        if event_type not in self.VALID_EVENT_TYPES:
            raise ValueError(f"event_type must be one of: {self.VALID_EVENT_TYPES}")

        self.event_type = event_type
        self.auto_send = auto_send
        self.weni_capi_url = weni_capi_url
        self.only_whatsapp = only_whatsapp
        self.timeout = timeout
        self._sent = False

    def finalize_result(self, result: Dict[str, Any], context: "SearchContext") -> Dict[str, Any]:
        """
        Send CAPI event after finalizing result (if auto_send=True).
        """
        if not self.auto_send:
            return result

        # Avoid duplicate send
        if self._sent:
            return result

        contact_urn = context.get_contact("urn")
        channel_uuid = context.get_contact("channel_uuid")
        auth_token = context.credentials.get("auth_token") or context.get_contact("auth_token")

        # Check if it's WhatsApp (if configured for WhatsApp only)
        if self.only_whatsapp and contact_urn and "whatsapp" not in contact_urn.lower():
            return result

        success = self.send_event(
            auth_token=auth_token,
            channel_uuid=channel_uuid,
            contact_urn=contact_urn,
            event_type=self.event_type,
        )

        if success:
            self._sent = True
            result["capi_event_sent"] = True
            result["capi_event_type"] = self.event_type

        return result

    def send_event(
        self, auth_token: str, channel_uuid: str, contact_urn: str, event_type: str
    ) -> bool:
        """
        Send conversion event to Meta.

        Args:
            auth_token: Authentication token
            channel_uuid: Channel UUID
            contact_urn: Contact URN
            event_type: Event type (lead or purchase)

        Returns:
            True if sent successfully
        """
        if not all([auth_token, channel_uuid, contact_urn]):
            print("CAPI: Missing required parameters")
            return False

        if event_type not in self.VALID_EVENT_TYPES:
            print(f"CAPI: Invalid event type: {event_type}")
            return False

        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

        payload = {
            "channel_uuid": channel_uuid,
            "contact_urn": contact_urn,
            "event_type": event_type,
        }

        try:
            response = requests.post(
                self.weni_capi_url, headers=headers, json=payload, timeout=self.timeout
            )

            if response.status_code == 200:
                print(f"CAPI: Event '{event_type}' sent successfully")
                return True
            else:
                print(f"CAPI: Failed to send event: {response.status_code}")
                return False

        except Exception as e:
            print(f"CAPI: Error sending event: {e}")
            return False

    def send_purchase_event(self, context: "SearchContext") -> bool:
        """
        Send purchase event manually.

        Useful to call after purchase confirmation.

        Args:
            context: Context with contact information

        Returns:
            True if sent successfully
        """
        contact_urn = context.get_contact("urn")
        channel_uuid = context.get_contact("channel_uuid")
        auth_token = context.credentials.get("auth_token")

        return self.send_event(
            auth_token=auth_token,
            channel_uuid=channel_uuid,
            contact_urn=contact_urn,
            event_type="purchase",
        )

    def reset(self) -> None:
        """Reset plugin state to allow new send."""
        self._sent = False
