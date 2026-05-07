# vendors.py
# Dummy vendor database for each port and part
vendors = {
    'MUMBAI': [
        {'name': 'Marine Parts Co.', 'part': 'Engine Gasket', 'price': 5000, 'stock': True},
        {'name': 'Ship Spares Ltd.', 'part': 'Engine Gasket', 'price': 4800, 'stock': True},
        {'name': 'Mumbai Fuel Systems', 'part': 'Fuel Pump', 'price': 12000, 'stock': True},
        {'name': 'Mumbai Light House', 'part': 'Navigation Light', 'price': 2200, 'stock': True}
    ],
    'CHENNAI': [
        {'name': 'Chennai Marine', 'part': 'Engine Gasket', 'price': 5200, 'stock': True},
        {'name': 'SS Marine', 'part': 'Engine Gasket', 'price': 4900, 'stock': False},
        {'name': 'Chennai Ship Chandlers', 'part': 'Fuel Pump', 'price': 11000, 'stock': True}
    ],
    'KANDLA': [
        {'name': 'Kandla Ship Chandlers', 'part': 'Engine Gasket', 'price': 4500, 'stock': True},
        {'name': 'Kandla Pumps', 'part': 'Fuel Pump', 'price': 10500, 'stock': True}
    ],
    'KOCHI': [
        {'name': 'Kochi Marine Services', 'part': 'Engine Gasket', 'price': 5100, 'stock': True},
        {'name': 'Kerala Shipcare', 'part': 'Navigation Light', 'price': 2400, 'stock': True}
    ],
    'VISAKHAPATNAM': [
        {'name': 'Vizag Ship Spares', 'part': 'Fuel Pump', 'price': 11500, 'stock': True}
    ],
    'MANGALORE': [
        {'name': 'Mangalore Marine', 'part': 'Engine Gasket', 'price': 4700, 'stock': True}
    ],
    'KOLKATA': [
        {'name': 'Calcutta Dockyard', 'part': 'Engine Gasket', 'price': 5300, 'stock': True}
    ],
    'GOA': [
        {'name': 'Goa Ship Chandlers', 'part': 'Navigation Light', 'price': 2500, 'stock': True}
    ]
}

def get_vendors_for_port(port_name, part_name):
    """
    Returns list of vendors (with stock=True) for a given port and part.
    Search is case-insensitive.
    """
    port_vendors = vendors.get(port_name.upper(), [])  # port name uppercase match
    part_lower = part_name.lower()
    return [v for v in port_vendors if v['part'].lower() == part_lower and v['stock']]
