import * as cp from 'child_process';
import * as path from 'path';
import * as vscode from 'vscode';

export class AgentForgeClient {
    private pythonPath: string;
    private pluginPath: string;
    private outputChannel: vscode.OutputChannel;

    constructor(outputChannel: vscode.OutputChannel) {
        this.outputChannel = outputChannel;
        const config = vscode.workspace.getConfiguration('agentforge');
        this.pythonPath = config.get<string>('pythonPath', 'python3');
        const rawPluginPath = config.get<string>('pluginPath', '../plugin.py');

        // Resolve plugin path relative to workspace root if possible, or extension
        if (path.isAbsolute(rawPluginPath)) {
            this.pluginPath = rawPluginPath;
        } else {
            // Fallback: assume relative to the workspace root first
            if (vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders.length > 0) {
                this.pluginPath = path.join(vscode.workspace.workspaceFolders[0].uri.fsPath, rawPluginPath);
            } else {
                // Fallback: assume relative to this extension's root (less likely to be correct for ../plugin.py but safe default)
                this.pluginPath = path.join(__dirname, '../../', rawPluginPath);
            }
        }
    }

    private runCommand(args: string[]): Promise<string> {
        return new Promise((resolve, reject) => {
            const command = `${this.pythonPath} ${this.pluginPath} ${args.join(' ')}`;
            this.outputChannel.appendLine(`[Running] ${command}`);

            cp.exec(command, (error, stdout, stderr) => {
                if (stderr) {
                    this.outputChannel.appendLine(`[Stderr] ${stderr}`);
                }
                if (error) {
                    this.outputChannel.appendLine(`[Error] ${error.message}`);
                    reject(error);
                    return;
                }
                this.outputChannel.appendLine(`[Stdout] ${stdout}`);
                resolve(stdout.trim());
            });
        });
    }

    public async connect(): Promise<any> {
        try {
            const result = await this.runCommand(['--init']);
            // --init output might contain the handshake JSON
            // We'll try to parse the last line or the whole output
            return result;
        } catch (e) {
            throw new Error('Failed to connect to AgentForge.');
        }
    }

    public async checkStatus(): Promise<any> {
        return this.runCommand(['--check-connection']);
    }

    public async sendAction(action: string, data: any): Promise<any> {
        const dataStr = JSON.stringify(data);
        // Escape quotes for shell safety serves as a basic measure; 
        // real implementation should spawn with args array to avoid shell injection
        // Re-implementing runCommand to use spawn for safety
        return this.runSpawn(['--action', action, '--data', dataStr, '--wait', '30']);
    }

    public async syncSpokes(hubUrl?: string): Promise<string> {
        const args = ['../sync_spoke.py'];

        // If config has a specific hub URL, use it. Otherwise, let python script use its default (100.111.236.92)
        // However, the python script default is now robust.
        // We can allow override via config if needed.
        const config = vscode.workspace.getConfiguration('agentforge');
        const configHubUrl = config.get<string>('hubUrl');

        if (configHubUrl) {
            args.push('--hub', configHubUrl);
        } else if (hubUrl) {
            args.push('--hub', hubUrl);
        }

        return this.runSpawn(args);
    }

    private runSpawn(args: string[]): Promise<string> {
        return new Promise((resolve, reject) => {
            this.outputChannel.appendLine(`[Running] ${this.pythonPath} ${this.pluginPath} ${args.join(' ')}`);

            // Check if we are running the plugin or a separate script
            let script = this.pluginPath;
            let finalArgs = args;

            // Hack: if the first arg ends in .py, assume it's the script and replace pluginPath
            if (args.length > 0 && args[0].endsWith('.py')) {
                script = path.join(path.dirname(this.pluginPath), args[0]);
                // If the path is relative to the plugin path (starts with ..), resolve it
                // Actually the logic above for args[0] is flawed if we just join.
                // Better approach: assume sync_spoke.py is in the same dir as plugin.py
                script = path.join(path.dirname(this.pluginPath), 'sync_spoke.py');
                finalArgs = args.slice(1);
            } else {
                finalArgs = [this.pluginPath, ...args];
                script = this.pythonPath; // runSpawn usually calls python executable
                // Re-evaluating runSpawn logic from previous step...
                // Previous runSpawn: cp.spawn(this.pythonPath, [this.pluginPath, ...args]);
                // We need to support running a DIFFERENT script.
            }

            // Revised launch logic to support arbitrary scripts in same dir
            // If we are calling syncSpokes, we want to run: python3 /path/to/sync_spoke.py [args]

            let cmd = this.pythonPath;
            let cmdArgs = [];

            if (args[0] === '../sync_spoke.py') {
                // Special case for sync script
                const syncScript = path.join(path.dirname(this.pluginPath), 'sync_spoke.py');
                cmdArgs = [syncScript, ...args.slice(1)];
            } else {
                cmdArgs = [this.pluginPath, ...args];
            }

            this.outputChannel.appendLine(`[Spawn] ${cmd} ${cmdArgs.join(' ')}`);
            const child = cp.spawn(cmd, cmdArgs);

            let stdout = '';
            let stderr = '';

            child.stdout.on('data', (data) => {
                stdout += data.toString();
                this.outputChannel.append(`[Stdout] ${data.toString()}`);
            });

            child.stderr.on('data', (data) => {
                stderr += data.toString();
                this.outputChannel.append(`[Stderr] ${data.toString()}`);
            });

            child.on('close', (code) => {
                if (code !== 0) {
                    reject(new Error(`Process exited with code ${code}`));
                } else {
                    resolve(stdout.trim());
                }
            });
        });
    }
}
