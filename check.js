const c = require("fs").readFileSync("frontend/dist/assets/ChatView-D1-sOQCW.js", "utf-8");
const idx = c.indexOf('__name:"ProfilePanel"');
console.log(c.substring(idx, idx + 400));
