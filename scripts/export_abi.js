import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const contracts = ["AgentRegistry", "PaymentChannel", "ResultAttestation"];
const outDir = path.join(__dirname, "..", "contracts", "abi");

if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

for (const name of contracts) {
  const artifactPath = path.join(__dirname, "..", "artifacts", "contracts", `${name}.sol`, `${name}.json`);
  const artifact = JSON.parse(fs.readFileSync(artifactPath, "utf8"));
  const outPath = path.join(outDir, `${name}.json`);
  fs.writeFileSync(outPath, JSON.stringify(artifact.abi, null, 2));
  console.log(`Exported ABI: contracts/abi/${name}.json`);
}
