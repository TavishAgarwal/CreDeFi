// SPDX-License-Identifier: MIT
pragma solidity ^0.8.27;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

/**
 * @title  SoulboundReputationNFT
 * @notice A non-transferable ERC-721 that stores an on-chain trust score
 *         for every CreDeFi user.  Each address may hold at most ONE token.
 *
 *         The SCORE_UPDATER_ROLE (assigned to the backend oracle / keeper)
 *         can mint a reputation token and update the trust score at any time.
 *
 *         Soulbound enforcement: all transfer / approval methods revert.
 */
contract SoulboundReputationNFT is ERC721, AccessControl {
    bytes32 public constant SCORE_UPDATER_ROLE = keccak256("SCORE_UPDATER_ROLE");

    uint256 private _nextTokenId;

    struct ReputationData {
        uint256 score;        // 0–1000  (maps to 300-1000 in the report)
        uint256 updatedAt;    // block.timestamp of last update
        string  riskTier;     // "EXCELLENT", "GOOD", "FAIR", "POOR", "VERY_POOR"
    }

    // tokenId → reputation
    mapping(uint256 => ReputationData) public reputation;

    // owner → tokenId  (reverse lookup, 0 means no token)
    mapping(address => uint256) public tokenOfOwner;

    event ScoreUpdated(address indexed user, uint256 indexed tokenId, uint256 score, string riskTier);
    event ReputationMinted(address indexed user, uint256 indexed tokenId);
    event ScoreExplained(
        address indexed user,
        uint256 score,
        uint256 heuristicComponent,
        uint256 mlComponent,
        uint256 penalties,
        string  breakdown
    );

    constructor() ERC721("CreDeFi Reputation", "CREP") {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(SCORE_UPDATER_ROLE, msg.sender);
        _nextTokenId = 1; // start from 1 so 0 means "none"
    }

    // ── Soulbound overrides ──────────────────────────────────────

    function _update(
        address to,
        uint256 tokenId,
        address auth
    ) internal override returns (address) {
        address from = _ownerOf(tokenId);
        // Allow minting (from == address(0)) and burning (to == address(0))
        // Block all other transfers
        require(from == address(0) || to == address(0), "Soulbound: non-transferable");
        return super._update(to, tokenId, auth);
    }

    function approve(address, uint256) public pure override {
        revert("Soulbound: approval disabled");
    }

    function setApprovalForAll(address, bool) public pure override {
        revert("Soulbound: approval disabled");
    }

    // ── Score management ─────────────────────────────────────────

    /**
     * @notice Mint a reputation NFT for a user who doesn't have one yet,
     *         and set their initial score.
     */
    function mintReputation(
        address user,
        uint256 score,
        string calldata riskTier
    ) external onlyRole(SCORE_UPDATER_ROLE) returns (uint256 tokenId) {
        require(tokenOfOwner[user] == 0, "SBT: already minted");
        require(score <= 1000, "SBT: score out of range");

        tokenId = _nextTokenId++;
        _safeMint(user, tokenId);

        tokenOfOwner[user] = tokenId;
        reputation[tokenId] = ReputationData({
            score: score,
            updatedAt: block.timestamp,
            riskTier: riskTier
        });

        emit ReputationMinted(user, tokenId);
        emit ScoreUpdated(user, tokenId, score, riskTier);
    }

    /**
     * @notice Mint with full explainability — logs score breakdown on-chain.
     */
    function mintReputationExplained(
        address user,
        uint256 score,
        string calldata riskTier,
        uint256 heuristicComponent,
        uint256 mlComponent,
        uint256 penalties,
        string calldata breakdown
    ) external onlyRole(SCORE_UPDATER_ROLE) returns (uint256 tokenId) {
        require(tokenOfOwner[user] == 0, "SBT: already minted");
        require(score <= 1000, "SBT: score out of range");

        tokenId = _nextTokenId++;
        _safeMint(user, tokenId);

        tokenOfOwner[user] = tokenId;
        reputation[tokenId] = ReputationData({
            score: score,
            updatedAt: block.timestamp,
            riskTier: riskTier
        });

        emit ReputationMinted(user, tokenId);
        emit ScoreUpdated(user, tokenId, score, riskTier);
        emit ScoreExplained(user, score, heuristicComponent, mlComponent, penalties, breakdown);
    }

    /**
     * @notice Update the trust score of an existing reputation token.
     */
    function updateScore(
        address user,
        uint256 newScore,
        string calldata newRiskTier
    ) external onlyRole(SCORE_UPDATER_ROLE) {
        uint256 tokenId = tokenOfOwner[user];
        require(tokenId != 0, "SBT: no token");
        require(newScore <= 1000, "SBT: score out of range");

        ReputationData storage data = reputation[tokenId];
        data.score = newScore;
        data.riskTier = newRiskTier;
        data.updatedAt = block.timestamp;

        emit ScoreUpdated(user, tokenId, newScore, newRiskTier);
    }

    /**
     * @notice Update score with full explainability — logs breakdown on-chain.
     */
    function updateScoreExplained(
        address user,
        uint256 newScore,
        string calldata newRiskTier,
        uint256 heuristicComponent,
        uint256 mlComponent,
        uint256 penalties,
        string calldata breakdown
    ) external onlyRole(SCORE_UPDATER_ROLE) {
        uint256 tokenId = tokenOfOwner[user];
        require(tokenId != 0, "SBT: no token");
        require(newScore <= 1000, "SBT: score out of range");

        ReputationData storage data = reputation[tokenId];
        data.score = newScore;
        data.riskTier = newRiskTier;
        data.updatedAt = block.timestamp;

        emit ScoreUpdated(user, tokenId, newScore, newRiskTier);
        emit ScoreExplained(user, newScore, heuristicComponent, mlComponent, penalties, breakdown);
    }

    /**
     * @notice Read the trust score for a user (0 if no token).
     */
    function trustScoreOf(address user) external view returns (uint256) {
        uint256 tokenId = tokenOfOwner[user];
        if (tokenId == 0) return 0;
        return reputation[tokenId].score;
    }

    /**
     * @notice Full reputation data for a user.
     */
    function reputationOf(address user)
        external
        view
        returns (uint256 score, uint256 updatedAt, string memory riskTier)
    {
        uint256 tokenId = tokenOfOwner[user];
        require(tokenId != 0, "SBT: no token");
        ReputationData storage data = reputation[tokenId];
        return (data.score, data.updatedAt, data.riskTier);
    }

    // ── ERC-165 ──────────────────────────────────────────────────

    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC721, AccessControl)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}
