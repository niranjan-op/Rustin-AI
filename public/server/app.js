const http = require("http");
const { exec } = require("child_process"); // Module to run terminal commands
const fs = require("fs");
const path = require("path");

const hostname = "127.0.0.1";
const port = 3000;

// Maintain current working directory for stateful command execution
let lastProjectPath = null;
let currentCwd = process.cwd();

const server = http.createServer((req, res) => {
  if (req.method === "POST" && req.url === "/shutdown") {
    res.statusCode = 200;
    res.end(JSON.stringify({ success: true, message: "Shutting down" }));
    process.exit(0);
    return;
  }

  if (req.method === "POST") {
    let body = "";

    req.on("data", (chunk) => {
      body += chunk.toString();
    });

    req.on("end", () => {
      try {
        const payload = JSON.parse(body);

        if (payload.command) {
          // If active project path changed, update the current working directory to the new project path
          if (payload.projectPath !== undefined) {
            let newPath = payload.projectPath || process.cwd();
            if (newPath !== lastProjectPath) {
              lastProjectPath = newPath;
              currentCwd = newPath;
              console.log(`Working directory dynamically updated to project path: ${currentCwd}`);
            }
          }

          let commandToRun = payload.command.trim();
          console.log(`Executing command: ${commandToRun}`);

          // Security validation: Block malicious, network, identity, and system modification commands
          const blacklist = [
            /\bipconfig\b/i, /\bping\b/i, /\bnetstat\b/i, /\bnmap\b/i, /\btracert\b/i, 
            /\bnslookup\b/i, /\barp\b/i, /\broute\b/i, /\bifconfig\b/i, /\bcurl\b/i, /\bwget\b/i,
            /\bshutdown\b/i, /\breboot\b/i, /\bhalt\b/i, /\bpoweroff\b/i, /\bdel\b/i, 
            /\brm\b/i, /\bformat\b/i, /\bmkfs\b/i, /\bfdisk\b/i, /\bdiskpart\b/i, 
            /\breg\b/i, /\bschtasks\b/i,
            /\bwhoami\b/i, /\bhostname\b/i, /\bnetsh\b/i, /\bsysteminfo\b/i, 
            /\btasklist\b/i, /\bwmic\b/i, /\bvssadmin\b/i,
            /%USERNAME%/i, /%USERPROFILE%/i, /\$USER\b/i, /\bprintenv\b/i, /\benv\b/i, /\bset\b/i
          ];

          const isBlocked = blacklist.some(regex => regex.test(commandToRun));
          if (isBlocked) {
            res.statusCode = 403;
            res.setHeader("Content-Type", "application/json");
            res.end(JSON.stringify({
              success: false,
              error: "Command blocked: Security policy violation. Executing malicious, network discovery, or identity revealing commands is strictly prohibited. Only coding-related activities are allowed."
            }));
            return;
          }

          // Handle cd commands manually to persist cwd
          if (commandToRun.startsWith("cd ")) {
            const targetDir = commandToRun.slice(3).trim().replace(/['"]/g, ""); // strip quotes
            const newCwd = path.resolve(currentCwd, targetDir);
            if (fs.existsSync(newCwd) && fs.statSync(newCwd).isDirectory()) {
              currentCwd = newCwd;
              res.statusCode = 200;
              res.setHeader("Content-Type", "application/json");
              res.end(JSON.stringify({ success: true, output: `Changed directory to ${currentCwd}` }));
            } else {
              res.statusCode = 400;
              res.setHeader("Content-Type", "application/json");
              res.end(JSON.stringify({ success: false, error: `Directory not found: ${targetDir}` }));
            }
            return;
          }

          // Execute the terminal command safely inside Node.js using spawn to avoid maxBuffer issues
          const { spawn } = require("child_process");
          const childProcess = spawn(commandToRun, { cwd: currentCwd, shell: true });
          
          let stdoutData = "";
          let stderrData = "";
          let isResponded = false;
          
          // Truncate buffers to prevent memory leaks from infinite output after responding
          const appendData = (type, data) => {
            if (!isResponded) {
              if (type === 'out') stdoutData += data;
              else stderrData += data;
            }
          };

          childProcess.stdout.on("data", data => appendData('out', data));
          childProcess.stderr.on("data", data => appendData('err', data));

          // If the process is a long-running server (like django), we don't want to wait forever.
          // Wait 3 seconds, if it's still running, return success.
          const timer = setTimeout(() => {
            if (!isResponded) {
              isResponded = true;
              res.statusCode = 200;
              res.setHeader("Content-Type", "application/json");
              res.end(JSON.stringify({ 
                success: true, 
                output: `[Background Process Started]\n${stdoutData}\n${stderrData}` 
              }));
              
              // Disconnect streams to prevent memory leaks for long-running background tasks
              childProcess.stdout.removeAllListeners("data");
              childProcess.stderr.removeAllListeners("data");
            }
          }, 3000);

          childProcess.on("close", (code) => {
            if (!isResponded) {
              clearTimeout(timer);
              isResponded = true;
              res.statusCode = code === 0 ? 200 : 400;
              res.setHeader("Content-Type", "application/json");
              if (code !== 0) {
                res.end(JSON.stringify({ success: false, error: stderrData || `Process exited with code ${code}` }));
              } else {
                res.end(JSON.stringify({ success: true, output: stdoutData }));
              }
            }
          });
          
          childProcess.on("error", (error) => {
            if (!isResponded) {
              clearTimeout(timer);
              isResponded = true;
              res.statusCode = 400;
              res.setHeader("Content-Type", "application/json");
              res.end(JSON.stringify({ success: false, error: error.message }));
            }
          });

        } else {
          res.statusCode = 400;
          res.end("Missing 'command' key in payload");
        }
      } catch (err) {
        res.statusCode = 400;
        res.end("Invalid JSON");
      }
    });
  }
});

// Explicitly handle server shutdown/cleanup if requested via a special route or signal (handled outside in python mostly)

server.listen(port, hostname, () => {
  console.log(`Server running at http://${hostname}:${port}/`);
});
