// Map a framework key/name to a CSS badge class.
export function badgeClass(frameworkKey: string): string {
  const k = frameworkKey.toLowerCase();
  if (k.includes("soc")) return "badge soc2";
  if (k.includes("pci")) return "badge pci";
  if (k.includes("nist")) return "badge nist";
  return "badge generic";
}
