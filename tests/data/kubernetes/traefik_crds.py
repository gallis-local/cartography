from tests.data.kubernetes.namespaces import KUBERNETES_CLUSTER_1_NAMESPACES_DATA

_TARGET_NS = KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"]

# ────────────────────────────────────────────────
# IngressRoute
# ────────────────────────────────────────────────

TRAEFIK_INGRESSROUTES_RAW = [
    {
        "apiVersion": "traefik.io/v1alpha1",
        "kind": "IngressRoute",
        "metadata": {
            "name": "my-ingressroute",
            "namespace": _TARGET_NS,
            "uid": "ir-uid-001",
            "creationTimestamp": "2021-10-07T06:21:06+00:00",
        },
        "spec": {
            "entryPoints": ["web", "websecure"],
            "routes": [
                {
                    "match": "Host(`app.example.com`) && PathPrefix(`/api`)",
                    "kind": "Rule",
                    "middlewares": [
                        {"name": "my-middleware"},
                    ],
                    "services": [
                        {"name": "api-service", "port": 80},
                        {"name": "app-service", "namespace": _TARGET_NS, "port": 8080},
                    ],
                },
            ],
            "tls": {
                "secretName": "my-tls-secret",
                "certResolver": "letsencrypt",
            },
        },
    },
]

TRAEFIK_INGRESSROUTES_DATA = [
    {
        "uid": "ir-uid-001",
        "name": "my-ingressroute",
        "namespace": _TARGET_NS,
        "qualified_name": f"{_TARGET_NS}/my-ingressroute",
        "entry_points": ["web", "websecure"],
        "hostnames": ["app.example.com"],
        "has_tls": True,
        "tls_secret_name": "my-tls-secret",
        "tls_cert_resolver": "letsencrypt",
        "backend_service_qualified_names": [
            f"{_TARGET_NS}/api-service",
            f"{_TARGET_NS}/app-service",
        ],
        "middleware_qualified_names": [
            f"{_TARGET_NS}/my-middleware",
        ],
        "parent_qualified_names": [],
        "creation_timestamp": 1633587666,
    },
]

# ────────────────────────────────────────────────
# IngressRouteTCP
# ────────────────────────────────────────────────

TRAEFIK_INGRESSROUTETCPS_RAW = [
    {
        "apiVersion": "traefik.io/v1alpha1",
        "kind": "IngressRouteTCP",
        "metadata": {
            "name": "my-tcp-route",
            "namespace": _TARGET_NS,
            "uid": "irtcp-uid-001",
            "creationTimestamp": "2021-10-07T06:22:00+00:00",
        },
        "spec": {
            "entryPoints": ["websecure"],
            "routes": [
                {
                    "match": "HostSNI(`*`)",
                    "services": [
                        {"name": "api-service", "port": 443},
                    ],
                },
            ],
            "tls": {
                "passthrough": True,
            },
        },
    },
]

TRAEFIK_INGRESSROUTETCPS_DATA = [
    {
        "uid": "irtcp-uid-001",
        "name": "my-tcp-route",
        "namespace": _TARGET_NS,
        "qualified_name": f"{_TARGET_NS}/my-tcp-route",
        "entry_points": ["websecure"],
        "has_tls": True,
        "tls_passthrough": True,
        "backend_service_qualified_names": [
            f"{_TARGET_NS}/api-service",
        ],
        "creation_timestamp": 1633587720,
    },
]

# ────────────────────────────────────────────────
# IngressRouteUDP
# ────────────────────────────────────────────────

TRAEFIK_INGRESSROUTEUDPS_RAW = [
    {
        "apiVersion": "traefik.io/v1alpha1",
        "kind": "IngressRouteUDP",
        "metadata": {
            "name": "my-udp-route",
            "namespace": _TARGET_NS,
            "uid": "irudp-uid-001",
            "creationTimestamp": "2021-10-07T06:23:00+00:00",
        },
        "spec": {
            "entryPoints": ["dnsserver"],
            "routes": [
                {
                    "services": [
                        {"name": "app-service", "port": 53},
                    ],
                },
            ],
        },
    },
]

TRAEFIK_INGRESSROUTEUDPS_DATA = [
    {
        "uid": "irudp-uid-001",
        "name": "my-udp-route",
        "namespace": _TARGET_NS,
        "qualified_name": f"{_TARGET_NS}/my-udp-route",
        "entry_points": ["dnsserver"],
        "backend_service_qualified_names": [
            f"{_TARGET_NS}/app-service",
        ],
        "creation_timestamp": 1633587780,
    },
]

# ────────────────────────────────────────────────
# Middleware
# ────────────────────────────────────────────────

TRAEFIK_MIDDLEWARES_RAW = [
    {
        "apiVersion": "traefik.io/v1alpha1",
        "kind": "Middleware",
        "metadata": {
            "name": "my-middleware",
            "namespace": _TARGET_NS,
            "uid": "mw-uid-001",
            "creationTimestamp": "2021-10-07T06:20:00+00:00",
        },
        "spec": {
            "forwardAuth": {
                "address": "https://auth.example.com/auth",
            },
        },
    },
]

TRAEFIK_MIDDLEWARES_DATA = [
    {
        "uid": "mw-uid-001",
        "name": "my-middleware",
        "namespace": _TARGET_NS,
        "qualified_name": f"{_TARGET_NS}/my-middleware",
        "middleware_type": "forwardAuth",
        "creation_timestamp": 1633587600,
    },
]
