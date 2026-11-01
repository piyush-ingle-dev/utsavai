import { describe, expect, it } from "vitest";
import { dayMonthYear, isoDate, rupees } from "./format";

describe("format helpers", () => {
  it("groups rupees the Indian way", () => {
    expect(rupees(1000000)).toBe("10,00,000");
    expect(rupees(999)).toBe("999");
  });

  it("turns an ISO date into day/month/year", () => {
    expect(dayMonthYear("2026-12-30")).toBe("30/12/2026");
  });

  it("adds days across month and year ends", () => {
    expect(isoDate(0, new Date(2026, 0, 5))).toBe("2026-01-05");
    expect(isoDate(30, new Date(2026, 11, 15))).toBe("2027-01-14");
    expect(isoDate(1, new Date(2028, 1, 28))).toBe("2028-02-29");
  });
});
