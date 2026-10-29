// Prints the bcrypt hash for Node-RED's admin password, run inside the
// container with Node-RED's own bcryptjs. Reads {"password", "hash"} JSON on
// stdin; the current hash is kept while it still matches the password, so an
// unchanged password changes nothing.
const bcrypt = require('/usr/src/node-red/node_modules/bcryptjs');

let input = '';
process.stdin.on('data', chunk => { input += chunk; });
process.stdin.on('end', () => {
    const { password, hash } = JSON.parse(input);
    const keep = hash && bcrypt.compareSync(password, hash);
    process.stdout.write(keep ? hash : bcrypt.hashSync(password, 8));
});
