import { expect } from "chai";
import { network } from "hardhat";

const { ethers } = await network.create();

describe("AgentRegistry", function () {
  let registry, owner, agent1, agent2;

  beforeEach(async function () {
    [owner, agent1, agent2] = await ethers.getSigners();
    const AgentRegistry = await ethers.getContractFactory("AgentRegistry");
    registry = await AgentRegistry.deploy(ethers.parseEther("0.01")); // 0.01 ETH stake
  });

  it("registers an agent with stake", async function () {
    const capabilities = JSON.stringify({ task_types: ["data_analysis"], max_budget: 100 });
    await registry.connect(agent1).register(capabilities, { value: ethers.parseEther("0.01") });
    const info = await registry.getAgent(agent1.address);
    expect(info.capabilities).to.equal(capabilities);
    expect(info.active).to.be.true;
    expect(info.reputation).to.equal(100);
  });

  it("reverts if stake is insufficient", async function () {
    await expect(
      registry.connect(agent1).register("cap", { value: ethers.parseEther("0.001") })
    ).to.be.revertedWith("Insufficient stake");
  });

  it("updates reputation", async function () {
    await registry.connect(agent1).register("cap", { value: ethers.parseEther("0.01") });
    await registry.connect(owner).updateReputation(agent1.address, 120);
    const info = await registry.getAgent(agent1.address);
    expect(info.reputation).to.equal(120);
  });

  it("deregisters agent and returns stake", async function () {
    await registry.connect(agent1).register("cap", { value: ethers.parseEther("0.01") });
    const balBefore = await ethers.provider.getBalance(agent1.address);
    await registry.connect(agent1).deregister();
    const balAfter = await ethers.provider.getBalance(agent1.address);
    expect(balAfter).to.be.gt(balBefore);
    const info = await registry.getAgent(agent1.address);
    expect(info.active).to.be.false;
  });

  it("reverts if already registered", async function () {
    await registry.connect(agent1).register("cap", { value: ethers.parseEther("0.01") });
    await expect(
      registry.connect(agent1).register("cap2", { value: ethers.parseEther("0.01") })
    ).to.be.revertedWith("Already registered");
  });

  it("reverts deregister if not registered", async function () {
    await expect(registry.connect(agent1).deregister()).to.be.revertedWith("Not registered");
  });

  it("reverts updateReputation from non-owner", async function () {
    await registry.connect(agent1).register("cap", { value: ethers.parseEther("0.01") });
    await expect(
      registry.connect(agent1).updateReputation(agent1.address, 120)
    ).to.be.revertedWith("Not owner");
  });
});
