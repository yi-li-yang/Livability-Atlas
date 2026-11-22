import { describe, expect, it } from "vitest";
import {
  findPostcode,
  freeName,
  loadPlaces,
  MAX_PLACES,
  normalisePostcode,
  PLACES_KEY,
  type Place,
  savePlaces,
  withoutPlace,
  withPlace,
} from "./places";

const memory = (initial: Record<string, string> = {}) => {
  const data = { ...initial };
  return {
    data,
    getItem: (key: string) => data[key] ?? null,
    setItem: (key: string, value: string) => {
      data[key] = value;
    },
  };
};

const work: Place = { name: "Work", lat: 51.5136, lng: -0.1337 };

describe("the user's places", () => {
  it("are kept in this browser and read back", () => {
    const store = memory();
    savePlaces([work], store);
    expect(Object.keys(store.data)).toEqual([PLACES_KEY]);
    expect(loadPlaces(store)).toEqual([work]);
  });

  it("are none where nothing is kept, the text is broken or storage throws", () => {
    expect(loadPlaces(memory())).toEqual([]);
    expect(loadPlaces(memory({ [PLACES_KEY]: "{nope" }))).toEqual([]);
    const throwing = {
      getItem: () => {
        throw new Error("blocked");
      },
      setItem: () => {
        throw new Error("blocked");
      },
    };
    expect(loadPlaces(throwing)).toEqual([]);
    expect(() => savePlaces([work], throwing)).not.toThrow();
  });

  it("drop an entry that is not a place, and keep at most three", () => {
    const text = JSON.stringify([
      work,
      { name: "No place", lat: "x", lng: 0 },
      { name: "", lat: 51, lng: 0 },
      { name: "B", lat: 51.4, lng: -0.1 },
      { name: "C", lat: 51.6, lng: -0.2 },
      { name: "D", lat: 51.7, lng: -0.3 },
    ]);
    const places = loadPlaces(memory({ [PLACES_KEY]: text }));
    expect(places.map((p) => p.name)).toEqual(["Work", "B", "C"]);
    expect(MAX_PLACES).toBe(3);
  });

  it("are added up to three, and removed by position", () => {
    let places: Place[] = [];
    for (const name of ["A", "B", "C", "D"]) {
      places = withPlace(places, { ...work, name });
    }
    expect(places.map((p) => p.name)).toEqual(["A", "B", "C"]);
    expect(withoutPlace(places, 1).map((p) => p.name)).toEqual(["A", "C"]);
  });

  it("numbers a name that another place has already, so no two places share one", () => {
    let places: Place[] = [];
    for (let i = 0; i < 3; i += 1)
      places = withPlace(places, { ...work, name: "Work" });
    expect(places.map((p) => p.name)).toEqual(["Work", "Work 2", "Work 3"]);
  });
});

describe("a postcode", () => {
  const table = {
    postcodes: ["E16AN", "SW1A1AA", "SW98HE"],
    lat: Float64Array.from([51.52, 51.501, 51.4627]),
    lng: Float64Array.from([-0.07, -0.141, -0.1145]),
  };

  it("is written without spaces in capitals, as the table holds it", () => {
    expect(normalisePostcode(" sw1a 1aa ")).toBe("SW1A1AA");
  });

  it("is found in the region's table, wherever the user puts the space", () => {
    expect(findPostcode(table, "sw9 8he")).toEqual({
      lat: 51.4627,
      lng: -0.1145,
    });
    expect(findPostcode(table, "E1 6AN")).toEqual({ lat: 51.52, lng: -0.07 });
  });

  it("that the table lacks is not found", () => {
    expect(findPostcode(table, "ZZ1 1ZZ")).toBeNull();
    expect(findPostcode(table, "")).toBeNull();
  });
});

describe("freeName", () => {
  it("is the first numbered name that no place has, so two places never share one", () => {
    const at = (name: string): Place => ({ name, lat: 51.5, lng: -0.1 });
    expect(freeName([])).toBe("Place 1");
    expect(freeName([at("Place 1"), at("Place 2")])).toBe("Place 3");
    expect(freeName([at("Place 2")])).toBe("Place 1");
    expect(freeName([at("Place 1"), at("Place 3")])).toBe("Place 2");
  });
});
