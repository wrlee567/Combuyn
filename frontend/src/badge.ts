// Map a framework key/name to a CSS badge class.
export function badgeClass(frameworkKey: string): string {
  const k = frameworkKey.toLowerCase();
  if (k.includes("soc")) return "badge soc2";
  if (k.includes("pci")) return "badge pci";
  if (k.includes("nist")) return "badge nist";
  return "badge generic";
}

// Map an inherent-risk tier to a CSS badge class.
export function riskClass(tier: string): string {
  return `badge risk-${tier.toLowerCase()}`;
}

// Human-friendly label for snake_case enum values (e.g. "financial_services").
export function humanize(value: string): string {
  return value
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}
