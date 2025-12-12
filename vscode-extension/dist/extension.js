"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = require("vscode");
const agentForgeClient_1 = require("./agentForgeClient");
function activate(context) {
    const outputChannel = vscode.window.createOutputChannel("AgentForge");
    outputChannel.appendLine("AgentForge Extension Activated.");
    const client = new agentForgeClient_1.AgentForgeClient(outputChannel);
    let connectDisposable = vscode.commands.registerCommand('agentforge.connect', async () => {
        try {
            vscode.window.showInformationMessage("Connecting to AgentForge Junior Developer...");
            const response = await client.connect();
            outputChannel.appendLine(response);
            // Trigger Sync
            vscode.commands.executeCommand('agentforge.syncWorkspace');
            vscode.window.showInformationMessage("AgentForge Connected! Sync started in background.");
        }
        catch (e) {
            vscode.window.showErrorMessage(`AgentForge Connection Failed: ${e.message}`);
        }
    });
    let statusDisposable = vscode.commands.registerCommand('agentforge.status', async () => {
        try {
            const response = await client.checkStatus();
            vscode.window.showInformationMessage(`AgentForge Status: ${response}`);
        }
        catch (e) {
            vscode.window.showErrorMessage(`AgentForge Check Failed: ${e.message}`);
        }
    });
    let sendCommandDisposable = vscode.commands.registerCommand('agentforge.sendCommand', async () => {
        const action = await vscode.window.showInputBox({ prompt: "Action (e.g., analyze_project)" });
        if (!action)
            return;
        const dataStr = await vscode.window.showInputBox({ prompt: "Data JSON (optional)", value: "{}" });
        let data = {};
        try {
            data = JSON.parse(dataStr || "{}");
        }
        catch (e) {
            vscode.window.showErrorMessage("Invalid JSON data");
            return;
        }
        try {
            vscode.window.showInformationMessage("Sending command to AgentForge...");
            const response = await client.sendAction(action, data);
            outputChannel.appendLine(response);
            vscode.window.showInformationMessage("Command Sent! detailed response in Output.");
        }
        catch (e) {
            vscode.window.showErrorMessage(`Failed to send command: ${e.message}`);
        }
    });
    let syncDisposable = vscode.commands.registerCommand('agentforge.syncWorkspace', async () => {
        try {
            vscode.window.showInformationMessage("Synchronizing Spokes...");
            const response = await client.syncSpokes();
            outputChannel.appendLine(response);
            vscode.window.showInformationMessage("Synchronization Complete!");
        }
        catch (e) {
            vscode.window.showErrorMessage(`Sync Failed: ${e.message}`);
        }
    });
    // Auto-sync on connect? Or just offer it?
    // User requirement: "align all the spokes at every connection asynchronously"
    // hooking into connect command.
    context.subscriptions.push(connectDisposable);
    context.subscriptions.push(statusDisposable);
    context.subscriptions.push(sendCommandDisposable);
    context.subscriptions.push(syncDisposable);
    // Auto-connect on startup
    vscode.commands.executeCommand('agentforge.connect');
}
function deactivate() { }
//# sourceMappingURL=extension.js.map