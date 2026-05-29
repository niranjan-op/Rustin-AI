const http = require("http");
const { exec } = require("child_process"); // Module to run terminal commands

const hostname = "127.0.0.1";
const port = 3000;

const server = http.createServer((req, res) => {
  if (req.method === "POST") {
    let body = "";

    req.on("data", (chunk) => {
      body += chunk.toString();
      console.log("Body", body);
      console.log("chunk", chunk);
    });

    req.on("end", () => {
      try {
        const payload = JSON.parse(body);

        // Check if the payload contains a 'command' key
        if (payload.command) {
          const commandToRun = payload.command.trim();
          console.log(`Executing command: ${commandToRun}`);

          // Security validation: Block malicious, network, identity, and system modification commands
          const blacklist = [
            // Network & Discovery
            /\bipconfig\b/i, /\bping\b/i, /\bnetstat\b/i, /\bnmap\b/i, /\btracert\b/i, 
            /\bnslookup\b/i, /\barp\b/i, /\broute\b/i, /\bifconfig\b/i, /\bcurl\b/i, /\bwget\b/i,
            // System Modification & Shutdown
            /\bshutdown\b/i, /\breboot\b/i, /\bhalt\b/i, /\bpoweroff\b/i, /\bdel\b/i, 
            /\brm\b/i, /\bformat\b/i, /\bmkfs\b/i, /\bfdisk\b/i, /\bdiskpart\b/i, 
            /\breg\b/i, /\bschtasks\b/i,
            // Identity & Info Gathering
            /\bwhoami\b/i, /\bhostname\b/i, /\bnetsh\b/i, /\bsysteminfo\b/i, 
            /\btasklist\b/i, /\bwmic\b/i, /\bvssadmin\b/i,
            // Environment Variables
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

          // Execute the terminal command safely inside Node.js
          exec(commandToRun, (error, stdout, stderr) => {
            res.statusCode = 200;
            res.setHeader("Content-Type", "application/json");

            if (error) {
              // Command failed or returned an error code
              res.end(
                JSON.stringify({
                  success: false,
                  error: stderr || error.message,
                }),
              );
              return;
            }

            // Command succeeded, return the terminal output
            res.end(JSON.stringify({ success: true, output: stdout }));
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

server.listen(port, hostname, () => {
  console.log(`Server running at http://${hostname}:${port}/`);
});
