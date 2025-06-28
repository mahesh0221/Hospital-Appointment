from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Association table: Many-to-Many between Doctor and Department
doctor_department = db.Table('doctor_department',
    db.Column('doctor_id', db.Integer, db.ForeignKey('doctor.id')),
    db.Column('department_id', db.Integer, db.ForeignKey('department.id'))
)

class Hospital(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    departments = db.relationship('Department', backref='hospital', lazy=True)
    doctor_hospitals = db.relationship('DoctorHospital', backref='hospital', lazy=True)
    appointments = db.relationship('Appointment', backref='hospital', lazy=True)

class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id'), nullable=False)
    doctors = db.relationship('Doctor', secondary=doctor_department, backref='departments')

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    qualifications = db.Column(db.String(200), nullable=False)
    specializations = db.Column(db.String(200), nullable=False)  # Comma-separated specializations
    experience = db.Column(db.Integer, nullable=False)
    doctor_hospitals = db.relationship('DoctorHospital', backref='doctor', lazy=True)
    appointments = db.relationship('Appointment', backref='doctor', lazy=True)

class DoctorHospital(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id'), nullable=False)
    consultation_fee = db.Column(db.Integer, nullable=False)

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    dob = db.Column(db.String(20), nullable=False)
    unique_id = db.Column(db.String(100), unique=True, nullable=False)
    appointments = db.relationship('Appointment', backref='patient', lazy=True)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id'), nullable=False)
    start_time = db.Column(db.String(50), nullable=False)
    consultation_fee = db.Column(db.Integer, nullable=False)
    booked = db.Column(db.Boolean, default=False)

@app.route('/initdb')
def initdb():
    db.create_all()
    return "Database initialized!"

@app.route('/admin_dashboard/<int:hospital_id>', methods=['GET'])
def admin_dashboard(hospital_id):
    hospital = Hospital.query.get(hospital_id)
    if not hospital:
        return jsonify({'error': 'Hospital not found'}), 404

    # List of all doctors in the hospital
    doctor_assocs = DoctorHospital.query.filter_by(hospital_id=hospital_id).all()
    doctors = []
    doctor_revenue = {}
    for assoc in doctor_assocs:
        doctor = Doctor.query.get(assoc.doctor_id)
        doctors.append({
            "doctor_id": doctor.id,
            "name": doctor.name,
            "specializations": doctor.specializations,
            "experience": doctor.experience,
            "consultation_fee": assoc.consultation_fee
        })

        # Revenue per doctor
        appointments = Appointment.query.filter_by(doctor_id=doctor.id, hospital_id=hospital_id).all()
        doctor_total = sum(a.consultation_fee for a in appointments)
        doctor_revenue[doctor.name] = doctor_total

    # Total consultations & revenue in the hospital
    all_appointments = Appointment.query.filter_by(hospital_id=hospital_id).all()
    total_consultations = len(all_appointments)
    total_revenue = sum(a.consultation_fee for a in all_appointments)

    # Revenue per department
    dept_revenue = {}
    departments = Department.query.filter_by(hospital_id=hospital_id).all()
    for dept in departments:
        dept_total = 0
        for doc in dept.doctors:
            # Ensure doctor is associated with this hospital
            if DoctorHospital.query.filter_by(doctor_id=doc.id, hospital_id=hospital_id).first():
                appts = Appointment.query.filter_by(doctor_id=doc.id, hospital_id=hospital_id).all()
                dept_total += sum(a.consultation_fee for a in appts)
        dept_revenue[dept.name] = dept_total

    return jsonify({
        "hospital": hospital.name,
        "location": hospital.location,
        "total_consultations": total_consultations,
        "total_revenue": total_revenue,
        "doctors": doctors,
        "revenue_per_doctor": doctor_revenue,
        "revenue_per_department": dept_revenue
    })

@app.route('/register_doctor', methods=['POST'])
def register_doctor():
    data = request.get_json()
    doctor = Doctor(
        name=data['name'],
        qualifications=data['qualifications'],
        specializations=data['specializations'],
        experience=data['experience']
    )
    db.session.add(doctor)
    db.session.commit()
    return jsonify({"message": "Doctor registered successfully", "doctor_id": doctor.id})

@app.route('/associate_doctor', methods=['POST'])
def associate_doctor():
    data = request.get_json()

    doctor_id = data['doctor_id']
    hospital_id = data['hospital_id']
    consultation_fee = data['consultation_fee']

    # Validate doctor and hospital exist
    doctor = Doctor.query.get(doctor_id)
    hospital = Hospital.query.get(hospital_id)

    if not doctor or not hospital:
        return jsonify({"error": "Doctor or Hospital not found"}), 404

    # Create doctor-hospital association
    assoc = DoctorHospital(
        doctor_id=doctor_id,
        hospital_id=hospital_id,
        consultation_fee=consultation_fee
    )
    db.session.add(assoc)
    db.session.commit()

    return jsonify({"message": "Doctor associated with hospital successfully"})

@app.route('/doctor_dashboard/<int:doctor_id>', methods=['GET'])
def doctor_dashboard(doctor_id):
    doctor = db.session.get(Doctor, doctor_id)
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404

    appointments = Appointment.query.filter_by(doctor_id=doctor_id, booked=True).all()

    total_earnings = sum(a.consultation_fee * 0.6 for a in appointments)
    total_consultations = len(appointments)

    # Unique patients
    unique_patients = {}
    for appt in appointments:
        patient = db.session.get(Patient, appt.patient_id)
        if patient and patient.id not in unique_patients:
            unique_patients[patient.id] = patient.name

    # Earnings per hospital
    hospital_earnings = {}
    for appt in appointments:
        hospital = db.session.get(Hospital, appt.hospital_id)
        if hospital:
            if hospital.name not in hospital_earnings:
                hospital_earnings[hospital.name] = 0
            hospital_earnings[hospital.name] += appt.consultation_fee * 0.6

    # Prepare patient list
    patient_list = [{"patient_id": pid, "name": pname} for pid, pname in unique_patients.items()]

    return jsonify({
        "doctor_name": doctor.name,
        "total_consultations": total_consultations,
        "total_unique_patients": len(unique_patients),
        "patients": patient_list,
        "total_earnings": total_earnings,
        "earnings_per_hospital": hospital_earnings
    })

@app.route('/create_hospital', methods=['POST'])
def create_hospital():
    data = request.get_json()
    new_hospital = Hospital(name=data['name'], location=data['location'])
    db.session.add(new_hospital)
    db.session.commit()
    return jsonify({"message": "Hospital created successfully", "hospital_id": new_hospital.id})

@app.route('/add_department', methods=['POST'])
def add_department():
    data = request.get_json()
    department = Department(name=data['name'], hospital_id=data['hospital_id'])
    db.session.add(department)
    db.session.commit()
    return jsonify({"message": "Department added successfully"})

@app.route('/register_patient', methods=['POST'])
def register_patient():
    data = request.get_json()

    # Ensure all required fields are present
    if not all(k in data for k in ('name', 'gender', 'dob', 'unique_id')):
        return jsonify({'error': 'Missing required fields'}), 400

    # Check for duplicate unique ID
    if Patient.query.filter_by(unique_id=data['unique_id']).first():
        return jsonify({'error': 'Patient with this unique ID already exists'}), 400

    patient = Patient(
        name=data['name'],
        gender=data['gender'],
        dob=data['dob'],
        unique_id=data['unique_id']
    )

    db.session.add(patient)
    db.session.commit()

    return jsonify({"message": "Patient registered successfully", "patient_id": patient.id})
@app.route('/book_appointment', methods=['POST'])
def book_appointment():
    data = request.get_json()

    patient_id = data['patient_id']
    doctor_id = data['doctor_id']
    hospital_id = data['hospital_id']
    start_time = data['start_time']
    consultation_fee = data['consultation_fee']

    # Check if doctor is already booked at that time
    conflict = Appointment.query.filter_by(doctor_id=doctor_id, start_time=start_time).first()
    if conflict:
        return jsonify({"error": "This time slot is already booked"}), 400

    # Create the appointment
    appointment = Appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        hospital_id=hospital_id,
        start_time=start_time,
        consultation_fee=consultation_fee,
        booked=True
    )
    db.session.add(appointment)
    db.session.commit()

    return jsonify({"message": "Appointment booked successfully", "appointment_id": appointment.id})


@app.route('/patient_history/<int:patient_id>', methods=['GET'])
def patient_history(patient_id):
    patient = db.session.get(Patient, patient_id)
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404

    appointments = Appointment.query.filter_by(patient_id=patient_id).all()
    history = []
    for a in appointments:
        doctor = db.session.get(Doctor, a.doctor_id)
        hospital = db.session.get(Hospital, a.hospital_id)
        history.append({
            "doctor_name": doctor.name if doctor else "Unknown",
            "hospital_name": hospital.name if hospital else "Unknown",
            "consultation_fee": a.consultation_fee,
            "start_time": a.start_time
        })

    return jsonify({
        "patient_name": patient.name,
        "total_consultations": len(appointments),
        "consultation_history": history
    })

@app.route('/doctor_dashboard/<int:doctor_id>', methods=['GET'])
def doctor_dashboard_updated(doctor_id):
    doctor = Doctor.query.get(doctor_id)
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404

    appointments = Appointment.query.filter_by(doctor_id=doctor_id).all()

    total_earnings = sum(a.consultation_fee for a in appointments)
    total_consultations = len(appointments)

    # Unique patients with IDs and names
    unique_patients = {}
    for appt in appointments:
        patient = Patient.query.get(appt.patient_id)
        if patient and patient.id not in unique_patients:
            unique_patients[patient.id] = patient.name

    total_unique_patients = len(unique_patients)

    # Earnings per hospital
    hospital_earnings = {}
    for appt in appointments:
        hospital = db.session.get(Hospital, a.hospital_id)

        if hospital:
            if hospital.name not in hospital_earnings:
                hospital_earnings[hospital.name] = 0
            hospital_earnings[hospital.name] += appt.consultation_fee

    # Format patient list
    patient_list = [
        {"patient_id": pid, "name": pname} for pid, pname in unique_patients.items()
    ]

    return jsonify({
        "doctor_name": doctor.name,
        "total_consultations": total_consultations,
        "total_unique_patients": total_unique_patients,
        "patients": patient_list,
        "total_earnings": total_earnings,
        "earnings_per_hospital": hospital_earnings
    })

if __name__ == '__main__':
    app.run(debug=True)

