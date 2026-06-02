#!/usr/bin/env node
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const packageRoot = path.resolve(__dirname, "..");
const source = path.join(packageRoot, "skills", "voicebox-cli");

const codexHome = process.env.CODEX_HOME || path.join(os.homedir(), ".codex");
const globalAgentsHome = process.env.AGENTS_HOME || path.join(os.homedir(), ".agents");
const destinationRoots = process.env.AGENT_SKILLS_DIR
  ? [process.env.AGENT_SKILLS_DIR]
  : [
      path.join(codexHome, "skills"),
      path.join(globalAgentsHome, "skills"),
    ];

if (!fs.existsSync(source)) {
  console.error(`Skill source not found: ${source}`);
  process.exit(1);
}

for (const destinationRoot of destinationRoots) {
  const destination = path.join(destinationRoot, "voicebox-cli");
  fs.mkdirSync(destinationRoot, { recursive: true });
  fs.rmSync(destination, { recursive: true, force: true });
  fs.cpSync(source, destination, { recursive: true });

  console.log(`Installed voicebox-cli skill to ${destination}`);
}
