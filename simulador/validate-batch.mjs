import { createInterface } from "node:readline";
import { readFileSync, writeSync } from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

const engineRoot = process.argv[2];
const modelPath = process.argv[3];

if (!engineRoot || !modelPath) {
  console.error("uso: node validate-batch.mjs <spl-js-engine> <model.json>");
  process.exit(1);
}

const engineIndex = pathToFileURL(path.join(engineRoot, "src", "index.js")).href;
const { FeatureModel } = await import(engineIndex);
const featureModel = FeatureModel.fromJson(
  JSON.parse(readFileSync(modelPath, "utf8")),
);

function errorText(error) {
  if (error == null) {
    return "error";
  }
  if (typeof error === "string") {
    return error;
  }
  return error.message || String(error);
}

function completeOne(features) {
  try {
    const completed = featureModel.completeFeatureSelection(features);
    const asked = new Set(features);
    return {
      ok: true,
      features: completed,
      added: completed.filter((name) => !asked.has(name)),
      error: null,
    };
  } catch (error) {
    return {
      ok: false,
      features: features,
      added: [],
      error: errorText(error),
    };
  }
}

const input = createInterface({ input: process.stdin, terminal: false });

input.on("line", (line) => {
  const trimmed = line.trim();
  if (!trimmed) {
    return;
  }
  const batch = JSON.parse(trimmed);
  const results = batch.map((features) => completeOne(features));
  writeSync(1, `${JSON.stringify(results)}\n`);
});
