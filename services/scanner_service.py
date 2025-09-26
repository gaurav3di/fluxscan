from typing import Dict, List, Any, Optional
from models import Scanner, ScanResult, ScanHistory
from scanners import ScannerEngine, ScannerValidator
from datetime import datetime

class ScannerService:
    def __init__(self, data_service):
        self.data_service = data_service
        self.validator = ScannerValidator()

    def create_scanner(self, name: str, code: str, description: str = None,
                      category: str = 'custom', parameters: Dict = None) -> Scanner:
        # Validate code
        is_valid, errors, warnings = self.validator.validate(code)
        if not is_valid:
            raise ValueError(f"Scanner validation failed: {', '.join(errors)}")

        # Create scanner
        scanner = Scanner(
            name=name,
            code=code,
            description=description,
            category=category,
            is_active=True
        )

        if parameters:
            scanner.set_parameters(parameters)

        scanner.save()
        return scanner

    def update_scanner(self, scanner_id: int, **kwargs) -> Scanner:
        scanner = Scanner.get_by_id(scanner_id)
        if not scanner:
            raise ValueError(f"Scanner {scanner_id} not found")

        # Validate code if provided
        if 'code' in kwargs:
            is_valid, errors, warnings = self.validator.validate(kwargs['code'])
            if not is_valid:
                raise ValueError(f"Scanner validation failed: {', '.join(errors)}")

        # Update fields
        for key, value in kwargs.items():
            if hasattr(scanner, key):
                setattr(scanner, key, value)

        scanner.save()
        return scanner

    def execute_scanner(self, scanner_id: int, watchlist_symbols: List[str],
                       parameters: Dict = None, progress_callback=None) -> Dict[str, Any]:
        scanner = Scanner.get_by_id(scanner_id)
        if not scanner:
            raise ValueError(f"Scanner {scanner_id} not found")

        # Create scanner engine
        engine = ScannerEngine(self.data_service)

        # Merge parameters
        scan_params = scanner.get_parameters()
        if parameters:
            scan_params.update(parameters)

        # Execute scan
        result = engine.execute_scanner(
            scanner.code,
            watchlist_symbols,
            scan_params,
            progress_callback
        )

        return result

    def test_scanner(self, scanner_id: int, test_symbols: List[str] = None) -> Dict[str, Any]:
        if not test_symbols:
            test_symbols = ['RELIANCE', 'TCS', 'INFY']

        scanner = Scanner.get_by_id(scanner_id)
        if not scanner:
            raise ValueError(f"Scanner {scanner_id} not found")

        # Execute with test data
        return self.execute_scanner(scanner_id, test_symbols, scanner.get_parameters())

    def get_scanner_statistics(self, scanner_id: int) -> Dict[str, Any]:
        scanner = Scanner.get_by_id(scanner_id)
        if not scanner:
            return {}

        # Get execution history
        histories = ScanHistory.query.filter_by(scanner_id=scanner_id).all()

        total_scans = len(histories)
        successful_scans = len([h for h in histories if h.status == 'completed'])
        total_signals = sum(h.signals_found or 0 for h in histories)

        # Get recent results
        recent_results = ScanResult.get_by_scanner(scanner_id, limit=100)

        return {
            'total_scans': total_scans,
            'successful_scans': successful_scans,
            'success_rate': (successful_scans / total_scans * 100) if total_scans > 0 else 0,
            'total_signals': total_signals,
            'average_signals_per_scan': total_signals / total_scans if total_scans > 0 else 0,
            'recent_signals': len(recent_results),
            'last_run': histories[-1].started_at if histories else None
        }

    def clone_scanner(self, scanner_id: int, new_name: str) -> Scanner:
        original = Scanner.get_by_id(scanner_id)
        if not original:
            raise ValueError(f"Scanner {scanner_id} not found")

        # Create clone
        clone = Scanner(
            name=new_name,
            description=f"Clone of {original.name}",
            code=original.code,
            category=original.category,
            is_active=True
        )

        if original.parameters:
            clone.parameters = original.parameters

        clone.save()
        return clone