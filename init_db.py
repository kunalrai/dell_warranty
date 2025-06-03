from app import db, Asset
from datetime import datetime, timedelta
import random

# Sample data
models = ['Dell Latitude 5420', 'Dell Precision 5550', 'Dell OptiPlex 7070', 'Dell XPS 13', 'Dell Precision 3660']
warranty_types = ['ProSupport Plus', 'ProSupport', 'Basic Hardware Service', 'Premium Support']
service_levels = ['Next Business Day', 'Same Day', '4 Hour Response', 'Keep Your Hard Drive']
locations = ['New York', 'San Francisco', 'Chicago', 'Austin', 'Seattle']

def generate_service_tag():
    """Generate a random Dell service tag."""
    chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    return ''.join(random.choices(chars, k=7))

def generate_sample_data():
    """Generate sample warranty data."""
    # Clear existing data
    db.drop_all()
    db.create_all()
    
    # Generate 100 sample assets
    for _ in range(100):
        start_date = datetime.now() - timedelta(days=random.randint(0, 730))  # Up to 2 years ago
        duration = random.choice([365, 730, 1095])  # 1, 2, or 3 year warranty
        end_date = start_date + timedelta(days=duration)
        
        asset = Asset(
            service_tag=generate_service_tag(),
            model=random.choice(models),
            warranty_type=random.choice(warranty_types),
            warranty_start=start_date,
            warranty_end=end_date,
            service_level=random.choice(service_levels),
            location=random.choice(locations),
            cost=random.uniform(800, 2500)
        )
        db.session.add(asset)
    
    db.session.commit()

if __name__ == '__main__':
    generate_sample_data()
    print("Sample data generated successfully!")
