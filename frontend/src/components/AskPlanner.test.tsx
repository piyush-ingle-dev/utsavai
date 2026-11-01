import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { PLAN_ID } from "../test/fixtures";
import AskPlanner from "./AskPlanner";

const api = vi.hoisted(() => ({ askPlanner: vi.fn() }));
vi.mock("../api", () => api);

describe("AskPlanner", () => {
  beforeEach(() => api.askPlanner.mockReset());

  it("keeps the button disabled until a real question is typed", async () => {
    const user = userEvent.setup();
    render(<AskPlanner planId={PLAN_ID} />);
    const button = screen.getByRole("button", { name: "Ask" });
    expect(button).toBeDisabled();
    await user.type(screen.getByLabelText("Your question"), "ab");
    expect(button).toBeDisabled();
    await user.type(screen.getByLabelText("Your question"), "c");
    expect(button).toBeEnabled();
  });

  it("shows the answer with its sources", async () => {
    api.askPlanner.mockResolvedValue({ answer: "Apply early.", sources: ["Permissions", "Sound"] });
    const user = userEvent.setup();
    render(<AskPlanner planId={PLAN_ID} />);
    await user.type(screen.getByLabelText("Your question"), "permits?");
    await user.click(screen.getByRole("button", { name: "Ask" }));
    expect(await screen.findByText("Apply early.")).toBeInTheDocument();
    expect(screen.getByText("Sources: Permissions, Sound")).toBeInTheDocument();
    expect(api.askPlanner).toHaveBeenCalledWith(PLAN_ID, "permits?");
  });

  it("omits the sources line when there are none", async () => {
    api.askPlanner.mockResolvedValue({ answer: "No idea.", sources: [] });
    const user = userEvent.setup();
    render(<AskPlanner planId={PLAN_ID} />);
    await user.type(screen.getByLabelText("Your question"), "anything");
    await user.click(screen.getByRole("button", { name: "Ask" }));
    await screen.findByText("No idea.");
    expect(screen.queryByText(/Sources:/)).not.toBeInTheDocument();
  });

  it("shows an error and clears the old answer when a request fails", async () => {
    api.askPlanner.mockResolvedValueOnce({ answer: "First.", sources: [] }).mockRejectedValueOnce(new Error("Too many requests."));
    const user = userEvent.setup();
    render(<AskPlanner planId={PLAN_ID} />);
    await user.type(screen.getByLabelText("Your question"), "one");
    await user.click(screen.getByRole("button", { name: "Ask" }));
    await screen.findByText("First.");
    await user.click(screen.getByRole("button", { name: "Ask" }));
    expect(await screen.findByText("Too many requests.")).toBeInTheDocument();
    expect(screen.queryByText("First.")).not.toBeInTheDocument();
  });
});
