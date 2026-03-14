╔══════════════════════════════════════════════════════════╗
║ VulnForge - Built with Blood by DemonKing369.0 👑        ║
║ GitHub: https://github.com/Arunking9                     ║
║ AI-Powered Security Framework for Bug Bounty Warriors ⚔️║
╚══════════════════════════════════════════════════════════╝

# VulnForge Report

Generated on {{ timestamp }}


## Target Information

- **Domain:** {{ target.domain }}
- **IP:** {{ target.ip }}
- **Scan Time:** {{ target.scan_time }}
- **Duration:** {{ target.duration }}

## Modules

{% for module in modules %}
### {{ module.name }}
- **Status:** {{ module.status }}
- **Start Time:** {{ module.start_time }}
- **End Time:** {{ module.end_time }}
{% if module.findings %}
- **Findings:**
{% for finding in module.findings %}
  - {{ finding }}
{% endfor %}
{% endif %}
{% if module.errors %}
- **Errors:**
{% for error in module.errors %}
  - {{ error }}
{% endfor %}
{% endif %}
{% endfor %}

## Tools Used

{% for tool in tools %}
### {{ tool.name }}
- **Status:** {{ tool.status }}
- **Purpose:** {{ tool.purpose }}
- **Configuration:** {{ tool.config }}
- **Installation Status:** {{ tool.installed }}
{% endfor %}

## Vulnerabilities

{% for vuln in vulnerabilities %}
### {{ vuln.title }}
- **Severity:** {{ vuln.severity }}
- **CVSS Score:** {{ vuln.cvss_score }}
- **Description:** {{ vuln.description }}
- **Location:** {{ vuln.location }}
{% if vuln.references %}
- **References:**
{% for ref in vuln.references %}
  - [{{ ref.title }}]({{ ref.url }})
{% endfor %}
{% endif %}
{% endfor %}

## Exploits

{% for exploit in exploits %}
### {{ exploit.name }}
- **Status:** {{ exploit.status }}
- **Command:** `{{ exploit.command }}`
{% if exploit.output %}
- **Output:**
```
{{ exploit.output }}
```
{% endif %}
{% endfor %}

## Defensive Measures

{% for measure in defensive_measures %}
### {{ measure.name }}
{{ measure.description }}
{% if measure.details %}
```
{{ measure.details }}
```
{% endif %}
{% endfor %}

## Recommendations

{% for rec in recommendations %}
### {{ rec.title }}
{{ rec.description }}
{% if rec.steps %}
Steps:
{% for step in rec.steps %}
1. {{ step }}
{% endfor %}
{% endif %}
{% endfor %}

## Errors

{% for error in errors %}
### {{ error.timestamp }}
{{ error.message }}
{% if error.context %}
```
{{ error.context }}
```
{% endif %}
{% endfor %} 