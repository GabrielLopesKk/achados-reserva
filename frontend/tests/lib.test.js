import test from "node:test";
import assert from "node:assert/strict";
import { buildQuery, formatDate, scoreLabel, statusLabel, validateClaim } from "../lib.js";

test("buildQuery ignora campos vazios", () => {
  assert.equal(buildQuery({ q: " capuz ", type: "", color: null }), "?q=capuz");
  assert.equal(buildQuery({}), "");
});

test("statusLabel traduz status conhecidos", () => {
  assert.equal(statusLabel("awaiting_pickup"), "Aguardando retirada");
  assert.equal(statusLabel("x"), "x");
});

test("scoreLabel classifica a confiança", () => {
  assert.match(scoreLabel(0.85), /muito provável/);
  assert.match(scoreLabel(0.5), /provável/);
  assert.match(scoreLabel(0.36), /possível/);
});

test("validateClaim exige nome e contato", () => {
  assert.equal(validateClaim({ name: "Ana", contact: "ana@x.com" }).length, 0);
  assert.equal(validateClaim({ name: "", contact: "1" }).length, 2);
});

test("formatDate converte ISO para dd/mm/aaaa", () => {
  assert.equal(formatDate("2026-11-23T10:00:00+00:00"), "23/11/2026");
});
