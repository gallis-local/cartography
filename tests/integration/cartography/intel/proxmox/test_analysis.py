"""
Integration tests for Proxmox analysis jobs.

Tests each post-ingestion analysis job defined in cartography/data/jobs/analysis/
to verify they correctly enrich graph data with risk flags and computed properties.

Each test class uses a unique cluster ID to avoid cross-test contamination
(since the neo4j_session fixture is module-scoped).
"""

from cartography.util import run_analysis_job
from tests.integration.cartography.intel.proxmox import create_test_cluster

TEST_UPDATE_TAG = 123456789


class TestBackupAnalysis:
    def test_marks_disabled_backup_jobs(self, neo4j_session):
        c = "test-bak-disabled"
        create_test_cluster(neo4j_session, c, TEST_UPDATE_TAG)
        neo4j_session.run(
            "MERGE (j:ProxmoxBackupJob {id: $id1}) SET j.enabled=false, j.cluster_id=$c, j.lastupdated=$u, j.schedule='0 2 * * *' MERGE (j2:ProxmoxBackupJob {id: $id2}) SET j2.enabled=true, j2.cluster_id=$c, j2.lastupdated=$u, j2.schedule='0 3 * * *'",
            id1=f"{c}/backup/disabled-job",
            id2=f"{c}/backup/enabled-job",
            c=c,
            u=TEST_UPDATE_TAG,
        )
        run_analysis_job(
            "proxmox_backup_analysis.json",
            neo4j_session,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "CLUSTER_ID": c},
        )
        rows = {
            r["id"]: r["risk"]
            for r in neo4j_session.run(
                "MATCH (j:ProxmoxBackupJob) RETURN j.id as id, j.backup_risk as risk"
            )
        }
        assert rows.get(f"{c}/backup/disabled-job") is True
        risk = rows.get(f"{c}/backup/enabled-job")
        assert risk is None or risk is False

    def test_marks_jobs_without_retention(self, neo4j_session):
        c = "test-bak-retention"
        create_test_cluster(neo4j_session, c, TEST_UPDATE_TAG)
        neo4j_session.run(
            "MERGE (j:ProxmoxBackupJob {id: $id_with}) SET j.enabled=true, j.cluster_id=$c, j.prune_keep_last=7, j.lastupdated=$u, j.schedule='0 2 * * *' MERGE (j2:ProxmoxBackupJob {id: $id_without}) SET j2.enabled=true, j2.cluster_id=$c, j2.lastupdated=$u, j2.schedule='0 3 * * *'",
            id_with=f"{c}/backup/with-retention",
            id_without=f"{c}/backup/no-retention",
            c=c,
            u=TEST_UPDATE_TAG,
        )
        run_analysis_job(
            "proxmox_backup_analysis.json",
            neo4j_session,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "CLUSTER_ID": c},
        )
        rows = {
            r["id"]: r["risk"]
            for r in neo4j_session.run(
                "MATCH (j:ProxmoxBackupJob) RETURN j.id as id, j.retention_risk as risk"
            )
        }
        assert rows.get(f"{c}/backup/no-retention") is True
        risk = rows.get(f"{c}/backup/with-retention")
        assert risk is None or risk is False

    def test_marks_unbacked_up_vms(self, neo4j_session):
        c = "test-bak-unbacked"
        create_test_cluster(neo4j_session, c, TEST_UPDATE_TAG)
        neo4j_session.run(
            "MERGE (v1:ProxmoxVM {id: $unbacked}) SET v1.template=false, v1.vmid=100, v1.cluster_id=$c, v1.lastupdated=$u MERGE (v2:ProxmoxVM {id: $backed}) SET v2.template=false, v2.vmid=101, v2.cluster_id=$c, v2.lastupdated=$u MERGE (j:ProxmoxBackupJob {id: $job}) SET j.enabled=true, j.cluster_id=$c, j.lastupdated=$u, j.schedule='0 2 * * *' MERGE (j)-[:BACKS_UP]->(v2)",
            unbacked=f"{c}/vm/100",
            backed=f"{c}/vm/101",
            job=f"{c}/backup/test-job",
            c=c,
            u=TEST_UPDATE_TAG,
        )
        run_analysis_job(
            "proxmox_backup_analysis.json",
            neo4j_session,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "CLUSTER_ID": c},
        )
        rows = {
            r["id"]: r["risk"]
            for r in neo4j_session.run(
                "MATCH (v:ProxmoxVM) RETURN v.id as id, v.backup_risk as risk"
            )
        }
        assert rows.get(f"{c}/vm/100") is True
        risk = rows.get(f"{c}/vm/101")
        assert risk is None or risk is False


class TestReplicationAnalysis:
    def test_marks_disabled_replication_jobs(self, neo4j_session):
        c = "test-rep-disabled"
        create_test_cluster(neo4j_session, c, TEST_UPDATE_TAG)
        neo4j_session.run(
            "MERGE (r:ProxmoxReplicationJob {id: $id1}) SET r.disable = true, r.cluster_id = $c, r.lastupdated = $u, r.job_id = '100-0' MERGE (r2:ProxmoxReplicationJob {id: $id2}) SET r2.disable = false, r2.cluster_id = $c, r2.lastupdated = $u, r2.job_id = '101-0'",
            id1=f"{c}/replication/100-0",
            id2=f"{c}/replication/101-0",
            c=c,
            u=TEST_UPDATE_TAG,
        )
        run_analysis_job(
            "proxmox_replication_analysis.json",
            neo4j_session,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "CLUSTER_ID": c},
        )
        rows = {
            r["id"]: r["risk"]
            for r in neo4j_session.run(
                "MATCH (r:ProxmoxReplicationJob) RETURN r.id as id, r.replication_risk as risk"
            )
        }
        assert rows.get(f"{c}/replication/100-0") is True
        risk = rows.get(f"{c}/replication/101-0")
        assert risk is None or risk is False

    def test_marks_jobs_without_target_node(self, neo4j_session):
        c = "test-rep-target"
        create_test_cluster(neo4j_session, c, TEST_UPDATE_TAG)
        neo4j_session.run(
            "CREATE (n:ProxmoxNode {id: $nid}) SET n.name='node1', n.status='online', n.cluster_id=$c, n.lastupdated=$u CREATE (r1:ProxmoxReplicationJob {id: $id1}) SET r1.disable=false, r1.cluster_id=$c, r1.lastupdated=$u, r1.job_id='100-0', r1.rate=10 CREATE (r2:ProxmoxReplicationJob {id: $id2}) SET r2.disable=false, r2.cluster_id=$c, r2.lastupdated=$u, r2.job_id='101-0', r2.rate=10 CREATE (r1)-[:REPLICATES_TO]->(n)",
            nid=f"{c}/node/node1",
            id1=f"{c}/replication/100-0",
            id2=f"{c}/replication/101-0",
            c=c,
            u=TEST_UPDATE_TAG,
        )
        run_analysis_job(
            "proxmox_replication_analysis.json",
            neo4j_session,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "CLUSTER_ID": c},
        )
        rows = {
            r["id"]: r["risk"]
            for r in neo4j_session.run(
                "MATCH (r:ProxmoxReplicationJob) RETURN r.id as id, r.target_risk as risk"
            )
        }
        assert (
            rows.get(f"{c}/replication/100-0") is None
            or rows.get(f"{c}/replication/100-0") is False
        )
        assert rows.get(f"{c}/replication/101-0") is True


class TestHaAnalysis:
    CLUSTER = "test-ha-analysis"

    def test_marks_stopped_ha_resources(self, neo4j_session):
        create_test_cluster(neo4j_session, self.CLUSTER, TEST_UPDATE_TAG)
        neo4j_session.run(
            """
            MERGE (r1:ProxmoxHAResource {id: $id1})
            SET r1.state = 'started', r1.cluster_id = $cluster, r1.lastupdated = $update,
                r1.sid = 'vm:100'
            MERGE (r2:ProxmoxHAResource {id: $id2})
            SET r2.state = 'stopped', r2.cluster_id = $cluster, r2.lastupdated = $update,
                r2.sid = 'vm:101'
            """,
            id1=f"{self.CLUSTER}/ha/resource/vm:100",
            id2=f"{self.CLUSTER}/ha/resource/vm:101",
            cluster=self.CLUSTER,
            update=TEST_UPDATE_TAG,
        )
        run_analysis_job(
            "proxmox_ha_analysis.json",
            neo4j_session,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "CLUSTER_ID": self.CLUSTER},
        )
        rows = {
            r["id"]: r["risk"]
            for r in neo4j_session.run(
                "MATCH (r:ProxmoxHAResource) RETURN r.id as id, r.ha_risk as risk"
            )
        }
        assert (
            rows.get(f"{self.CLUSTER}/ha/resource/vm:100") is None
            or rows.get(f"{self.CLUSTER}/ha/resource/vm:100") is False
        )
        assert rows.get(f"{self.CLUSTER}/ha/resource/vm:101") is True


class TestCertificateAnalysis:
    def _create_cert(self, neo4j_session, cid, cluster, props):
        props_str = ", ".join(f"c.{k} = ${k}" for k in props)
        neo4j_session.run(
            f"MERGE (c:ProxmoxCertificate {{id: $id}}) SET c.cluster_id = $cluster, c.lastupdated = $update, {props_str}",
            id=cid,
            cluster=cluster,
            update=TEST_UPDATE_TAG,
            **props,
        )

    def test_marks_expired_certificates(self, neo4j_session):
        c = "test-cert-expired"
        create_test_cluster(neo4j_session, c, TEST_UPDATE_TAG)
        self._create_cert(
            neo4j_session,
            f"{c}/cert/expired",
            c,
            {"is_expired": True, "filename": "expired.pem"},
        )
        self._create_cert(
            neo4j_session,
            f"{c}/cert/valid",
            c,
            {"is_expired": False, "filename": "valid.pem"},
        )
        run_analysis_job(
            "proxmox_certificate_analysis.json",
            neo4j_session,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "CLUSTER_ID": c},
        )
        rows = {
            (r["id"], r["risk"], r["status"])
            for r in neo4j_session.run(
                "MATCH (c:ProxmoxCertificate) RETURN c.id as id, c.cert_risk as risk, c.cert_status as status"
            )
        }
        expired = [r for r in rows if r[0].endswith("expired")][0]
        assert expired[1] is True
        assert expired[2] == "expired"

    def test_marks_expiring_soon_certificates(self, neo4j_session):
        c = "test-cert-expiring"
        create_test_cluster(neo4j_session, c, TEST_UPDATE_TAG)
        self._create_cert(
            neo4j_session,
            f"{c}/cert/expiring",
            c,
            {"expires_soon": True, "filename": "expiring.pem", "is_expired": False},
        )
        run_analysis_job(
            "proxmox_certificate_analysis.json",
            neo4j_session,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "CLUSTER_ID": c},
        )
        row = neo4j_session.run(
            "MATCH (c:ProxmoxCertificate {id: $id}) RETURN c.cert_risk as risk, c.cert_status as status",
            id=f"{c}/cert/expiring",
        ).single()
        assert row["risk"] is True
        assert row["status"] == "expiring_soon"

    def test_marks_within_90d_certificates(self, neo4j_session):
        c = "test-cert-90d"
        create_test_cluster(neo4j_session, c, TEST_UPDATE_TAG)
        self._create_cert(
            neo4j_session,
            f"{c}/cert/within-90",
            c,
            {
                "expires_in_days": 60,
                "filename": "within-90.pem",
                "is_expired": False,
                "expires_soon": False,
            },
        )
        run_analysis_job(
            "proxmox_certificate_analysis.json",
            neo4j_session,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "CLUSTER_ID": c},
        )
        row = neo4j_session.run(
            "MATCH (c:ProxmoxCertificate {id: $id}) RETURN c.cert_status as status",
            id=f"{c}/cert/within-90",
        ).single()
        assert row["status"] == "expiring_within_90d"

    def test_marks_weak_key_certificates(self, neo4j_session):
        c = "test-cert-weak"
        create_test_cluster(neo4j_session, c, TEST_UPDATE_TAG)
        self._create_cert(
            neo4j_session,
            f"{c}/cert/weak",
            c,
            {
                "public_key_type": "RSA",
                "public_key_bits": 1024,
                "filename": "weak.pem",
                "is_expired": False,
            },
        )
        run_analysis_job(
            "proxmox_certificate_analysis.json",
            neo4j_session,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "CLUSTER_ID": c},
        )
        row = neo4j_session.run(
            "MATCH (c:ProxmoxCertificate {id: $id}) RETURN c.cert_risk as risk, c.cert_weak_key as weak",
            id=f"{c}/cert/weak",
        ).single()
        assert row["risk"] is True
        assert row["weak"] is True


class TestGuestAgentAnalysis:
    def test_marks_running_vms_without_agent(self, neo4j_session):
        c = "test-ga-noagent"
        create_test_cluster(neo4j_session, c, TEST_UPDATE_TAG)
        neo4j_session.run(
            "MERGE (v1:ProxmoxVM {id: $id1}) SET v1.status='running', v1.template=false, v1.cluster_id=$c, v1.vmid=100, v1.lastupdated=$u MERGE (v2:ProxmoxVM {id: $id2}) SET v2.status='running', v2.template=false, v2.agent_enabled=true, v2.guest_hostname='test-host', v2.cluster_id=$c, v2.vmid=101, v2.lastupdated=$u",
            id1=f"{c}/vm/100",
            id2=f"{c}/vm/101",
            c=c,
            u=TEST_UPDATE_TAG,
        )
        run_analysis_job(
            "proxmox_guest_agent_analysis.json",
            neo4j_session,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "CLUSTER_ID": c},
        )
        rows = {
            r["id"]: r["risk"]
            for r in neo4j_session.run(
                "MATCH (v:ProxmoxVM) RETURN v.id as id, v.agent_risk as risk"
            )
        }
        assert rows.get(f"{c}/vm/100") is True
        risk = rows.get(f"{c}/vm/101")
        assert risk is None or risk is False

    def test_marks_agent_enabled_but_not_responding(self, neo4j_session):
        c = "test-ga-noresp"
        create_test_cluster(neo4j_session, c, TEST_UPDATE_TAG)
        neo4j_session.run(
            "MERGE (v:ProxmoxVM {id: $id}) SET v.status='running', v.template=false, v.agent_enabled=true, v.guest_hostname='', v.cluster_id=$c, v.vmid=100, v.lastupdated=$u",
            id=f"{c}/vm/100",
            c=c,
            u=TEST_UPDATE_TAG,
        )
        run_analysis_job(
            "proxmox_guest_agent_analysis.json",
            neo4j_session,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "CLUSTER_ID": c},
        )
        row = neo4j_session.run(
            "MATCH (v:ProxmoxVM {id: $id}) RETURN v.agent_risk as risk",
            id=f"{c}/vm/100",
        ).single()
        assert row["risk"] is True

    def test_marks_eol_guest_os(self, neo4j_session):
        c = "test-ga-eol"
        create_test_cluster(neo4j_session, c, TEST_UPDATE_TAG)
        neo4j_session.run(
            "MERGE (v1:ProxmoxVM {id: $id1}) SET v1.guest_os_name='windows 7', v1.cluster_id=$c, v1.vmid=100, v1.lastupdated=$u, v1.template=false MERGE (v2:ProxmoxVM {id: $id2}) SET v2.guest_os_name='ubuntu 22.04', v2.cluster_id=$c, v2.vmid=101, v2.lastupdated=$u, v2.template=false",
            id1=f"{c}/vm/100",
            id2=f"{c}/vm/101",
            c=c,
            u=TEST_UPDATE_TAG,
        )
        run_analysis_job(
            "proxmox_guest_agent_analysis.json",
            neo4j_session,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "CLUSTER_ID": c},
        )
        rows = {
            r["id"]: r["risk"]
            for r in neo4j_session.run(
                "MATCH (v:ProxmoxVM) RETURN v.id as id, v.os_risk as risk"
            )
        }
        assert rows.get(f"{c}/vm/100") is True
        risk = rows.get(f"{c}/vm/101")
        assert risk is None or risk is False


class TestStorageAnalysis:
    def test_marks_critically_full_storage(self, neo4j_session):
        c = "test-stor-critical"
        create_test_cluster(neo4j_session, c, TEST_UPDATE_TAG)
        neo4j_session.run(
            "MERGE (s:ProxmoxStorage {id: $id}) SET s.total=100, s.used=95, s.enabled=true, s.cluster_id=$c, s.name='critical', s.lastupdated=$u",
            id=f"{c}/storage/critical",
            c=c,
            u=TEST_UPDATE_TAG,
        )
        run_analysis_job(
            "proxmox_storage_analysis.json",
            neo4j_session,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "CLUSTER_ID": c},
        )
        row = neo4j_session.run(
            "MATCH (s:ProxmoxStorage {id: $id}) RETURN s.storage_risk as risk, s.storage_status as status",
            id=f"{c}/storage/critical",
        ).single()
        assert row["risk"] is True
        assert row["status"] == "critical"

    def test_marks_warning_level_storage(self, neo4j_session):
        c = "test-stor-warning"
        create_test_cluster(neo4j_session, c, TEST_UPDATE_TAG)
        neo4j_session.run(
            "MERGE (s:ProxmoxStorage {id: $id}) SET s.total=100, s.used=85, s.enabled=true, s.cluster_id=$c, s.name='warning', s.lastupdated=$u",
            id=f"{c}/storage/warning",
            c=c,
            u=TEST_UPDATE_TAG,
        )
        run_analysis_job(
            "proxmox_storage_analysis.json",
            neo4j_session,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "CLUSTER_ID": c},
        )
        row = neo4j_session.run(
            "MATCH (s:ProxmoxStorage {id: $id}) RETURN s.storage_risk as risk, s.storage_status as status",
            id=f"{c}/storage/warning",
        ).single()
        assert row["risk"] is True
        assert row["status"] == "warning"

    def test_marks_disabled_storage(self, neo4j_session):
        c = "test-stor-disabled"
        create_test_cluster(neo4j_session, c, TEST_UPDATE_TAG)
        neo4j_session.run(
            "MERGE (s:ProxmoxStorage {id: $id}) SET s.enabled=false, s.total=100, s.used=10, s.cluster_id=$c, s.name='disabled', s.lastupdated=$u",
            id=f"{c}/storage/disabled",
            c=c,
            u=TEST_UPDATE_TAG,
        )
        run_analysis_job(
            "proxmox_storage_analysis.json",
            neo4j_session,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "CLUSTER_ID": c},
        )
        row = neo4j_session.run(
            "MATCH (s:ProxmoxStorage {id: $id}) RETURN s.storage_risk as risk, s.storage_status as status",
            id=f"{c}/storage/disabled",
        ).single()
        assert row["risk"] is True
        assert row["status"] == "disabled"


class TestOntologyLinking:
    def test_links_apitoken_to_canonical_user(self, neo4j_session):
        c = "test-onto-apitoken"
        create_test_cluster(neo4j_session, c, TEST_UPDATE_TAG)
        neo4j_session.run(
            "MERGE (key:ProxmoxAPIToken {id: $token_id}) SET key.cluster_id=$c, key.lastupdated=$u MERGE (pu:ProxmoxUser {id: $user_id}) SET pu.cluster_id=$c, pu.lastupdated=$u MERGE (u:User {id: $canonical_id}) MERGE (key)-[:BELONGS_TO]->(pu) MERGE (u)-[:HAS_ACCOUNT]->(pu)",
            token_id=f"{c}/apitoken/test-token",
            user_id=f"{c}/user/root@pam",
            canonical_id="urn:proxmox:user:root@pam",
            c=c,
            u=TEST_UPDATE_TAG,
        )
        run_analysis_job(
            "proxmox_ontology_linking.json",
            neo4j_session,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "CLUSTER_ID": c},
        )
        result = list(
            neo4j_session.run(
                "MATCH (u:User)-[:OWNS]->(key:ProxmoxAPIToken) RETURN u.id as uid, key.id as key_id"
            )
        )
        assert len(result) == 1
        assert result[0]["key_id"] == f"{c}/apitoken/test-token"

    def test_links_certificate_to_device(self, neo4j_session):
        c = "test-onto-cert"
        create_test_cluster(neo4j_session, c, TEST_UPDATE_TAG)
        neo4j_session.run(
            "MERGE (cert:ProxmoxCertificate {id: $cert_id}) SET cert.cluster_id=$c, cert.lastupdated=$u, cert.filename='test.pem' MERGE (pn:ProxmoxNode {id: $node_id}) SET pn.cluster_id=$c, pn.lastupdated=$u, pn.name='node1' MERGE (d:Device {id: $device_id}) MERGE (cert)<-[:HAS_CERTIFICATE]-(pn) MERGE (d)-[:OBSERVED_AS]->(pn)",
            cert_id=f"{c}/cert/test",
            node_id=f"{c}/node/node1",
            device_id="urn:proxmox:node:node1",
            c=c,
            u=TEST_UPDATE_TAG,
        )
        run_analysis_job(
            "proxmox_ontology_linking.json",
            neo4j_session,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "CLUSTER_ID": c},
        )
        result = list(
            neo4j_session.run(
                "MATCH (cert:ProxmoxCertificate)-[:HAS_CERTIFICATE]->(d:Device) RETURN cert.id as cert_id, d.id as device_id"
            )
        )
        assert len(result) == 1
