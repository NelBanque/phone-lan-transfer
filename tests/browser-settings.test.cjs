const { test } = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const { runInNewContext } = require("node:vm");
const { resolve } = require("node:path");

const script = readFileSync(resolve(__dirname, "../src/phone_lan_transfer/static/app.js"), "utf8");

function element() {
  return {
    hidden: true, disabled: true, textContent: "", children: [], listeners: {}, attributes: {},
    addEventListener(event, handler) { this.listeners[event] = handler; },
    append(...children) { this.children.push(...children); },
    replaceChildren() { this.children = []; },
    setAttribute(name, value) { this.attributes[name] = value; },
    focus() {},
    querySelectorAll(selector) {
      return this.children.flatMap((child) => [
        ...(child.className === selector.slice(1) ? [child] : []),
        ...child.querySelectorAll(selector),
      ]);
    },
  };
}

async function page(fetchResponse, hash = "#token=test-token") {
  const nodes = new Map();
  const calls = [];
  runInNewContext(script, {
    document: {
      querySelector(selector) {
        if (!nodes.has(selector)) nodes.set(selector, element());
        return nodes.get(selector);
      },
      createElement: element,
    },
    window: {
      location: { hash, pathname: "/", search: "" },
      history: { replaceState() {} }, setTimeout, clearTimeout,
    },
    URLSearchParams, AbortController, Intl, TextEncoder,
    fetch: async (...args) => { calls.push(args); return fetchResponse(...args); },
  });
  await new Promise(setImmediate);
  return { nodes, calls };
}

const settings = (limit) => ({ status: 200, ok: true, json: async () => ({ max_file_bytes: limit }) });

test("valid settings authenticate, display the actual limit, and flag only oversized files", async () => {
  const { nodes, calls } = await page(() => settings(10));
  assert.equal(calls[0][0], "/transfer-settings");
  assert.equal(calls[0][1].headers.Authorization, "Bearer test-token");
  assert.equal(nodes.get("#choose-files").disabled, false);
  assert.match(nodes.get("#file-limit").textContent, /10 bytes/);
  const input = nodes.get("#file-input");
  input.files = [{ name: "exact.txt", size: 10 }, { name: "large.txt", size: 11 }];
  input.listeners.change();
  const items = nodes.get("#selected-files").children;
  assert.equal(items[0].children.some((child) => child.className === "file-size-error"), false);
  assert.equal(items[1].children.some((child) => child.className === "file-size-error"), true);
});

function pick(nodes, files) {
  const input = nodes.get("#file-input");
  input.files = files;
  input.listeners.change();
  return nodes.get("#selected-files");
}

test("upload sends the original body and encoded destination, and waits for confirmation", async () => {
  let finish;
  const pendingResponse = new Promise((resolve) => { finish = resolve; });
  const { nodes, calls } = await page((url) => url === "/transfer-settings" ? settings(100) : pendingResponse);
  const file = { name: "résumé #1.txt", size: 10, type: "text/plain" };
  const list = pick(nodes, [file]);
  const button = list.querySelectorAll(".send-file")[0];
  const sending = button.listeners.click();
  await button.listeners.click();
  assert.equal(calls.length, 2, "duplicate clicks must not submit twice");
  assert.equal(calls[1][1].method, "POST");
  assert.equal(calls[1][1].headers.Authorization, "Bearer test-token");
  assert.equal(calls[1][1].body, file);
  assert.equal(new URL(calls[1][0], "http://localhost").searchParams.get("destination_name"), file.name);
  assert.equal(list.querySelectorAll(".send-file")[0].disabled, true);
  assert.equal(list.querySelectorAll(".remove-file")[0].disabled, true);
  assert.match(list.querySelectorAll(".transfer-status")[0].textContent, /Sending/);
  finish({ status: 201, ok: true, json: async () => ({ status: "saved", destination_name: file.name }) });
  await sending;
  assert.equal(list.querySelectorAll(".send-file")[0].textContent, "Saved");
  assert.equal(list.querySelectorAll(".send-file")[0].disabled, true);
});

test("invalid names and oversized files cannot be submitted even by directly invoking the handler", async () => {
  const { nodes, calls } = await page(() => settings(10));
  const list = pick(nodes, [{ name: "CON.txt", size: 1 }, { name: "large.txt", size: 11 }]);
  for (const button of list.querySelectorAll(".send-file")) {
    assert.equal(button.disabled, true);
    await button.listeners.click();
  }
  assert.equal(calls.length, 1);
});

test("collision can be corrected and retried while other successful files remain saved", async () => {
  const { nodes } = await page((url) => {
    if (url === "/transfer-settings") return settings(100);
    const name = new URL(url, "http://localhost").searchParams.get("destination_name");
    return name === "existing.txt" ? { status: 409, ok: false }
      : { status: 201, ok: true, json: async () => ({ status: "saved", destination_name: name }) };
  });
  const list = pick(nodes, [
    { name: "good.txt", size: 1, type: "text/plain" },
    { name: "existing.txt", size: 1, type: "text/plain" },
  ]);
  await list.querySelectorAll(".send-file")[0].listeners.click();
  await list.querySelectorAll(".send-file")[1].listeners.click();
  assert.match(list.querySelectorAll(".transfer-status")[1].textContent, /already exists/);
  list.querySelectorAll(".file-open")[1].listeners.click();
  const editor = list.querySelectorAll(".rename-input")[0];
  editor.value = "renamed";
  editor.listeners.input();
  await list.querySelectorAll(".send-file")[1].listeners.click();
  for (const button of list.querySelectorAll(".send-file")) assert.equal(button.textContent, "Saved");
});

test("network loss and unconfirmed success never claim saved", async () => {
  for (const uploadResponse of [
    () => { throw new Error("offline"); },
    () => ({ status: 201, ok: true, json: async () => { throw new Error("response lost"); } }),
    () => ({ status: 201, ok: true, json: async () => ({ status: "saved", destination_name: "wrong.txt" }) }),
  ]) {
    const { nodes } = await page((url) => url === "/transfer-settings" ? settings(100) : uploadResponse());
    const list = pick(nodes, [{ name: "test.txt", size: 1 }]);
    await list.querySelectorAll(".send-file")[0].listeners.click();
    assert.equal(list.querySelectorAll(".send-file")[0].textContent, "Retry");
    assert.match(list.querySelectorAll(".transfer-status")[0].textContent, /may already be on the computer/);
  }
});

test("upload failures show actionable per-file errors", async () => {
  for (const [status, message] of [[400, /name/], [401, /QR/], [413, /size limit/], [422, /rejected/], [500, /destination folder/], [507, /space/]]) {
    const { nodes } = await page((url) => url === "/transfer-settings" ? settings(100) : { status, ok: false });
    const list = pick(nodes, [{ name: "test.txt", size: 1 }]);
    await list.querySelectorAll(".send-file")[0].listeners.click();
    assert.match(list.querySelectorAll(".transfer-status")[0].textContent, message);
    assert.equal(list.querySelectorAll(".send-file")[0].textContent, "Retry");
  }
});

test("missing token makes no request", async () => {
  const { nodes, calls } = await page(() => settings(10), "");
  assert.equal(calls.length, 0);
  assert.equal(nodes.get("#choose-files").disabled, true);
  assert.equal(nodes.get("#connection-status").hidden, false);
});

test("invalid token requires a new QR link", async () => {
  const { nodes } = await page(() => ({ status: 401, ok: false }));
  assert.equal(nodes.get("#choose-files").disabled, true);
  assert.match(nodes.get("#status-message").textContent, /QR/);
  assert.equal(nodes.get("#retry-settings").hidden, true);
});

test("network failure can be retried successfully", async () => {
  let failing = true;
  const { nodes } = await page(() => {
    if (failing) throw new Error("offline");
    return settings(1234);
  });
  assert.equal(nodes.get("#retry-settings").hidden, false);
  assert.equal(nodes.get("#choose-files").disabled, true);
  failing = false;
  await nodes.get("#retry-settings").listeners.click();
  assert.equal(nodes.get("#choose-files").disabled, false);
  assert.equal(nodes.get("#connection-status").hidden, true);
});

test("invalid server limits do not enable selection", async () => {
  for (const limit of [0, -1, "10", null, 1.5]) {
    const { nodes } = await page(() => settings(limit));
    assert.equal(nodes.get("#choose-files").disabled, true);
    assert.equal(nodes.get("#retry-settings").hidden, false);
  }
});

test("destination feedback counts full UTF-8 names and allows correction without renaming the source", async () => {
  const { nodes } = await page(() => settings(100));
  const original = { name: "original.txt", size: 1, type: "text/plain" };
  const input = nodes.get("#file-input");
  input.files = [original];
  input.listeners.change();
  const list = nodes.get("#selected-files");
  list.querySelectorAll(".file-open")[0].listeners.click();
  const editor = list.querySelectorAll(".rename-input")[0];
  const error = list.querySelectorAll(".file-name-error")[0];
  for (const [name, valid, message] of [
    ["a".repeat(251), true],
    ["a".repeat(252), false, /255 UTF-8 bytes/],
    ["é".repeat(125) + "a", true],
    ["é".repeat(126), false, /255 UTF-8 bytes/],
    ["😀".repeat(62) + "abc", true],
    ["😀".repeat(63), false, /255 UTF-8 bytes/],
    ["CON", false, /reserved by Windows/],
    ["COM¹", false, /reserved by Windows/],
    ["folder/name", false, /control characters/],
    ["a\x7f", false, /control characters/],
    ["a\x85b", false, /control characters/],
    ["\ud800", false, /invalid Unicode/],
    [" report", false, /whitespace/],
    ["\u001creport", false, /whitespace/],
    ["\ufeffreport", true],
    ["", false, /before the extension/],
    ["corrected", true],
  ]) {
    editor.value = name;
    editor.listeners.input();
    assert.equal(error.hidden, valid, JSON.stringify(name));
    assert.equal(editor.attributes["aria-invalid"], String(!valid));
    if (message) assert.match(error.textContent, message);
  }
  assert.equal(original.name, "original.txt");
  assert.equal(list.querySelectorAll(".file-name")[0].textContent, "corrected.txt");
});
