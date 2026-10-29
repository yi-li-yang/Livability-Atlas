import { describe, expect, it } from "vitest";
import {
  decodeProfile,
  encodeProfile,
  encodeStored,
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

describe("choices", () => {
  const profile = {
    weights: { faith: 3 },
    choices: { faith: ["hindu", "sikh"], "your-community": ["ethnic-indian"] },
  };

  it("stay out of the link, which a friend may read (D08)", () => {
    expect(encodeProfile(profile)).toBe("w=faith:3");
  });

  it("are kept in the browser's storage and round-trip there", () => {
    const stored = encodeStored(profile);
    expect(stored).toContain("c=");
    expect(decodeProfile(stored)).toEqual(profile);
  });

  it("are not read from a link, even one that carries them", () => {
    const store = memory();
    const loaded = loadProfile(`#${encodeStored(profile)}`, store);
    expect(loaded.weights).toEqual({ faith: 3 });
    expect(loaded.choices).toBeUndefined();
  });

  it("come back from storage even when a link sets the weights", () => {
    const store = memory();
    saveProfile(profile, store);
    const loaded = loadProfile("#w=park:1", store);
    expect(loaded.weights).toEqual({ park: 1 });
    expect(loaded.choices).toEqual(profile.choices);
  });

  it("are saved with the weights", () => {
    const store = memory();
    saveProfile(profile, store);
    expect(decodeProfile(store.data[STORAGE_KEY])).toEqual(profile);
  });

  it("are dropped when malformed", () => {
    expect(
      decodeProfile("c=faith:,:hindu,a b:c,faith:hi ndu").choices,
    ).toBeUndefined();
  });

  it("are pruned to the indicators and options that the bundle has", () => {
    const known = new Set(["faith", "faith:hindu"]);
    const pruned = pruneProfile(profile, known);
    expect(pruned.choices).toEqual({ faith: ["hindu"] });
  });
});

describe("limits", () => {
  const profile = {
    weights: {},
    limits: [
      { indicator: "renting-cost", max: 2000 },
      { indicator: "gp-walk", min: 6.5 },
      { indicator: "service-level", in: ["3", "6a", "6b"] },
    ],
  };

  it("round-trip through the link and the storage", () => {
    expect(decodeProfile(encodeProfile(profile))).toEqual(profile);
    expect(decodeProfile(encodeStored(profile))).toEqual(profile);
  });

  it("are written as l=indicator:kind:value", () => {
    expect(encodeProfile(profile)).toBe(
      "l=renting-cost:max:2000,gp-walk:min:6.5,service-level:in:3.6a.6b",
    );
  });

  it("travel in a link, which carries the preferences but not the choices", () => {
    const loaded = loadProfile(`#${encodeProfile(profile)}`, memory());
    expect(loaded.limits).toEqual(profile.limits);
  });

  it("are dropped when malformed, one by one", () => {
    const decoded = decodeProfile(
      "l=a:max:x,b:max:5,c:mid:5,d:in:,e:in:ok,f:min:-3,g:max:1:2,:max:1",
    );
    expect(decoded.limits).toEqual([
      { indicator: "b", max: 5 },
      { indicator: "e", in: ["ok"] },
    ]);
  });

  it("are pruned to the indicators that the bundle has", () => {
    const known = new Set(["renting-cost", "service-level"]);
    expect(pruneProfile(profile, known).limits).toEqual([
      { indicator: "renting-cost", max: 2000 },
      { indicator: "service-level", in: ["3", "6a", "6b"] },
    ]);
  });

  it("leave a profile without them as it was", () => {
    expect(encodeProfile({ weights: { transport: 3 } })).toBe("w=transport:3");
    expect(decodeProfile("w=transport:3").limits).toBeUndefined();
  });
});
