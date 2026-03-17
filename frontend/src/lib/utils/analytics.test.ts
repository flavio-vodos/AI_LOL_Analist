/**
 * Property-based and unit tests for analytics utility functions.
 *
 * Validates: Requirements 2.3, 11.6, 14.5, 14.7
 */

import { describe, it, expect } from 'vitest';
import fc from 'fast-check';
import { filterTeams, calcStats, riskTier, oddFromProb } from './analytics';

// ---------------------------------------------------------------------------
// filterTeams — unit tests
// ---------------------------------------------------------------------------
describe('filterTeams', () => {
  it('returns all teams when query is empty', () => {
    expect(filterTeams(['T1', 'G2', 'Cloud9'], '')).toEqual(['T1', 'G2', 'Cloud9']);
  });

  it('filters case-insensitively', () => {
    expect(filterTeams(['T1', 'G2', 'Cloud9'], 'cloud')).toEqual(['Cloud9']);
    expect(filterTeams(['T1', 'G2', 'Cloud9'], 'CLOUD')).toEqual(['Cloud9']);
  });

  it('returns empty array when no match', () => {
    expect(filterTeams(['T1', 'G2'], 'xyz')).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
// Property 2: Team filter is case-insensitive and inclusive
// Validates: Requirements 2.3
// ---------------------------------------------------------------------------
describe('Property 2: filterTeams is case-insensitive and inclusive', () => {
  it('filtered result contains exactly the matching teams', () => {
    fc.assert(
      fc.property(fc.array(fc.string()), fc.string(), (teams, query) => {
        const result = filterTeams(teams, query);
        const q = query.toLowerCase();
        // Every result item must match the query
        const allMatch = result.every((t) => t.toLowerCase().includes(q));
        // Every team that matches must be in the result
        const noneSkipped = teams
          .filter((t) => t.toLowerCase().includes(q))
          .every((t) => result.includes(t));
        return allMatch && noneSkipped;
      })
    );
  });
});

// ---------------------------------------------------------------------------
// calcStats — unit tests
// ---------------------------------------------------------------------------
describe('calcStats', () => {
  it('computes correct stats for a simple array', () => {
    const stats = calcStats([1, 2, 3, 4, 5]);
    expect(stats.n).toBe(5);
    expect(stats.avg).toBeCloseTo(3, 6);
    expect(stats.med).toBe(3);
    expect(stats.min).toBe(1);
    expect(stats.max).toBe(5);
  });

  it('throws on empty array', () => {
    expect(() => calcStats([])).toThrow();
  });
});

// ---------------------------------------------------------------------------
// riskTier — unit tests
// ---------------------------------------------------------------------------
describe('riskTier', () => {
  it('returns low for prob >= 65', () => {
    expect(riskTier(65)).toBe('low');
    expect(riskTier(100)).toBe('low');
  });

  it('returns med for 50 <= prob < 65', () => {
    expect(riskTier(50)).toBe('med');
    expect(riskTier(64.9)).toBe('med');
  });

  it('returns high for prob < 50', () => {
    expect(riskTier(0)).toBe('high');
    expect(riskTier(49.9)).toBe('high');
  });
});

// ---------------------------------------------------------------------------
// Property 7: Risk tier classification (TypeScript)
// Validates: Requirements 11.6, 14.5
// ---------------------------------------------------------------------------
describe('Property 7: riskTier classification is correct for all probabilities', () => {
  it('tier matches threshold rules for any prob in [0, 100]', () => {
    fc.assert(
      fc.property(fc.double({ min: 0, max: 100, noNaN: true }), (prob) => {
        const tier = riskTier(prob);
        if (prob >= 65) return tier === 'low';
        if (prob >= 50) return tier === 'med';
        return tier === 'high';
      }),
      { numRuns: 500 }
    );
  });
});

// ---------------------------------------------------------------------------
// oddFromProb — unit tests
// ---------------------------------------------------------------------------
describe('oddFromProb', () => {
  it('computes 100 / prob', () => {
    expect(oddFromProb(50)).toBeCloseTo(2, 6);
    expect(oddFromProb(100)).toBeCloseTo(1, 6);
    expect(oddFromProb(25)).toBeCloseTo(4, 6);
  });
});

// ---------------------------------------------------------------------------
// Property 8: Odd formula correctness (TypeScript)
// Validates: Requirements 14.7
// ---------------------------------------------------------------------------
describe('Property 8: oddFromProb equals 100 / prob for any positive prob', () => {
  it('odd = 100 / prob within floating-point tolerance', () => {
    fc.assert(
      fc.property(fc.double({ min: 0.1, max: 100, noNaN: true }), (prob) => {
        return Math.abs(oddFromProb(prob) - 100 / prob) < 1e-6;
      }),
      { numRuns: 500 }
    );
  });
});
