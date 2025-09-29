from app import app, db
from models import Scanner, Watchlist, ScanResult, ScanHistory, ScannerTemplate

with app.app_context():
    # Create all tables
    db.create_all()
    print("Database tables created!")
    
    # Add a test scanner
    scanner = Scanner(
        name="Test Scanner",
        description="Always generates signals for testing",
        code='''# Test Scanner - Always generates signals
signal = True
signal_type = 'TEST'
metrics = {'message': 'Test signal', 'price': float(close.iloc[-1]) if len(close) > 0 else 0}''',
        category="test",
        is_active=True
    )
    db.session.add(scanner)
    
    # Add a test watchlist
    watchlist = Watchlist(
        name="Test Watchlist",
        description="Test stocks",
        exchange="NSE"
    )
    watchlist.set_symbols(['SBIN', 'TATASTEEL'])
    db.session.add(watchlist)
    
    db.session.commit()
    print("Test data added!")
