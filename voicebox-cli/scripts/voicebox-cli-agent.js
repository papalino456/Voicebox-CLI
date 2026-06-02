#!/usr/bin/env node
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const packageRoot = path.resolve(__dirname, "..");
const home = process.env.VOICEBOX_CLI_HOME || path.join(os.homedir(), ".voicebox-cli");
const venv = path.join(home, "venv");
const binDir = process.env.VOICEBOX_CLI_BIN_DIR || (
  process.platform === "win32" ? path.join(home, "bin") : path.join(os.homedir(), ".local", "bin")
);

function usage() {
  console.log(`Voicebox CLI Agent installer

Usage:
  voicebox-cli-agent-skill setup          Install Python CLI and agent skill
  voicebox-cli-agent-skill install-cli    Install only the Python CLI
  voicebox-cli-agent-skill install-skill  Install only the agent skill
  voicebox-cli-agent-skill status         Show install paths

Environment:
  VOICEBOX_CLI_HOME   Managed CLI home. Default: ~/.voicebox-cli
  VOICEBOX_CLI_BIN_DIR Directory for persistent command shims. Default: ~/.local/bin
  VOICEBOX_CLI_PYTHON Python executable. Default: python3, or python on Windows
  CODEX_HOME          Agent home for skills. Default: ~/.codex
  AGENT_SKILLS_DIR    Explicit skills directory override
`);
}

function run(command, args, options = {}) {
  const result = spawnSync(command, args, { stdio: "inherit", ...options });
  if (result.status !== 0) {
    const rendered = [command, ...args].join(" ");
    throw new Error(`Command failed: ${rendered}`);
  }
}

function pythonCommand() {
  if (process.env.VOICEBOX_CLI_PYTHON) {
    return process.env.VOICEBOX_CLI_PYTHON;
  }
  return process.platform === "win32" ? "python" : "python3";
}

function pythonInVenv() {
  return process.platform === "win32"
    ? path.join(venv, "Scripts", "python.exe")
    : path.join(venv, "bin", "python");
}

function cliExecutable() {
  return process.platform === "win32"
    ? path.join(venv, "Scripts", "cli-anything-voicebox.exe")
    : path.join(venv, "bin", "cli-anything-voicebox");
}

function installCli() {
  fs.mkdirSync(home, { recursive: true });
  if (!fs.existsSync(pythonInVenv())) {
    console.log(`Creating Python venv at ${venv}`);
    run(pythonCommand(), ["-m", "venv", venv]);
  }

  console.log("Installing Voicebox CLI Python package");
  run(pythonInVenv(), ["-m", "pip", "install", "--upgrade", "pip"]);
  run(pythonInVenv(), ["-m", "pip", "install", packageRoot]);
  installShim();
  console.log(`Installed cli-anything-voicebox at ${cliExecutable()}`);
}

function installShim() {
  fs.mkdirSync(binDir, { recursive: true });
  if (process.platform === "win32") {
    const shim = path.join(binDir, "cli-anything-voicebox.cmd");
    fs.writeFileSync(shim, `@echo off\r\n"${cliExecutable()}" %*\r\n`);
    console.log(`Installed command shim at ${shim}`);
    return;
  }

  const shim = path.join(binDir, "cli-anything-voicebox");
  fs.writeFileSync(shim, `#!/usr/bin/env sh\nexec "${cliExecutable()}" "$@"\n`);
  fs.chmodSync(shim, 0o755);
  console.log(`Installed command shim at ${shim}`);
  if (!(process.env.PATH || "").split(path.delimiter).includes(binDir)) {
    console.log(`Add ${binDir} to PATH if cli-anything-voicebox is not found by your shell.`);
  }
}

function installSkill() {
  run(process.execPath, [path.join(__dirname, "install-skill.js")]);
}

function status() {
  const codexHome = process.env.CODEX_HOME || path.join(os.homedir(), ".codex");
  const skillsRoot = process.env.AGENT_SKILLS_DIR || path.join(codexHome, "skills");
  console.log(JSON.stringify({
    packageRoot,
    voiceboxCliHome: home,
    binDir,
    python: pythonInVenv(),
    cli: cliExecutable(),
    cliInstalled: fs.existsSync(cliExecutable()),
    shim: process.platform === "win32"
      ? path.join(binDir, "cli-anything-voicebox.cmd")
      : path.join(binDir, "cli-anything-voicebox"),
    shimInstalled: fs.existsSync(process.platform === "win32"
      ? path.join(binDir, "cli-anything-voicebox.cmd")
      : path.join(binDir, "cli-anything-voicebox")),
    skillPath: path.join(skillsRoot, "voicebox-cli"),
    skillInstalled: fs.existsSync(path.join(skillsRoot, "voicebox-cli", "SKILL.md")),
  }, null, 2));
}

const command = process.argv[2] || "help";

try {
  if (command === "setup") {
    installCli();
    installSkill();
    status();
  } else if (command === "install-cli") {
    installCli();
  } else if (command === "install-skill") {
    installSkill();
  } else if (command === "status") {
    status();
  } else if (command === "help" || command === "--help" || command === "-h") {
    usage();
  } else {
    usage();
    process.exit(2);
  }
} catch (error) {
  console.error(error.message);
  process.exit(1);
}
