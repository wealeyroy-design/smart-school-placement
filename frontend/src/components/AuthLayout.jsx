/** Shared two-panel layout for the login and registration pages: a short
 * description of the system on the left, the form on the right. */
export default function AuthLayout({ children }) {
  return (
    <div className="auth-split">
      <aside className="auth-brand">
        <div className="auth-brand-mark">Smart School Placement</div>
        <h2>Fair, proximity-aware secondary school placement for Kenya.</h2>
        <p>
          Places students using a merit- and distance-weighted Gale-Shapley matching algorithm, so that
          academic performance is respected and unnecessary long-distance placements are reduced.
        </p>
        <ul>
          <li><strong>Students &amp; parents</strong> view results, placements and appeals</li>
          <li><strong>School administrators</strong> manage capacity and placed students</li>
          <li><strong>Ministry officials</strong> run placements and monitor equity analytics</li>
        </ul>
        <div className="auth-brand-foot">Kabarak University · Final Year Project</div>
      </aside>
      <main className="auth-page">{children}</main>
    </div>
  );
}
