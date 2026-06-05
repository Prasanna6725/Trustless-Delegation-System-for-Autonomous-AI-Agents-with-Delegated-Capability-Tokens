const { expect } = require('chai');
const { ethers } = require('hardhat');

describe('LineageRegistry & EnforcementLayer flow', function () {
  let Lineage, TrustScorer, Enforcement, MockVerifier;
  let lineage, scorer, enforcement, verifier;
  let owner, agentA, agentB;

  beforeEach(async () => {
    [owner, agentA, agentB] = await ethers.getSigners();

    Lineage = await ethers.getContractFactory('LineageRegistry');
    lineage = await Lineage.deploy(owner.address);
    await lineage.deployed();

    TrustScorer = await ethers.getContractFactory('TrustScorer');
    scorer = await TrustScorer.deploy(owner.address);
    await scorer.deployed();

    MockVerifier = await ethers.getContractFactory('MockBiscuitVerifier');
    verifier = await MockVerifier.deploy();
    await verifier.deployed();

    Enforcement = await ethers.getContractFactory('EnforcementLayer');
    enforcement = await Enforcement.deploy(lineage.address, scorer.address, verifier.address);
    await enforcement.deployed();
  });

  it('registers and revokes and respects isActive', async () => {
    // register agentA as child of owner
    await expect(lineage.register(agentA.address, owner.address)).to.emit(lineage, 'Registered');
    expect(await lineage.depthOf(agentA.address)).to.equal(1);
    expect(await lineage.isActive(agentA.address)).to.equal(true);

    // revoke by parent
    await expect(lineage.connect(owner).revoke(agentA.address)).to.emit(lineage, 'Revoked');
    expect(await lineage.isActive(agentA.address)).to.equal(false);
  });

  it('commits proof and enforcement redeemDelegation passes with mock verifier', async () => {
    // register agentB
    await lineage.register(agentB.address, owner.address);
    const proofHash = ethers.utils.formatBytes32String('proof1');
    await lineage.connect(agentB).commitProof(agentB.address, proofHash);
    expect(await lineage.getCommittedProof(agentB.address)).to.equal(proofHash);

    // build delegation payload: token bytes, agent, proofHash, rootPubKey
    const token = ethers.utils.toUtf8Bytes('tok');
    const rootPub = ethers.utils.toUtf8Bytes('root');
    const delegation = ethers.utils.defaultAbiCoder.encode(['bytes','address','bytes32','bytes'], [token, agentB.address, proofHash, rootPub]);

    const Action = { target: owner.address, value: 0, data: '0x' };
    await expect(enforcement.redeemDelegation(delegation, Action)).to.emit(enforcement, 'DelegationRedeemed');
  });
});
