import { describe, expect, it } from "vitest";
import {
  decodeProfile,
  encodeProfile,
  loadProfile,
  pruneProfile,
  STORAGE_KEY,
  type Store,
  saveProfile,
} from "./storage";

const memory = (
  initial: Record<string, string> = {},
): Store & { data: Record<string, string> } => {
  const data = { ...initial };
  return {
    data,
    getItem: (key) => data[key] ?? null,
    setItem: (key, value) => {
      data[key] = value;
    },
  };
};

describe("encodeProfile and decodeProfile", () => {
  it("round-trip weights and flipped directions", () => {
    const profile = {
      weights: { transport: 0, "green-space": 5, safety: 2 },
      flipped: ["rain", "nightlife"],
    };
    expect(decodeProfile(encodeProfile(profile))).toEqual(profile);
  });

  it("write nothing for a profile with nothing set", () => {
    expect(encodeProfile({ weights: {} })).toBe("");
    expect(decodeProfile("")).toEqual({ weights: {} });
  });

  it("read the text of a URL's fragment, with its leading #", () => {
    expect(decodeProfile("#w=transport:3&f=rain")).toEqual({
      weights: { transport: 3 },
      flipped: ["rain"],
    });
  });

  it("leave out whatever is malformed, and keep the rest", () => {
    const bad =
      "w=transport:9,safety:-1,crime:2.5,rain:x,:3,ok:4,double:1:2,noval&f=Bad Id,fine";
    expect(decodeProfile(bad)).toEqual({
      weights: { ok: 4 },
      flipped: ["fine"],
    });
  });

  it("do not let an id carry markup or a path", () => {
    expect(decodeProfile("w=<script>:3,../x:1,a:1")).toEqual({
      weights: { a: 1 },
    });
  });
});

describe("pruneProfile", () => {
  it("drops ids that the factor tree does not have", () => {
    const profile = {
      weights: { transport: 1, gone: 2 },
      flipped: ["gone", "rain"],
    };
    expect(pruneProfile(profile, new Set(["transport", "rain"]))).toEqual({
      weights: { transport: 1 },
      flipped: ["rain"],
    });
  });
});

describe("loadProfile and saveProfile", () => {
  it("start from the saved profile", () => {
    const store = memory();
    saveProfile({ weights: { safety: 5 } }, store);
    expect(store.data[STORAGE_KEY]).toBe("w=safety:5");
    expect(loadProfile("", store)).toEqual({ weights: { safety: 5 } });
  });

  it("prefer the profile in the link to the saved one", () => {
    const store = memory({ [STORAGE_KEY]: "w=safety:5" });
    expect(loadProfile("#w=transport:1", store)).toEqual({
      weights: { transport: 1 },
    });
  });

  it("fall back to the saved profile when the link carries none", () => {
    const store = memory({ [STORAGE_KEY]: "w=safety:5" });
    expect(loadProfile("#nothing=here", store)).toEqual({
      weights: { safety: 5 },
    });
  });

  it("work without storage, and where storage throws", () => {
    const blocked: Store = {
      getItem: () => {
        throw new Error("blocked");
      },
      setItem: () => {
        throw new Error("blocked");
      },
    };
    expect(loadProfile("", null)).toEqual({ weights: {} });
    expect(loadProfile("", blocked)).toEqual({ weights: {} });
    expect(() => saveProfile({ weights: { a: 1 } }, blocked)).not.toThrow();
    expect(() => saveProfile({ weights: { a: 1 } }, null)).not.toThrow();
  });
});
