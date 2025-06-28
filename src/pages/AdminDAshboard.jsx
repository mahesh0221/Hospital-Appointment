
import React, { useEffect, useState } from "react";
import axios from "axios";

const AdminDashboard = () => {
  const [hospitals, setHospitals] = useState([]);

  useEffect(() => {
    axios.get("http://127.0.0.1:5000/hospitals")
      .then(res => setHospitals(res.data))
      .catch(err => console.log(err));
  }, []);

  return (
    <div className="p-4">
      <h2>Admin Dashboard</h2>
      <ul>
        {hospitals.map(h => (
          <li key={h.id}>{h.name} ({h.location})</li>
        ))}
      </ul>
    </div>
  );
};

export default AdminDashboard;
