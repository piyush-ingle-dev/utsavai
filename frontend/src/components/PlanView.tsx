import { useEffect } from "react";
import { usePlan } from "../hooks/usePlan";
import AgentTrace from "./AgentTrace";
import AskPlanner from "./AskPlanner";
import BudgetTable from "./BudgetTable";
import { TimelineSection, VendorSection } from "./ChecklistSections";
import PlanHeader from "./PlanHeader";
import { IdeasSection, RisksSection } from "./PlanSections";

interface PlanViewProps {
  planId: string;
  onNew: () => void;
}

export default function PlanView({ planId, onNew }: PlanViewProps) {
  const { plan, error, saveError, toggle } = usePlan(planId);

  useEffect(() => {
    document.title = plan ? `${plan.title} | UtsavAI` : "Loading plan | UtsavAI";
  }, [plan?.title]); // eslint-disable-line react-hooks/exhaustive-deps -- only the title matters here

  if (error) {
    return (
      <section className="hero">
        <h1>Plan not found</h1>
        <p>{error}</p>
        <button type="button" className="btn" onClick={onNew}>
          Back to the planner
        </button>
      </section>
    );
  }
  if (!plan) return <p role="status">Loading your plan...</p>;

  const { plan: data } = plan;
  return (
    <>
      <PlanHeader plan={plan} saveError={saveError} onNew={onNew} />
      {data.warnings.map((warning) => (
        <div className="alert" role="note" key={warning}>
          {warning}
        </div>
      ))}
      <BudgetTable lines={data.budget} total={plan.budget} />
      <TimelineSection items={data.timeline} canEdit={plan.can_edit} onToggle={toggle} />
      <VendorSection items={data.vendors} tips={data.vendor_tips} canEdit={plan.can_edit} onToggle={toggle} />
      <IdeasSection ideas={data.ideas} />
      <RisksSection risks={data.risks} />
      <AskPlanner planId={planId} />
      <AgentTrace trace={data.trace} source={data.source} />
    </>
  );
}
