#!/usr/bin/env node
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";

const home = process.env.VOICEBOX_CLI_HOME || path.join(os.homedir(), ".voicebox-cli");
const executable = process.platform === "win32"
  ? path.join(home, "venv", "Scripts", "cli-anything-voicebox.exe")
  : path.join(home, "venv", "bin", "cli-anything-voicebox");

if (!fs.existsSync(executable)) {
  console.error("Voicebox CLI is not installed yet.");
  console.error("Run: voicebox-cli-agent-skill setup");
  process.exit(1);
}

const result = spawnSync(executable, process.argv.slice(2), { stdio: "inherit" });
process.exit(result.status ?? 1);

