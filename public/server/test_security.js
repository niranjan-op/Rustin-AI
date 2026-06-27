const http = require('http');

const testCommand = (command, expectedStatus) => {
  return new Promise((resolve) => {
    const req = http.request({
      hostname: '127.0.0.1',
      port: 3000,
      path: '/',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        console.log(`Command: "${command}" -> Status: ${res.statusCode} (Expected: ${expectedStatus})`);
        if (res.statusCode !== expectedStatus) {
            console.error(`  [FAILED] Response: ${data}`);
        } else {
            console.log(`  [PASSED]`);
        }
        resolve();
      });
    });

    req.on('error', (e) => {
      console.error(`Problem with request: ${e.message}`);
      resolve();
    });

    req.write(JSON.stringify({ command }));
    req.end();
  });
};

const runTests = async () => {
  console.log("Running tests...");
  
  // Allowed commands (Expected 200)
  await testCommand("node -v", 200);
  await testCommand("echo hello", 200);
  
  // Blocked commands (Expected 403)
  await testCommand("whoami", 403);
  await testCommand("ipconfig", 403);
  await testCommand("ping google.com", 403);
  await testCommand("shutdown /s", 403);
  await testCommand("echo %USERNAME%", 403);
  await testCommand("netsh wlan show profile", 403);

  console.log("Tests completed.");
  process.exit(0);
};

runTests();
