
import React, { useEffect, useState } from "react";
import axios from "axios";

function DoctorDashboard() {
  const [data, setData] = useState(null);

  useEffect(() => {
    axios.get("http://127.0.0.1:5000/doctor_dashboard/1") // update ID as needed
      .then((res) => setData(res.data))
      .catch((err) => console.log(err));
  }, []);

  return (
    <div className="p-4">
      <h2>Doctor Dashboard</h2>
      {data ? (
        <div>
          <p><strong>Total Consultations:</strong> {data.total_consultations}</p>
          <p><strong>Total Earnings:</strong> ₹{data.total_earnings}</p>
          <h4>Earnings by Hospital:</h4>
          <ul>
            {Object.entries(data.earnings_by_hospital).map(([hospital, amount]) => (
              <li key={hospital}>{hospital}: ₹{amount}</li>
            ))}
          </ul>
        </div>
      ) : <p>Loading...</p>}
    </div>
  );
}

export default DoctorDashboard;
