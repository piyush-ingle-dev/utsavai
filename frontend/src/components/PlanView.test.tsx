import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "vitest-axe";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../api";
import { makePlan, PLAN_ID } from "../test/fixtures";
import PlanView from "./PlanView";

const api = vi.hoisted(() => ({ getPlan: vi.fn(), toggleItem: vi.fn(), askPlanner: vi.fn() }));
vi.mock("../api", async (importOriginal) => ({ ...(await importOriginal<Record<string, unknown>>()), ...api }));

describe("PlanView", () => {
  beforeEach(() => {
    Object.values(api).forEach((mock) => mock.mockReset());
  });

  it("shows a loading state, then the plan with every section", async () => {
    api.getPlan.mockResolvedValue(makePlan());
    render(<PlanView planId={PLAN_ID} onNew={vi.fn()} />);
    expect(screen.getByRole("status")).toHaveTextContent("Loading your plan");

    expect(await screen.findByRole("heading", { level: 1, name: "Riya and Aman" })).toBeInTheDocument();
    for (const name of ["Budget split", "Timeline", "Vendor checklist", "Ideas for your event", "What could go wrong", "Ask the planner", "How this plan was made"]) {
      expect(screen.getByRole("heading", { name })).toBeInTheDocument();
    }
    expect(screen.getByText("Your budget is tight")).toBeInTheDocument();
    expect(screen.getByText("compressed")).toBeInTheDocument();
    expect(screen.getByText("3,00,000")).toBeInTheDocument();
    expect(document.title).toBe("Riya and Aman | UtsavAI");
  });

  it("has no accessibility violations", async () => {
    api.getPlan.mockResolvedValue(makePlan());
    const { container } = render(<PlanView planId={PLAN_ID} onNew={vi.fn()} />);
    await screen.findByRole("heading", { level: 1 });
    expect(await axe(container)).toHaveNoViolations();
  });

  it("lets the owner tick an item and shows progress straight away", async () => {
    api.getPlan.mockResolvedValue(makePlan());
    api.toggleItem.mockResolvedValue({ id: "t0", done: true, completed: 1, total: 3 });
    const user = userEvent.setup();
    render(<PlanView planId={PLAN_ID} onNew={vi.fn()} />);

    const box = await screen.findByRole("checkbox", { name: /Book the venue/ });
    await user.click(box);
    expect(box).toBeChecked();
    expect(api.toggleItem).toHaveBeenCalledWith(PLAN_ID, "t0");
    expect(await screen.findByText(/1 of 3 items done/)).toBeInTheDocument();
  });

  it("undoes the tick and explains when saving fails", async () => {
    api.getPlan.mockResolvedValue(makePlan());
    api.toggleItem.mockRejectedValue(new ApiError("nope", 403));
    const user = userEvent.setup();
    render(<PlanView planId={PLAN_ID} onNew={vi.fn()} />);

    const box = await screen.findByRole("checkbox", { name: /Caterer/ });
    await user.click(box);
    expect(await screen.findByRole("alert")).toHaveTextContent("Could not save that change");
    expect(box).not.toBeChecked();
  });

  it("is read-only for visitors without the edit token", async () => {
    api.getPlan.mockResolvedValue(makePlan({ can_edit: false }));
    render(<PlanView planId={PLAN_ID} onNew={vi.fn()} />);
    await screen.findByRole("heading", { level: 1 });
    expect(screen.getByText(/View only/)).toBeInTheDocument();
    for (const box of screen.getAllByRole("checkbox")) expect(box).toBeDisabled();
  });

  it("says when a plan does not exist and offers a way back", async () => {
    api.getPlan.mockRejectedValue(new ApiError("Not found.", 404));
    const onNew = vi.fn();
    const user = userEvent.setup();
    render(<PlanView planId={PLAN_ID} onNew={onNew} />);
    expect(await screen.findByText("We could not find that plan.")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Back to the planner" }));
    expect(onNew).toHaveBeenCalled();
  });

  it("shows other load errors as they are", async () => {
    api.getPlan.mockRejectedValue(new Error("Server is down"));
    render(<PlanView planId={PLAN_ID} onNew={vi.fn()} />);
    expect(await screen.findByText("Server is down")).toBeInTheDocument();
  });

  it("links the calendar download and hides empty sections", async () => {
    const plan = makePlan();
    plan.plan.risks = [];
    plan.plan.vendor_tips = [];
    api.getPlan.mockResolvedValue(plan);
    render(<PlanView planId={PLAN_ID} onNew={vi.fn()} />);
    const link = await screen.findByRole("link", { name: "Add timeline to calendar" });
    expect(link).toHaveAttribute("href", `/api/plans/${PLAN_ID}/calendar.ics`);
    expect(screen.queryByRole("heading", { name: "What could go wrong" })).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Tips" })).not.toBeInTheDocument();
  });

  it("prints the plan and starts a new one from the header buttons", async () => {
    api.getPlan.mockResolvedValue(makePlan());
    const print = vi.spyOn(window, "print").mockImplementation(() => undefined);
    const onNew = vi.fn();
    const user = userEvent.setup();
    render(<PlanView planId={PLAN_ID} onNew={onNew} />);
    await user.click(await screen.findByRole("button", { name: "Print or save as PDF" }));
    await user.click(screen.getByRole("button", { name: "New plan" }));
    expect(print).toHaveBeenCalledOnce();
    expect(onNew).toHaveBeenCalledOnce();
    print.mockRestore();
  });

  it("lists the agent trace in order", async () => {
    api.getPlan.mockResolvedValue(makePlan());
    render(<PlanView planId={PLAN_ID} onNew={vi.fn()} />);
    const section = (await screen.findByRole("heading", { name: "How this plan was made" })).closest("section");
    const steps = within(section as HTMLElement).getAllByRole("listitem");
    expect(steps[0]).toHaveTextContent("Researcher");
    expect(steps[1]).toHaveTextContent("Critic");
  });
});
