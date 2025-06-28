
import React from "react";
import { Link } from "react-router-dom";

const Navbar = () => (
  <nav style={{ padding: "10px", background: "#333", color: "#fff" }}>
    <Link to="/admin" style={{ marginRight: 20, color: "#fff" }}>Admin</Link>
    <Link to="/doctor" style={{ marginRight: 20, color: "#fff" }}>Doctor</Link>
    <Link to="/patient" style={{ color: "#fff" }}>Patient</Link>
  </nav>
);

export default Navbar;
