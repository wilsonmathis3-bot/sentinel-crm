import os
from sqlalchemy.orm import Session
from sqlalchemy import text
import re
from typing import Dict, List
from datetime import datetime, timedelta

# Simple pattern-based NLP to SQL converter
# In production, this would use an LLM or more sophisticated parser

def parse_query(query: str) -> Dict:
    """Parse natural language query into structured components"""
    query_lower = query.lower()
    
    result = {
        "entity": "contacts",  # default
        "filters": [],
        "aggregations": [],
        "sort": None,
        "limit": None
    }
    
    # Detect entity (use deal-specific terms, not "lead" which is also a contact type)
    if any(word in query_lower for word in ["deal", "pipeline", "opportunity", "sale", "stage"]):
        result["entity"] = "deals"
    elif any(word in query_lower for word in ["task", "todo", "follow up", "follow-up"]):
        result["entity"] = "tasks"
    
    # Detect city filter
    city_match = re.search(r'in\s+([A-Za-z\s]+?)(?:\s+who|\s+with|\s+that|\s+and|\s+or|$)', query, re.IGNORECASE)
    if city_match:
        result["filters"].append({"field": "city", "op": "=", "value": city_match.group(1).strip()})
    
    # Detect industry filter
    industry_match = re.search(r'(?:in|from)\s+(?:the\s+)?([A-Za-z\s]+?)\s+(?:industry|sector)', query, re.IGNORECASE)
    if industry_match:
        result["filters"].append({"field": "industry", "op": "=", "value": industry_match.group(1).strip()})
    
    # Detect score filters
    if "high score" in query_lower or "hot lead" in query_lower or "best prospect" in query_lower:
        result["filters"].append({"field": "lead_score", "op": ">=", "value": 70})
    elif "low score" in query_lower or "cold lead" in query_lower:
        result["filters"].append({"field": "lead_score", "op": "<=", "value": 30})
    
    # Detect health filters
    if "healthy" in query_lower or "good health" in query_lower:
        result["filters"].append({"field": "health_score", "op": ">=", "value": 70})
    elif "unhealthy" in query_lower or "at risk" in query_lower or "cold" in query_lower:
        result["filters"].append({"field": "health_score", "op": "<=", "value": 40})
    
    # Detect response rate filters
    if "responsive" in query_lower:
        result["filters"].append({"field": "avg_response_time_hours", "op": "<=", "value": 24})
    
    # Detect recency filters
    if "recently" in query_lower or "this week" in query_lower:
        result["filters"].append({"field": "last_contact", "op": ">=", "value": "7_days_ago"})
    elif "not contacted" in query_lower or "no contact" in query_lower or "dormant" in query_lower:
        result["filters"].append({"field": "last_contact", "op": "<=", "value": "30_days_ago"})
    
    # Detect stage filters for deals ONLY
    if result["entity"] == "deals":
        stage_keywords = {
            "lead": "lead",
            "qualified": "qualified",
            "proposal": "proposal",
            "negotiation": "negotiation",
            "won": "closed_won",
            "closed won": "closed_won",
            "lost": "closed_lost",
            "closed lost": "closed_lost"
        }
        for keyword, stage in stage_keywords.items():
            if keyword in query_lower:
                result["filters"].append({"field": "stage", "op": "=", "value": stage})
    
    # Detect aggregations
    if any(word in query_lower for word in ["how many", "count", "number of"]):
        result["aggregations"].append("count")
    if any(word in query_lower for word in ["total", "sum"]):
        result["aggregations"].append("sum")
    if any(word in query_lower for word in ["average", "avg"]):
        result["aggregations"].append("avg")
    
    # Detect sorting
    if "highest" in query_lower or "top" in query_lower or "best" in query_lower:
        result["sort"] = ("lead_score", "DESC")
    elif "lowest" in query_lower or "worst" in query_lower:
        result["sort"] = ("lead_score", "ASC")
    
    # Detect limit
    limit_match = re.search(r'top\s+(\d+)', query, re.IGNORECASE)
    if limit_match:
        result["limit"] = int(limit_match.group(1))
    
    return result

def build_sql(parsed: Dict) -> str:
    """Build SQL query from parsed components"""
    entity = parsed["entity"]
    
    if entity == "contacts":
        select_clause = "SELECT c.*"
        from_clause = "FROM contacts c"
        where_clauses = []
        
        for filt in parsed["filters"]:
            field = filt["field"]
            op = filt["op"]
            value = filt["value"]
            
            if field == "last_contact":
                if value == "7_days_ago":
                    where_clauses.append(f"c.last_contact >= datetime('now', '-7 days')")
                elif value == "30_days_ago":
                    where_clauses.append("(c.last_contact <= datetime('now', '-30 days') OR c.last_contact IS NULL)")
            elif isinstance(value, str):
                where_clauses.append(f"c.{field} {op} '{value}'")
            else:
                where_clauses.append(f"c.{field} {op} {value}")
        
        sql = f"{select_clause} {from_clause}"
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
        
        if parsed["sort"]:
            sql += f" ORDER BY {parsed['sort'][0]} {parsed['sort'][1]}"
        
        if parsed["limit"]:
            sql += f" LIMIT {parsed['limit']}"
        
        return sql
    
    elif entity == "deals":
        select_clause = "SELECT d.*, c.first_name, c.last_name, c.company"
        from_clause = "FROM deals d JOIN contacts c ON d.contact_id = c.id"
        where_clauses = []
        
        for filt in parsed["filters"]:
            field = filt["field"]
            op = filt["op"]
            value = filt["value"]
            
            if field == "stage":
                where_clauses.append(f"d.stage = '{value}'")
            elif field == "city":
                where_clauses.append(f"c.city = '{value}'")
            elif isinstance(value, str):
                where_clauses.append(f"d.{field} {op} '{value}'")
            else:
                where_clauses.append(f"d.{field} {op} {value}")
        
        sql = f"{select_clause} {from_clause}"
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
        
        return sql
    
    elif entity == "tasks":
        select_clause = "SELECT t.*, c.first_name, c.last_name"
        from_clause = "FROM tasks t JOIN contacts c ON t.contact_id = c.id"
        where_clauses = ["t.status != 'done'"]
        
        for filt in parsed["filters"]:
            field = filt["field"]
            op = filt["op"]
            value = filt["value"]
            
            if field == "city":
                where_clauses.append(f"c.city = '{value}'")
            elif isinstance(value, str):
                where_clauses.append(f"t.{field} {op} '{value}'")
            else:
                where_clauses.append(f"t.{field} {op} {value}")
        
        sql = f"{select_clause} {from_clause}"
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
        
        return sql
    
    return "SELECT * FROM contacts LIMIT 10"

def process_natural_language_query(db: Session, query: str) -> Dict:
    """Process a natural language query and return results"""
    parsed = parse_query(query)
    sql = build_sql(parsed)
    
    try:
        result = db.execute(text(sql))
        rows = [dict(row._mapping) for row in result]
        
        # Generate summary
        entity = parsed["entity"]
        count = len(rows)
        
        if count == 0:
            summary = f"No {entity} found matching your criteria."
        elif count == 1:
            summary = f"Found 1 {entity[:-1] if entity.endswith('s') else entity} matching your criteria."
        else:
            summary = f"Found {count} {entity} matching your criteria."
        
        # Add context to summary
        if parsed["filters"]:
            filter_desc = []
            for f in parsed["filters"]:
                if f["field"] == "city":
                    filter_desc.append(f"in {f['value']}")
                elif f["field"] == "industry":
                    filter_desc.append(f"in {f['value']} industry")
                elif f["field"] == "lead_score":
                    filter_desc.append(f"with lead score {f['op']} {f['value']}")
                elif f["field"] == "health_score":
                    filter_desc.append(f"with health score {f['op']} {f['value']}")
            
            if filter_desc:
                summary += f" Filters applied: {', '.join(filter_desc)}."
        
        return {
            "sql": sql if os.getenv("DEBUG_SQL") == "true" else "(hidden)",
            "results": rows,
            "summary": summary
        }
    
    except Exception as e:
        return {
            "sql": "(hidden)",
            "results": [],
            "summary": "That query couldn't be executed. Try rephrasing your question."
        }
