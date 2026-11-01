import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import { makePlan, PLAN_ID } from "./test/fixtures";

const api = vi.hoisted(() => ({ getPlan: vi.fn(), createPlan: vi.fn(), saveEditToken: vi.fn() }));
vi.mock("./api", async (importOriginal) => ({ ...(await importOriginal<Record<string, unknown>>()), ...api }));

afterEach(() => {
  window.history.pushState({}, "", "/");
  Object.values(api).forEach((mock) => mock.mockReset());
});

describe("App routing", () => {
  it("starts on the form with the home title", () => {
    render(<App />);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Plan your celebration");
    expect(document.title).toBe("UtsavAI | Celebration & Event Planner");
    expect(screen.getByRole("link", { name: "Skip to main content" })).toHaveAttribute("href", "#main");
  });

  it("opens a plan straight from its link", async () => {
    window.history.pushState({}, "", `/plan/${PLAN_ID}`);
    api.getPlan.mockResolvedValue(makePlan());
    render(<App />);
    expect(await screen.findByRole("heading", { level: 1, name: "Riya and Aman" })).toBeInTheDocument();
  });

  it("moves to the plan after creating it, updates the URL and focuses the main area", async () => {
    api.createPlan.mockResolvedValue({ id: PLAN_ID, edit_token: "t" });
    api.getPlan.mockResolvedValue(makePlan());
    const user = userEvent.setup();
    render(<App />);
    await user.type(screen.getByLabelText("Number of guests"), "10");
    await user.type(screen.getByLabelText("Total budget (Rs)"), "50000");
    await user.click(screen.getByRole("button", { name: "Create my plan" }));

    expect(await screen.findByRole("heading", { level: 1, name: "Riya and Aman" })).toBeInTheDocument();
    expect(window.location.pathname).toBe(`/plan/${PLAN_ID}`);
    expect(screen.getByRole("main")).toHaveFocus();
  });

  it("returns home from a plan with the brand link and New plan button", async () => {
    window.history.pushState({}, "", `/plan/${PLAN_ID}`);
    api.getPlan.mockResolvedValue(makePlan());
    const user = userEvent.setup();
    render(<App />);
    await screen.findByRole("heading", { level: 1, name: "Riya and Aman" });
    await user.click(screen.getByRole("link", { name: "UtsavAI" }));
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Plan your celebration");
    expect(window.location.pathname).toBe("/");
  });

  it("follows the browser back button", async () => {
    api.createPlan.mockResolvedValue({ id: PLAN_ID, edit_token: "t" });
    api.getPlan.mockResolvedValue(makePlan());
    const user = userEvent.setup();
    render(<App />);
    await user.type(screen.getByLabelText("Number of guests"), "10");
    await user.type(screen.getByLabelText("Total budget (Rs)"), "50000");
    await user.click(screen.getByRole("button", { name: "Create my plan" }));
    await screen.findByRole("heading", { level: 1, name: "Riya and Aman" });

    window.history.back();
    expect(await screen.findByRole("heading", { level: 1, name: /Plan your celebration/ })).toBeInTheDocument();
  });
});
