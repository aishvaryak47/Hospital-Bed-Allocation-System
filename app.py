from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from datetime import datetime, timedelta
import random

from config import Config
from models import db, Department, Patient, Bed, Allocation, AllocationHistory
from discrete_math import GraphTheoryEngine, PriorityQueueEngine, SetTheoryEngine, RelationalAlgebraEngine

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Create database tables if they do not exist
with app.app_context():
    db.create_all()

# --- Page Routes ---

@app.route('/')
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', active_page='dashboard')

@app.route('/patients')
def patients_page():
    return render_template('patients.html', active_page='patients')

@app.route('/beds')
def beds_page():
    return render_template('beds.html', active_page='beds')

@app.route('/allocation')
def allocation_page():
    return render_template('allocation.html', active_page='allocation')

@app.route('/history')
def history_page():
    return render_template('history.html', active_page='history')

@app.route('/reports')
def reports_page():
    return render_template('reports.html', active_page='reports')

@app.route('/settings')
def settings_page():
    return render_template('settings.html', active_page='settings')


# --- REST API Endpoints ---

@app.route('/api/dashboard/stats')
def api_dashboard_stats():
    total_patients = Patient.query.count()
    pending_patients = Patient.query.filter_by(status='Pending').count()
    allocated_patients = Patient.query.filter_by(status='Allocated').count()
    emergency_patients = Patient.query.filter_by(priority='Emergency', status='Pending').count()
    
    total_beds = Bed.query.count()
    available_beds = Bed.query.filter_by(availability='Available').count()
    occupied_beds = Bed.query.filter_by(availability='Occupied').count()
    maintenance_beds = Bed.query.filter_by(availability='Maintenance').count()
    
    overall_occupancy_rate = round((occupied_beds / total_beds * 100), 1) if total_beds > 0 else 0.0

    dept_stats = [d.to_dict() for d in Department.query.all()]

    return jsonify({
        'total_patients': total_patients,
        'pending_patients': pending_patients,
        'allocated_patients': allocated_patients,
        'emergency_patients': emergency_patients,
        'total_beds': total_beds,
        'available_beds': available_beds,
        'occupied_beds': occupied_beds,
        'maintenance_beds': maintenance_beds,
        'overall_occupancy_rate': overall_occupancy_rate,
        'departments': dept_stats
    })

@app.route('/api/dashboard/charts')
def api_dashboard_charts():
    depts = Department.query.all()
    dept_names = [d.name for d in depts]
    dept_occupied = [sum(1 for b in d.beds if b.availability == 'Occupied') for d in depts]
    dept_available = [sum(1 for b in d.beds if b.availability == 'Available') for d in depts]

    # Priority distribution
    emergency_cnt = Patient.query.filter_by(priority='Emergency').count()
    critical_cnt = Patient.query.filter_by(priority='Critical').count()
    general_cnt = Patient.query.filter_by(priority='General').count()

    # Bed status distribution
    available_cnt = Bed.query.filter_by(availability='Available').count()
    occupied_cnt = Bed.query.filter_by(availability='Occupied').count()
    maint_cnt = Bed.query.filter_by(availability='Maintenance').count()

    # Daily admissions (simulated last 7 days)
    today = datetime.utcnow().date()
    days = [(today - timedelta(days=i)).strftime('%b %d') for i in range(6, -1, -1)]
    admissions_count = [random.randint(5, 12) for _ in range(7)]

    return jsonify({
        'dept_occupancy': {
            'labels': dept_names,
            'occupied': dept_occupied,
            'available': dept_available
        },
        'priority_distribution': {
            'labels': ['Emergency', 'Critical', 'General'],
            'data': [emergency_cnt, critical_cnt, general_cnt]
        },
        'bed_status': {
            'labels': ['Available', 'Occupied', 'Maintenance'],
            'data': [available_cnt, occupied_cnt, maint_cnt]
        },
        'daily_admissions': {
            'labels': days,
            'data': admissions_count
        }
    })

@app.route('/api/graph/data')
def api_graph_data():
    data = GraphTheoryEngine.get_network_graph_data()
    return jsonify(data)

@app.route('/api/patients', methods=['GET', 'POST'])
def api_patients():
    if request.method == 'POST':
        data = request.json or request.form
        
        dept_id = int(data.get('department_id'))
        dept = Department.query.get_or_404(dept_id)
        
        priority = data.get('priority', 'General')
        priority_map = {'Emergency': 1, 'Critical': 2, 'General': 3}
        
        count = Patient.query.count() + 1
        patient_code = f"P-{1000 + count}"

        new_patient = Patient(
            patient_code=patient_code,
            name=data.get('name'),
            age=int(data.get('age')),
            gender=data.get('gender'),
            disease=data.get('disease'),
            priority=priority,
            priority_level=priority_map.get(priority, 3),
            department_id=dept.id,
            status='Pending'
        )
        db.session.add(new_patient)
        db.session.commit()
        return jsonify({'message': 'Patient registered successfully', 'patient': new_patient.to_dict()}), 201

    status_filter = request.args.get('status')
    priority_filter = request.args.get('priority')
    search_query = request.args.get('search')

    query = Patient.query
    if status_filter and status_filter != 'All':
        query = query.filter_by(status=status_filter)
    if priority_filter and priority_filter != 'All':
        query = query.filter_by(priority=priority_filter)
    if search_query:
        query = query.filter((Patient.name.ilike(f"%{search_query}%")) | (Patient.patient_code.ilike(f"%{search_query}%")) | (Patient.disease.ilike(f"%{search_query}%")))

    patients = query.order_by(Patient.priority_level.asc(), Patient.admission_time.desc()).all()
    return jsonify([p.to_dict() for p in patients])

@app.route('/api/patients/<int:patient_id>', methods=['PUT', 'DELETE'])
def api_patient_detail(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    
    if request.method == 'DELETE':
        # Clear allocations if any
        allocs = Allocation.query.filter_by(patient_id=patient.id, allocation_status='Active').all()
        for a in allocs:
            a.bed.availability = 'Available'
            a.allocation_status = 'Discharged'
        
        db.session.delete(patient)
        db.session.commit()
        return jsonify({'message': 'Patient record deleted successfully'})

    data = request.json
    patient.name = data.get('name', patient.name)
    patient.age = int(data.get('age', patient.age))
    patient.gender = data.get('gender', patient.gender)
    patient.disease = data.get('disease', patient.disease)
    
    if 'priority' in data:
        patient.priority = data['priority']
        patient.priority_level = {'Emergency': 1, 'Critical': 2, 'General': 3}.get(patient.priority, 3)

    if 'department_id' in data:
        patient.department_id = int(data['department_id'])

    db.session.commit()
    return jsonify({'message': 'Patient updated successfully', 'patient': patient.to_dict()})

@app.route('/api/beds', methods=['GET', 'POST'])
def api_beds():
    if request.method == 'POST':
        data = request.json
        bed_id = data.get('bed_id')
        new_avail = data.get('availability')
        
        bed = Bed.query.get_or_404(bed_id)
        bed.availability = new_avail
        db.session.commit()
        return jsonify({'message': 'Bed availability updated', 'bed': bed.to_dict()})

    dept_filter = request.args.get('department_id')
    avail_filter = request.args.get('availability')

    query = Bed.query
    if dept_filter and dept_filter != 'All':
        query = query.filter_by(department_id=int(dept_filter))
    if avail_filter and avail_filter != 'All':
        query = query.filter_by(availability=avail_filter)

    beds = query.order_by(Bed.bed_number.asc()).all()
    return jsonify([b.to_dict() for b in beds])

@app.route('/api/allocate/auto', methods=['POST'])
def api_allocate_auto():
    results = GraphTheoryEngine.find_bipartite_matching_allocation()
    return jsonify({
        'message': f'Allocated {len(results)} patients using Graph Bipartite Priority Matching algorithm.',
        'allocations': results
    })

@app.route('/api/allocate/manual', methods=['POST'])
def api_allocate_manual():
    data = request.json
    patient_id = data.get('patient_id')
    bed_id = data.get('bed_id')

    patient = Patient.query.get_or_404(patient_id)
    bed = Bed.query.get_or_404(bed_id)

    if bed.availability != 'Available':
        return jsonify({'error': 'Selected bed is not available'}), 400

    patient.status = 'Allocated'
    bed.availability = 'Occupied'

    alloc = Allocation(
        patient_id=patient.id,
        bed_id=bed.id,
        allocation_time=datetime.utcnow(),
        allocation_status='Active'
    )
    db.session.add(alloc)

    history = AllocationHistory(
        patient_code=patient.patient_code,
        patient_name=patient.name,
        bed_number=bed.bed_number,
        department_name=bed.department.name,
        action='Allocated',
        priority=patient.priority,
        timestamp=datetime.utcnow(),
        notes='Manual allocation by administrator.'
    )
    db.session.add(history)
    db.session.commit()

    return jsonify({'message': 'Manual allocation successful', 'allocation': alloc.to_dict()})

@app.route('/api/discharge/<int:patient_id>', methods=['POST'])
def api_discharge_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    
    active_alloc = Allocation.query.filter_by(patient_id=patient.id, allocation_status='Active').first()
    if not active_alloc:
        return jsonify({'error': 'No active bed allocation found for this patient'}), 400

    bed = active_alloc.bed
    bed.availability = 'Available'
    patient.status = 'Discharged'

    active_alloc.allocation_status = 'Discharged'
    active_alloc.discharge_time = datetime.utcnow()

    history = AllocationHistory(
        patient_code=patient.patient_code,
        patient_name=patient.name,
        bed_number=bed.bed_number,
        department_name=bed.department.name,
        action='Discharged',
        priority=patient.priority,
        timestamp=datetime.utcnow(),
        notes='Patient discharged. Bed moved from Occupied Set back to Available Set.'
    )
    db.session.add(history)
    db.session.commit()

    return jsonify({'message': f'Patient {patient.name} discharged successfully. Bed {bed.bed_number} is now Available.'})

@app.route('/api/reallocate', methods=['POST'])
def api_reallocate_patient():
    data = request.json
    patient_id = data.get('patient_id')
    new_bed_id = data.get('new_bed_id')

    patient = Patient.query.get_or_404(patient_id)
    new_bed = Bed.query.get_or_404(new_bed_id)

    if new_bed.availability != 'Available':
        return jsonify({'error': 'Target bed is not available'}), 400

    active_alloc = Allocation.query.filter_by(patient_id=patient.id, allocation_status='Active').first()
    if active_alloc:
        old_bed = active_alloc.bed
        old_bed.availability = 'Available'
        active_alloc.allocation_status = 'Reallocated'
        active_alloc.discharge_time = datetime.utcnow()

    new_bed.availability = 'Occupied'
    new_alloc = Allocation(
        patient_id=patient.id,
        bed_id=new_bed.id,
        allocation_time=datetime.utcnow(),
        allocation_status='Active'
    )
    db.session.add(new_alloc)

    history = AllocationHistory(
        patient_code=patient.patient_code,
        patient_name=patient.name,
        bed_number=new_bed.bed_number,
        department_name=new_bed.department.name,
        action='Reallocated',
        priority=patient.priority,
        timestamp=datetime.utcnow(),
        notes=f"Reallocated to bed {new_bed.bed_number}."
    )
    db.session.add(history)
    db.session.commit()

    return jsonify({'message': 'Bed reallocated successfully'})

@app.route('/api/history')
def api_history():
    logs = AllocationHistory.query.order_by(AllocationHistory.timestamp.desc()).all()
    return jsonify([l.to_dict() for l in logs])

@app.route('/api/set-theory')
def api_set_theory():
    return jsonify(SetTheoryEngine.get_bed_sets())

@app.route('/api/relations')
def api_relations():
    return jsonify(RelationalAlgebraEngine.get_relations_summary())

@app.route('/api/seed/reset', methods=['POST'])
def api_seed_reset():
    from seed_data import seed_database
    seed_database()
    return jsonify({'message': 'Database re-seeded with sample patients and beds successfully.'})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
