// Bundled demo data so the frontend renders a complete, realistic view when no
// backend is reachable (e.g. a Vercel preview deploy before the Render API is
// wired up). Mirrors the backend CCF seed in app/seed/ccf_reference.py.
import type { ControlCoverage, Framework, Summary } from "./api";

export const demoSummary: Summary = {
  frameworks: 3,
  requirements: 16,
  common_controls: 6,
  mappings: 18,
};

export const demoFrameworks: Framework[] = [
  {
    id: "demo-soc2",
    key: "soc2",
    name: "SOC 2",
    version: "2017 TSC",
    authority: "AICPA",
    description:
      "Trust Services Criteria for Security, Availability, Processing Integrity, Confidentiality, and Privacy.",
    category: "enterprise",
    requirement_count: 5,
  },
  {
    id: "demo-pci",
    key: "pci_dss",
    name: "PCI DSS",
    version: "v4.0.1",
    authority: "PCI Security Standards Council",
    description: "Payment Card Industry Data Security Standard.",
    category: "enterprise",
    requirement_count: 5,
  },
  {
    id: "demo-nist",
    key: "nist_800_53",
    name: "NIST 800-53",
    version: "Rev 5",
    authority: "NIST",
    description:
      "Security and Privacy Controls for Information Systems and Organizations.",
    category: "enterprise",
    requirement_count: 6,
  },
];

export const demoCoverage: ControlCoverage[] = [
  {
    id: "demo-crypto-001",
    key: "CCF-CRYPTO-001",
    name: "Data Encryption at Rest",
    domain: "Cryptographic Protections",
    description:
      "All sensitive data and account data is encrypted at rest using approved, strong cryptography with managed keys.",
    frameworks_covered: ["NIST 800-53", "PCI DSS", "SOC 2"],
    requirements: [
      { framework_key: "nist_800_53", framework_name: "NIST 800-53", citation: "SC-28", title: "Protection of information at rest", relationship_type: "equal" },
      { framework_key: "pci_dss", framework_name: "PCI DSS", citation: "3.5", title: "Protect stored account data", relationship_type: "subset" },
      { framework_key: "soc2", framework_name: "SOC 2", citation: "CC6.1", title: "Logical access security controls", relationship_type: "intersects" },
    ],
  },
  {
    id: "demo-net-001",
    key: "CCF-NET-001",
    name: "Network Boundary Protection",
    domain: "Network Security",
    description:
      "Boundary defenses monitor and restrict traffic at external and key internal boundaries.",
    frameworks_covered: ["NIST 800-53", "PCI DSS", "SOC 2"],
    requirements: [
      { framework_key: "nist_800_53", framework_name: "NIST 800-53", citation: "SC-7", title: "Boundary protection", relationship_type: "equal" },
      { framework_key: "pci_dss", framework_name: "PCI DSS", citation: "1.2", title: "Network security controls configuration", relationship_type: "subset" },
      { framework_key: "soc2", framework_name: "SOC 2", citation: "CC6.6", title: "Boundary protection", relationship_type: "intersects" },
    ],
  },
  {
    id: "demo-crypto-002",
    key: "CCF-CRYPTO-002",
    name: "Encryption in Transit",
    domain: "Cryptographic Protections",
    description:
      "Sensitive data is protected with strong cryptography (TLS 1.2+) during transmission over untrusted networks.",
    frameworks_covered: ["NIST 800-53", "PCI DSS", "SOC 2"],
    requirements: [
      { framework_key: "nist_800_53", framework_name: "NIST 800-53", citation: "SC-8", title: "Transmission confidentiality and integrity", relationship_type: "equal" },
      { framework_key: "pci_dss", framework_name: "PCI DSS", citation: "1.2", title: "Network security controls configuration", relationship_type: "intersects" },
      { framework_key: "soc2", framework_name: "SOC 2", citation: "CC6.7", title: "Restrict data transmission", relationship_type: "intersects" },
    ],
  },
  {
    id: "demo-iam-001",
    key: "CCF-IAM-001",
    name: "Identity & Access Management",
    domain: "Identification & Authentication",
    description:
      "User accounts are provisioned, reviewed, and de-provisioned under least privilege, with strong (multi-factor) authentication.",
    frameworks_covered: ["NIST 800-53", "PCI DSS", "SOC 2"],
    requirements: [
      { framework_key: "nist_800_53", framework_name: "NIST 800-53", citation: "AC-2", title: "Account management", relationship_type: "equal" },
      { framework_key: "pci_dss", framework_name: "PCI DSS", citation: "8.3", title: "Strong authentication for access", relationship_type: "subset" },
      { framework_key: "soc2", framework_name: "SOC 2", citation: "CC6.1", title: "Logical access security controls", relationship_type: "intersects" },
    ],
  },
  {
    id: "demo-log-001",
    key: "CCF-LOG-001",
    name: "Audit Logging & Monitoring",
    domain: "Continuous Monitoring",
    description:
      "Security-relevant events are logged centrally and monitored for anomalies and suspicious activity.",
    frameworks_covered: ["NIST 800-53", "PCI DSS", "SOC 2"],
    requirements: [
      { framework_key: "nist_800_53", framework_name: "NIST 800-53", citation: "AU-2", title: "Event logging", relationship_type: "equal" },
      { framework_key: "pci_dss", framework_name: "PCI DSS", citation: "10.2", title: "Audit logs capture events", relationship_type: "subset" },
      { framework_key: "soc2", framework_name: "SOC 2", citation: "CC7.2", title: "Security event monitoring", relationship_type: "intersects" },
    ],
  },
  {
    id: "demo-sdlc-001",
    key: "CCF-SDLC-001",
    name: "Secure Change Management",
    domain: "Change Management",
    description:
      "Changes to systems and software are authorized, tested, and securely developed before deployment.",
    frameworks_covered: ["NIST 800-53", "PCI DSS", "SOC 2"],
    requirements: [
      { framework_key: "nist_800_53", framework_name: "NIST 800-53", citation: "CM-3", title: "Configuration change control", relationship_type: "equal" },
      { framework_key: "pci_dss", framework_name: "PCI DSS", citation: "6.3", title: "Security in software development", relationship_type: "intersects" },
      { framework_key: "soc2", framework_name: "SOC 2", citation: "CC8.1", title: "Change management", relationship_type: "intersects" },
    ],
  },
];
