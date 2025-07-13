import uuid
import random
import pandas as pd
from datetime import datetime
# Generating synthetic transaction
def generate_transaction(is_fraud = False):
    return{
        "transaction_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "amount": random.uniform(10,10000) if not is_fraud else random.uniform(10000,20000),
        "merchant_id": random.randint(1000,1100),
        "user_id": random.randint(1,1000),
        "location": random.choice(["NY", "SF", "LDN", "DEL", "TKY"]),
        "device_type": random.choice(["mobile","web","POS"]),
        "transaction_type": random.choice(["debit","credit","transfer"]),
        "is_fraud": int(is_fraud)
    }

def generate_dataset(n_normal=950, n_fraud=50):
    data = [generate_transaction(False) for _ in range(n_normal)] + \
           [generate_transaction(True) for _ in range(n_fraud)]
    
    random.shuffle(data)
    print("generated random data\n")
    return pd.DataFrame(data)