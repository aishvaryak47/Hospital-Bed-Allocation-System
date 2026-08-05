import random
from datetime import datetime, timedelta
from app import app
from models import db, Department, Patient, Bed, Allocation, AllocationHistory

FIRST_NAMES = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", 
               "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
               "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
               "Matthew", "Betty", "Anthony", "Margaret", "Donald", "Sandra", "Mark", "Ashley",
               "Paul", "Kimberly", "Steven", "Emily", "Andrew", "Donna", "Kenneth", "Michelle"]

LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
              "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
              "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White"]

DISEASES = {
    'ICU': ["Acute Respiratory Distress Syndrome", "Severe Sepsis", "Myocardial Infarction", "Multiple Trauma", "Post-Cardiac Arrest"],
    'EMG': ["Acute Chest Pain", "Traumatic Fracture", "Severe Allergic Reaction", "Head Injury", "Acute Stroke"],
    'GEN': ["Pneumonia", "Gastroenteritis", "Type 2 Diabetes Complication", "Hypertension Crisis", "Urinary Tract Infection"],
    'PED': ["Pediatric Asthma", "Bronchiolitis", "Febrile Seizure", "Dehydration", "Viral Fever"],
    'ORT': ["Femur Fracture", "Total Knee Replacement", "Spinal Stenosis", "Rotator Cuff Tear", "Dislocated Shoulder"]
}

BED_TYPES = {
    'ICU': ['ICU Ventilator Bed', 'Cardiac Monitor Bed', 'Specialized ICU Bed'],
    'EMG': ['Trauma Stretcher Bed', 'Emergency Triage Bed', 'Resuscitation Bed'],
    'GEN': ['Standard Ward Bed', 'Semiprivate Ward Bed', 'Isolation Ward Bed'],
    'PED': ['Pediatric Bed', 'Infant Crib Bed', 'Junior Ward Bed'],
    'ORT': ['Orthopedic Traction Bed', 'Post-Op Surgical Bed', 'Motorized Ortho Bed']
}

def seed_database():
    with app.app_context():

        db.drop_all()
        db.create_all()
        print("Database tables recreated.")

        # 1. Create Departments
        departments_data = [
            {'name': 'Intensive Care Unit', 'code': 'ICU', 'capacity': 20, 'description': 'Critical care with 24/7 advanced monitoring and ventilators.'},
            {'name': 'Emergency Department', 'code': 'EMG', 'capacity': 25, 'description': 'Immediate trauma response and urgent care treatment.'},
            {'name': 'General Ward', 'code': 'GEN', 'capacity': 35, 'description': 'Inpatient care for acute and subacute non-critical illnesses.'},
            {'name': 'Pediatrics', 'code': 'PED', 'capacity': 20, 'description': 'Specialized medical care for infants, children, and adolescents.'},
            {'name': 'Orthopedics', 'code': 'ORT', 'capacity': 20, 'description': 'Specialized bone, joint, and musculoskeletal surgical recovery.'}
        ]

        dept_objs = {}
        for d_info in departments_data:
            dept = Department(
                name=d_info['name'],
                code=d_info['code'],
                capacity=d_info['capacity'],
                description=d_info['description']
            )
            db.session.add(dept)
            dept_objs[d_info['code']] = dept

        db.session.commit()
        print("Departments created.")

        # 2. Create 120 Beds across departments
        beds_list = []
        bed_counts = {'ICU': 25, 'EMG': 25, 'GEN': 40, 'PED': 20, 'ORT': 20}
        
        for code, count in bed_counts.items():
            dept = dept_objs[code]
            for i in range(1, count + 1):
                bed_num = f"{code}-{i:03d}"
                b_type = random.choice(BED_TYPES[code])
                bed = Bed(
                    bed_number=bed_num,
                    department_id=dept.id,
                    bed_type=b_type,
                    availability='Available'
                )
                db.session.add(bed)
                beds_list.append(bed)

        db.session.commit()
        print(f"Created {len(beds_list)} beds.")

        # 3. Create 45 Patients
        priorities = [('Emergency', 1), ('Critical', 2), ('General', 3)]
        priority_weights = [0.25, 0.35, 0.40]
        genders = ['Male', 'Female']

        patients_list = []
        now = datetime.utcnow()

        for i in range(1, 46):
            patient_code = f"P-{1000 + i}"
            name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            dept_code = random.choice(list(dept_objs.keys()))
            dept = dept_objs[dept_code]
            
            p_type, p_level = random.choices(priorities, weights=priority_weights)[0]
            age = random.randint(1, 14) if dept_code == 'PED' else random.randint(18, 88)
            disease = random.choice(DISEASES[dept_code])
            
            # Admission time between 2 days ago and now
            adm_time = now - timedelta(hours=random.randint(1, 48), minutes=random.randint(0, 59))
            
            patient = Patient(
                patient_code=patient_code,
                name=name,
                age=age,
                gender=random.choice(genders),
                disease=disease,
                priority=p_type,
                priority_level=p_level,
                department_id=dept.id,
                admission_time=adm_time,
                status='Pending'
            )
            db.session.add(patient)
            patients_list.append(patient)

        db.session.commit()
        print(f"Created {len(patients_list)} patients.")

        # 4. Allocate beds to ~30 patients initially based on priority
        # Sort patients by priority level then admission time
        patients_list.sort(key=lambda p: (p.priority_level, p.admission_time))
        
        allocated_count = 0
        for patient in patients_list[:30]:
            # Find available bed in department
            avail_bed = Bed.query.filter_by(department_id=patient.department_id, availability='Available').first()
            if not avail_bed:
                # Fallback to general ward
                gen_dept = dept_objs['GEN']
                avail_bed = Bed.query.filter_by(department_id=gen_dept.id, availability='Available').first()

            if avail_bed:
                patient.status = 'Allocated'
                avail_bed.availability = 'Occupied'
                
                alloc_time = patient.admission_time + timedelta(minutes=random.randint(10, 45))
                alloc = Allocation(
                    patient_id=patient.id,
                    bed_id=avail_bed.id,
                    allocation_time=alloc_time,
                    allocation_status='Active'
                )
                db.session.add(alloc)

                hist = AllocationHistory(
                    patient_code=patient.patient_code,
                    patient_name=patient.name,
                    bed_number=avail_bed.bed_number,
                    department_name=avail_bed.department.name,
                    action='Allocated',
                    priority=patient.priority,
                    timestamp=alloc_time,
                    notes='Initial batch allocation via discrete priority graph logic.'
                )
                db.session.add(hist)
                allocated_count += 1

        # Mark 3 random remaining available beds as Maintenance
        maintenance_beds = Bed.query.filter_by(availability='Available').all()
        for mb in random.sample(maintenance_beds, min(4, len(maintenance_beds))):
            mb.availability = 'Maintenance'

        db.session.commit()
        print(f"Initially allocated {allocated_count} patients to beds.")
        print("Database successfully seeded!")

if __name__ == '__main__':
    seed_database()
