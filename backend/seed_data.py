import requests
import datetime

BASE = "http://localhost:8000/api"

def seed():
    # Create contacts
    contacts = [
        {"first_name": "Alice", "last_name": "Chen", "email": "alice@techcorp.com", "company": "TechCorp", "city": "San Francisco", "state": "CA", "industry": "Technology"},
        {"first_name": "Bob", "last_name": "Smith", "email": "bob@retailplus.com", "company": "RetailPlus", "city": "New York", "state": "NY", "industry": "Retail"},
        {"first_name": "Carol", "last_name": "Williams", "email": "carol@financehub.com", "company": "FinanceHub", "city": "Chicago", "state": "IL", "industry": "Finance"},
        {"first_name": "David", "last_name": "Lee", "email": "david@startup.io", "company": "StartupIO", "city": "San Francisco", "state": "CA", "industry": "Technology"},
        {"first_name": "Eve", "last_name": "Johnson", "email": "eve@healthfirst.com", "company": "HealthFirst", "city": "Boston", "state": "MA", "industry": "Healthcare"},
    ]
    
    contact_ids = []
    for c in contacts:
        r = requests.post(f"{BASE}/contacts/", json=c)
        if r.status_code == 200:
            contact_ids.append(r.json()["id"])
            print(f"Created contact: {c['first_name']} {c['last_name']}")
        else:
            print(f"Failed to create {c['email']}: {r.text}")
    
    # Add interactions
    interactions = [
        {"contact_id": contact_ids[0], "type": "email", "summary": "Initial outreach - interested in demo", "response_time_hours": 2},
        {"contact_id": contact_ids[0], "type": "call", "summary": "Discovery call went well", "response_time_hours": 1},
        {"contact_id": contact_ids[0], "type": "email", "summary": "Follow-up with pricing", "response_time_hours": 5},
        {"contact_id": contact_ids[1], "type": "email", "summary": "Cold outreach - no response yet"},
        {"contact_id": contact_ids[2], "type": "meeting", "summary": "Quarterly review", "response_time_hours": 0.5},
        {"contact_id": contact_ids[2], "type": "email", "summary": "Contract renewal discussion", "response_time_hours": 3},
        {"contact_id": contact_ids[3], "type": "email", "summary": "Product inquiry", "response_time_hours": 1},
        {"contact_id": contact_ids[4], "type": "call", "summary": "Support call", "response_time_hours": 8},
    ]
    
    for i in interactions:
        r = requests.post(f"{BASE}/contacts/{i['contact_id']}/interactions", json=i)
        if r.status_code == 200:
            print(f"Added interaction for contact {i['contact_id']}")
    
    # Create deals
    deals = [
        {"contact_id": contact_ids[0], "title": "Enterprise License", "value": 50000, "stage": "proposal", "probability": 0.7},
        {"contact_id": contact_ids[2], "title": "Contract Renewal", "value": 120000, "stage": "negotiation", "probability": 0.8},
        {"contact_id": contact_ids[3], "title": "Starter Package", "value": 5000, "stage": "qualified", "probability": 0.4},
        {"contact_id": contact_ids[1], "title": "Retail Expansion", "value": 25000, "stage": "lead", "probability": 0.2},
        {"contact_id": contact_ids[4], "title": "Healthcare Suite", "value": 80000, "stage": "closed_won", "probability": 1.0},
    ]
    
    for d in deals:
        r = requests.post(f"{BASE}/deals/", json=d)
        if r.status_code == 200:
            print(f"Created deal: {d['title']}")
    
    # Create tasks
    tasks = [
        {"contact_id": contact_ids[0], "title": "Send proposal", "priority": "high", "due_date": "2026-08-21T17:00:00"},
        {"contact_id": contact_ids[1], "title": "Follow up on email", "priority": "medium", "due_date": "2026-08-22T17:00:00"},
        {"contact_id": contact_ids[2], "title": "Prepare contract", "priority": "high", "due_date": "2026-08-20T17:00:00"},
        {"contact_id": contact_ids[3], "title": "Schedule demo", "priority": "low"},
    ]
    
    for t in tasks:
        r = requests.post(f"{BASE}/tasks/", json=t)
        if r.status_code == 200:
            print(f"Created task: {t['title']}")
    
    print("\nSeed complete!")

if __name__ == "__main__":
    seed()
