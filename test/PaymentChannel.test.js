import { expect } from "chai";
import { network } from "hardhat";

const { ethers } = await network.create();

describe("PaymentChannel", function () {
  let channel, owner, requester, provider, auditor;

  beforeEach(async function () {
    [owner, requester, provider, auditor] = await ethers.getSigners();
    const PaymentChannel = await ethers.getContractFactory("PaymentChannel");
    channel = await PaymentChannel.deploy(auditor.address);
  });

  it("locks payment for a task", async function () {
    const taskId = ethers.id("task-001");
    const amount = ethers.parseEther("0.1");
    const block = await ethers.provider.getBlock("latest");
    const deadline = block.timestamp + 3600;

    await channel.connect(requester).lock(taskId, provider.address, deadline, { value: amount });

    const task = await channel.getTask(taskId);
    expect(task.amount).to.equal(amount);
    expect(task.provider).to.equal(provider.address);
    expect(task.settled).to.be.false;
  });

  it("releases payment to provider on settlement", async function () {
    const taskId = ethers.id("task-002");
    const amount = ethers.parseEther("0.1");
    const block = await ethers.provider.getBlock("latest");
    const deadline = block.timestamp + 3600;

    await channel.connect(requester).lock(taskId, provider.address, deadline, { value: amount });

    const balBefore = await ethers.provider.getBalance(provider.address);
    await channel.connect(requester).release(taskId);
    const balAfter = await ethers.provider.getBalance(provider.address);

    expect(balAfter).to.be.gt(balBefore);

    const task = await channel.getTask(taskId);
    expect(task.settled).to.be.true;
  });

  it("refunds requester after deadline", async function () {
    const taskId = ethers.id("task-003");
    const amount = ethers.parseEther("0.1");
    const block = await ethers.provider.getBlock("latest");
    const deadline = block.timestamp + 60;

    await channel.connect(requester).lock(taskId, provider.address, deadline, { value: amount });

    // Advance time past deadline
    await ethers.provider.send("evm_increaseTime", [120]);
    await ethers.provider.send("evm_mine", []);

    const balBefore = await ethers.provider.getBalance(requester.address);
    await channel.connect(requester).refund(taskId);
    const balAfter = await ethers.provider.getBalance(requester.address);

    expect(balAfter).to.be.gt(balBefore);

    const task = await channel.getTask(taskId);
    expect(task.settled).to.be.true;
  });

  it("auditor can force release on dispute", async function () {
    const taskId = ethers.id("task-004");
    const amount = ethers.parseEther("0.1");
    const block = await ethers.provider.getBlock("latest");
    const deadline = block.timestamp + 3600;

    await channel.connect(requester).lock(taskId, provider.address, deadline, { value: amount });

    await channel.connect(auditor).forceRelease(taskId);

    const task = await channel.getTask(taskId);
    expect(task.settled).to.be.true;
  });
});
