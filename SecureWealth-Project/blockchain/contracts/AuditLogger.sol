// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title AuditLogger
 * @dev Stores immutable hashes of financial transactions and security events.
 */
contract AuditLogger {
    struct AuditEntry {
        address actor;
        string actionType;
        string dataHash; // SHA-256 hash of the transaction/log data
        uint256 timestamp;
        string riskLabel;
    }

    mapping(uint256 => AuditEntry) private _entries;
    uint256 private _entryCount;

    event EntryLogged(uint256 indexed id, address indexed actor, string actionType, string dataHash);

    address public owner;

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can perform this action");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    /**
     * @dev Logs a new audit entry.
     * @param actionType The type of action (e.g., "INVESTMENT", "LOGIN", "TRANSFER")
     * @param dataHash The IPFS or SHA-256 hash of the full data payload.
     * @param riskLabel The risk label assigned by the AI engine (Low/Med/High).
     */
    function logEntry(
        string memory actionType,
        string memory dataHash,
        string memory riskLabel
    ) public {
        _entryCount++;
        _entries[_entryCount] = AuditEntry({
            actor: msg.sender,
            actionType: actionType,
            dataHash: dataHash,
            timestamp: block.timestamp,
            riskLabel: riskLabel
        });

        emit EntryLogged(_entryCount, msg.sender, actionType, dataHash);
    }

    function getEntry(uint256 id) public view returns (
        address actor,
        string memory actionType,
        string memory dataHash,
        uint256 timestamp,
        string memory riskLabel
    ) {
        require(id > 0 && id <= _entryCount, "Entry does not exist");
        AuditEntry memory entry = _entries[id];
        return (entry.actor, entry.actionType, entry.dataHash, entry.timestamp, entry.riskLabel);
    }

    function getEntryCount() public view returns (uint256) {
        return _entryCount;
    }
}
