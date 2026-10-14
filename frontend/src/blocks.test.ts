import { describe, expect, it } from "vitest";
import { splitBold, toBlocks } from "./blocks";

describe("toBlocks", () => {
  it("groups consecutive bullets into one list", () => {
    expect(toBlocks("- uno [1]\n- dos [2]")).toEqual([{ kind: "ul", items: ["uno [1]", "dos [2]"] }]);
  });

  it("keeps paragraphs and lists apart and skips blank lines", () => {
    expect(toBlocks("Intro\n\n1. a\n2) b\nCierre")).toEqual([
      { kind: "p", text: "Intro" },
      { kind: "ol", items: ["a", "b"] },
      { kind: "p", text: "Cierre" },
    ]);
  });

  it("does not treat a hyphenated word as a bullet", () => {
    expect(toBlocks("-3 grados")).toEqual([{ kind: "p", text: "-3 grados" }]);
  });
});

describe("splitBold", () => {
  it("puts bold runs at odd positions", () => {
    expect(splitBold("a **b** c")).toEqual(["a ", "b", " c"]);
  });

  it("leaves an unclosed marker alone while streaming", () => {
    expect(splitBold("a **b")).toEqual(["a **b"]);
  });
});
