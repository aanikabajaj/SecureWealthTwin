// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title AccessControl
 * @dev Manages roles and permissions for the SecureWealth ecosystem.
 */
contract AccessControl {
    mapping(address => bool) private _admins;
    mapping(address => bool) private _authorizedloggers;

    event AdminAdded(address indexed account);
    event AdminRemoved(address indexed account);
    event LoggerAuthorized(address indexed account);
    event LoggerDeauthorized(address indexed account);

    address public root;

    modifier onlyRoot() {
        require(msg.sender == root, "Caller is not root");
        _;
    }

    modifier onlyAdmin() {
        require(_admins[msg.sender] || msg.sender == root, "Caller is not admin");
        _;
    }

    constructor() {
        root = msg.sender;
    }

    function addAdmin(address account) public onlyRoot {
        _admins[account] = true;
        emit AdminAdded(account);
    }

    function removeAdmin(address account) public onlyRoot {
        _admins[account] = false;
        emit AdminRemoved(account);
    }

    function authorizeLogger(address account) public onlyAdmin {
        _authorizedloggers[account] = true;
        emit LoggerAuthorized(account);
    }

    function deauthorizeLogger(address account) public onlyAdmin {
        _authorizedloggers[account] = false;
        emit LoggerDeauthorized(account);
    }

    function isAdmin(address account) public view returns (bool) {
        return _admins[account] || account == root;
    }

    function isAuthorizedLogger(address account) public view returns (bool) {
        return _authorizedloggers[account];
    }
}
