import test from "node:test";
import assert from "node:assert/strict";
import { toCsv } from "../src/csv.js";

test("serializes rows as quoted CSV", () => {
  assert.equal(
    toCsv([
      ["材料", "Bandgap"],
      ["ZnO", "3.20 eV"],
    ]),
    '"材料","Bandgap"\n"ZnO","3.20 eV"',
  );
});

test("escapes quotes, commas, newlines, and null values", () => {
  assert.equal(
    toCsv([["a,b", 'say "hi"', "line 1\nline 2", null]]),
    '"a,b","say ""hi""","line 1\nline 2",""',
  );
});
