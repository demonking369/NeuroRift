import os
import json
import asyncio
import pytest
from pathlib import Path
from datetime import datetime

from ai_controller import AIController
from utils.report_generator import ReportGenerator

class TestAIFeatures:
    """Test suite for AI features."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Setup test environment."""
        self.test_dir = tmp_path / "test_session"
        self.test_dir.mkdir(parents=True)
        
        # Create test config
        self.config_path = self.test_dir / "test_config.json"
        with open(self.config_path, "w") as f:
            json.dump({
                "ai": {
                    "model": "deepseek-coder",
                    "temperature": 0.7,
                    "max_tokens": 1000
                },
                "notifications": {
                    "enabled": False
                }
            }, f)
        
        # Initialize AI controller
        self.ai_controller = AIController(str(self.test_dir), str(self.config_path))
        
        # Initialize report generator
        self.report_generator = ReportGenerator(str(self.test_dir))

    @pytest.mark.asyncio
    async def test_ai_query_processing(self):
        """Test AI query processing."""
        # Test basic query
        query = "What should I do if port 8080 is open?"
        response = await self.ai_controller.process_query(query)
        
        assert "answer" in response
        assert "logs" in response
        assert "prompt" in response
        assert isinstance(response["answer"], str)
        
        # Test query with context
        context = {
            "open_ports": [8080],
            "services": {"8080": "http-alt"},
            "previous_findings": ["Potential web server detected"]
        }
        response = await self.ai_controller.process_query(query, context)
        
        assert "answer" in response
        assert "logs" in response
        assert "prompt" in response
        assert isinstance(response["answer"], str)

    def test_report_generation(self):
        """Test report generation in all formats."""
        # Prepare test data
        context = {
            "target": {
                "domain": "example.com",
                "ip": "93.184.216.34",
                "scan_time": datetime.now().isoformat(),
                "duration": "00:05:23"
            },
            "modules": [
                {
                    "name": "recon",
                    "status": "success",
                    "start_time": "2024-03-20T10:00:00",
                    "end_time": "2024-03-20T10:05:00",
                    "findings": ["Open port 80", "Open port 443"]
                }
            ],
            "tools": {
                "nmap": {
                    "status": "success",
                    "purpose": "Port scanning",
                    "config": "-sS -sV",
                    "installed": True
                }
            },
            "vulnerabilities": [
                {
                    "title": "Test Vulnerability",
                    "severity": "high",
                    "cvss_score": 8.5,
                    "description": "Test vulnerability description",
                    "location": "http://example.com/test",
                    "references": [
                        {
                            "title": "CVE-2024-1234",
                            "url": "https://nvd.nist.gov/vuln/detail/CVE-2024-1234"
                        }
                    ]
                }
            ],
            "exploits": [
                {
                    "name": "Test Exploit",
                    "status": "success",
                    "command": "test_command",
                    "output": "Test output"
                }
            ],
            "defensive_measures": [
                {
                    "name": "WAF Detection",
                    "description": "Web Application Firewall detected",
                    "details": "Cloudflare WAF"
                }
            ],
            "recommendations": [
                {
                    "title": "Test Recommendation",
                    "description": "Test recommendation description",
                    "steps": ["Step 1", "Step 2"]
                }
            ],
            "errors": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "message": "Test error",
                    "context": "Test error context"
                }
            ]
        }
        
        # Generate reports
        report_paths = self.report_generator.generate_reports(context)
        
        # Verify report files exist
        assert "html" in report_paths
        assert "markdown" in report_paths
        assert "json" in report_paths
        
        # Verify HTML report
        html_path = Path(report_paths["html"])
        assert html_path.exists()
        html_content = html_path.read_text()
        assert "VulnForge Report" in html_content
        assert "example.com" in html_content
        
        # Verify Markdown report
        md_path = Path(report_paths["markdown"])
        assert md_path.exists()
        md_content = md_path.read_text()
        assert "# VulnForge Report" in md_content
        assert "example.com" in md_content
        
        # Verify JSON report
        json_path = Path(report_paths["json"])
        assert json_path.exists()
        json_content = json.loads(json_path.read_text())
        assert json_content["target"]["domain"] == "example.com"

    def test_session_data_management(self):
        """Test session data management."""
        # Add test data
        self.ai_controller.session_data["target_domain"] = "example.com"
        self.ai_controller.session_data["target_ip"] = "93.184.216.34"
        self.ai_controller.session_data["modules"].append({
            "name": "test_module",
            "status": "success"
        })
        self.ai_controller.session_data["findings"].append({
            "type": "vulnerability",
            "severity": "high"
        })
        
        # Generate report
        report_paths = self.ai_controller._generate_report()
        
        # Verify report contains session data
        json_path = Path(report_paths["json"])
        json_content = json.loads(json_path.read_text())
        
        assert json_content["target"]["domain"] == "example.com"
        assert json_content["target"]["ip"] == "93.184.216.34"
        assert len(json_content["modules"]) > 0
        assert len(json_content["vulnerabilities"]) > 0

    def test_error_handling(self):
        """Test error handling."""
        # Test invalid query
        with pytest.raises(Exception):
            asyncio.run(self.ai_controller.process_query(None))
        
        # Test invalid context
        with pytest.raises(Exception):
            self.report_generator.generate_reports(None)
        
        # Test invalid session data
        self.ai_controller.session_data = None
        with pytest.raises(Exception):
            self.ai_controller._generate_report()

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 