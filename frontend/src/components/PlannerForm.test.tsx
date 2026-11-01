import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "vitest-axe";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../api";
import { PLAN_ID } from "../test/fixtures";
import PlannerForm from "./PlannerForm";

const api = vi.hoisted(() => ({ createPlan: vi.fn(), saveEditToken: vi.fn() }));
vi.mock("../api", async (importOriginal) => ({ ...(await importOriginal<Record<string, unknown>>()), ...api }));

describe("PlannerForm", () => {
  beforeEach(() => {
    api.createPlan.mockReset();
    api.saveEditToken.mockReset();
  });

  it("has no accessibility violations", async () => {
    const { container } = render(<PlannerForm onCreated={vi.fn()} />);
    expect(await axe(container)).toHaveNoViolations();
  });

  it("submits the entered values, stores the edit token and opens the plan", async () => {
    api.createPlan.mockResolvedValue({ id: PLAN_ID, edit_token: "tok" });
    const onCreated = vi.fn();
    const user = userEvent.setup();
    render(<PlannerForm onCreated={onCreated} />);

    await user.click(screen.getByLabelText("Birthday"));
    await user.type(screen.getByLabelText("Number of guests"), "40");
    await user.type(screen.getByLabelText("Total budget (Rs)"), "60000");
    await user.type(screen.getByLabelText("Anything special? (optional)"), "Pure veg");
    await user.click(screen.getByRole("button", { name: "Create my plan" }));

    await waitFor(() => expect(onCreated).toHaveBeenCalledWith(PLAN_ID));
    expect(api.saveEditToken).toHaveBeenCalledWith(PLAN_ID, "tok");
    expect(api.createPlan).toHaveBeenCalledWith(
      expect.objectContaining({ event_type: "birthday", guests: "40", budget: "60000", preferences: "Pure veg" }),
    );
  });

  it("shows server validation errors next to the fields and moves focus to the summary", async () => {
    api.createPlan.mockRejectedValue(new ApiError("Please fix the highlighted fields.", 400, { guests: "Guests must be a whole number." }));
    const user = userEvent.setup();
    render(<PlannerForm onCreated={vi.fn()} />);
    await user.click(screen.getByRole("button", { name: "Create my plan" }));

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("Please fix the highlighted fields.");
    expect(alert).toHaveFocus();
    const guests = screen.getByLabelText("Number of guests");
    expect(guests).toBeInvalid();
    expect(guests).toHaveAccessibleDescription("Guests must be a whole number.");
  });

  it("disables the button while the agents are working", async () => {
    let finish: (value: { id: string; edit_token: string }) => void = () => undefined;
    api.createPlan.mockReturnValue(new Promise((resolve) => (finish = resolve)));
    const user = userEvent.setup();
    render(<PlannerForm onCreated={vi.fn()} />);
    await user.click(screen.getByRole("button", { name: "Create my plan" }));

    expect(await screen.findByRole("button", { name: "Agents are planning..." })).toBeDisabled();
    expect(screen.getByRole("status")).toHaveTextContent("up to 20 seconds");
    finish({ id: PLAN_ID, edit_token: "t" });
    await waitFor(() => expect(screen.getByRole("button", { name: "Create my plan" })).toBeEnabled());
  });

  it("shows a generic message for unexpected failures", async () => {
    api.createPlan.mockRejectedValue("boom");
    const user = userEvent.setup();
    render(<PlannerForm onCreated={vi.fn()} />);
    await user.click(screen.getByRole("button", { name: "Create my plan" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Something went wrong.");
  });
});
