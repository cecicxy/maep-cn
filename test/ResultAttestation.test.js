import { expect } from "chai";
import { network } from "hardhat";

const { ethers } = await network.create();

describe("ResultAttestation", function () {
  let attestation, provider, requester;

  beforeEach(async function () {
    [provider, requester] = await ethers.getSigners();
    const ResultAttestation = await ethers.getContractFactory("ResultAttestation");
    attestation = await ResultAttestation.deploy();
  });

  it("stores result hash by provider", async function () {
    const taskId = ethers.id("task-001");
    const resultHash = ethers.keccak256(ethers.toUtf8Bytes("result data"));
    await attestation.connect(provider).attest(taskId, resultHash);
    const stored = await attestation.getAttestation(taskId);
    expect(stored.resultHash).to.equal(resultHash);
    expect(stored.provider).to.equal(provider.address);
    expect(stored.disputed).to.be.false;
  });

  it("flags attestation as disputed", async function () {
    const taskId = ethers.id("task-002");
    const resultHash = ethers.keccak256(ethers.toUtf8Bytes("result data"));
    await attestation.connect(provider).attest(taskId, resultHash);
    await attestation.connect(requester).dispute(taskId);
    const stored = await attestation.getAttestation(taskId);
    expect(stored.disputed).to.be.true;
  });

  it("reverts duplicate attestation", async function () {
    const taskId = ethers.id("task-003");
    const resultHash = ethers.keccak256(ethers.toUtf8Bytes("result data"));
    await attestation.connect(provider).attest(taskId, resultHash);
    await expect(
      attestation.connect(provider).attest(taskId, resultHash)
    ).to.be.revertedWith("Already attested");
  });
});
