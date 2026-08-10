import os
import json
import logging
from app.models.state import ChaosPilotState, RunStatus

logger = logging.getLogger(__name__)

REPORT_TEMPLATE = """# ChaosPilot Bug Report Summary
**Target URL**: {target_url}  
**Run ID**: `{run_id}`  
**Status**: {status}  
**Total Routes Mapped**: {routes_count}  
**Total Tests Executed**: {tests_count}  
**Bugs Discovered**: {bugs_count}  

---

## Discovered Bugs

{bugs_section}

---

## SiteMap Overview
{sitemap_section}
"""

async def reporter_node(state: ChaosPilotState) -> ChaosPilotState:
    """
    Reporter Node (Report Generator Agent):
    Generates structured Markdown and JSON reports for the completed test run.
    """
    state.logs.append("📝 [ReportGeneratorAgent] Generating final bug reports and artifacts...")
    logger.info(f"ReportGeneratorAgent running for run {state.run_id}")

    output_dir = f"./artifacts/{state.run_id}"
    os.makedirs(output_dir, exist_ok=True)

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
        bugs_formatted.append("🎉 *No critical bugs or unhandled failures were detected during this run.*")

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
        bugs_section="\n\n".join(bugs_formatted),
        sitemap_section="\n".join(sitemap_list)
    )

    # Save Markdown report
    report_md_path = os.path.join(output_dir, "BUG_REPORT.md")
    with open(report_md_path, "w", encoding="utf-8") as f:
        f.write(markdown_report)

    # Save JSON state report
    report_json_path = os.path.join(output_dir, "state_report.json")
    with open(report_json_path, "w", encoding="utf-8") as f:
        f.write(state.model_dump_json(indent=2))

    state.status = RunStatus.COMPLETED if state.status != RunStatus.FAILED else RunStatus.FAILED
    state.logs.append(f"🎉 [ReportGeneratorAgent] Report complete! Saved to {report_md_path}")
    return state
