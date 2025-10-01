from http.server import BaseHTTPRequestHandler
import json

# Embedded telemetry data
TELEMETRY_DATA = [{"region":"apac","service":"checkout","latency_ms":222.81,"uptime_pct":97.728,"timestamp":20250301},{"region":"apac","service":"support","latency_ms":144.2,"uptime_pct":99.283,"timestamp":20250302},{"region":"apac","service":"catalog","latency_ms":194.04,"uptime_pct":97.357,"timestamp":20250303},{"region":"apac","service":"catalog","latency_ms":140.25,"uptime_pct":98.887,"timestamp":20250304},{"region":"apac","service":"recommendations","latency_ms":129.1,"uptime_pct":98.783,"timestamp":20250305},{"region":"apac","service":"checkout","latency_ms":181.91,"uptime_pct":97.72,"timestamp":20250306},{"region":"apac","service":"payments","latency_ms":218.04,"uptime_pct":97.511,"timestamp":20250307},{"region":"apac","service":"support","latency_ms":161.74,"uptime_pct":98.452,"timestamp":20250308},{"region":"apac","service":"payments","latency_ms":219.86,"uptime_pct":98.609,"timestamp":20250309},{"region":"apac","service":"analytics","latency_ms":162.1,"uptime_pct":97.802,"timestamp":20250310},{"region":"apac","service":"catalog","latency_ms":172.95,"uptime_pct":99.432,"timestamp":20250311},{"region":"apac","service":"analytics","latency_ms":214.36,"uptime_pct":97.432,"timestamp":20250312},{"region":"emea","service":"payments","latency_ms":166.72,"uptime_pct":98.22,"timestamp":20250301},{"region":"emea","service":"payments","latency_ms":211.69,"uptime_pct":99.137,"timestamp":20250302},{"region":"emea","service":"support","latency_ms":216.79,"uptime_pct":98.775,"timestamp":20250303},{"region":"emea","service":"support","latency_ms":203.64,"uptime_pct":98.918,"timestamp":20250304},{"region":"emea","service":"checkout","latency_ms":194.79,"uptime_pct":98.375,"timestamp":20250305},{"region":"emea","service":"catalog","latency_ms":131.75,"uptime_pct":99.351,"timestamp":20250306},{"region":"emea","service":"checkout","latency_ms":128.8,"uptime_pct":98.397,"timestamp":20250307},{"region":"emea","service":"recommendations","latency_ms":222.15,"uptime_pct":97.589,"timestamp":20250308},{"region":"emea","service":"recommendations","latency_ms":224.38,"uptime_pct":98.129,"timestamp":20250309},{"region":"emea","service":"recommendations","latency_ms":150.01,"uptime_pct":99.199,"timestamp":20250310},{"region":"emea","service":"analytics","latency_ms":146.37,"uptime_pct":97.77,"timestamp":20250311},{"region":"emea","service":"catalog","latency_ms":163.99,"uptime_pct":98.849,"timestamp":20250312},{"region":"amer","service":"recommendations","latency_ms":127.43,"uptime_pct":97.503,"timestamp":20250301},{"region":"amer","service":"payments","latency_ms":199.65,"uptime_pct":98.623,"timestamp":20250302},{"region":"amer","service":"payments","latency_ms":231.09,"uptime_pct":98.399,"timestamp":20250303},{"region":"amer","service":"analytics","latency_ms":210.59,"uptime_pct":98.44,"timestamp":20250304},{"region":"amer","service":"analytics","latency_ms":200.28,"uptime_pct":98.966,"timestamp":20250305},{"region":"amer","service":"analytics","latency_ms":169.44,"uptime_pct":97.459,"timestamp":20250306},{"region":"amer","service":"catalog","latency_ms":125.88,"uptime_pct":97.401,"timestamp":20250307},{"region":"amer","service":"recommendations","latency_ms":210.5,"uptime_pct":97.113,"timestamp":20250308},{"region":"amer","service":"checkout","latency_ms":130.4,"uptime_pct":97.401,"timestamp":20250309},{"region":"amer","service":"catalog","latency_ms":177.2,"uptime_pct":98.175,"timestamp":20250310},{"region":"amer","service":"support","latency_ms":212.25,"uptime_pct":97.907,"timestamp":20250311},{"region":"amer","service":"recommendations","latency_ms":166.12,"uptime_pct":97.318,"timestamp":20250312}]

def percentile(data, p):
    """Calculate percentile without numpy"""
    sorted_data = sorted(data)
    n = len(sorted_data)
    idx = (p / 100) * (n - 1)
    
    if idx.is_integer():
        return sorted_data[int(idx)]
    
    lower = int(idx)
    fraction = idx - lower
    return sorted_data[lower] + fraction * (sorted_data[lower + 1] - sorted_data[lower])

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Enable CORS
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        # Parse request body
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        data = json.loads(body)
        
        regions = data.get('regions', [])
        threshold_ms = data.get('threshold_ms', 0)
        
        results = {"regions": []}
        
        for region in regions:
            # Filter data for this region
            region_data = [item for item in TELEMETRY_DATA if item['region'] == region]
            
            if not region_data:
                continue
            
            # Extract metrics
            latencies = [item['latency_ms'] for item in region_data]
            uptimes = [item['uptime_pct'] for item in region_data]
            
            # Calculate statistics
            avg_latency = sum(latencies) / len(latencies)
            p95_latency = percentile(latencies, 95)
            avg_uptime = sum(uptimes) / len(uptimes)
            breaches = sum(1 for lat in latencies if lat > threshold_ms)
            
            results["regions"].append({
                "region": region,
                "avg_latency": round(avg_latency, 2),
                "p95_latency": round(p95_latency, 2),
                "avg_uptime": round(avg_uptime, 3),
                "breaches": breaches
            })
        
        # Return JSON response
        self.wfile.write(json.dumps(results).encode())
        
    def do_OPTIONS(self):
        # Handle preflight CORS request
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()