export function setIntersection<T>(a: Set<T>, b: Set<T>): Set<T> {
  const result = new Set<T>();
  const smaller = a.size <= b.size ? a : b;
  const larger = a.size <= b.size ? b : a;
  for (const item of smaller) {
    if (larger.has(item)) result.add(item);
  }
  return result;
}

export function setDifference<T>(a: Set<T>, b: Set<T>): Set<T> {
  const result = new Set<T>();
  for (const item of a) {
    if (!b.has(item)) result.add(item);
  }
  return result;
}


