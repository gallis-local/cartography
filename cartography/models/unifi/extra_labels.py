from cartography.models.core.nodes import ExtraNodeLabel
from cartography.models.core.nodes import LabelKind

NETWORK_ACCESS_POINT = ExtraNodeLabel(
    label="NetworkAccessPoint",
    description="A unifi node participating in the shared NetworkAccessPoint graph interface.",
)


NETWORK_ADDRESS_TRANSLATION = ExtraNodeLabel(
    label="NetworkAddressTranslation",
    description="A unifi node participating in the shared NetworkAddressTranslation graph interface.",
)


NETWORK_CONTROLLER = ExtraNodeLabel(
    label="NetworkController",
    description="A unifi node participating in the shared NetworkController graph interface.",
)


NETWORK_ENDPOINT = ExtraNodeLabel(
    label="NetworkEndpoint",
    description="A unifi node participating in the shared NetworkEndpoint graph interface.",
)


NETWORK_GUEST_ACCESS = ExtraNodeLabel(
    label="NetworkGuestAccess",
    description="A unifi node participating in the shared NetworkGuestAccess graph interface.",
)


NETWORK_INFRASTRUCTURE_DEVICE = ExtraNodeLabel(
    label="NetworkInfrastructureDevice",
    description="A unifi node participating in the shared NetworkInfrastructureDevice graph interface.",
)


NETWORK_INTERFACE = ExtraNodeLabel(
    label="NetworkInterface",
    description="A unifi node participating in the shared NetworkInterface graph interface.",
)


NETWORK_PERFORMANCE_TEST = ExtraNodeLabel(
    label="NetworkPerformanceTest",
    description="A unifi node participating in the shared NetworkPerformanceTest graph interface.",
)


NETWORK_QOS_POLICY = ExtraNodeLabel(
    label="NetworkQoSPolicy",
    description="A unifi node participating in the shared NetworkQoSPolicy graph interface.",
)


NETWORK_ROUTING_POLICY = ExtraNodeLabel(
    label="NetworkRoutingPolicy",
    description="A unifi node participating in the shared NetworkRoutingPolicy graph interface.",
)


NETWORK_ROUTING_RULE = ExtraNodeLabel(
    label="NetworkRoutingRule",
    description="A unifi node participating in the shared NetworkRoutingRule graph interface.",
)


NETWORK_SECURITY_POLICY = ExtraNodeLabel(
    label="NetworkSecurityPolicy",
    description="A unifi node participating in the shared NetworkSecurityPolicy graph interface.",
)


NETWORK_ZONE = ExtraNodeLabel(
    label="NetworkZone",
    description="A unifi node participating in the shared NetworkZone graph interface.",
)


POWER_OUTLET = ExtraNodeLabel(
    label="PowerOutlet",
    description="A unifi node participating in the shared PowerOutlet graph interface.",
)


IOT_DEVICE = ExtraNodeLabel(
    label="IoTDevice",
    description="A unifi node participating in the shared IoTDevice graph interface.",
)
