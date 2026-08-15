"""
OpenVAS task (scan), target, config, schedule, port list and credential ingestion.
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.openvas.credentials import OpenVASCredentialSchema
from cartography.models.openvas.credentials import OpenVASPortListSchema
from cartography.models.openvas.tasks import OpenVASConfigSchema
from cartography.models.openvas.tasks import OpenVASScheduleSchema
from cartography.models.openvas.tasks import OpenVASTargetSchema
from cartography.models.openvas.tasks import OpenVASTaskSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _transform_task(task: Any) -> dict:
    target = task.find("target")
    config = task.find("config")
    schedule = task.find("schedule")
    last_report = task.find("last_report")

    return {
        "id": task.get("id"),
        "name": task.findtext("name"),
        "comment": task.findtext("comment"),
        "status": task.findtext("status"),
        "alterable": task.findtext("alterable"),
        "creation_time": task.findtext("creation_time"),
        "modification_time": task.findtext("modification_time"),
        "last_report_id": last_report.get("id") if last_report is not None else None,
        "last_report_timestamp": (
            last_report.findtext("timestamp") if last_report is not None else None
        ),
        "last_report_severity": (
            last_report.findtext("severity") if last_report is not None else None
        ),
        "last_report_scan_start": (
            last_report.findtext("scan_start") if last_report is not None else None
        ),
        "last_report_scan_end": (
            last_report.findtext("scan_end") if last_report is not None else None
        ),
        "target_id": target.get("id") if target is not None else None,
        "target_name": target.findtext("name") if target is not None else None,
        "config_id": config.get("id") if config is not None else None,
        "config_name": config.findtext("name") if config is not None else None,
        "schedule_id": schedule.get("id") if schedule is not None else None,
        "schedule_name": schedule.findtext("name") if schedule is not None else None,
    }


def _transform_target(target: Any) -> dict:
    port_list = target.find("port_list")
    ssh_credential = target.find("ssh_credential")
    smb_credential = target.find("smb_credential")
    esxi_credential = target.find("esxi_credential")
    snmp_credential = target.find("snmp_credential")

    return {
        "id": target.get("id"),
        "name": target.findtext("name"),
        "comment": target.findtext("comment"),
        "creation_time": target.findtext("creation_time"),
        "modification_time": target.findtext("modification_time"),
        "hosts": target.findtext("hosts"),
        "max_hosts": target.findtext("max_hosts"),
        "exclude_hosts": target.findtext("exclude_hosts"),
        "port_list_id": port_list.get("id") if port_list is not None else None,
        "port_list_name": port_list.findtext("name") if port_list is not None else None,
        "alive_test": target.findtext("alive_test"),
        "allow_simultaneous_ips": target.findtext("allow_simultaneous_ips"),
        "reverse_lookup_only": target.findtext("reverse_lookup_only"),
        "reverse_lookup_unify": target.findtext("reverse_lookup_unify"),
        "ssh_credential_id": (
            ssh_credential.get("id") if ssh_credential is not None else None
        ),
        "smb_credential_id": (
            smb_credential.get("id") if smb_credential is not None else None
        ),
        "esxi_credential_id": (
            esxi_credential.get("id") if esxi_credential is not None else None
        ),
        "snmp_credential_id": (
            snmp_credential.get("id") if snmp_credential is not None else None
        ),
    }


def _transform_config(config: Any) -> dict:
    return {
        "id": config.get("id"),
        "name": config.findtext("name"),
        "comment": config.findtext("comment"),
        "config_type": config.findtext("config_type"),
        "usage_type": config.findtext("usage_type"),
        "family_count": config.findtext("family_count"),
        "nvt_count": config.findtext("nvt_count"),
        "creation_time": config.findtext("creation_time"),
        "modification_time": config.findtext("modification_time"),
    }


def _transform_schedule(schedule: Any) -> dict:
    return {
        "id": schedule.get("id"),
        "name": schedule.findtext("name"),
        "comment": schedule.findtext("comment"),
        "timezone": schedule.findtext("timezone"),
        "icalendar": schedule.findtext("icalendar"),
        "next_run": schedule.findtext("next_run"),
        "creation_time": schedule.findtext("creation_time"),
        "modification_time": schedule.findtext("modification_time"),
    }


def _transform_port_list(port_list: Any) -> dict:
    return {
        "id": port_list.get("id"),
        "name": port_list.findtext("name"),
        "comment": port_list.findtext("comment"),
        "port_count": port_list.findtext("port_count"),
        "creation_time": port_list.findtext("creation_time"),
        "modification_time": port_list.findtext("modification_time"),
    }


def _transform_credential(credential: Any) -> dict:
    return {
        "id": credential.get("id"),
        "name": credential.findtext("name"),
        "comment": credential.findtext("comment"),
        "credential_type": credential.findtext("type"),
        "allow_insecure": credential.findtext("allow_insecure"),
        "creation_time": credential.findtext("creation_time"),
        "modification_time": credential.findtext("modification_time"),
    }


def _get(gmp: Any, command: str) -> list:
    from cartography.intel.openvas import api

    return getattr(api, command)(gmp)


@timeit
def _load_nodes(
    neo4j_session: neo4j.Session,
    schema: Any,
    data: list,
    instance_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        schema,
        data,
        lastupdated=update_tag,
        OPENVAS_INSTANCE_ID=instance_id,
    )


@timeit
def _cleanup_nodes(
    neo4j_session: neo4j.Session,
    schema: Any,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(schema, common_job_parameters).run(neo4j_session)


@timeit
def sync_tasks_and_supporting(
    neo4j_session: neo4j.Session,
    gmp: Any,
    instance_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync OpenVAS tasks and their supporting resources into the graph.

    Leaf nodes (credentials, port lists, configs, schedules) are loaded before
    targets and tasks so that the USES/SCANS relationship targets exist when
    the edges are created.
    """
    logger.info("Syncing OpenVAS tasks and supporting resources")

    credentials = [_transform_credential(c) for c in _get(gmp, "get_credentials")]
    _load_nodes(
        neo4j_session, OpenVASCredentialSchema(), credentials, instance_id, update_tag
    )
    _cleanup_nodes(neo4j_session, OpenVASCredentialSchema(), common_job_parameters)

    port_lists = [_transform_port_list(p) for p in _get(gmp, "get_ports")]
    _load_nodes(
        neo4j_session, OpenVASPortListSchema(), port_lists, instance_id, update_tag
    )
    _cleanup_nodes(neo4j_session, OpenVASPortListSchema(), common_job_parameters)

    configs = [_transform_config(c) for c in _get(gmp, "get_configs")]
    _load_nodes(neo4j_session, OpenVASConfigSchema(), configs, instance_id, update_tag)
    _cleanup_nodes(neo4j_session, OpenVASConfigSchema(), common_job_parameters)

    schedules = [_transform_schedule(s) for s in _get(gmp, "get_schedules")]
    _load_nodes(
        neo4j_session, OpenVASScheduleSchema(), schedules, instance_id, update_tag
    )
    _cleanup_nodes(neo4j_session, OpenVASScheduleSchema(), common_job_parameters)

    targets = [_transform_target(t) for t in _get(gmp, "get_targets")]
    _load_nodes(neo4j_session, OpenVASTargetSchema(), targets, instance_id, update_tag)
    _cleanup_nodes(neo4j_session, OpenVASTargetSchema(), common_job_parameters)

    tasks = [_transform_task(t) for t in _get(gmp, "get_tasks")]
    _load_nodes(neo4j_session, OpenVASTaskSchema(), tasks, instance_id, update_tag)
    _cleanup_nodes(neo4j_session, OpenVASTaskSchema(), common_job_parameters)
