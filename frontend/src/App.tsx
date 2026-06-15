import { NavLink, Route, Routes } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Frameworks from "./pages/Frameworks";
import Coverage from "./pages/Coverage";
import Vendors from "./pages/Vendors";
import VendorDetail from "./pages/VendorDetail";
import AddVendor from "./pages/AddVendor";

export default function App() {
  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="brand">
          Com<span className="dot">buy</span>n
        </div>
        <div className="tagline">buy in to compliance</div>
        <nav className="nav">
          <NavLink to="/" end>
            Dashboard
          </NavLink>
          <div className="nav-group">TPRM</div>
          <NavLink to="/vendors">Vendors</NavLink>
          <div className="nav-group">Compliance</div>
          <NavLink to="/frameworks">Frameworks</NavLink>
          <NavLink to="/coverage">Control Coverage</NavLink>
        </nav>
      </aside>
      <main className="main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/frameworks" element={<Frameworks />} />
          <Route path="/coverage" element={<Coverage />} />
          <Route path="/vendors" element={<Vendors />} />
          <Route path="/vendors/new" element={<AddVendor />} />
          <Route path="/vendors/:id" element={<VendorDetail />} />
        </Routes>
      </main>
    </div>
  );
}
