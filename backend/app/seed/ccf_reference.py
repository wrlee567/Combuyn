"""Bundled CCF reference data — Iteration 1.

A curated, *real* starter set: three enterprise frameworks with current
citations, plus common controls that demonstrate the many-to-many payoff (one
control satisfying SOC 2 + PCI DSS + NIST 800-53 simultaneously).

Framework versions reflect the current standards as of 2025-2026:
  - SOC 2          : 2017 Trust Services Criteria (incl. 2022 points of focus)
  - PCI DSS        : v4.0.1
  - NIST 800-53    : Rev 5

This is intentionally a representative subset, not the full control catalogs.
Later iterations can ingest the Secure Controls Framework export wholesale.
"""

from __future__ import annotations

# Frameworks keyed by stable slug.
FRAMEWORKS: list[dict] = [
    {
        "key": "soc2",
        "name": "SOC 2",
        "version": "2017 TSC",
        "authority": "AICPA",
        "category": "enterprise",
        "description": "Trust Services Criteria for Security, Availability, "
        "Processing Integrity, Confidentiality, and Privacy.",
    },
    {
        "key": "pci_dss",
        "name": "PCI DSS",
        "version": "v4.0.1",
        "authority": "PCI Security Standards Council",
        "category": "enterprise",
        "description": "Payment Card Industry Data Security Standard.",
    },
    {
        "key": "nist_800_53",
        "name": "NIST 800-53",
        "version": "Rev 5",
        "authority": "NIST",
        "category": "enterprise",
        "description": "Security and Privacy Controls for Information Systems "
        "and Organizations.",
    },
]

# Requirements per framework: (citation, title, description).
REQUIREMENTS: dict[str, list[tuple[str, str, str]]] = {
    "soc2": [
        ("CC6.1", "Logical access security controls",
         "Implements logical access security software, infrastructure, and "
         "architectures over protected information assets."),
        ("CC6.6", "Boundary protection",
         "Implements controls to protect against threats from sources outside "
         "its system boundaries."),
        ("CC6.7", "Restrict data transmission",
         "Restricts the transmission, movement, and removal of information and "
         "protects it during transmission."),
        ("CC7.2", "Security event monitoring",
         "Monitors system components for anomalies indicative of malicious acts, "
         "natural disasters, and errors."),
        ("CC8.1", "Change management",
         "Authorizes, designs, develops, tests, approves, and implements changes "
         "to infrastructure, data, and software."),
    ],
    "pci_dss": [
        ("3.5", "Protect stored account data",
         "Primary account number (PAN) is secured wherever it is stored."),
        ("1.2", "Network security controls configuration",
         "Network security controls (NSCs) are configured and maintained."),
        ("8.3", "Strong authentication for access",
         "Strong authentication for users and administrators is established and "
         "managed."),
        ("10.2", "Audit logs capture events",
         "Audit logs are implemented to support the detection of anomalies and "
         "suspicious activity."),
        ("6.3", "Security in software development",
         "Security vulnerabilities are identified and addressed; bespoke and "
         "custom software is developed securely."),
    ],
    "nist_800_53": [
        ("SC-28", "Protection of information at rest",
         "Protect the confidentiality and integrity of information at rest."),
        ("SC-7", "Boundary protection",
         "Monitor and control communications at external and key internal "
         "boundaries of the system."),
        ("SC-8", "Transmission confidentiality and integrity",
         "Protect the confidentiality and integrity of transmitted information."),
        ("AC-2", "Account management",
         "Manage system accounts, including establishment, activation, "
         "modification, review, and removal."),
        ("AU-2", "Event logging",
         "Identify the types of events that the system is capable of logging in "
         "support of the audit function."),
        ("CM-3", "Configuration change control",
         "Determine and document the types of changes to the system that are "
         "configuration-controlled."),
    ],
}

# Common controls and the framework requirements each one satisfies.
# Each mapping is (framework_key, citation, relationship_type).
COMMON_CONTROLS: list[dict] = [
    {
        "key": "CCF-CRYPTO-001",
        "name": "Data Encryption at Rest",
        "domain": "Cryptographic Protections",
        "description": "All sensitive data and account data is encrypted at rest "
        "using approved, strong cryptography with managed keys.",
        "maps": [
            ("nist_800_53", "SC-28", "equal"),
            ("pci_dss", "3.5", "subset"),
            ("soc2", "CC6.1", "intersects"),
        ],
    },
    {
        "key": "CCF-NET-001",
        "name": "Network Boundary Protection",
        "domain": "Network Security",
        "description": "Boundary defenses (firewalls / network security controls) "
        "monitor and restrict traffic at external and key internal boundaries.",
        "maps": [
            ("nist_800_53", "SC-7", "equal"),
            ("pci_dss", "1.2", "subset"),
            ("soc2", "CC6.6", "intersects"),
        ],
    },
    {
        "key": "CCF-CRYPTO-002",
        "name": "Encryption in Transit",
        "domain": "Cryptographic Protections",
        "description": "Sensitive data is protected with strong cryptography "
        "(TLS 1.2+) during transmission over untrusted networks.",
        "maps": [
            ("nist_800_53", "SC-8", "equal"),
            ("pci_dss", "1.2", "intersects"),
            ("soc2", "CC6.7", "intersects"),
        ],
    },
    {
        "key": "CCF-IAM-001",
        "name": "Identity & Access Management",
        "domain": "Identification & Authentication",
        "description": "User accounts are provisioned, reviewed, and de-provisioned "
        "under least privilege, with strong (multi-factor) authentication.",
        "maps": [
            ("nist_800_53", "AC-2", "equal"),
            ("pci_dss", "8.3", "subset"),
            ("soc2", "CC6.1", "intersects"),
        ],
    },
    {
        "key": "CCF-LOG-001",
        "name": "Audit Logging & Monitoring",
        "domain": "Continuous Monitoring",
        "description": "Security-relevant events are logged centrally and "
        "monitored for anomalies and suspicious activity.",
        "maps": [
            ("nist_800_53", "AU-2", "equal"),
            ("pci_dss", "10.2", "subset"),
            ("soc2", "CC7.2", "intersects"),
        ],
    },
    {
        "key": "CCF-SDLC-001",
        "name": "Secure Change Management",
        "domain": "Change Management",
        "description": "Changes to systems and software are authorized, tested, "
        "and securely developed before deployment.",
        "maps": [
            ("nist_800_53", "CM-3", "equal"),
            ("pci_dss", "6.3", "intersects"),
            ("soc2", "CC8.1", "intersects"),
        ],
    },
]
