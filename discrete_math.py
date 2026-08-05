import heapq
import networkx as nx
from datetime import datetime
from models import Patient, Bed, Department, Allocation, AllocationHistory, db

class PriorityQueueEngine:

    @staticmethod
    def get_priority_queue():

        pending_patients = Patient.query.filter_by(status='Pending').all()
        

        pq = []
        for p in pending_patients:

            adm_timestamp = p.admission_time.timestamp() if p.admission_time else datetime.utcnow().timestamp()
            heapq.heappush(pq, (p.priority_level, adm_timestamp, p.id, p))
            
        sorted_patients = []
        while pq:
            _, _, _, patient = heapq.heappop(pq)
            sorted_patients.append(patient)
            
        return sorted_patients

class GraphTheoryEngine:

    @staticmethod
    def build_allocation_graph():

        G = nx.DiGraph()
        

        depts = Department.query.all()
        beds = Bed.query.all()
        patients = Patient.query.all()
        

        for d in depts:
            G.add_node(f"D_{d.id}", type="department", label=d.name, code=d.code, id=d.id)
            

        for b in beds:
            color = "#10b981" if b.availability == 'Available' else ("#ef4444" if b.availability == 'Occupied' else "#f59e0b")
            G.add_node(f"B_{b.id}", type="bed", label=b.bed_number, availability=b.availability, dept_id=b.department_id, color=color, id=b.id)
            # Edge: Dept -> Bed
            G.add_edge(f"D_{b.department_id}", f"B_{b.id}", weight=1.0, type="dept_bed")
            

        for p in patients:
            color = "#dc2626" if p.priority == 'Emergency' else ("#f97316" if p.priority == 'Critical' else "#3b82f6")
            G.add_node(f"P_{p.id}", type="patient", label=f"{p.patient_code} ({p.priority[0]})", name=p.name, priority=p.priority, status=p.status, color=color, id=p.id)
            
            # Edge: Patient -> Department
            G.add_edge(f"P_{p.id}", f"D_{p.department_id}", weight=(4 - p.priority_level), type="patient_dept")
            
            # If allocated, edge Patient -> Bed directly
            active_alloc = Allocation.query.filter_by(patient_id=p.id, allocation_status='Active').first()
            if active_alloc:
                G.add_edge(f"P_{p.id}", f"B_{active_alloc.bed_id}", weight=10.0, type="allocated")

        return G

    @staticmethod
    def get_network_graph_data():

        G = GraphTheoryEngine.build_allocation_graph()
        nodes = []
        edges = []

        for n, attrs in G.nodes(data=True):
            node_item = {
                'id': n,
                'label': attrs.get('label', n),
                'group': attrs.get('type'),
                'color': attrs.get('color', '#64748b'),
                'title': f"<b>{attrs.get('type').capitalize()}:</b> {attrs.get('label')}<br>Status: {attrs.get('status', attrs.get('availability', 'N/A'))}"
            }
            if attrs.get('type') == 'patient':
                node_item['shape'] = 'dot'
                node_item['size'] = 22 if attrs.get('priority') == 'Emergency' else 16
            elif attrs.get('type') == 'department':
                node_item['shape'] = 'diamond'
                node_item['size'] = 30
                node_item['color'] = '#0284c7'
            elif attrs.get('type') == 'bed':
                node_item['shape'] = 'square'
                node_item['size'] = 14
            nodes.append(node_item)

        for u, v, attrs in G.edges(data=True):
            edge_type = attrs.get('type')
            edge_item = {
                'from': u,
                'to': v,
                'arrows': 'to',
                'color': {'color': '#10b981' if edge_type == 'allocated' else '#cbd5e1'}
            }
            if edge_type == 'allocated':
                edge_item['width'] = 3
                edge_item['dashes'] = False
            elif edge_type == 'patient_dept':
                edge_item['width'] = 1.5
                edge_item['dashes'] = True
            else:
                edge_item['width'] = 1
            edges.append(edge_item)

        return {'nodes': nodes, 'edges': edges}

    @staticmethod
    def find_bipartite_matching_allocation():

        pending_queue = PriorityQueueEngine.get_priority_queue()
        allocations_made = []

        for patient in pending_queue:

            available_bed = Bed.query.filter_by(
                department_id=patient.department_id, 
                availability='Available'
            ).first()

            # Fallback 1: If patient is Emergency and target department is full, check Emergency department beds
            if not available_bed and patient.priority == 'Emergency':
                emergency_dept = Department.query.filter_by(code='EMG').first()
                if emergency_dept:
                    available_bed = Bed.query.filter_by(
                        department_id=emergency_dept.id,
                        availability='Available'
                    ).first()

            # Fallback 2: General Ward for non-emergency if target dept full
            if not available_bed and patient.priority != 'Emergency':
                gen_dept = Department.query.filter_by(code='GEN').first()
                if gen_dept:
                    available_bed = Bed.query.filter_by(
                        department_id=gen_dept.id,
                        availability='Available'
                    ).first()

            if available_bed:

                patient.status = 'Allocated'
                available_bed.availability = 'Occupied'
                
                new_alloc = Allocation(
                    patient_id=patient.id,
                    bed_id=available_bed.id,
                    allocation_time=datetime.utcnow(),
                    allocation_status='Active'
                )
                db.session.add(new_alloc)

                history_entry = AllocationHistory(
                    patient_code=patient.patient_code,
                    patient_name=patient.name,
                    bed_number=available_bed.bed_number,
                    department_name=available_bed.department.name,
                    action='Allocated',
                    priority=patient.priority,
                    timestamp=datetime.utcnow(),
                    notes=f"Auto-allocated via Graph Priority Matching engine."
                )
                db.session.add(history_entry)
                
                allocations_made.append({
                    'patient_code': patient.patient_code,
                    'patient_name': patient.name,
                    'priority': patient.priority,
                    'bed_number': available_bed.bed_number,
                    'department': available_bed.department.name
                })

        db.session.commit()
        return allocations_made


class SetTheoryEngine:

    @staticmethod
    def get_bed_sets():

        all_beds = Bed.query.all()
        
        all_bed_ids = {b.id for b in all_beds}
        available_set = {b.id for b in all_beds if b.availability == 'Available'}
        occupied_set = {b.id for b in all_beds if b.availability == 'Occupied'}
        maintenance_set = {b.id for b in all_beds if b.availability == 'Maintenance'}

        dept_sets = {}
        for d in Department.query.all():
            dept_beds = {b.id for b in all_beds if b.department_id == d.id}
            dept_sets[d.name] = {
                'total': list(dept_beds),
                'available': list(dept_beds.intersection(available_set)),
                'occupied': list(dept_beds.intersection(occupied_set)),
                'count_total': len(dept_beds),
                'count_available': len(dept_beds.intersection(available_set)),
                'count_occupied': len(dept_beds.intersection(occupied_set))
            }

        return {
            'total_beds_count': len(all_bed_ids),
            'available_beds_count': len(available_set),
            'occupied_beds_count': len(occupied_set),
            'maintenance_beds_count': len(maintenance_set),
            'is_disjoint': available_set.isdisjoint(occupied_set) and available_set.isdisjoint(maintenance_set),
            'is_union_complete': (available_set | occupied_set | maintenance_set) == all_bed_ids,
            'dept_sets': dept_sets
        }


class RelationalAlgebraEngine:

    @staticmethod
    def get_relations_summary():

        patients = Patient.query.all()
        allocations = Allocation.query.filter_by(allocation_status='Active').all()

        patient_to_dept = []
        for p in patients:
            if p.department:
                patient_to_dept.append((p.patient_code, p.department.code))

        dept_to_bed = []
        for b in Bed.query.all():
            if b.department:
                dept_to_bed.append((b.department.code, b.bed_number))

        patient_to_bed = []
        for a in allocations:
            if a.patient and a.bed:
                patient_to_bed.append({
                    'patient_code': a.patient.patient_code,
                    'patient_name': a.patient.name,
                    'department_code': a.bed.department.code if a.bed.department else 'N/A',
                    'bed_number': a.bed.bed_number,
                    'priority': a.patient.priority
                })

        return {
            'patient_dept_relation_count': len(patient_to_dept),
            'dept_bed_relation_count': len(dept_to_bed),
            'patient_bed_relation_count': len(patient_to_bed),
            'active_mappings': patient_to_bed
        }
