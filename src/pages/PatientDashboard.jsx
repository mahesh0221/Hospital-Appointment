
import React, { useEffect, useState } from "react";
import axios from "axios";

const PatientDashboard = () => {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    axios.get("http://127.0.0.1:5000/patient_history/1")  // replace 1 with patient ID
      .then(res => setHistory(res.data.history))
      .catch(err => console.log(err));
  }, []);

  return (
    <div className="p-4">
      <h2>Patient Dashboard</h2>
      <ul>
        {history.map((item, i) => (
          <li key={i}>
            {item.doctor} at {item.hospital} on {item.date} – ₹{item.fee}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default PatientDashboard;
