import os
import json
import logging
from app.models.state import ChaosPilotState, RunStatus

logger = logging.getLogger(__name__)

REPORT_TEMPLATE = """# ChaosPilot Bug & Execution Report Summary
**Target URL**: {target_url}  
**Run ID**: `{run_id}`  
**Final Status**: `{status}`  
**Total Routes Mapped**: {routes_count}  
**Total Tests Executed**: {tests_count}  
**Confirmed Application Bugs**: {bugs_count}  
**Execution Issues / Blocked Tests**: {exec_issues_count}  

---

## Discovered Application Bugs

{bugs_section}

---

## Execution & Infrastructure Issues

{issues_section}

---

## SiteMap Overview
{sitemap_section}
"""

async def reporter_node(state: ChaosPilotState) -> ChaosPilotState:
    """
    Reporter Node (Report Generator Agent):
    Calculates final accurate RunStatus and generates structured Markdown and JSON reports.
    """
    state.logs.append("📝 [ReportGeneratorAgent] Calculating final run status and generating reports...")
    logger.info(f"ReportGeneratorAgent running for run {state.run_id}")

    output_dir = f"./artifacts/{state.run_id}"
    os.makedirs(output_dir, exist_ok=True)

    # Calculate final status accurately
    if not state.target_reachable or state.status == RunStatus.TARGET_UNAVAILABLE:
        state.status = RunStatus.TARGET_UNAVAILABLE
    elif state.status == RunStatus.FAILED:
        state.status = RunStatus.EXECUTION_FAILED
    elif state.discovered_bugs:
        state.status = RunStatus.COMPLETED_WITH_BUGS
    elif state.execution_issues:
        state.status = RunStatus.COMPLETED_WITH_BLOCKED_TESTS
    else:
        state.status = RunStatus.COMPLETED

    bugs_formatted = []
    if state.discovered_bugs:
        for bug in state.discovered_bugs:
            bugs_formatted.append(f"""### {bug.id}: {bug.title}
- **Severity**: `{bug.severity.value}`
- **Route**: `{bug.route}`
- **Description**: {bug.description}
- **Reproduction Steps**:
{"\n".join([f"  1. {s}" for s in bug.reproduction_steps])}
- **Reproduction Script**: `{bug.reproduction_script_path}`
- **Screenshot Artifact**: `{bug.screenshot_path}`
""")
    else:
        bugs_formatted.append("🎉 *No application bugs detected during this run.*")

    issues_formatted = []
    if state.execution_issues:
        for issue in state.execution_issues:
            issues_formatted.append(f"""### {issue.id}: {issue.title}
- **Target URL**: `{issue.target_url}`
- **Reason**: {issue.reason}
- **Blocked Tests**: {issue.blocked_tests_count}
""")
    else:
        issues_formatted.append("✨ *No infrastructure or navigation timeouts recorded.*")

    sitemap_list = []
    for url, node in state.site_map.items():
        sitemap_list.append(f"- [{node.title or url}]({url}) — {len(node.forms)} forms mapped")

    markdown_report = REPORT_TEMPLATE.format(
        target_url=state.target_url,
        run_id=state.run_id,
        status=state.status.value,
        routes_count=len(state.site_map),
        tests_count=len(state.test_plan),
        bugs_count=len(state.discovered_bugs),
        exec_issues_count=len(state.execution_issues),
        bugs_section="\n\n".join(bugs_formatted),
        issues_section="\n\n".join(issues_formatted),
        sitemap_section="\n".join(sitemap_list) if sitemap_list else "None"
    )

    # Save Markdown report
    report_md_path = os.path.join(output_dir, "BUG_REPORT.md")
    with open(report_md_path, "w", encoding="utf-8") as f:
        f.write(markdown_report)

    # Save JSON state report
    report_json_path = os.path.join(output_dir, "state_report.json")
    with open(report_json_path, "w", encoding="utf-8") as f:
        f.write(state.model_dump_json(indent=2))

    state.logs.append(f"🎉 [ReportGeneratorAgent] Report complete! Final Status: {state.status.value}. Artifacts saved to {report_md_path}")
    return state
