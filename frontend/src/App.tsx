import { useEffect, useRef, useState } from "react";
import PlannerForm from "./components/PlannerForm";
import PlanView from "./components/PlanView";

const HOME_TITLE = "UtsavAI | Celebration & Event Planner";

/** Tiny router: "/" shows the form, "/plan/<id>" shows a saved plan. */
function readPlanId(): string | null {
  return /^\/plan\/([0-9a-f]{32})\/?$/.exec(window.location.pathname)?.[1] ?? null;
}

export default function App() {
  const [planId, setPlanId] = useState<string | null>(readPlanId);
  const mainRef = useRef<HTMLElement>(null);
  const firstRender = useRef(true);

  useEffect(() => {
    const onPop = (): void => setPlanId(readPlanId());
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  // After moving between the form and a plan, set the page title and move focus to the main area
  // so keyboard and screen reader users start at the new content instead of the old position.
  useEffect(() => {
    if (!planId) document.title = HOME_TITLE;
    if (firstRender.current) {
      firstRender.current = false;
      return;
    }
    mainRef.current?.focus();
  }, [planId]);

  function open(id: string | null): void {
    window.history.pushState({}, "", id ? `/plan/${id}` : "/");
    setPlanId(id);
    window.scrollTo(0, 0);
  }

  return (
    <>
      <a className="skip" href="#main">
        Skip to main content
      </a>
      <header className="site">
        <a
          className="brand"
          href="/"
          onClick={(event) => {
            event.preventDefault();
            open(null);
          }}
        >
          UtsavAI
        </a>
        <span className="tag">Celebration &amp; Event Planner</span>
      </header>
      <main id="main" tabIndex={-1} ref={mainRef}>
        {planId ? <PlanView planId={planId} onNew={() => open(null)} /> : <PlannerForm onCreated={open} />}
      </main>
      <footer className="site">
        <p>Plans are saved at a private link. Anyone with the link can view it.</p>
      </footer>
    </>
  );
}
