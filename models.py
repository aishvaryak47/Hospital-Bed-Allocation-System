from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Department(db.Model):
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    code = db.Column(db.String(10), nullable=False, unique=True)
    capacity = db.Column(db.Integer, nullable=False, default=20)
    description = db.Column(db.String(255), nullable=True)

    # Relationships
    beds = db.relationship('Bed', backref='department', lazy=True, cascade="all, delete-orphan")
    patients = db.relationship('Patient', backref='department', lazy=True)

    def to_dict(self):
        total_beds = len(self.beds)
        occupied_beds = sum(1 for b in self.beds if b.availability == 'Occupied')
        available_beds = sum(1 for b in self.beds if b.availability == 'Available')
        occupancy_rate = round((occupied_beds / total_beds * 100), 1) if total_beds > 0 else 0.0

        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'capacity': self.capacity,
            'description': self.description,
            'total_beds': total_beds,
            'occupied_beds': occupied_beds,
            'available_beds': available_beds,
            'occupancy_rate': occupancy_rate
        }

class Patient(db.Model):
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    disease = db.Column(db.String(200), nullable=False)
    priority = db.Column(db.String(20), nullable=False, default='General') # Emergency, Critical, General
    priority_level = db.Column(db.Integer, nullable=False, default=3) # 1: Emergency, 2: Critical, 3: General
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    admission_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='Pending') # Pending, Allocated, Discharged

    # Relationships
    allocations = db.relationship('Allocation', backref='patient', lazy=True)

    def to_dict(self):
        allocated_bed = None
        active_allocation = Allocation.query.filter_by(patient_id=self.id, allocation_status='Active').first()
        if active_allocation and active_allocation.bed:
            allocated_bed = active_allocation.bed.bed_number

        return {
            'id': self.id,
            'patient_code': self.patient_code,
            'name': self.name,
            'age': self.age,
            'gender': self.gender,
            'disease': self.disease,
            'priority': self.priority,
            'priority_level': self.priority_level,
            'department_id': self.department_id,
            'department_name': self.department.name if self.department else 'N/A',
            'admission_time': self.admission_time.strftime('%Y-%m-%d %H:%M:%S') if self.admission_time else None,
            'status': self.status,
            'allocated_bed': allocated_bed
        }

class Bed(db.Model):
    __tablename__ = 'beds'
    
    id = db.Column(db.Integer, primary_key=True)
    bed_number = db.Column(db.String(20), unique=True, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    bed_type = db.Column(db.String(50), nullable=False, default='Standard')
    availability = db.Column(db.String(20), nullable=False, default='Available') # Available, Occupied, Maintenance

    # Relationships
    allocations = db.relationship('Allocation', backref='bed', lazy=True)

    def to_dict(self):
        current_patient = None
        active_allocation = Allocation.query.filter_by(bed_id=self.id, allocation_status='Active').first()
        if active_allocation and active_allocation.patient:
            current_patient = {
                'id': active_allocation.patient.id,
                'name': active_allocation.patient.name,
                'patient_code': active_allocation.patient.patient_code,
                'priority': active_allocation.patient.priority
            }

        return {
            'id': self.id,
            'bed_number': self.bed_number,
            'department_id': self.department_id,
            'department_name': self.department.name if self.department else 'N/A',
            'bed_type': self.bed_type,
            'availability': self.availability,
            'current_patient': current_patient
        }

class Allocation(db.Model):
    __tablename__ = 'allocations'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    bed_id = db.Column(db.Integer, db.ForeignKey('beds.id'), nullable=False)
    allocation_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    discharge_time = db.Column(db.DateTime, nullable=True)
    allocation_status = db.Column(db.String(20), nullable=False, default='Active') # Active, Discharged, Reallocated

    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'patient_name': self.patient.name if self.patient else 'Unknown',
            'patient_code': self.patient.patient_code if self.patient else 'N/A',
            'patient_priority': self.patient.priority if self.patient else 'General',
            'bed_id': self.bed_id,
            'bed_number': self.bed.bed_number if self.bed else 'N/A',
            'department_name': self.bed.department.name if (self.bed and self.bed.department) else 'N/A',
            'allocation_time': self.allocation_time.strftime('%Y-%m-%d %H:%M:%S') if self.allocation_time else None,
            'discharge_time': self.discharge_time.strftime('%Y-%m-%d %H:%M:%S') if self.discharge_time else None,
            'allocation_status': self.allocation_status
        }

class AllocationHistory(db.Model):
    __tablename__ = 'allocation_history'

    id = db.Column(db.Integer, primary_key=True)
    patient_code = db.Column(db.String(20), nullable=False)
    patient_name = db.Column(db.String(100), nullable=False)
    bed_number = db.Column(db.String(20), nullable=False)
    department_name = db.Column(db.String(100), nullable=False)
    action = db.Column(db.String(30), nullable=False) # 'Allocated', 'Reallocated', 'Discharged'
    priority = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'patient_code': self.patient_code,
            'patient_name': self.patient_name,
            'bed_number': self.bed_number,
            'department_name': self.department_name,
            'action': self.action,
            'priority': self.priority,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S') if self.timestamp else None,
            'notes': self.notes
        }
