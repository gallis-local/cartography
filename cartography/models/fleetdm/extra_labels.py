from cartography.models.core.nodes import ExtraNodeLabel
from cartography.models.core.nodes import LabelKind

FINDING = ExtraNodeLabel(
    label="Finding",
    description="A fleetdm node participating in the shared Finding graph interface.",
)


RISK = ExtraNodeLabel(
    label="Risk",
    description="A fleetdm node participating in the shared Risk graph interface.",
)
