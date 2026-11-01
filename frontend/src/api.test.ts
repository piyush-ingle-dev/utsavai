import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, askPlanner, createPlan, getPlan, saveEditToken, toggleItem } from "./api";
import { PLAN_ID } from "./test/fixtures";
import type { PlanFormValues } from "./types";

const form: PlanFormValues = {
  event_type: "wedding", title: "", event_date: "2027-01-01", guests: "10", budget: "50000", city: "", theme: "", preferences: "",
};

function reply(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

describe("api client", () => {
  const fetchMock = vi.fn();

  beforeEach(() => vi.stubGlobal("fetch", fetchMock));
  afterEach(() => {
    fetchMock.mockReset();
    vi.unstubAllGlobals();
  });

  it("posts the form as JSON", async () => {
    fetchMock.mockResolvedValue(reply({ id: PLAN_ID, edit_token: "tok" }, 201));
    await expect(createPlan(form)).resolves.toEqual({ id: PLAN_ID, edit_token: "tok" });
    const [path, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(path).toBe("/api/plans");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body as string)).toEqual(form);
  });

  it("sends the saved edit token for that plan only", async () => {
    saveEditToken(PLAN_ID, "secret");
    fetchMock.mockResolvedValue(reply({}));
    await getPlan(PLAN_ID);
    await getPlan("b".repeat(32));
    const headers = (i: number): Record<string, string> => (fetchMock.mock.calls[i]?.[1] as RequestInit).headers as Record<string, string>;
    expect(headers(0)["X-Edit-Token"]).toBe("secret");
    expect(headers(1)["X-Edit-Token"]).toBeUndefined();
  });

  it("calls toggle and ask with the right bodies", async () => {
    fetchMock.mockResolvedValue(reply({}));
    await toggleItem(PLAN_ID, "t3");
    await askPlanner(PLAN_ID, "why?");
    expect(JSON.parse((fetchMock.mock.calls[0]?.[1] as RequestInit).body as string)).toEqual({ id: "t3" });
    expect(JSON.parse((fetchMock.mock.calls[1]?.[1] as RequestInit).body as string)).toEqual({ question: "why?" });
  });

  it("throws an ApiError carrying the status and field errors", async () => {
    fetchMock.mockResolvedValue(reply({ error: "Please fix", errors: { guests: "Too many" } }, 400));
    const failure = await createPlan(form).catch((e: unknown) => e);
    expect(failure).toBeInstanceOf(ApiError);
    expect(failure).toMatchObject({ message: "Please fix", status: 400, fieldErrors: { guests: "Too many" } });
  });

  it("falls back to a friendly message when the body is not JSON", async () => {
    fetchMock.mockResolvedValue(new Response("<html>oops</html>", { status: 502 }));
    await expect(getPlan(PLAN_ID)).rejects.toThrow("Something went wrong. Please try again.");
  });

  it("still works when localStorage is blocked", async () => {
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    fetchMock.mockResolvedValue(reply({}));
    expect(() => saveEditToken(PLAN_ID, "x")).not.toThrow();
    await expect(getPlan(PLAN_ID)).resolves.toEqual({});
    vi.restoreAllMocks();
  });
});
