"""
Data models for the OpenVAS intel module.
"""

from cartography.models.openvas.credentials import OpenVASCredentialSchema
from cartography.models.openvas.credentials import OpenVASPortListSchema
from cartography.models.openvas.hosts import OpenVASHostSchema
from cartography.models.openvas.instance import OpenVASInstanceSchema
from cartography.models.openvas.results import OpenVASNVTSchema
from cartography.models.openvas.results import OpenVASResultSchema
from cartography.models.openvas.tasks import OpenVASConfigSchema
from cartography.models.openvas.tasks import OpenVASScheduleSchema
from cartography.models.openvas.tasks import OpenVASTargetSchema
from cartography.models.openvas.tasks import OpenVASTaskSchema
from cartography.models.openvas.tls_certificates import OpenVASTLSCertificateSchema

__all__ = [
    "OpenVASCredentialSchema",
    "OpenVASPortListSchema",
    "OpenVASHostSchema",
    "OpenVASInstanceSchema",
    "OpenVASNVTSchema",
    "OpenVASResultSchema",
    "OpenVASConfigSchema",
    "OpenVASScheduleSchema",
    "OpenVASTargetSchema",
    "OpenVASTaskSchema",
    "OpenVASTLSCertificateSchema",
]
