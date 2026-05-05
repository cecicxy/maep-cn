import { network } from "hardhat";
import fs from "fs";

const { ethers } = await network.create();

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying with:", deployer.address);

  // Use 0.0001 ETH min stake for testnet (saves funds)
  const AgentRegistry = await ethers.getContractFactory("AgentRegistry");
  const registry = await AgentRegistry.deploy(ethers.parseEther("0.0001"));
  await registry.waitForDeployment();
  console.log("AgentRegistry:", await registry.getAddress());

  const PaymentChannel = await ethers.getContractFactory("PaymentChannel");
  const channel = await PaymentChannel.deploy(deployer.address);
  await channel.waitForDeployment();
  console.log("PaymentChannel:", await channel.getAddress());

  const ResultAttestation = await ethers.getContractFactory("ResultAttestation");
  const attestation = await ResultAttestation.deploy();
  await attestation.waitForDeployment();
  console.log("ResultAttestation:", await attestation.getAddress());

  const addresses = {
    AgentRegistry: await registry.getAddress(),
    PaymentChannel: await channel.getAddress(),
    ResultAttestation: await attestation.getAddress(),
    network: (await ethers.provider.getNetwork()).name,
    deployedAt: new Date().toISOString(),
  };

  fs.writeFileSync("deployments.json", JSON.stringify(addresses, null, 2));
  console.log("Addresses saved to deployments.json");
}

await main();
