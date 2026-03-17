// frontend/src/lib/utils/analytics.ts
// Pure utility functions for analytics data processing

import type { StatsBadgeData } from '../types/analytics';

/**
 * Filters a list of team names by a query string (case-insensitive).
 * Returns only teams whose names include the query string.
 */
export function filterTeams(teams: string[], query: string): string[] {
  const q = query.toLowerCase();
  return teams.filter((t) => t.toLowerCase().includes(q));
}

/**
 * Computes descriptive statistics for a numeric array.
 * Returns avg, med, std, min, max, mode, p25, p75, n.
 */
export function calcStats(data: number[]): StatsBadgeData {
  if (data.length === 0) {
    throw new Error('calcStats requires a non-empty array');
  }

  const n = data.length;
  const sorted = [...data].sort((a, b) => a - b);

  const avg = data.reduce((s, v) => s + v, 0) / n;

  const med =
    n % 2 === 0
      ? (sorted[n / 2 - 1] + sorted[n / 2]) / 2
      : sorted[Math.floor(n / 2)];

  const variance = data.reduce((s, v) => s + (v - avg) ** 2, 0) / (n > 1 ? n - 1 : 1);
  const std = Math.sqrt(variance);

  const min = sorted[0];
  const max = sorted[n - 1];

  // Percentile helper (linear interpolation)
  const percentile = (p: number): number => {
    const idx = (p / 100) * (n - 1);
    const lo = Math.floor(idx);
    const hi = Math.ceil(idx);
    if (lo === hi) return sorted[lo];
    return sorted[lo] + (sorted[hi] - sorted[lo]) * (idx - lo);
  };

  const p25 = percentile(25);
  const p75 = percentile(75);

  // Mode: most frequent value
  const freq = new Map<number, number>();
  for (const v of data) freq.set(v, (freq.get(v) ?? 0) + 1);
  let mode = data[0];
  let maxFreq = 0;
  for (const [val, count] of freq) {
    if (count > maxFreq) {
      maxFreq = count;
      mode = val;
    }
  }

  return { avg, med, std, min, max, mode, p25, p75, n };
}

/**
 * Classifies a probability value into a risk tier.
 * - 'low'  if prob >= 65
 * - 'med'  if prob >= 50
 * - 'high' otherwise
 */
export function riskTier(prob: number): 'low' | 'med' | 'high' {
  if (prob >= 65) return 'low';
  if (prob >= 50) return 'med';
  return 'high';
}

/**
 * Computes the fair odd from a probability percentage.
 * odd = 100 / prob
 */
export function oddFromProb(prob: number): number {
  return 100 / prob;
}
