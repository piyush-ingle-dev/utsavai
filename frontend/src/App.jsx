import { useEffect, useState } from "react";
import PlannerForm from "./components/PlannerForm.jsx";
import PlanView from "./components/PlanView.jsx";

// Tiny router: "/" shows the form, "/plan/<id>" shows a saved plan.
function readPlanId() {
  const match = window.location.pathname.match(/^\/plan\/([0-9a-f]{32})\/?$/);
  return match ? match[1] : null;
}

export default function App() {
  const [planId, setPlanId] = useState(readPlanId());

  useEffect(() => {
    const onPop = () => setPlanId(readPlanId());
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  function open(id) {
    window.history.pushState({}, "", id ? `/plan/${id}` : "/");
    setPlanId(id);
    window.scrollTo(0, 0);
  }

  return (
    <>
      <a className="skip" href="#main">Skip to main content</a>
      <header className="site">
        <a className="brand" href="/" onClick={(e) => { e.preventDefault(); open(null); }}>UtsavAI</a>
        <span className="tag">Celebration &amp; Event Planner</span>
      </header>
      <main id="main" tabIndex={-1}>
        {planId ? <PlanView planId={planId} onNew={() => open(null)} /> : <PlannerForm onCreated={open} />}
      </main>
      <footer className="site">
        <p>Plans are saved at a private link. Anyone with the link can view it.</p>
      </footer>
    </>
  );
}
