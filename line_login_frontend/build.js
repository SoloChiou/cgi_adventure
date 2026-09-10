const fs = require("node:fs");
const path = require("node:path");

const liffId = (process.env.LINE_LIFF_ID || "").trim();
const backendLoginUrl = (process.env.LINE_BACKEND_LOGIN_URL || "").trim();

if (!liffId || !backendLoginUrl) {
  throw new Error("LINE_LIFF_ID 與 LINE_BACKEND_LOGIN_URL 不得留白");
}

const sourceDirectory = path.join(__dirname, "src");
const outputDirectory = path.join(__dirname, "dist");
fs.mkdirSync(outputDirectory, { recursive: true });

for (const filename of ["index.html", "line_login.js", "style.css"]) {
  fs.copyFileSync(
    path.join(sourceDirectory, filename),
    path.join(outputDirectory, filename),
  );
}

const config = `window.LINE_LOGIN_CONFIG = ${JSON.stringify({ liffId, backendLoginUrl })};\n`;
fs.writeFileSync(path.join(outputDirectory, "config.js"), config, "utf8");
