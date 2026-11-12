/**
 * When the client tries again.
 *
 * The decision is pure and the clock, the jitter and the limits all come in as
 * parameters, so every case here is exact rather than approximate.
 */
import { describe, expect, it } from "vitest";
import { DEFAULT_RETRY_LIMITS, type RetryLimits, decideRetry } from "../src/retry.js";

const HALF: () => number = () => 0.5;

interface Question {
  method?: string;
  status?: number | undefined;
  code?: string | undefined;
  retryAfterSeconds?: number | undefined;
  attempt?: number;
  limits?: Partial<RetryLimits>;
  random?: () => number;
}

function ask(question: Question = {}) {
  return decideRetry({
    method: question.method ?? "POST",
    status: question.status,
    code: question.code,
    retryAfterSeconds: question.retryAfterSeconds,
    attempt: question.attempt ?? 1,
    limits: { ...DEFAULT_RETRY_LIMITS, ...question.limits },
    random: question.random ?? HALF,
  });
}

describe("no answer at all", () => {
  it("tries again, because nothing says the request was received", () => {
    expect(ask({ status: undefined })).toEqual({ retry: true, waitMs: 125 });
  });

  it("doubles the wait on each attempt", () => {
    expect(ask({ status: undefined, attempt: 2 })).toEqual({ retry: true, waitMs: 250 });
    expect(ask({ status: undefined, attempt: 3, limits: { attempts: 5 } })).toEqual({
      retry: true,
      waitMs: 500,
    });
  });

  it("jitters the wait, so many clients do not come back together", () => {
    expect(ask({ status: undefined, random: () => 0 }).retry).toBe(true);
    expect(ask({ status: undefined, random: () => 0 })).toEqual({ retry: true, waitMs: 0 });
    expect(ask({ status: undefined, random: () => 1 })).toEqual({ retry: true, waitMs: 250 });
  });

  it("never waits more than the ceiling of one backoff", () => {
    const decision = ask({
      status: undefined,
      attempt: 20,
      limits: { attempts: 50 },
      random: () => 1,
    });

    expect(decision).toEqual({ retry: true, waitMs: DEFAULT_RETRY_LIMITS.maxBackoffMs });
  });
});

describe("an answer that says to come back", () => {
  it("waits exactly what Retry-After says on a 429", () => {
    expect(ask({ status: 429, retryAfterSeconds: 2 })).toEqual({ retry: true, waitMs: 2000 });
  });

  it("waits exactly what Retry-After says on a 503", () => {
    expect(ask({ status: 503, retryAfterSeconds: 5 })).toEqual({ retry: true, waitMs: 5000 });
  });

  it("falls back to the backoff when the answer carried no Retry-After", () => {
    expect(ask({ status: 503 })).toEqual({ retry: true, waitMs: 125 });
  });

  it("stops instead of sitting on a wait above the ceiling", () => {
    expect(ask({ status: 429, retryAfterSeconds: 3600 })).toEqual({ retry: false });
  });

  it("accepts a wait exactly at the ceiling", () => {
    const seconds = DEFAULT_RETRY_LIMITS.maxRetryAfterSeconds;

    expect(ask({ status: 429, retryAfterSeconds: seconds })).toEqual({
      retry: true,
      waitMs: seconds * 1000,
    });
  });
});

describe("a server failure", () => {
  it("does not retry a POST answered 500, because it may have written", () => {
    expect(ask({ method: "POST", status: 500 })).toEqual({ retry: false });
  });

  it("does not retry a POST answered 502 either", () => {
    expect(ask({ method: "POST", status: 502 })).toEqual({ retry: false });
  });

  it("retries a GET answered 500, which changes nothing", () => {
    expect(ask({ method: "GET", status: 500 })).toEqual({ retry: true, waitMs: 125 });
  });

  it("retries a GET answered 504", () => {
    expect(ask({ method: "GET", status: 504 })).toEqual({ retry: true, waitMs: 125 });
  });
});

describe("an answer the client cannot change", () => {
  it("does not retry a refusal by contract", () => {
    expect(ask({ status: 422 })).toEqual({ retry: false });
  });

  it("does not retry an unauthenticated call", () => {
    expect(ask({ status: 401 })).toEqual({ retry: false });
  });

  it("does not retry a success", () => {
    expect(ask({ status: 201 })).toEqual({ retry: false });
  });
});

describe("the attempt ceiling", () => {
  it("stops once the attempts are spent, whatever the answer was", () => {
    expect(ask({ status: 503, retryAfterSeconds: 1, attempt: 3 })).toEqual({ retry: false });
  });

  it("never retries when the client was built with one attempt", () => {
    expect(ask({ status: undefined, limits: { attempts: 1 } })).toEqual({ retry: false });
  });
});
