/** A full turn, in radians. */
export const TURN = 2 * Math.PI;

export interface Slice<T> {
  item: T;
  /** Angles in radians, clockwise from the top. */
  start: number;
  end: number;
}

/**
 * Shares the angle from `from` to `to` among the items in proportion to their values, in their
 * order. Items with a value of 0 or less take no angle and are left out. The slices meet exactly,
 * and the last ends exactly at `to`, however many there are.
 */
export function slices<T extends { value: number }>(
  items: readonly T[],
  from = 0,
  to = TURN,
): Slice<T>[] {
  const shown = items.filter((item) => item.value > 0);
  const total = shown.reduce((sum, item) => sum + item.value, 0);
  if (total === 0) return [];
  const edges = [from];
  let used = 0;
  for (const [index, item] of shown.entries()) {
    used += item.value;
    edges.push(
      index === shown.length - 1 ? to : from + ((to - from) * used) / total,
    );
  }
  return shown.map((item, index) => ({
    item,
    start: edges[index],
    end: edges[index + 1],
  }));
}

/** A number for a path: three decimals, and never "-0". */
const n = (value: number): string => String(Number(value.toFixed(3)));

/** The point at an angle (clockwise from the top) and a radius, centred on 0, 0. */
const point = (radius: number, angle: number): string =>
  `${n(radius * Math.sin(angle))} ${n(-radius * Math.cos(angle))}`;

/**
 * The SVG path of the part of a ring between two radii and two angles, centred on 0, 0. With an
 * inner radius of 0 it is a slice of a pie. A whole turn is drawn as two circles with opposite
 * directions, because an arc cannot start and end at the same point.
 */
export function arcPath(
  inner: number,
  outer: number,
  start: number,
  end: number,
): string {
  if (end - start >= TURN - 1e-9) {
    const circle = (radius: number, sweep: 0 | 1): string =>
      `M ${point(radius, 0)} A ${n(radius)} ${n(radius)} 0 0 ${sweep} ${point(radius, TURN / 2)} ` +
      `A ${n(radius)} ${n(radius)} 0 0 ${sweep} ${point(radius, 0)} Z`;
    return inner > 0
      ? `${circle(outer, 1)} ${circle(inner, 0)}`
      : circle(outer, 1);
  }
  const far = end - start > TURN / 2 ? 1 : 0;
  const outerArc = `M ${point(outer, start)} A ${n(outer)} ${n(outer)} 0 ${far} 1 ${point(outer, end)}`;
  if (inner <= 0) return `${outerArc} L 0 0 Z`;
  return (
    `${outerArc} L ${point(inner, end)} ` +
    `A ${n(inner)} ${n(inner)} 0 ${far} 0 ${point(inner, start)} Z`
  );
}

/**
 * A name in lines of at most `max` characters, broken between words, for the centre of the rings.
 * A word longer than a line has a line of its own. A name that needs more than `maxLines` lines
 * ends the last one with an ellipsis.
 */
export function wrapName(name: string, max: number, maxLines = 3): string[] {
  const lines: string[] = [];
  for (const word of name.split(/\s+/).filter(Boolean)) {
    const last = lines[lines.length - 1];
    if (last !== undefined && last.length + 1 + word.length <= max) {
      lines[lines.length - 1] = `${last} ${word}`;
    } else {
      lines.push(word);
    }
  }
  if (lines.length <= maxLines) return lines;
  return [...lines.slice(0, maxLines - 1), `${lines[maxLines - 1]}…`];
}
