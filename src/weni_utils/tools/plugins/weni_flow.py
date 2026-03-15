"""
WeniFlowTrigger Plugin - Weni Flow Triggering

Plugin for triggering flows on the Weni platform during product search.
Useful for tracking, analytics or custom actions.
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

import requests

from .base import PluginBase

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    # from ..client import VTEXClient
    from ..context import SearchContext


class WeniFlowTrigger(PluginBase):
    """
    Plugin for triggering Weni flows.

    Features:
    - Triggers flows after product search
    - Passes custom parameters to the flow
    - Controls single execution per session

    Example:
        concierge = ProductConcierge(
            base_url_vtex="...",
            store_url_vtex="...",
            plugins=[
                WeniFlowTrigger(
                    flow_uuid="flow-uuid",
                    trigger_once=True
                )
            ]
        )

        result = concierge.search(
            product_name="drill",
            credentials={
                "API_TOKEN_WENI": "your-token"
            },
            contact_info={
                "urn": "whatsapp:5511999999999"
            }
        )
    """

    name = "weni_flow_trigger"

    def __init__(
        self,
        flow_uuid: Optional[str] = None,
        weni_api_url: str = "https://flows.weni.ai/api/v2/flow_starts.json",
        trigger_once: bool = True,
        flow_params: Optional[Dict[str, Any]] = None,
        timeout: int = 10,
    ):
        """
        Initialize the Weni flow plugin.

        Args:
            flow_uuid: UUID of the flow to trigger (can come from credentials)
            weni_api_url: Flows API URL
            trigger_once: If True, triggers only once per session
            flow_params: Extra parameters to pass to the flow
            timeout: Request timeout
        """
        self.flow_uuid = flow_uuid
        self.weni_api_url = weni_api_url
        self.trigger_once = trigger_once
        self.flow_params = flow_params or {}
        self.timeout = timeout
        self._triggered = False

    def finalize_result(self, result: Dict[str, Any], context: "SearchContext") -> Dict[str, Any]:
        """
        Trigger flow after finalizing result.
        """
        # Check if already triggered (if trigger_once=True)
        if self.trigger_once and self._triggered:
            return result

        # Get credentials
        api_token = context.get_credential("API_TOKEN_WENI")
        flow_uuid = self.flow_uuid or context.get_credential("EVENT_ID_CONCIERGE")
        contact_urn = context.get_contact("urn")

        if not all([api_token, flow_uuid, contact_urn]):
            return result

        success = self.trigger_flow(
            api_token=api_token,
            flow_uuid=flow_uuid,
            contact_urn=contact_urn,
            params=self.flow_params,
        )

        if success:
            self._triggered = True

        return result

    def trigger_flow(
        self,
        api_token: str,
        flow_uuid: str,
        contact_urn: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Trigger a Weni flow.

        Args:
            api_token: Authentication token
            flow_uuid: Flow UUID
            contact_urn: Contact URN
            params: Parameters for the flow

        Returns:
            True if triggered successfully
        """
        headers = {"Authorization": f"Token {api_token}", "Content-Type": "application/json"}

        payload = {"flow": flow_uuid, "urns": [contact_urn], "params": params or {"executions": 1}}

        try:
            response = requests.post(
                self.weni_api_url, headers=headers, json=payload, timeout=self.timeout
            )

            if response.status_code == 200:
                logger.info("Flow %s triggered for contact %s", flow_uuid, contact_urn)
                return True
            else:
                logger.error(
                    "Flow trigger failed: status=%d flow=%s", response.status_code, flow_uuid
                )
                return False

        except Exception as e:
            logger.error("Flow trigger error for flow=%s: %s", flow_uuid, e)
            return False

    def reset(self) -> None:
        """Reset plugin state to allow new trigger."""
        self._triggered = False
