import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(dirname(fileURLToPath(import.meta.url)));

function read(path) {
  return readFileSync(join(root, path), "utf8");
}

function assertContains(file, expected, message) {
  const text = read(file);
  if (!text.includes(expected)) {
    throw new Error(`${message}\nMissing in ${file}: ${expected}`);
  }
}

function assertRegex(file, pattern, message) {
  const text = read(file);
  if (!pattern.test(text)) {
    throw new Error(`${message}\nPattern not found in ${file}: ${pattern}`);
  }
}

const addVendor = "src/pages/AddVendor.tsx";
[
  "vendor-name",
  "vendor-contact-name",
  "vendor-contact-email",
  "vendor-description",
].forEach((id) => {
  assertContains(addVendor, `htmlFor="${id}"`, "Add Vendor controls must keep programmatic labels.");
  assertContains(addVendor, `id="${id}"`, "Add Vendor controls must keep label target IDs.");
});
assertContains(
  addVendor,
  "htmlFor={`vendor-${key}`}",
  "Add Vendor select helper must keep programmatic labels.",
);
assertContains(
  addVendor,
  "id={`vendor-${key}`}",
  "Add Vendor select helper must keep label target IDs.",
);

assertContains(
  "src/pages/VendorDetail.tsx",
  'aria-label="Lifecycle phase"',
  "Vendor detail lifecycle select must keep an accessible name.",
);
assertRegex(
  "src/pages/VendorDetail.tsx",
  /aria-label=\{q\.text\}/,
  "Questionnaire controls must use question text as their accessible name.",
);

["src/pages/Vendors.tsx", "src/pages/Workflows.tsx"].forEach((file) => {
  assertContains(file, "tabIndex={0}", "Clickable rows must remain keyboard reachable.");
  assertContains(file, 'role="link"', "Clickable rows must expose link semantics.");
  assertContains(file, "onKeyDown=", "Clickable rows must handle keyboard activation.");
});

assertContains(
  "src/styles.css",
  ":focus-visible",
  "Interactive controls must keep visible focus styling.",
);
assertContains(
  "src/api.ts",
  "function formatApiDetail",
  "API validation details must be formatted before display.",
);

console.log("Quality smoke checks passed.");
